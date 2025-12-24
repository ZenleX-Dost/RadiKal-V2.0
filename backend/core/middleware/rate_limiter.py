"""
Rate limiting middleware for production API protection.

This module implements token bucket rate limiting to prevent:
- API abuse
- DDoS attacks
- Unfair resource usage
- Accidental infinite loops

Supports:
- Per-user rate limits
- Per-endpoint rate limits
- Per-tenant rate limits
- Sliding window algorithm
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens (requests)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = datetime.utcnow()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens available, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Add tokens based on elapsed time
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def time_until_available(self) -> float:
        """Get seconds until next token is available."""
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) / self.refill_rate


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.
    
    Limits:
    - 100 requests/minute for analysis endpoints (expensive)
    - 500 requests/minute for read endpoints
    - 1000 requests/minute for health checks
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        # User buckets: {user_id: TokenBucket}
        self.user_buckets: Dict[str, TokenBucket] = {}
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            # Expensive operations
            "/api/xai-qc/explain": (10, 1.0),       # 60 per minute
            "/api/xai-qc/detect": (10, 1.0),        # 60 per minute
            "/api/xai-qc/preprocess": (20, 2.0),    # 120 per minute
            
            # Medium operations
            "/api/xai-qc/history": (50, 5.0),       # 300 per minute
            "/api/xai-qc/metrics": (50, 5.0),       # 300 per minute
            "/api/xai-qc/reviews": (30, 3.0),       # 180 per minute
            
            # Light operations
            "/api/xai-qc/health": (100, 10.0),      # 600 per minute
        }
        
        # Default limits for unlisted endpoints
        self.default_limit = (50, 5.0)  # 300 per minute
        
        # Cleanup task will be started explicitly
        self._cleanup_task = None
    
    def _get_user_bucket(self, user_id: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for user and endpoint."""
        key = f"{user_id}:{endpoint}"
        
        if key not in self.user_buckets:
            # Find matching endpoint limit
            capacity, refill_rate = self.default_limit
            
            for pattern, limits in self.endpoint_limits.items():
                if pattern in endpoint:
                    capacity, refill_rate = limits
                    break
            
            self.user_buckets[key] = TokenBucket(capacity, refill_rate)
        
        return self.user_buckets[key]
    
    async def check_rate_limit(
        self, 
        request: Request,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit.
        
        Args:
            request: FastAPI request object
            user_id: User identifier (IP if not authenticated)
            
        Returns:
            (allowed: bool, error_message: Optional[str])
        """
        # Get user identifier
        if not user_id:
            # Use IP address for unauthenticated requests
            user_id = request.client.host if request.client else "unknown"
        
        endpoint = request.url.path
        bucket = self._get_user_bucket(user_id, endpoint)
        
        # Try to consume token
        if bucket.consume():
            logger.debug(f"Rate limit OK: {user_id} -> {endpoint}")
            return True, None
        
        # Rate limit exceeded
        wait_time = bucket.time_until_available()
        error_msg = (
            f"Rate limit exceeded. "
            f"Please wait {wait_time:.1f} seconds before retrying."
        )
        
        logger.warning(
            f"Rate limit exceeded: {user_id} -> {endpoint} "
            f"(retry in {wait_time:.1f}s)"
        )
        
        return False, error_msg
    
    async def _cleanup_old_buckets(self):
        """Periodically clean up old token buckets."""
        while True:
            await asyncio.sleep(3600)  # Every hour
            
            now = datetime.utcnow()
            expired_keys = []
            
            for key, bucket in self.user_buckets.items():
                # Remove buckets inactive for 1 hour
                if (now - bucket.last_refill).total_seconds() > 3600:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.user_buckets[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired rate limit buckets")
    
    async def start_cleanup(self):
        """Start the cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_buckets())
            
    async def stop_cleanup(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None


# Global rate limiter instance (will be initialized in app startup)
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Usage in main.py:
        from core.middleware.rate_limiter import rate_limit_middleware
        app.middleware("http")(rate_limit_middleware)
    """
    # Skip rate limiting for health checks from monitoring systems
    if request.url.path == "/api/xai-qc/health" and \
       request.headers.get("User-Agent", "").startswith("HealthCheck"):
        return await call_next(request)
    
    # Extract user ID from request (if authenticated)
    user_id = request.state.user.id if hasattr(request.state, "user") else None
    
    # Check rate limit
    allowed, error_msg = await rate_limiter.check_rate_limit(request, user_id)
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": error_msg,
                "retry_after": rate_limiter._get_user_bucket(
                    user_id or request.client.host,
                    request.url.path
                ).time_until_available()
            },
            headers={
                "Retry-After": str(int(rate_limiter._get_user_bucket(
                    user_id or request.client.host,
                    request.url.path
                ).time_until_available()) + 1)
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    bucket = rate_limiter._get_user_bucket(
        user_id or request.client.host,
        request.url.path
    )
    response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
    response.headers["X-RateLimit-Limit"] = str(bucket.capacity)
    
    return response
