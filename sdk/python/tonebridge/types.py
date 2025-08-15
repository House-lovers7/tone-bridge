"""
Type definitions for ToneBridge SDK
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field


class TransformationType(str, Enum):
    """Transformation types"""
    SOFTEN = "soften"
    CLARIFY = "clarify"
    STRUCTURE = "structure"
    SUMMARIZE = "summarize"
    TERMINOLOGY = "terminology"
    REQUIREMENT_STRUCTURING = "requirement_structuring"
    BACKGROUND_COMPLETION = "background_completion"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisType(str, Enum):
    """Analysis types"""
    TONE = "tone"
    CLARITY = "clarity"
    PRIORITY = "priority"
    SENTIMENT = "sentiment"
    STRUCTURE = "structure"
    COMPLETENESS = "completeness"


class TriggerType(str, Enum):
    """Auto-transform trigger types"""
    KEYWORD = "keyword"
    SENTIMENT = "sentiment"
    RECIPIENT = "recipient"
    CHANNEL = "channel"
    TIME = "time"
    PATTERN = "pattern"


class Platform(str, Enum):
    """Supported platforms"""
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    OUTLOOK = "outlook"
    WEB = "web"


@dataclass
class TransformOptions:
    """Options for text transformation"""
    preserve_formatting: bool = False
    include_signature: bool = False
    target_audience: Optional[str] = None
    custom_instructions: Optional[str] = None
    language: Optional[str] = None


@dataclass
class TransformRequest:
    """Transform request"""
    text: str
    transformation_type: Union[TransformationType, str]
    intensity: int = 2
    options: Optional[TransformOptions] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TransformResponse:
    """Transform response"""
    success: bool
    original_text: str
    transformed_text: str
    transformation_type: str
    intensity: int
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None


@dataclass
class AnalyzeRequest:
    """Analyze request"""
    text: str
    analysis_types: Optional[List[Union[AnalysisType, str]]] = None
    include_suggestions: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AnalyzeResponse:
    """Analyze response"""
    success: bool
    text: str
    tone: str
    clarity_score: float
    priority: Priority
    priority_quadrant: Optional[str] = None
    sentiment: Optional[Dict[str, float]] = None
    suggestions: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AutoTransformConfig:
    """Auto-transform configuration"""
    enabled: bool = False
    default_transformation_type: Union[TransformationType, str] = TransformationType.SOFTEN
    default_intensity: int = 2
    min_message_length: int = 50
    max_processing_delay_ms: int = 500
    require_confirmation: bool = True
    show_preview: bool = True
    preserve_original: bool = True


@dataclass
class AutoTransformRule:
    """Auto-transform rule"""
    rule_name: str
    trigger_type: Union[TriggerType, str]
    trigger_value: Dict[str, Any]
    transformation_type: Union[TransformationType, str]
    transformation_intensity: int = 2
    id: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    priority: int = 0
    transformation_options: Optional[Dict[str, Any]] = None
    platforms: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    user_roles: List[str] = field(default_factory=list)


@dataclass
class MessageContext:
    """Message context for auto-transform"""
    message: str
    user_id: str
    tenant_id: str
    platform: Union[Platform, str]
    channel_id: Optional[str] = None
    recipient_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TransformationResult:
    """Transformation evaluation result"""
    should_transform: bool
    transformation_type: Union[TransformationType, str]
    transformation_intensity: int
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    transformation_options: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    reason: Optional[str] = None


@dataclass
class BatchTransformRequest:
    """Batch transform request"""
    items: List[TransformRequest]
    parallel: bool = True
    stop_on_error: bool = False


@dataclass
class User:
    """User information"""
    id: str
    email: str
    name: str
    role: str
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class AuthResponse:
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Optional[User] = None