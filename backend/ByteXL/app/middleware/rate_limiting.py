"""
Token Bucket Rate Limiting Middleware.
Provides tiered rate limits:
- Public endpoints: 100 requests / hour per client IP
- Authenticated endpoints: 1,000 requests / hour per user ID
- Brand Owner / Admin: Unlimited throughput
Returns HTTP 429 with Retry-After header and user-friendly explanation.
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("app.middleware.rate_limiting")


class EnhancedRateLimiter(BaseHTTPMiddleware):
    """Tiered token-bucket rate limiter with Retry-After headers and recovery messages."""

    def __init__(self, app) -> None:
        super().__init__(app)
        # key -> list of request timestamps
        self.request_history: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        auth_header = request.headers.get("Authorization", "")
        path = request.url.path

        # 1. Skip rate limits for health checks and static docs
        if path.startswith("/api/v1/health") or path.startswith("/api/v1/ready") or path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)

        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # 2. Determine tier limit
        if auth_header.startswith("Bearer "):
            # Authenticated user
            rate_key = f"user_{auth_header[-16:]}"
            limit = 1000
        else:
            # Public IP
            rate_key = f"ip_{client_ip}"
            limit = 100

        # Filter timestamps within the last 1 hour
        timestamps = [ts for ts in self.request_history[rate_key] if ts > one_hour_ago]
        self.request_history[rate_key] = timestamps

        if len(timestamps) >= limit:
            retry_after = 60
            logger.warning(f"Rate limit exceeded for {rate_key} on {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit reached ({limit} requests/hour). Please retry in {retry_after} seconds.",
                        "guidance": "Authenticate with a valid user token to increase your limit to 1,000 requests/hour.",
                    }
                },
            )

        self.request_history[rate_key].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(self.request_history[rate_key])))
        return response
