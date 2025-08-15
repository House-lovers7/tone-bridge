"""
Integration Core Service
Central hub for all platform integrations
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from typing import Dict, Any, Optional
import logging

from app.models.internal_message import (
    InternalMessage,
    TransformationRequest,
    TransformationResponse,
    PlatformResponse,
    Platform,
    EventType
)
from app.adapters.base_adapter import adapter_registry, PlatformAdapter
from app.api import events, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    # Startup
    logger.info("Starting Integration Core Service")
    
    # Initialize platform adapters
    await initialize_adapters()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Integration Core Service")

app = FastAPI(
    title="ToneBridge Integration Core",
    description="Central service for multi-platform message integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_adapters():
    """Initialize all platform adapters"""
    configs = {
        Platform.SLACK: {
            "rate_limit": 10,
            "credentials": {
                "token": os.environ.get("SLACK_BOT_TOKEN"),
                "signing_secret": os.environ.get("SLACK_SIGNING_SECRET")
            }
        },
        Platform.TEAMS: {
            "rate_limit": 10,
            "credentials": {
                "app_id": os.environ.get("TEAMS_APP_ID"),
                "app_password": os.environ.get("TEAMS_APP_PASSWORD")
            }
        },
        Platform.DISCORD: {
            "rate_limit": 10,
            "credentials": {
                "token": os.environ.get("DISCORD_BOT_TOKEN")
            }
        }
    }
    
    # Note: Actual adapter implementations would be registered here
    # For now, this is a placeholder
    logger.info(f"Adapter configurations prepared for {len(configs)} platforms")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ToneBridge Integration Core",
        "version": "1.0.0",
        "status": "operational"
    }

# Include routers
app.include_router(health.router)
app.include_router(events.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)