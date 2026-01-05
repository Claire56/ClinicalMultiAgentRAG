"""Rate limiting middleware."""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog
from app.core.redis_client import get_redis
from app.core.config import settings

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Get client identifier (API key or IP)
        client_id = self._get_client_id(request)
        
        try:
            redis = await get_redis()
            
            # Check per-minute limit
            minute_key = f"rate_limit:minute:{client_id}"
            minute_count = await redis.incr(minute_key)
            if minute_count == 1:
                await redis.expire(minute_key, 60)
            
            if minute_count > settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(
                    "Rate limit exceeded (minute)",
                    client_id=client_id,
                    path=request.url.path,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"},
                )
            
            # Check per-hour limit
            hour_key = f"rate_limit:hour:{client_id}"
            hour_count = await redis.incr(hour_key)
            if hour_count == 1:
                await redis.expire(hour_key, 3600)
            
            if hour_count > settings.RATE_LIMIT_PER_HOUR:
                logger.warning(
                    "Rate limit exceeded (hour)",
                    client_id=client_id,
                    path=request.url.path,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Hourly rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "3600"},
                )
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            # Allow request to proceed if Redis is down (fail open)
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try API key first
        api_key = request.headers.get(settings.API_KEY_HEADER_NAME.lower())
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

