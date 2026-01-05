"""
Redis client for caching and rate limiting.
"""
import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

redis_client: redis.Redis = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    try:
        redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

