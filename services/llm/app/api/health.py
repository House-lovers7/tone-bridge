from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis_client import get_redis
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "llm",
        "timestamp": int(time.time())
    }

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Readiness check endpoint"""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        # Check Redis connection
        await redis_client.ping()
        
        return {
            "status": "ready",
            "service": "llm",
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "not ready",
            "service": "llm",
            "error": str(e),
            "timestamp": int(time.time())
        }