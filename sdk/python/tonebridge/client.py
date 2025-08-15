"""
ToneBridge API Client
"""

from typing import Optional, Dict, Any, Callable
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .services.transform import TransformService
from .services.analyze import AnalyzeService
from .services.auto_transform import AutoTransformService
from .websocket import WebSocketClient
from .exceptions import (
    ToneBridgeError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES


class ToneBridgeClient:
    """
    Main ToneBridge client class
    
    Example:
        >>> client = ToneBridgeClient(api_key='your-api-key')
        >>> result = client.transform.soften("This needs to be fixed immediately!")
        >>> print(result['data']['transformed_text'])
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        enable_websocket: bool = False,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        Initialize ToneBridge client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_websocket: Enable WebSocket connection
            on_connect: WebSocket connect callback
            on_disconnect: WebSocket disconnect callback
            on_message: WebSocket message callback
            on_error: WebSocket error callback
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Authentication tokens
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        
        # Setup session with retry logic
        self.session = self._create_session()
        
        # Initialize services
        self.transform = TransformService(self)
        self.analyze = AnalyzeService(self)
        self.auto_transform = AutoTransformService(self)
        
        # WebSocket client
        self.ws: Optional[WebSocketClient] = None
        if enable_websocket:
            self._init_websocket(
                on_connect=on_connect,
                on_disconnect=on_disconnect,
                on_message=on_message,
                on_error=on_error,
            )
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"ToneBridge-Python-SDK/1.0.0",
        })
        
        return session
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with email and password
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication response with tokens
        """
        response = self.request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
        )
        
        self._access_token = response["access_token"]
        self._refresh_token = response["refresh_token"]
        
        # Reinitialize WebSocket if enabled
        if self.ws:
            self._init_websocket()
        
        return response
    
    def set_api_key(self, api_key: str) -> None:
        """Set API key for authentication"""
        self.api_key = api_key
    
    def set_access_token(self, token: str) -> None:
        """Set access token directly"""
        self._access_token = token
        
        # Reinitialize WebSocket if enabled
        if self.ws:
            self._init_websocket()
    
    def refresh_auth(self) -> Dict[str, Any]:
        """Refresh authentication token"""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")
        
        response = self.request(
            "POST",
            "/auth/refresh",
            json={"refresh_token": self._refresh_token},
        )
        
        self._access_token = response["access_token"]
        self._refresh_token = response["refresh_token"]
        
        return response
    
    def get_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        return self.request("GET", "/profile")
    
    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        return self.request("PUT", "/profile", json=data)
    
    def logout(self) -> None:
        """Logout and clear tokens"""
        self._access_token = None
        self._refresh_token = None
        
        # Close WebSocket connection
        if self.ws:
            self.ws.disconnect()
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        Make API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            data: Request data
            headers: Additional headers
            **kwargs: Additional request arguments
            
        Returns:
            Response data
            
        Raises:
            ToneBridgeError: On API errors
        """
        # Prepare URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        req_headers = headers or {}
        
        # Add authentication
        if self._access_token:
            req_headers["Authorization"] = f"Bearer {self._access_token}"
        elif self.api_key:
            req_headers["X-API-Key"] = self.api_key
        
        # Make request
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=req_headers,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                # Try to refresh token if available
                if self._refresh_token and endpoint != "/auth/refresh":
                    self.refresh_auth()
                    # Retry request with new token
                    req_headers["Authorization"] = f"Bearer {self._access_token}"
                    response = self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json,
                        data=data,
                        headers=req_headers,
                        timeout=self.timeout,
                        **kwargs
                    )
                else:
                    raise AuthenticationError("Authentication failed")
            
            # Handle authorization errors
            if response.status_code == 403:
                raise AuthorizationError("Authorization failed")
            
            # Handle validation errors
            if response.status_code == 400:
                error_data = response.json() if response.content else {}
                raise ValidationError(
                    error_data.get("message", "Validation failed"),
                    details=error_data.get("details"),
                )
            
            # Handle server errors
            if response.status_code >= 500:
                raise ServerError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                )
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Return JSON response if available
            if response.content:
                return response.json()
            return None
            
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timeout")
        except requests.exceptions.ConnectionError as e:
            raise ToneBridgeError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise ToneBridgeError(f"Request failed: {str(e)}")
    
    def _init_websocket(
        self,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        """Initialize WebSocket client"""
        ws_url = self.base_url.replace("http", "ws") + "/ws"
        
        self.ws = WebSocketClient(
            url=ws_url,
            token=self._access_token or self.api_key,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
            on_message=on_message,
            on_error=on_error,
        )
        
        self.ws.connect()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.ws:
            self.ws.disconnect()
        self.session.close()