"""
Event Processing API
Handles incoming events from all platforms
"""

from fastapi import APIRouter, HTTPException, Request, Header
from typing import Dict, Any, Optional
import logging

from app.models.internal_message import (
    InternalMessage,
    TransformationRequest,
    TransformationResponse,
    PlatformResponse,
    Platform,
    EventType,
    UIMessage,
    UIComponent
)
from app.adapters.base_adapter import adapter_registry
import httpx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["events"])

# ToneBridge API client
TONEBRIDGE_API_URL = "http://gateway:8080"

@router.post("/events")
async def process_event(
    request: Request,
    platform: Platform,
    x_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Process incoming event from any platform
    
    This is the main entry point for all platform webhooks
    """
    try:
        # Get raw event data
        raw_event = await request.json()
        
        # Get appropriate adapter
        adapter = adapter_registry.get(platform)
        if not adapter:
            raise HTTPException(status_code=400, detail=f"No adapter for platform: {platform}")
        
        # Validate signature if provided
        if x_signature and hasattr(adapter, 'validate_signature'):
            if not adapter.validate_signature(raw_event, x_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event to internal format
        internal_message = await adapter.parse_event(raw_event)
        
        # Log the event
        logger.info(
            f"Received {internal_message.event_type} from {internal_message.user.username} "
            f"on {platform} in channel {internal_message.channel.id}"
        )
        
        # Process based on event type
        response = await process_internal_message(internal_message)
        
        # Format response for platform
        platform_response = await adapter.format_response(response.ui_message)
        
        return platform_response
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_internal_message(message: InternalMessage) -> PlatformResponse:
    """
    Process an internal message and generate response
    """
    try:
        # Handle different event types
        if message.event_type == EventType.COMMAND:
            return await handle_command(message)
        elif message.event_type == EventType.MESSAGE:
            return await handle_message(message)
        elif message.event_type == EventType.BUTTON_CLICK:
            return await handle_button_click(message)
        else:
            # Default response
            return PlatformResponse(
                platform=message.platform,
                channel_id=message.channel.id,
                ui_message=UIMessage(
                    components=[
                        UIComponent(
                            type="text",
                            content="Event received and processed"
                        )
                    ],
                    ephemeral=True
                )
            )
    except Exception as e:
        logger.error(f"Error processing internal message: {str(e)}")
        return error_response(message.platform, message.channel.id, str(e))

async def handle_command(message: InternalMessage) -> PlatformResponse:
    """Handle command events"""
    command = message.command
    args = message.command_args
    
    # Command routing
    if command == "/soften":
        return await transform_text(message, "tone", "warm")
    elif command == "/clarify":
        return await transform_text(message, "structure")
    elif command == "/analyze":
        return await analyze_text(message)
    elif command == "/prioritize":
        return await score_priority(message)
    elif command == "/structure":
        return await structure_requirements(message)
    elif command == "/help":
        return help_response(message.platform, message.channel.id)
    else:
        return PlatformResponse(
            platform=message.platform,
            channel_id=message.channel.id,
            ui_message=UIMessage(
                components=[
                    UIComponent(
                        type="text",
                        content=f"Unknown command: {command}"
                    )
                ],
                ephemeral=True
            )
        )

async def handle_message(message: InternalMessage) -> PlatformResponse:
    """Handle regular message events"""
    # Default behavior: offer to transform the message
    return PlatformResponse(
        platform=message.platform,
        channel_id=message.channel.id,
        ui_message=UIMessage(
            components=[
                UIComponent(
                    type="text",
                    content="Would you like me to help transform this message?"
                ),
                UIComponent(
                    type="button",
                    content="Soften",
                    actions={"command": "soften", "text": message.text}
                ),
                UIComponent(
                    type="button",
                    content="Clarify",
                    actions={"command": "clarify", "text": message.text}
                ),
                UIComponent(
                    type="button",
                    content="Analyze",
                    actions={"command": "analyze", "text": message.text}
                )
            ],
            ephemeral=True
        )
    )

async def handle_button_click(message: InternalMessage) -> PlatformResponse:
    """Handle button click events"""
    button_value = message.button_value
    
    # Parse button action
    if button_value:
        action_data = eval(button_value) if button_value.startswith("{") else {"action": button_value}
        command = action_data.get("command")
        text = action_data.get("text", message.text)
        
        # Create a new message with the command
        message.command = f"/{command}"
        message.command_args = text
        message.text = text
        
        return await handle_command(message)
    
    return error_response(message.platform, message.channel.id, "Invalid button action")

async def transform_text(
    message: InternalMessage,
    transformation_type: str,
    target_tone: Optional[str] = None
) -> PlatformResponse:
    """Transform text using ToneBridge API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TONEBRIDGE_API_URL}/api/v1/transform",
                json={
                    "text": message.text or message.command_args,
                    "transformation_type": transformation_type,
                    "target_tone": target_tone
                }
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                transformed_text = data["transformed_text"]
                suggestions = data.get("suggestions", [])
                
                components = [
                    UIComponent(
                        type="header",
                        content="✨ Transformed Message"
                    ),
                    UIComponent(
                        type="text",
                        content=transformed_text
                    )
                ]
                
                if suggestions:
                    components.append(
                        UIComponent(
                            type="text",
                            content="💡 Suggestions:\n" + "\n".join([f"• {s}" for s in suggestions])
                        )
                    )
                
                # Add action buttons
                components.extend([
                    UIComponent(
                        type="divider"
                    ),
                    UIComponent(
                        type="button",
                        content="Apply Another Transform",
                        actions={"command": "soften", "text": transformed_text}
                    ),
                    UIComponent(
                        type="button",
                        content="Analyze",
                        actions={"command": "analyze", "text": transformed_text}
                    )
                ])
                
                return PlatformResponse(
                    platform=message.platform,
                    channel_id=message.channel.id,
                    ui_message=UIMessage(
                        components=components,
                        thread_id=message.thread_id
                    )
                )
            else:
                raise Exception(f"API returned status {response.status_code}")
                
    except Exception as e:
        logger.error(f"Transform failed: {str(e)}")
        return error_response(message.platform, message.channel.id, f"Transform failed: {str(e)}")

async def analyze_text(message: InternalMessage) -> PlatformResponse:
    """Analyze text using ToneBridge API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TONEBRIDGE_API_URL}/api/v1/analyze",
                json={"text": message.text or message.command_args}
            )
            
            if response.status_code == 200:
                data = response.json()["data"]
                
                tone = data.get("tone", "unknown")
                clarity = data.get("clarity", 0)
                priority = data.get("priority", "medium")
                suggestions = data.get("suggestions", [])
                
                components = [
                    UIComponent(
                        type="header",
                        content="📊 Message Analysis"
                    ),
                    UIComponent(
                        type="text",
                        content=f"**Tone:** {tone.title()}\n**Clarity:** {clarity:.1%}\n**Priority:** {priority.title()}"
                    )
                ]
                
                if suggestions:
                    components.append(
                        UIComponent(
                            type="text",
                            content="**Suggestions:**\n" + "\n".join([f"• {s}" for s in suggestions])
                        )
                    )
                
                return PlatformResponse(
                    platform=message.platform,
                    channel_id=message.channel.id,
                    ui_message=UIMessage(
                        components=components,
                        thread_id=message.thread_id
                    )
                )
            else:
                raise Exception(f"API returned status {response.status_code}")
                
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return error_response(message.platform, message.channel.id, f"Analysis failed: {str(e)}")

async def score_priority(message: InternalMessage) -> PlatformResponse:
    """Score message priority"""
    # Mock implementation for now
    components = [
        UIComponent(
            type="header",
            content="🎯 Priority Score"
        ),
        UIComponent(
            type="text",
            content="**Urgency:** 65/100\n**Importance:** 70/100\n**Priority Level:** High\n**Recommended Response:** Within 4 hours"
        )
    ]
    
    return PlatformResponse(
        platform=message.platform,
        channel_id=message.channel.id,
        ui_message=UIMessage(
            components=components,
            thread_id=message.thread_id
        )
    )

async def structure_requirements(message: InternalMessage) -> PlatformResponse:
    """Structure text into requirements"""
    # Mock implementation for now
    components = [
        UIComponent(
            type="header",
            content="📋 Structured Requirements"
        ),
        UIComponent(
            type="text",
            content=(
                "**Background:** Project needs multi-platform support\n"
                "**Requests:** Implement Teams and Discord integration\n"
                "**Constraints:** Must maintain existing API compatibility\n"
                "**Timeline:** 2 weeks"
            )
        )
    ]
    
    return PlatformResponse(
        platform=message.platform,
        channel_id=message.channel.id,
        ui_message=UIMessage(
            components=components,
            thread_id=message.thread_id
        )
    )

def help_response(platform: Platform, channel_id: str) -> PlatformResponse:
    """Generate help response"""
    return PlatformResponse(
        platform=platform,
        channel_id=channel_id,
        ui_message=UIMessage(
            components=[
                UIComponent(
                    type="header",
                    content="ToneBridge Help"
                ),
                UIComponent(
                    type="text",
                    content=(
                        "**Available Commands:**\n"
                        "• `/soften [text]` - Make text warmer\n"
                        "• `/clarify [text]` - Improve structure\n"
                        "• `/analyze [text]` - Analyze tone\n"
                        "• `/prioritize [text]` - Score priority\n"
                        "• `/structure [text]` - Structure requirements\n"
                        "• `/help` - Show this help"
                    )
                )
            ],
            ephemeral=True
        )
    )

def error_response(platform: Platform, channel_id: str, error: str) -> PlatformResponse:
    """Generate error response"""
    return PlatformResponse(
        platform=platform,
        channel_id=channel_id,
        ui_message=UIMessage(
            components=[
                UIComponent(
                    type="text",
                    content=f"❌ Error: {error}",
                    style={"color": "red"}
                )
            ],
            ephemeral=True
        )
    )

@router.post("/send-message")
async def send_message(
    platform: Platform,
    channel_id: str,
    ui_message: UIMessage,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to a specific platform channel
    """
    try:
        adapter = adapter_registry.get(platform)
        if not adapter:
            raise HTTPException(status_code=400, detail=f"No adapter for platform: {platform}")
        
        result = await adapter.send_message(channel_id, ui_message, thread_id)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))