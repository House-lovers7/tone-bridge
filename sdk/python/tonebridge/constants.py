"""
Constants for ToneBridge SDK
"""

# API Configuration
DEFAULT_BASE_URL = "https://api.tonebridge.io/api/v1"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3

# API Endpoints
API_ENDPOINTS = {
    # Authentication
    "LOGIN": "/auth/login",
    "REGISTER": "/auth/register",
    "REFRESH": "/auth/refresh",
    "LOGOUT": "/auth/logout",
    
    # Profile
    "PROFILE": "/profile",
    
    # Transform
    "TRANSFORM": "/transform",
    "BATCH_TRANSFORM": "/transform/batch",
    
    # Analyze
    "ANALYZE": "/analyze",
    
    # Advanced
    "STRUCTURE_REQUIREMENTS": "/advanced/structure-requirements",
    "COMPLETE_BACKGROUND": "/advanced/complete-background",
    "SCORE_PRIORITY": "/advanced/score-priority",
    "BATCH_SCORE_PRIORITIES": "/advanced/batch-score-priorities",
    "ADJUST_TONE": "/advanced/adjust-tone",
    "AUTO_DETECT_INTENSITY": "/advanced/auto-detect-intensity",
    "TONE_PRESETS": "/advanced/tone-presets",
    
    # Auto-transform
    "AUTO_EVALUATE": "/auto-transform/evaluate",
    "AUTO_TRANSFORM": "/auto-transform/transform",
    "AUTO_CONFIG": "/auto-transform/config",
    "AUTO_RULES": "/auto-transform/rules",
    "AUTO_TEMPLATES": "/auto-transform/templates",
    
    # History
    "HISTORY": "/history",
    
    # Dictionaries
    "DICTIONARIES": "/dictionaries",
}

# Transformation defaults
DEFAULT_INTENSITY = 2
MIN_INTENSITY = 0
MAX_INTENSITY = 3

# Text limits
MAX_TEXT_LENGTH = 10000
DEFAULT_MIN_MESSAGE_LENGTH = 50

# Processing
DEFAULT_MAX_PROCESSING_DELAY = 500  # milliseconds

# Batch operations
MAX_BATCH_SIZE = 100

# HTTP Status codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# WebSocket events
WS_EVENTS = {
    "CONNECT": "connect",
    "DISCONNECT": "disconnect",
    "MESSAGE": "message",
    "ERROR": "error",
    "TRANSFORM": "transform",
    "ANALYZE": "analyze",
    "NOTIFICATION": "notification",
}

# Rate limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# Cache settings
DEFAULT_CACHE_TTL = 300  # seconds
DEFAULT_CACHE_MAX_SIZE = 1000  # items

# Version
SDK_VERSION = "1.0.0"
USER_AGENT = f"ToneBridge-Python-SDK/{SDK_VERSION}"