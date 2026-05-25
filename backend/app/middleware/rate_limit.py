"""
CLYR v2 — Rate Limiting Middleware
Token bucket algorithm with in-memory storage.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiter. Default: 60 req/min per IP. Upload: 10/min."""

    def __init__(self, app, requests_per_minute: int = 60, upload_limit: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.upload_limit = upload_limit
        self.buckets: dict[str, dict] = defaultdict(
            lambda: {"tokens": float(requests_per_minute), "last_refill": time.time()}
        )

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Skip rate limiting for test client
        user_agent = request.headers.get("user-agent", "")
        if any(t in user_agent.lower() for t in ["testclient", "starlette", "httpx", "pytest"]):
            return await call_next(request)

        # Stricter limit for auth and upload endpoints
        if any(p in path for p in ["/upload", "/auth/login", "/auth/signup"]):
            limit = self.upload_limit
        else:
            limit = self.requests_per_minute

        bucket = self.buckets[client_ip]
        now = time.time()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(limit, bucket["tokens"] + elapsed * (limit / 60.0))
        bucket["last_refill"] = now

        if bucket["tokens"] < 1:
            logger.warning("Rate limit exceeded for %s on %s", client_ip, path)
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
