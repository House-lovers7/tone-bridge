"""
Slack Integration for ToneBridge
Provides slash commands and interactive components for message transformation
"""

import os
import json
import asyncio
import httpx
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from typing import Dict, Any
import hashlib
import hmac
import time

# Configuration
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
TONEBRIDGE_API_URL = os.environ.get("TONEBRIDGE_API_URL", "http://localhost:8080")

# Initialize Slack app
slack_app = AsyncApp(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Initialize FastAPI
api = FastAPI(title="ToneBridge Slack Integration")

# Create handler
handler = AsyncSlackRequestHandler(slack_app)

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
        if not self.token:
            raise Exception("Not authenticated")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "text": text,
            "transformation_type": transformation_type,
            "target_tone": target_tone
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/transform",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Transformation failed: {response.text}")
    
    async def analyze_text(self, text: str):
        """Analyze text using ToneBridge API"""
        if not self.token:
            raise Exception("Not authenticated")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"text": text}
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/analyze",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Analysis failed: {response.text}")

# Initialize ToneBridge client
tb_client = ToneBridgeClient(TONEBRIDGE_API_URL)

# Slash Commands

@slack_app.command("/soften")
async def handle_soften_command(ack, command, say):
    """Handle /soften command to make text warmer and more considerate"""
    await ack()
    
    text = command.get("text", "").strip()
    if not text:
        await say("Please provide text to soften. Usage: `/soften your text here`")
        return
    
    try:
        # Transform text to warm tone
        result = await tb_client.transform_text(text, "tone", "warm")
        transformed_text = result["data"]["transformed_text"]
        suggestions = result["data"].get("suggestions", [])
        
        # Create response blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Original:*\n{text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Softened:*\n{transformed_text}"
                }
            }
        ]
        
        if suggestions:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💡 *Suggestions:* {' • '.join(suggestions)}"
                    }
                ]
            })
        
        await say(blocks=blocks)
        
    except Exception as e:
        await say(f"Sorry, I couldn't soften that text. Error: {str(e)}")

@slack_app.command("/clarify")
async def handle_clarify_command(ack, command, say):
    """Handle /clarify command to make text clearer and more structured"""
    await ack()
    
    text = command.get("text", "").strip()
    if not text:
        await say("Please provide text to clarify. Usage: `/clarify your text here`")
        return
    
    try:
        # Transform text structure
        result = await tb_client.transform_text(text, "structure")
        transformed_text = result["data"]["transformed_text"]
        
        # Analyze for additional insights
        analysis = await tb_client.analyze_text(text)
        clarity_score = analysis["data"]["clarity"]
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Original:*\n{text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Clarified:*\n{transformed_text}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 *Clarity Score:* {clarity_score:.1%}"
                    }
                ]
            }
        ]
        
        await say(blocks=blocks)
        
    except Exception as e:
        await say(f"Sorry, I couldn't clarify that text. Error: {str(e)}")

@slack_app.command("/analyze")
async def handle_analyze_command(ack, command, say):
    """Handle /analyze command to analyze message tone and priority"""
    await ack()
    
    text = command.get("text", "").strip()
    if not text:
        await say("Please provide text to analyze. Usage: `/analyze your text here`")
        return
    
    try:
        # Analyze text
        result = await tb_client.analyze_text(text)
        data = result["data"]
        
        tone = data.get("tone", "unknown")
        clarity = data.get("clarity", 0)
        priority = data.get("priority", "medium")
        suggestions = data.get("suggestions", [])
        
        # Map priority to emoji
        priority_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }.get(priority, "⚪")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Message Analysis"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Tone:* {tone.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Clarity:* {clarity:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:* {priority_emoji} {priority.title()}"
                    }
                ]
            }
        ]
        
        if suggestions:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Suggestions for improvement:*\n• " + "\n• ".join(suggestions)
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Soften"
                    },
                    "style": "primary",
                    "action_id": "soften_button",
                    "value": text
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Clarify"
                    },
                    "action_id": "clarify_button",
                    "value": text
                }
            ]
        })
        
        await say(blocks=blocks)
        
    except Exception as e:
        await say(f"Sorry, I couldn't analyze that text. Error: {str(e)}")

# Interactive Components

@slack_app.action("soften_button")
async def handle_soften_button(ack, body, say):
    """Handle soften button click"""
    await ack()
    
    text = body["actions"][0]["value"]
    
    try:
        result = await tb_client.transform_text(text, "tone", "warm")
        transformed_text = result["data"]["transformed_text"]
        
        await say(
            text=f"*Softened version:*\n{transformed_text}",
            thread_ts=body.get("message", {}).get("ts")
        )
    except Exception as e:
        await say(f"Error: {str(e)}")

@slack_app.action("clarify_button")
async def handle_clarify_button(ack, body, say):
    """Handle clarify button click"""
    await ack()
    
    text = body["actions"][0]["value"]
    
    try:
        result = await tb_client.transform_text(text, "structure")
        transformed_text = result["data"]["transformed_text"]
        
        await say(
            text=f"*Clarified version:*\n{transformed_text}",
            thread_ts=body.get("message", {}).get("ts")
        )
    except Exception as e:
        await say(f"Error: {str(e)}")

# Message shortcuts (right-click menu)

@slack_app.shortcut("transform_message")
async def handle_transform_shortcut(ack, shortcut, client):
    """Handle message transformation shortcut"""
    await ack()
    
    # Open modal for transformation options
    await client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "transform_modal",
            "title": {
                "type": "plain_text",
                "text": "Transform Message"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "text_input",
                    "label": {
                        "type": "plain_text",
                        "text": "Message to transform"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "text",
                        "multiline": True,
                        "initial_value": shortcut.get("message", {}).get("text", "")
                    }
                },
                {
                    "type": "input",
                    "block_id": "transformation_type",
                    "label": {
                        "type": "plain_text",
                        "text": "Transformation type"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "type",
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Soften (warm tone)"},
                                "value": "tone_warm"
                            },
                            {
                                "text": {"type": "plain_text", "text": "Professional"},
                                "value": "tone_professional"
                            },
                            {
                                "text": {"type": "plain_text", "text": "Clarify structure"},
                                "value": "structure"
                            },
                            {
                                "text": {"type": "plain_text", "text": "Summarize"},
                                "value": "summarize"
                            }
                        ]
                    }
                }
            ],
            "submit": {
                "type": "plain_text",
                "text": "Transform"
            }
        }
    )

@slack_app.view("transform_modal")
async def handle_transform_modal(ack, body, view, client):
    """Handle modal submission"""
    await ack()
    
    # Extract values
    text = view["state"]["values"]["text_input"]["text"]["value"]
    transform_type = view["state"]["values"]["transformation_type"]["type"]["selected_option"]["value"]
    
    # Parse transformation type
    if transform_type.startswith("tone_"):
        transformation_type = "tone"
        target_tone = transform_type.split("_")[1]
    else:
        transformation_type = transform_type
        target_tone = None
    
    try:
        # Transform text
        result = await tb_client.transform_text(text, transformation_type, target_tone)
        transformed_text = result["data"]["transformed_text"]
        
        # Post result to channel
        channel_id = body["view"]["private_metadata"] or body["user"]["id"]
        
        await client.chat_postMessage(
            channel=channel_id,
            text=f"*Transformed message:*\n{transformed_text}"
        )
        
    except Exception as e:
        await client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"Error transforming message: {str(e)}"
        )

# FastAPI endpoints

@api.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events"""
    return await handler.handle(request)

@api.post("/slack/interactions")
async def slack_interactions(request: Request):
    """Handle Slack interactions"""
    return await handler.handle(request)

@api.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "slack-integration"}

# Startup event
@api.on_event("startup")
async def startup_event():
    """Initialize ToneBridge client on startup"""
    # Use service account for Slack bot
    service_email = os.environ.get("TONEBRIDGE_SERVICE_EMAIL", "slack-bot@tonebridge.io")
    service_password = os.environ.get("TONEBRIDGE_SERVICE_PASSWORD", "slack-bot-password")
    
    try:
        await tb_client.authenticate(service_email, service_password)
        print("Successfully authenticated with ToneBridge API")
    except Exception as e:
        print(f"Warning: Could not authenticate with ToneBridge API: {e}")
        print("Some features may not work properly")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=3000)