import redis.asyncio as redis
from app.core.config import settings

redis_client = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    host, port = settings.REDIS_ADDR.split(":")
    redis_client = redis.Redis(
        host=host,
        port=int(port),
        decode_responses=True,
    )
    
    # Test connection
    await redis_client.ping()
    print("Redis connected successfully")

async def get_redis():
    """Get Redis client"""
    return redis_client