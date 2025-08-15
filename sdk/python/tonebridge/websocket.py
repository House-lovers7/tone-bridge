"""
WebSocket Client for real-time communication
"""

import json
import threading
import time
from typing import Optional, Callable, Any, Dict
import websocket
from .exceptions import WebSocketError


class WebSocketClient:
    """WebSocket client for real-time ToneBridge communication"""
    
    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_interval: int = 5,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        Initialize WebSocket client
        
        Args:
            url: WebSocket URL
            token: Authentication token
            reconnect: Enable auto-reconnect
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_interval: Interval between reconnection attempts (seconds)
            on_connect: Connection callback
            on_disconnect: Disconnection callback
            on_message: Message callback
            on_error: Error callback
        """
        self.url = url
        self.token = token
        self.reconnect = reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_interval = reconnect_interval
        
        # Callbacks
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message
        self.on_error = on_error
        
        # State
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.message_queue = []
        self.thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
    
    def connect(self) -> None:
        """Connect to WebSocket server"""
        if self.is_connected:
            return
        
        # Add token to URL if provided
        ws_url = self.url
        if self.token:
            separator = "&" if "?" in ws_url else "?"
            ws_url = f"{ws_url}{separator}token={self.token}"
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        
        # Start WebSocket in separate thread
        self.stop_flag.clear()
        self.thread = threading.Thread(target=self._run_forever)
        self.thread.daemon = True
        self.thread.start()
    
    def disconnect(self) -> None:
        """Disconnect from WebSocket server"""
        self.stop_flag.set()
        self.is_connected = False
        
        if self.ws:
            self.ws.close()
            self.ws = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
    
    def send(self, message_type: str, data: Any) -> None:
        """
        Send message through WebSocket
        
        Args:
            message_type: Type of message
            data: Message data
        """
        message = {
            "type": message_type,
            "data": data,
            "timestamp": time.time(),
            "id": self._generate_id(),
        }
        
        if self.is_connected and self.ws:
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                self._handle_error(e)
        else:
            # Queue message if not connected
            self.message_queue.append(message)
    
    def send_transform(self, data: Dict[str, Any]) -> None:
        """
        Send transform request
        
        Args:
            data: Transform data
        """
        self.send("transform", data)
    
    def send_analyze(self, data: Dict[str, Any]) -> None:
        """
        Send analyze request
        
        Args:
            data: Analyze data
        """
        self.send("analyze", data)
    
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.is_connected
    
    def _run_forever(self) -> None:
        """Run WebSocket connection loop"""
        while not self.stop_flag.is_set():
            try:
                self.ws.run_forever()
                
                if not self.stop_flag.is_set() and self.reconnect:
                    self._handle_reconnect()
                else:
                    break
            except Exception as e:
                self._handle_error(e)
                
                if self.reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                    time.sleep(self.reconnect_interval)
                else:
                    break
    
    def _on_open(self, ws) -> None:
        """Handle connection open"""
        self.is_connected = True
        self.reconnect_attempts = 0
        
        # Send queued messages
        self._flush_message_queue()
        
        if self.on_connect:
            try:
                self.on_connect()
            except Exception as e:
                self._handle_error(e)
    
    def _on_message(self, ws, message) -> None:
        """Handle incoming message"""
        try:
            data = json.loads(message)
            
            if self.on_message:
                self.on_message(data)
        except json.JSONDecodeError as e:
            self._handle_error(WebSocketError(f"Failed to parse message: {e}"))
        except Exception as e:
            self._handle_error(e)
    
    def _on_error(self, ws, error) -> None:
        """Handle WebSocket error"""
        self._handle_error(error)
    
    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Handle connection close"""
        self.is_connected = False
        
        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                self._handle_error(e)
    
    def _handle_error(self, error: Exception) -> None:
        """Handle error"""
        if self.on_error:
            try:
                self.on_error(error)
            except Exception:
                pass  # Ignore errors in error handler
    
    def _handle_reconnect(self) -> None:
        """Handle reconnection"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            return
        
        self.reconnect_attempts += 1
        time.sleep(self.reconnect_interval * self.reconnect_attempts)
    
    def _flush_message_queue(self) -> None:
        """Send queued messages"""
        while self.message_queue and self.is_connected:
            message = self.message_queue.pop(0)
            try:
                if self.ws:
                    self.ws.send(json.dumps(message))
            except Exception as e:
                # Re-queue message on failure
                self.message_queue.insert(0, message)
                self._handle_error(e)
                break
    
    def _generate_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())