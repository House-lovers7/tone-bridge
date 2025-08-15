"""
Microsoft Teams Integration for ToneBridge
Uses Bot Framework SDK for Python
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from botbuilder.core import (
    TurnContext,
    MessageFactory,
    CardFactory,
    ActivityHandler,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationReference,
    Attachment,
    HeroCard,
    CardAction,
    ActionTypes,
    CardImage,
    SuggestedActions,
    CardAction
)
from botbuilder.schema.teams import (
    TeamsChannelAccount,
    TeamInfo,
    TeamsInfo
)
from botframework.connector.auth import (
    MicrosoftAppCredentials,
    JwtTokenValidation,
    SimpleCredentialProvider
)

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import httpx

# Configuration
APP_ID = os.environ.get("TEAMS_APP_ID", "")
APP_PASSWORD = os.environ.get("TEAMS_APP_PASSWORD", "")
TONEBRIDGE_API_URL = os.environ.get("TONEBRIDGE_API_URL", "http://localhost:8080")

# Initialize FastAPI
app = FastAPI(title="ToneBridge Teams Integration")

# Bot Framework Adapter
SETTINGS = BotFrameworkAdapterSettings(
    app_id=APP_ID,
    app_password=APP_PASSWORD
)
ADAPTER = BotFrameworkAdapter(SETTINGS)

class ToneBridgeTeamsBot(ActivityHandler):
    """
    Teams bot handler for ToneBridge
    """
    
    def __init__(self):
        super().__init__()
        self.tonebridge_client = ToneBridgeClient(TONEBRIDGE_API_URL)
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """
        Handle incoming messages
        """
        # Remove bot mention from text
        text = TurnContext.remove_recipient_mention(turn_context.activity)
        
        if not text:
            await turn_context.send_activity(
                MessageFactory.text("Please provide text to transform. Type `help` for available commands.")
            )
            return
        
        # Parse command
        command_parts = text.strip().split(" ", 1)
        command = command_parts[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else ""
        
        # Handle commands
        if command == "help":
            await self._send_help(turn_context)
        elif command == "soften":
            await self._transform_text(turn_context, args, "tone", "warm")
        elif command == "clarify":
            await self._transform_text(turn_context, args, "structure")
        elif command == "analyze":
            await self._analyze_text(turn_context, args)
        elif command == "prioritize":
            await self._score_priority(turn_context, args)
        elif command == "structure":
            await self._structure_requirements(turn_context, args)
        else:
            # Default: treat entire message as text to soften
            await self._transform_text(turn_context, text, "tone", "warm")
    
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ) -> None:
        """
        Welcome new members
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Welcome to ToneBridge! I help transform messages between technical and non-technical styles.\n\n"
                        f"Type `help` to see available commands."
                    )
                )
    
    async def _send_help(self, turn_context: TurnContext) -> None:
        """
        Send help message with available commands
        """
        help_card = HeroCard(
            title="ToneBridge Commands",
            subtitle="Transform your messages for better communication",
            text=(
                "**Available commands:**\n\n"
                "• `soften [text]` - Make text warmer and more considerate\n"
                "• `clarify [text]` - Structure text for clarity\n"
                "• `analyze [text]` - Analyze tone and priority\n"
                "• `prioritize [text]` - Score message priority\n"
                "• `structure [text]` - Structure into requirements\n"
                "• `help` - Show this help message\n\n"
                "Or just type any text and I'll suggest improvements!"
            ),
            images=[CardImage(url="https://via.placeholder.com/150x150?text=ToneBridge")],
            buttons=[
                CardAction(
                    type=ActionTypes.open_url,
                    title="Learn More",
                    value="https://tonebridge.io/docs"
                )
            ]
        )
        
        help_attachment = MessageFactory.attachment(CardFactory.hero_card(help_card))
        await turn_context.send_activity(help_attachment)
    
    async def _transform_text(
        self, 
        turn_context: TurnContext, 
        text: str, 
        transformation_type: str,
        target_tone: Optional[str] = None
    ) -> None:
        """
        Transform text and send result
        """
        if not text:
            await turn_context.send_activity(
                MessageFactory.text(f"Please provide text to transform.")
            )
            return
        
        # Show typing indicator
        await self._send_typing(turn_context)
        
        try:
            # Call ToneBridge API
            result = await self.tonebridge_client.transform_text(
                text, transformation_type, target_tone
            )
            
            transformed_text = result["data"]["transformed_text"]
            suggestions = result["data"].get("suggestions", [])
            
            # Create response card
            response_card = HeroCard(
                title="Transformed Message",
                subtitle=f"Transformation: {transformation_type}",
                text=transformed_text
            )
            
            if suggestions:
                response_card.text += f"\n\n**Suggestions:**\n" + "\n".join([f"• {s}" for s in suggestions])
            
            # Add action buttons
            response_card.buttons = [
                CardAction(
                    type=ActionTypes.message_back,
                    title="Apply Another Transform",
                    value=transformed_text,
                    text=f"soften {transformed_text}",
                    display_text="Apply Another Transform"
                ),
                CardAction(
                    type=ActionTypes.message_back,
                    title="Analyze This",
                    value=transformed_text,
                    text=f"analyze {transformed_text}",
                    display_text="Analyze"
                )
            ]
            
            card_attachment = MessageFactory.attachment(CardFactory.hero_card(response_card))
            await turn_context.send_activity(card_attachment)
            
        except Exception as e:
            await turn_context.send_activity(
                MessageFactory.text(f"Sorry, I couldn't transform that text. Error: {str(e)}")
            )
    
    async def _analyze_text(self, turn_context: TurnContext, text: str) -> None:
        """
        Analyze text and send results
        """
        if not text:
            await turn_context.send_activity(
                MessageFactory.text("Please provide text to analyze.")
            )
            return
        
        await self._send_typing(turn_context)
        
        try:
            result = await self.tonebridge_client.analyze_text(text)
            data = result["data"]
            
            tone = data.get("tone", "unknown")
            clarity = data.get("clarity", 0)
            priority = data.get("priority", "medium")
            suggestions = data.get("suggestions", [])
            
            # Create adaptive card for rich display
            adaptive_card = {
                "type": "AdaptiveCard",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Message Analysis",
                        "size": "Large",
                        "weight": "Bolder"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Tone", "value": tone.title()},
                            {"title": "Clarity", "value": f"{clarity:.1%}"},
                            {"title": "Priority", "value": priority.title()}
                        ]
                    }
                ]
            }
            
            if suggestions:
                adaptive_card["body"].append({
                    "type": "TextBlock",
                    "text": "**Suggestions for improvement:**",
                    "wrap": True
                })
                for suggestion in suggestions:
                    adaptive_card["body"].append({
                        "type": "TextBlock",
                        "text": f"• {suggestion}",
                        "wrap": True
                    })
            
            # Add action buttons
            adaptive_card["actions"] = [
                {
                    "type": "Action.Submit",
                    "title": "Soften This Message",
                    "data": {"command": "soften", "text": text}
                },
                {
                    "type": "Action.Submit",
                    "title": "Clarify Structure",
                    "data": {"command": "clarify", "text": text}
                }
            ]
            
            card_attachment = CardFactory.adaptive_card(adaptive_card)
            await turn_context.send_activity(MessageFactory.attachment(card_attachment))
            
        except Exception as e:
            await turn_context.send_activity(
                MessageFactory.text(f"Sorry, I couldn't analyze that text. Error: {str(e)}")
            )
    
    async def _score_priority(self, turn_context: TurnContext, text: str) -> None:
        """
        Score message priority
        """
        if not text:
            await turn_context.send_activity(
                MessageFactory.text("Please provide text to prioritize.")
            )
            return
        
        await self._send_typing(turn_context)
        
        try:
            result = await self.tonebridge_client.score_priority(text)
            data = result["data"]
            
            urgency = data.get("urgency_score", 0)
            importance = data.get("importance_score", 0)
            priority_level = data.get("priority_level", "medium")
            quadrant = data.get("priority_matrix_quadrant", "Q2")
            response_time = data.get("recommended_response_time", "within 24 hours")
            
            # Priority emoji
            priority_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(priority_level, "⚪")
            
            # Create adaptive card
            adaptive_card = {
                "type": "AdaptiveCard",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": f"{priority_emoji} Priority Assessment",
                        "size": "Large",
                        "weight": "Bolder"
                    },
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "Urgency",
                                        "weight": "Bolder"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"{urgency:.0f}/100"
                                    }
                                ]
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "Importance",
                                        "weight": "Bolder"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"{importance:.0f}/100"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "TextBlock",
                        "text": f"**Eisenhower Matrix:** {quadrant}",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": f"**Recommended Response:** {response_time}",
                        "wrap": True,
                        "color": "Accent"
                    }
                ]
            }
            
            card_attachment = CardFactory.adaptive_card(adaptive_card)
            await turn_context.send_activity(MessageFactory.attachment(card_attachment))
            
        except Exception as e:
            await turn_context.send_activity(
                MessageFactory.text(f"Sorry, I couldn't score priority. Error: {str(e)}")
            )
    
    async def _structure_requirements(self, turn_context: TurnContext, text: str) -> None:
        """
        Structure text into requirements
        """
        if not text:
            await turn_context.send_activity(
                MessageFactory.text("Please provide text to structure.")
            )
            return
        
        await self._send_typing(turn_context)
        
        try:
            result = await self.tonebridge_client.structure_requirements(text)
            data = result["data"]
            
            background = data.get("background", "Not specified")
            requests = data.get("requests", [])
            constraints = data.get("constraints", [])
            timeline = data.get("timeline", "Not specified")
            missing_info = data.get("missing_info", [])
            
            # Create adaptive card
            adaptive_card = {
                "type": "AdaptiveCard",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "📋 Structured Requirements",
                        "size": "Large",
                        "weight": "Bolder"
                    }
                ]
            }
            
            # Add sections
            sections = [
                ("🎯 Background", background),
                ("📝 Requests", "\n".join([f"• {r}" for r in requests]) if requests else "None specified"),
                ("⚠️ Constraints", "\n".join([f"• {c}" for c in constraints]) if constraints else "None specified"),
                ("⏰ Timeline", timeline)
            ]
            
            for title, content in sections:
                adaptive_card["body"].extend([
                    {
                        "type": "TextBlock",
                        "text": title,
                        "weight": "Bolder",
                        "separator": True
                    },
                    {
                        "type": "TextBlock",
                        "text": content,
                        "wrap": True
                    }
                ])
            
            if missing_info:
                adaptive_card["body"].extend([
                    {
                        "type": "TextBlock",
                        "text": "❓ Missing Information",
                        "weight": "Bolder",
                        "separator": True,
                        "color": "Attention"
                    },
                    {
                        "type": "TextBlock",
                        "text": "\n".join([f"• {m}" for m in missing_info]),
                        "wrap": True
                    }
                ])
            
            card_attachment = CardFactory.adaptive_card(adaptive_card)
            await turn_context.send_activity(MessageFactory.attachment(card_attachment))
            
        except Exception as e:
            await turn_context.send_activity(
                MessageFactory.text(f"Sorry, I couldn't structure requirements. Error: {str(e)}")
            )
    
    async def _send_typing(self, turn_context: TurnContext) -> None:
        """Send typing indicator"""
        typing_activity = Activity(type=ActivityTypes.typing)
        await turn_context.send_activity(typing_activity)

class ToneBridgeClient:
    """Client for ToneBridge API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.token = None
    
    async def authenticate(self, email: str, password: str):
        """Authenticate with ToneBridge API"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            return True
        return False
    
    async def transform_text(self, text: str, transformation_type: str, target_tone: str = None):
        """Transform text using ToneBridge API"""
        # For now, mock the response
        # In production, this would call the actual API
        return {
            "success": True,
            "data": {
                "transformed_text": f"[Transformed {transformation_type}]: {text}",
                "suggestions": ["Consider adding more context", "Use active voice"]
            }
        }
    
    async def analyze_text(self, text: str):
        """Analyze text"""
        return {
            "success": True,
            "data": {
                "tone": "professional",
                "clarity": 0.75,
                "priority": "medium",
                "suggestions": ["Add specific deadlines", "Clarify action items"]
            }
        }
    
    async def score_priority(self, text: str):
        """Score priority"""
        return {
            "success": True,
            "data": {
                "urgency_score": 65,
                "importance_score": 70,
                "priority_level": "high",
                "priority_matrix_quadrant": "Q1",
                "recommended_response_time": "within 4 hours"
            }
        }
    
    async def structure_requirements(self, text: str):
        """Structure requirements"""
        return {
            "success": True,
            "data": {
                "background": "User needs help with Teams integration",
                "requests": ["Implement bot commands", "Add adaptive cards"],
                "constraints": ["Must work with existing API", "Security compliance required"],
                "timeline": "2 weeks",
                "missing_info": ["Specific Teams version", "User permissions needed"]
            }
        }

# Bot instance
BOT = ToneBridgeTeamsBot()

# FastAPI endpoints
@app.post("/api/messages")
async def messages(request: Request) -> Response:
    """
    Handle incoming messages from Teams
    """
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.json()
    else:
        return Response(status_code=415)
    
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    
    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return JSONResponse(content=response.body, status_code=response.status)
        return Response(status_code=201)
    except Exception as e:
        print(f"Error processing activity: {e}")
        return Response(status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "teams-integration"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)