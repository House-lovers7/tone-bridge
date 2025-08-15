"""
Custom exceptions for ToneBridge SDK
"""

from typing import Optional, Any, Dict


class ToneBridgeError(Exception):
    """Base exception for ToneBridge SDK"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 0,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code}, code={self.code!r})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "code": self.code,
            "details": self.details,
        }


class AuthenticationError(ToneBridgeError):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, status_code=401, code="AUTH_FAILED", details=details)


class AuthorizationError(ToneBridgeError):
    """Authorization failed"""
    
    def __init__(self, message: str = "Authorization failed", details: Optional[Any] = None):
        super().__init__(message, status_code=403, code="AUTH_FORBIDDEN", details=details)


class ValidationError(ToneBridgeError):
    """Validation error"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, status_code=400, code="VALIDATION_ERROR", details=details)


class RateLimitError(ToneBridgeError):
    """Rate limit exceeded"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message, status_code=429, code="RATE_LIMIT_EXCEEDED", details=details)
        self.retry_after = retry_after


class NetworkError(ToneBridgeError):
    """Network error"""
    
    def __init__(self, message: str = "Network error", details: Optional[Any] = None):
        super().__init__(message, status_code=0, code="NETWORK_ERROR", details=details)


class TimeoutError(ToneBridgeError):
    """Request timeout"""
    
    def __init__(self, message: str = "Request timeout", details: Optional[Any] = None):
        super().__init__(message, status_code=408, code="TIMEOUT", details=details)


class ServerError(ToneBridgeError):
    """Server error"""
    
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message, status_code=status_code, code="SERVER_ERROR", details=details)


class WebSocketError(ToneBridgeError):
    """WebSocket error"""
    
    def __init__(self, message: str = "WebSocket error", details: Optional[Any] = None):
        super().__init__(message, status_code=0, code="WEBSOCKET_ERROR", details=details)