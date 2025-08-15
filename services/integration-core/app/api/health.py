"""
Health Check API
"""

from fastapi import APIRouter
from typing import Dict, Any
from app.adapters.base_adapter import adapter_registry

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    """
    # Check registered adapters
    adapters = adapter_registry.get_all()
    adapter_status = {
        platform.value: "registered"
        for platform in adapters.keys()
    }
    
    return {
        "status": "healthy",
        "service": "integration-core",
        "adapters": adapter_status,
        "features": {
            "multi_platform": True,
            "message_normalization": True,
            "ui_abstraction": True
        }
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    """
    adapters = adapter_registry.get_all()
    
    return {
        "ready": len(adapters) > 0,
        "adapters_count": len(adapters)
    }