package tonebridge

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	// WebSocket message types
	MessageTypeTransform     = "transform"
	MessageTypeAnalyze       = "analyze"
	MessageTypeAutoTransform = "auto_transform"
	MessageTypeSubscribe     = "subscribe"
	MessageTypeUnsubscribe   = "unsubscribe"
	MessageTypePing          = "ping"
	MessageTypePong          = "pong"
	MessageTypeError         = "error"
	MessageTypeEvent         = "event"

	// Default WebSocket settings
	defaultPingInterval   = 30 * time.Second
	defaultPongTimeout    = 10 * time.Second
	defaultReconnectDelay = 5 * time.Second
	defaultMaxReconnects  = 10
	writeTimeout          = 10 * time.Second
)

// WebSocketClient handles WebSocket connections
type WebSocketClient struct {
	url            string
	token          string
	conn           *websocket.Conn
	mu             sync.RWMutex
	connected      bool
	reconnecting   bool
	reconnectCount int
	maxReconnects  int
	reconnectDelay time.Duration

	// Channels
	send      chan []byte
	receive   chan *WebSocketMessage
	done      chan struct{}
	reconnect chan struct{}

	// Callbacks
	onConnect    func()
	onDisconnect func()
	onMessage    func(interface{})
	onError      func(error)

	// Subscriptions
	subscriptions map[string]bool
	subMu         sync.RWMutex

	// Context for cancellation
	ctx    context.Context
	cancel context.CancelFunc
}

// WebSocketOption is a function that configures the WebSocket client
type WebSocketOption func(*WebSocketClient)

// NewWebSocketClient creates a new WebSocket client
func NewWebSocketClient(url, token string, opts ...WebSocketOption) *WebSocketClient {
	ctx, cancel := context.WithCancel(context.Background())

	client := &WebSocketClient{
		url:            url,
		token:          token,
		maxReconnects:  defaultMaxReconnects,
		reconnectDelay: defaultReconnectDelay,
		send:           make(chan []byte, 256),
		receive:        make(chan *WebSocketMessage, 256),
		done:           make(chan struct{}),
		reconnect:      make(chan struct{}, 1),
		subscriptions:  make(map[string]bool),
		ctx:            ctx,
		cancel:         cancel,
	}

	// Apply options
	for _, opt := range opts {
		opt(client)
	}

	return client
}

// WithWSCallbacks sets WebSocket callbacks
func WithWSCallbacks(onConnect, onDisconnect func(), onMessage func(interface{}), onError func(error)) WebSocketOption {
	return func(c *WebSocketClient) {
		c.onConnect = onConnect
		c.onDisconnect = onDisconnect
		c.onMessage = onMessage
		c.onError = onError
	}
}

// WithMaxReconnects sets the maximum reconnect attempts
func WithMaxReconnects(max int) WebSocketOption {
	return func(c *WebSocketClient) {
		c.maxReconnects = max
	}
}

// WithReconnectDelay sets the reconnect delay
func WithReconnectDelay(delay time.Duration) WebSocketOption {
	return func(c *WebSocketClient) {
		c.reconnectDelay = delay
	}
}

// Connect establishes WebSocket connection
func (c *WebSocketClient) Connect() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.connected {
		return nil
	}

	headers := http.Header{}
	if c.token != "" {
		headers.Add("Authorization", "Bearer "+c.token)
	}

	dialer := websocket.Dialer{
		HandshakeTimeout: 10 * time.Second,
	}

	conn, _, err := dialer.Dial(c.url, headers)
	if err != nil {
		c.handleError(fmt.Errorf("websocket dial error: %w", err))
		return err
	}

	c.conn = conn
	c.connected = true
	c.reconnectCount = 0

	// Set up ping/pong handlers
	c.conn.SetReadDeadline(time.Now().Add(defaultPongTimeout + defaultPingInterval))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(defaultPongTimeout + defaultPingInterval))
		return nil
	})

	// Start goroutines
	go c.readPump()
	go c.writePump()
	go c.pingLoop()

	// Resubscribe to previous subscriptions
	c.resubscribe()

	// Call onConnect callback
	if c.onConnect != nil {
		c.onConnect()
	}

	return nil
}

// Disconnect closes the WebSocket connection
func (c *WebSocketClient) Disconnect() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if !c.connected {
		return
	}

	c.connected = false
	c.cancel()
	close(c.done)

	if c.conn != nil {
		c.conn.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
		c.conn.Close()
	}

	// Call onDisconnect callback
	if c.onDisconnect != nil {
		c.onDisconnect()
	}
}

// IsConnected returns connection status
func (c *WebSocketClient) IsConnected() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.connected
}

// Send sends a message through WebSocket
func (c *WebSocketClient) Send(message interface{}) error {
	if !c.IsConnected() {
		return ErrNoConnection
	}

	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	select {
	case c.send <- data:
		return nil
	case <-time.After(writeTimeout):
		return fmt.Errorf("send timeout")
	}
}

// Subscribe subscribes to a channel or event
func (c *WebSocketClient) Subscribe(channel string) error {
	c.subMu.Lock()
	c.subscriptions[channel] = true
	c.subMu.Unlock()

	msg := map[string]interface{}{
		"type":    MessageTypeSubscribe,
		"channel": channel,
	}

	return c.Send(msg)
}

// Unsubscribe unsubscribes from a channel or event
func (c *WebSocketClient) Unsubscribe(channel string) error {
	c.subMu.Lock()
	delete(c.subscriptions, channel)
	c.subMu.Unlock()

	msg := map[string]interface{}{
		"type":    MessageTypeUnsubscribe,
		"channel": channel,
	}

	return c.Send(msg)
}

// TransformRealtime performs real-time transformation
func (c *WebSocketClient) TransformRealtime(req *TransformRequest, callback func(*TransformResponse, error)) error {
	if !c.IsConnected() {
		return ErrNoConnection
	}

	msgID := generateMessageID()
	msg := map[string]interface{}{
		"type": MessageTypeTransform,
		"id":   msgID,
		"data": req,
	}

	// Register callback for response
	c.registerCallback(msgID, func(data interface{}) {
		resp, ok := data.(*TransformResponse)
		if !ok {
			callback(nil, fmt.Errorf("invalid response type"))
			return
		}
		callback(resp, nil)
	})

	return c.Send(msg)
}

// AnalyzeRealtime performs real-time analysis
func (c *WebSocketClient) AnalyzeRealtime(req *AnalyzeRequest, callback func(*AnalyzeResponse, error)) error {
	if !c.IsConnected() {
		return ErrNoConnection
	}

	msgID := generateMessageID()
	msg := map[string]interface{}{
		"type": MessageTypeAnalyze,
		"id":   msgID,
		"data": req,
	}

	// Register callback for response
	c.registerCallback(msgID, func(data interface{}) {
		resp, ok := data.(*AnalyzeResponse)
		if !ok {
			callback(nil, fmt.Errorf("invalid response type"))
			return
		}
		callback(resp, nil)
	})

	return c.Send(msg)
}

// AutoTransformRealtime performs real-time auto-transformation
func (c *WebSocketClient) AutoTransformRealtime(ctx *MessageContext, callback func(*AutoTransformResponse, error)) error {
	if !c.IsConnected() {
		return ErrNoConnection
	}

	msgID := generateMessageID()
	msg := map[string]interface{}{
		"type": MessageTypeAutoTransform,
		"id":   msgID,
		"data": ctx,
	}

	// Register callback for response
	c.registerCallback(msgID, func(data interface{}) {
		resp, ok := data.(*AutoTransformResponse)
		if !ok {
			callback(nil, fmt.Errorf("invalid response type"))
			return
		}
		callback(resp, nil)
	})

	return c.Send(msg)
}

// readPump reads messages from WebSocket
func (c *WebSocketClient) readPump() {
	defer func() {
		c.mu.Lock()
		c.connected = false
		c.mu.Unlock()
		c.conn.Close()
		c.tryReconnect()
	}()

	for {
		select {
		case <-c.done:
			return
		default:
			var msg WebSocketMessage
			err := c.conn.ReadJSON(&msg)
			if err != nil {
				if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
					c.handleError(fmt.Errorf("websocket read error: %w", err))
				}
				return
			}

			// Handle message
			c.handleMessage(&msg)
		}
	}
}

// writePump writes messages to WebSocket
func (c *WebSocketClient) writePump() {
	ticker := time.NewTicker(defaultPingInterval)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				c.handleError(fmt.Errorf("websocket write error: %w", err))
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}

		case <-c.done:
			return
		}
	}
}

// pingLoop sends periodic ping messages
func (c *WebSocketClient) pingLoop() {
	ticker := time.NewTicker(defaultPingInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			msg := map[string]interface{}{
				"type": MessageTypePing,
			}
			if err := c.Send(msg); err != nil {
				c.handleError(fmt.Errorf("ping error: %w", err))
			}

		case <-c.done:
			return
		}
	}
}

// handleMessage processes incoming messages
func (c *WebSocketClient) handleMessage(msg *WebSocketMessage) {
	switch msg.Type {
	case MessageTypePong:
		// Pong received, connection is alive

	case MessageTypeError:
		if c.onError != nil {
			c.onError(fmt.Errorf("server error: %v", msg.Data))
		}

	case MessageTypeEvent:
		if c.onMessage != nil {
			c.onMessage(msg.Data)
		}

	default:
		// Check for registered callbacks
		if callback := c.getCallback(msg.ID); callback != nil {
			callback(msg.Data)
			c.removeCallback(msg.ID)
		} else if c.onMessage != nil {
			c.onMessage(msg)
		}
	}
}

// handleError handles errors
func (c *WebSocketClient) handleError(err error) {
	if c.onError != nil {
		c.onError(err)
	}
}

// tryReconnect attempts to reconnect
func (c *WebSocketClient) tryReconnect() {
	c.mu.Lock()
	if c.reconnecting || c.reconnectCount >= c.maxReconnects {
		c.mu.Unlock()
		return
	}
	c.reconnecting = true
	c.reconnectCount++
	c.mu.Unlock()

	time.Sleep(c.reconnectDelay)

	if err := c.Connect(); err != nil {
		c.mu.Lock()
		c.reconnecting = false
		c.mu.Unlock()
		c.tryReconnect()
	} else {
		c.mu.Lock()
		c.reconnecting = false
		c.mu.Unlock()
	}
}

// resubscribe resubscribes to previous subscriptions
func (c *WebSocketClient) resubscribe() {
	c.subMu.RLock()
	channels := make([]string, 0, len(c.subscriptions))
	for channel := range c.subscriptions {
		channels = append(channels, channel)
	}
	c.subMu.RUnlock()

	for _, channel := range channels {
		msg := map[string]interface{}{
			"type":    MessageTypeSubscribe,
			"channel": channel,
		}
		c.Send(msg)
	}
}

// Callback management
var (
	callbacks   = make(map[string]func(interface{}))
	callbacksMu sync.RWMutex
)

func registerCallback(id string, callback func(interface{})) {
	callbacksMu.Lock()
	defer callbacksMu.Unlock()
	callbacks[id] = callback
}

func (c *WebSocketClient) registerCallback(id string, callback func(interface{})) {
	registerCallback(id, callback)
}

func getCallback(id string) func(interface{}) {
	callbacksMu.RLock()
	defer callbacksMu.RUnlock()
	return callbacks[id]
}

func (c *WebSocketClient) getCallback(id string) func(interface{}) {
	return getCallback(id)
}

func removeCallback(id string) {
	callbacksMu.Lock()
	defer callbacksMu.Unlock()
	delete(callbacks, id)
}

func (c *WebSocketClient) removeCallback(id string) {
	removeCallback(id)
}

// generateMessageID generates a unique message ID
func generateMessageID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}