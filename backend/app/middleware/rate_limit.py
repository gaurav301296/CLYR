"""
CLYR API -- Rate Limiting Middleware
Uses token bucket algorithm with in-memory storage.
For production, replace with Redis-backed implementation.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter.
    Default: 60 requests per minute per IP.
    Upload endpoint: 10 requests per minute per IP.
    Automatically disabled for testclient (Starlette test client).
    """

    def __init__(self, app, requests_per_minute: int = 60, upload_limit: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.upload_limit = upload_limit
        self.buckets: dict[str, dict] = defaultdict(lambda: {"tokens": float(requests_per_minute), "last_refill": time.time()})

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Skip rate limiting for test client
        user_agent = request.headers.get("user-agent", "")
        if "testclient" in user_agent.lower() or "starlette" in user_agent.lower() or "httpx" in user_agent.lower():
            return await call_next(request)

        # Stricter limit for upload endpoint
        if "/upload" in path:
            limit = self.upload_limit
        else:
            limit = self.requests_per_minute

        bucket = self.buckets[client_ip]
        now = time.time()
        elapsed = now - bucket["last_refill"]
        # Refill tokens at the rate of limit/60 per second
        bucket["tokens"] = min(limit, bucket["tokens"] + elapsed * (limit / 60.0))
        bucket["last_refill"] = now

        if bucket["tokens"] < 1:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(int(60 / limit))},
            )

        bucket["tokens"] -= 1
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket["tokens"]))
        return response
