import asyncio
from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional
from fastapi import Request
from app.core.exceptions import RateLimitExceededError


class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter for sensitive API endpoints.
    Protects authentication, analysis, and submission endpoints from automated brute force.
    """

    def __init__(self, requests_limit: int = 60, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        """
        Record request timestamp for key and raise RateLimitExceededError if limit is breached.
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._history.get(key, [])
            # Purge expired timestamps
            timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(timestamps) >= self.requests_limit:
                retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
                raise RateLimitExceededError(
                    f"Rate limit exceeded: maximum {self.requests_limit} requests per {self.window_seconds}s. Try again in {retry_after}s.",
                    details={"retry_after_seconds": retry_after},
                )

            timestamps.append(now)
            self._history[key] = timestamps

    def reset(self) -> None:
        """Reset limiter history (useful for test isolation)."""
        with self._lock:
            self._history.clear()


def rate_limit(requests_limit: int = 30, window_seconds: int = 60):
    """
    FastAPI dependency factory enforcing rate limits by client IP or authenticated user.
    Bypassed in test environment to permit high-frequency integration testing suites.
    """
    limiter = InMemoryRateLimiter(requests_limit=requests_limit, window_seconds=window_seconds)

    async def dependency(request: Request) -> None:
        import os
        from app.core.config import get_settings
        if (
            os.environ.get("ENVIRONMENT", "").lower() == "test"
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
            or get_settings().ENVIRONMENT.lower() == "test"
        ):
            return

        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown_client"

        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"
        limiter.check(key)

    return dependency
