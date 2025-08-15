// Package tonebridge provides a Go SDK for the ToneBridge API
package tonebridge

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/go-resty/resty/v2"
)

const (
	// DefaultBaseURL is the default API base URL
	DefaultBaseURL = "https://api.tonebridge.io/api/v1"
	// DefaultTimeout is the default request timeout
	DefaultTimeout = 30 * time.Second
	// DefaultMaxRetries is the default maximum retry attempts
	DefaultMaxRetries = 3
	// SDKVersion is the SDK version
	SDKVersion = "1.0.0"
)

// Client is the main ToneBridge client
type Client struct {
	apiKey       string
	baseURL      string
	timeout      time.Duration
	maxRetries   int
	httpClient   *resty.Client
	accessToken  string
	refreshToken string

	// Services
	Transform     *TransformService
	Analyze       *AnalyzeService
	AutoTransform *AutoTransformService
	WebSocket     *WebSocketClient

	// Callbacks
	onConnect    func()
	onDisconnect func()
	onMessage    func(interface{})
	onError      func(error)
}

// ClientOption is a function that configures the client
type ClientOption func(*Client)

// NewClient creates a new ToneBridge client
func NewClient(apiKey string, opts ...ClientOption) *Client {
	client := &Client{
		apiKey:     apiKey,
		baseURL:    DefaultBaseURL,
		timeout:    DefaultTimeout,
		maxRetries: DefaultMaxRetries,
	}

	// Apply options
	for _, opt := range opts {
		opt(client)
	}

	// Initialize HTTP client
	client.httpClient = resty.New().
		SetBaseURL(client.baseURL).
		SetTimeout(client.timeout).
		SetRetryCount(client.maxRetries).
		SetRetryWaitTime(1 * time.Second).
		SetRetryMaxWaitTime(10 * time.Second).
		SetHeader("Content-Type", "application/json").
		SetHeader("User-Agent", fmt.Sprintf("ToneBridge-Go-SDK/%s", SDKVersion))

	// Set authentication
	if client.apiKey != "" {
		client.httpClient.SetHeader("X-API-Key", client.apiKey)
	}

	// Add request middleware
	client.httpClient.OnBeforeRequest(func(c *resty.Client, r *resty.Request) error {
		if client.accessToken != "" {
			r.SetHeader("Authorization", "Bearer "+client.accessToken)
		}
		return nil
	})

	// Add response middleware for error handling
	client.httpClient.OnAfterResponse(func(c *resty.Client, r *resty.Response) error {
		if r.StatusCode() == http.StatusUnauthorized && client.refreshToken != "" {
			// Try to refresh token
			if err := client.RefreshAuth(context.Background()); err == nil {
				// Retry request with new token
				r.Request.SetHeader("Authorization", "Bearer "+client.accessToken)
				_, err := c.R().
					SetHeaders(r.Request.Header).
					SetBody(r.Request.Body).
					Execute(r.Request.Method, r.Request.URL)
				return err
			}
		}
		return nil
	})

	// Initialize services
	client.Transform = &TransformService{client: client}
	client.Analyze = &AnalyzeService{client: client}
	client.AutoTransform = &AutoTransformService{client: client}

	return client
}

// WithBaseURL sets the base URL
func WithBaseURL(url string) ClientOption {
	return func(c *Client) {
		c.baseURL = url
	}
}

// WithTimeout sets the request timeout
func WithTimeout(timeout time.Duration) ClientOption {
	return func(c *Client) {
		c.timeout = timeout
	}
}

// WithMaxRetries sets the maximum retry attempts
func WithMaxRetries(retries int) ClientOption {
	return func(c *Client) {
		c.maxRetries = retries
	}
}

// WithWebSocket enables WebSocket connection
func WithWebSocket(onConnect, onDisconnect func(), onMessage func(interface{}), onError func(error)) ClientOption {
	return func(c *Client) {
		c.onConnect = onConnect
		c.onDisconnect = onDisconnect
		c.onMessage = onMessage
		c.onError = onError
		// WebSocket will be initialized after client creation
	}
}

// AuthRequest represents an authentication request
type AuthRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// AuthResponse represents an authentication response
type AuthResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	User         *User  `json:"user"`
}

// User represents user information
type User struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      string    `json:"role"`
	TenantID  string    `json:"tenant_id,omitempty"`
	CreatedAt time.Time `json:"created_at,omitempty"`
	UpdatedAt time.Time `json:"updated_at,omitempty"`
}

// Authenticate authenticates with email and password
func (c *Client) Authenticate(ctx context.Context, email, password string) (*AuthResponse, error) {
	var result AuthResponse
	resp, err := c.httpClient.R().
		SetContext(ctx).
		SetBody(AuthRequest{Email: email, Password: password}).
		SetResult(&result).
		Post("/auth/login")

	if err != nil {
		return nil, err
	}

	if resp.IsError() {
		return nil, c.parseError(resp)
	}

	c.accessToken = result.AccessToken
	c.refreshToken = result.RefreshToken

	// Initialize WebSocket if configured
	if c.onConnect != nil || c.onDisconnect != nil || c.onMessage != nil || c.onError != nil {
		c.initWebSocket()
	}

	return &result, nil
}

// SetAPIKey sets the API key
func (c *Client) SetAPIKey(apiKey string) {
	c.apiKey = apiKey
	c.httpClient.SetHeader("X-API-Key", apiKey)
}

// SetAccessToken sets the access token directly
func (c *Client) SetAccessToken(token string) {
	c.accessToken = token
	
	// Reinitialize WebSocket if configured
	if c.WebSocket != nil {
		c.initWebSocket()
	}
}

// RefreshAuth refreshes the authentication token
func (c *Client) RefreshAuth(ctx context.Context) error {
	if c.refreshToken == "" {
		return ErrNoRefreshToken
	}

	var result AuthResponse
	resp, err := c.httpClient.R().
		SetContext(ctx).
		SetBody(map[string]string{"refresh_token": c.refreshToken}).
		SetResult(&result).
		Post("/auth/refresh")

	if err != nil {
		return err
	}

	if resp.IsError() {
		return c.parseError(resp)
	}

	c.accessToken = result.AccessToken
	c.refreshToken = result.RefreshToken

	return nil
}

// GetProfile gets the current user profile
func (c *Client) GetProfile(ctx context.Context) (*User, error) {
	var result User
	resp, err := c.httpClient.R().
		SetContext(ctx).
		SetResult(&result).
		Get("/profile")

	if err != nil {
		return nil, err
	}

	if resp.IsError() {
		return nil, c.parseError(resp)
	}

	return &result, nil
}

// UpdateProfile updates the user profile
func (c *Client) UpdateProfile(ctx context.Context, updates map[string]interface{}) (*User, error) {
	var result User
	resp, err := c.httpClient.R().
		SetContext(ctx).
		SetBody(updates).
		SetResult(&result).
		Put("/profile")

	if err != nil {
		return nil, err
	}

	if resp.IsError() {
		return nil, c.parseError(resp)
	}

	return &result, nil
}

// Logout logs out and clears tokens
func (c *Client) Logout() {
	c.accessToken = ""
	c.refreshToken = ""

	// Close WebSocket connection
	if c.WebSocket != nil {
		c.WebSocket.Disconnect()
	}
}

// Request makes a custom API request
func (c *Client) Request(ctx context.Context, method, endpoint string, body interface{}, result interface{}) error {
	req := c.httpClient.R().SetContext(ctx)

	if body != nil {
		req.SetBody(body)
	}

	if result != nil {
		req.SetResult(result)
	}

	var resp *resty.Response
	var err error

	switch method {
	case http.MethodGet:
		resp, err = req.Get(endpoint)
	case http.MethodPost:
		resp, err = req.Post(endpoint)
	case http.MethodPut:
		resp, err = req.Put(endpoint)
	case http.MethodPatch:
		resp, err = req.Patch(endpoint)
	case http.MethodDelete:
		resp, err = req.Delete(endpoint)
	default:
		return fmt.Errorf("unsupported method: %s", method)
	}

	if err != nil {
		return err
	}

	if resp.IsError() {
		return c.parseError(resp)
	}

	return nil
}

// initWebSocket initializes the WebSocket client
func (c *Client) initWebSocket() {
	wsURL := c.baseURL
	// Convert HTTP to WebSocket URL
	if len(wsURL) > 4 {
		if wsURL[:5] == "https" {
			wsURL = "wss" + wsURL[5:]
		} else if wsURL[:4] == "http" {
			wsURL = "ws" + wsURL[4:]
		}
	}
	wsURL += "/ws"

	token := c.accessToken
	if token == "" {
		token = c.apiKey
	}

	c.WebSocket = NewWebSocketClient(wsURL, token,
		WithWSCallbacks(c.onConnect, c.onDisconnect, c.onMessage, c.onError))

	c.WebSocket.Connect()
}

// parseError parses error response
func (c *Client) parseError(resp *resty.Response) error {
	var apiErr APIError
	if err := json.Unmarshal(resp.Body(), &apiErr); err != nil {
		// If we can't parse the error, return a generic one
		return &ToneBridgeError{
			StatusCode: resp.StatusCode(),
			Message:    string(resp.Body()),
		}
	}

	return &ToneBridgeError{
		StatusCode: resp.StatusCode(),
		Message:    apiErr.Message,
		Code:       apiErr.Code,
		Details:    apiErr.Details,
	}
}

// Close closes the client and cleans up resources
func (c *Client) Close() {
	if c.WebSocket != nil {
		c.WebSocket.Disconnect()
	}
}