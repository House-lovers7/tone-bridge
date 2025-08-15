"""
ToneBridge Python SDK
Official SDK for ToneBridge API
"""

__version__ = "1.0.0"
__author__ = "ToneBridge Team"
__email__ = "sdk@tonebridge.io"

from .client import ToneBridgeClient
from .exceptions import (
    ToneBridgeError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    RateLimitError,
    NetworkError,
    TimeoutError,
    ServerError,
)
from .types import (
    TransformationType,
    Priority,
    AnalysisType,
    TriggerType,
    Platform,
)

__all__ = [
    "ToneBridgeClient",
    "ToneBridgeError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
    "ServerError",
    "TransformationType",
    "Priority",
    "AnalysisType",
    "TriggerType",
    "Platform",
    "__version__",
]