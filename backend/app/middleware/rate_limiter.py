"""
Rate limiting middleware using in-memory sliding window.
"""
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max requests in 1 second


class RateLimiter:
    """
    In-memory rate limiter using sliding window.
    For production, use Redis-based rate limiting.
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._minute_windows: dict[str, list[float]] = defaultdict(list)
        self._hour_windows: dict[str, list[float]] = defaultdict(list)
        self._second_windows: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def _clean_old_entries(self, window: list[float], max_age: float) -> list[float]:
        """Remove entries older than max_age seconds."""
        now = time.time()
        return [t for t in window if now - t < max_age]

    async def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for the given key.
        Returns (allowed, info) tuple.
        """
        async with self._lock:
            now = time.time()

            # Clean old entries
            self._second_windows[key] = self._clean_old_entries(
                self._second_windows[key], 1
            )
            self._minute_windows[key] = self._clean_old_entries(
                self._minute_windows[key], 60
            )
            self._hour_windows[key] = self._clean_old_entries(
                self._hour_windows[key], 3600
            )

            # Check limits
            second_count = len(self._second_windows[key])
            minute_count = len(self._minute_windows[key])
            hour_count = len(self._hour_windows[key])

            info = {
                "second": f"{second_count}/{self.config.burst_limit}",
                "minute": f"{minute_count}/{self.config.requests_per_minute}",
                "hour": f"{hour_count}/{self.config.requests_per_hour}",
            }

            # Check burst limit
            if second_count >= self.config.burst_limit:
                return False, {**info, "retry_after": 1, "limit": "burst"}

            # Check per-minute limit
            if minute_count >= self.config.requests_per_minute:
                oldest = min(self._minute_windows[key]) if self._minute_windows[key] else now
                retry_after = max(1, int(60 - (now - oldest)))
                return False, {**info, "retry_after": retry_after, "limit": "minute"}

            # Check per-hour limit
            if hour_count >= self.config.requests_per_hour:
                oldest = min(self._hour_windows[key]) if self._hour_windows[key] else now
                retry_after = max(1, int(3600 - (now - oldest)))
                return False, {**info, "retry_after": retry_after, "limit": "hour"}

            # Record request
            self._second_windows[key].append(now)
            self._minute_windows[key].append(now)
            self._hour_windows[key].append(now)

            return True, info


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    Rate limiting middleware.
    Uses client IP as the key.
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    allowed, info = await rate_limiter.is_allowed(client_ip)

    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Çok fazla istek. Lütfen bekleyin.",
                    "details": info,
                }
            },
            headers={
                "Retry-After": str(info.get("retry_after", 60)),
                "X-RateLimit-Limit": info.get("minute", ""),
            },
        )

    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = info.get("minute", "").split("/")[0]
    
    return response
