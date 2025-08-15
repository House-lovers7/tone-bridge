"""
Internal Message Models
Platform-agnostic message representations for ToneBridge
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class Platform(str, Enum):
    """Supported platforms"""
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    OUTLOOK = "outlook"
    WEB = "web"

class EventType(str, Enum):
    """Common event types across platforms"""
    MESSAGE = "message"
    COMMAND = "command"
    BUTTON_CLICK = "button_click"
    MODAL_SUBMIT = "modal_submit"
    MENTION = "mention"
    REACTION = "reaction"
    THREAD_REPLY = "thread_reply"

class MessagePriority(str, Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class UserRole(str, Enum):
    """User roles for context"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    GUEST = "guest"
    BOT = "bot"

class User(BaseModel):
    """Platform-agnostic user representation"""
    id: str = Field(..., description="Platform-specific user ID")
    username: str = Field(..., description="User display name")
    email: Optional[str] = Field(None, description="User email if available")
    role: Optional[UserRole] = Field(UserRole.MEMBER, description="User role")
    platform: Platform = Field(..., description="User's platform")
    tenant_id: Optional[str] = Field(None, description="Associated tenant ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")

class Channel(BaseModel):
    """Platform-agnostic channel/conversation representation"""
    id: str = Field(..., description="Platform-specific channel ID")
    name: Optional[str] = Field(None, description="Channel name")
    type: Literal["public", "private", "direct", "group"] = Field("public", description="Channel type")
    platform: Platform = Field(..., description="Channel's platform")
    tenant_id: Optional[str] = Field(None, description="Associated tenant ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")

class Attachment(BaseModel):
    """File or media attachment"""
    id: Optional[str] = Field(None, description="Attachment ID")
    filename: str = Field(..., description="File name")
    mime_type: Optional[str] = Field(None, description="MIME type")
    size: Optional[int] = Field(None, description="File size in bytes")
    url: Optional[str] = Field(None, description="Download URL")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InternalMessage(BaseModel):
    """
    Core message model that all platform messages are converted to/from
    """
    # Identifiers
    id: str = Field(..., description="Unique message ID")
    platform: Platform = Field(..., description="Source platform")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    
    # Event information
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    # Participants
    user: User = Field(..., description="User who triggered the event")
    channel: Channel = Field(..., description="Channel where event occurred")
    
    # Content
    text: str = Field("", description="Message text content")
    formatted_text: Optional[str] = Field(None, description="Rich formatted version")
    thread_id: Optional[str] = Field(None, description="Thread/conversation ID")
    parent_message_id: Optional[str] = Field(None, description="Parent message for replies")
    
    # Additional data
    command: Optional[str] = Field(None, description="Command if event_type is COMMAND")
    command_args: Optional[str] = Field(None, description="Command arguments")
    button_value: Optional[str] = Field(None, description="Button value if clicked")
    attachments: List[Attachment] = Field(default_factory=list, description="File attachments")
    mentions: List[User] = Field(default_factory=list, description="Mentioned users")
    
    # Metadata
    priority: Optional[MessagePriority] = Field(None, description="Message priority if analyzed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")
    raw_event: Optional[Dict[str, Any]] = Field(None, description="Original platform event")

class TransformationRequest(BaseModel):
    """Request to transform a message"""
    message: InternalMessage = Field(..., description="Message to transform")
    transformation_type: str = Field(..., description="Type of transformation")
    target_tone: Optional[str] = Field(None, description="Target tone for transformation")
    intensity: Optional[int] = Field(2, ge=0, le=3, description="Transformation intensity")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")

class TransformationResponse(BaseModel):
    """Response from transformation"""
    original_message: InternalMessage = Field(..., description="Original message")
    transformed_text: str = Field(..., description="Transformed text")
    suggestions: List[str] = Field(default_factory=list, description="Additional suggestions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Transformation metadata")
    platform_formatted: Optional[Dict[str, Any]] = Field(None, description="Platform-specific formatting")

class UIComponent(BaseModel):
    """Abstract UI component for cross-platform rendering"""
    type: Literal["text", "header", "button", "select", "input", "divider", "image"] = Field(..., description="Component type")
    content: Optional[str] = Field(None, description="Text content")
    style: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Style properties")
    actions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Interactive actions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")

class UIMessage(BaseModel):
    """Platform-agnostic UI message"""
    components: List[UIComponent] = Field(..., description="UI components")
    thread_id: Optional[str] = Field(None, description="Thread to post in")
    ephemeral: bool = Field(False, description="Whether message is ephemeral")
    replace_original: bool = Field(False, description="Whether to replace original message")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PlatformResponse(BaseModel):
    """Response to send back to platform"""
    platform: Platform = Field(..., description="Target platform")
    channel_id: str = Field(..., description="Channel to send to")
    ui_message: UIMessage = Field(..., description="UI message to render")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Platform-specific response")

# Conversion utilities
def normalize_platform_user(platform: Platform, user_data: Dict[str, Any]) -> User:
    """
    Convert platform-specific user data to internal User model
    """
    if platform == Platform.SLACK:
        return User(
            id=user_data.get("id", ""),
            username=user_data.get("name", user_data.get("real_name", "Unknown")),
            email=user_data.get("profile", {}).get("email"),
            platform=platform,
            metadata=user_data
        )
    elif platform == Platform.TEAMS:
        return User(
            id=user_data.get("id", ""),
            username=user_data.get("name", "Unknown"),
            email=user_data.get("userPrincipalName"),
            platform=platform,
            metadata=user_data
        )
    elif platform == Platform.DISCORD:
        return User(
            id=str(user_data.get("id", "")),
            username=user_data.get("username", "Unknown"),
            email=user_data.get("email"),
            platform=platform,
            metadata=user_data
        )
    else:
        return User(
            id=user_data.get("id", "unknown"),
            username=user_data.get("name", "Unknown"),
            platform=platform,
            metadata=user_data
        )

def normalize_platform_channel(platform: Platform, channel_data: Dict[str, Any]) -> Channel:
    """
    Convert platform-specific channel data to internal Channel model
    """
    if platform == Platform.SLACK:
        channel_type = "direct" if channel_data.get("is_im") else \
                      "private" if channel_data.get("is_private") else "public"
        return Channel(
            id=channel_data.get("id", ""),
            name=channel_data.get("name"),
            type=channel_type,
            platform=platform,
            metadata=channel_data
        )
    elif platform == Platform.TEAMS:
        return Channel(
            id=channel_data.get("id", ""),
            name=channel_data.get("displayName"),
            type="private" if channel_data.get("membershipType") == "private" else "public",
            platform=platform,
            metadata=channel_data
        )
    elif platform == Platform.DISCORD:
        return Channel(
            id=str(channel_data.get("id", "")),
            name=channel_data.get("name"),
            type="private" if channel_data.get("type") == 1 else "public",
            platform=platform,
            metadata=channel_data
        )
    else:
        return Channel(
            id=channel_data.get("id", "unknown"),
            name=channel_data.get("name"),
            type="public",
            platform=platform,
            metadata=channel_data
        )