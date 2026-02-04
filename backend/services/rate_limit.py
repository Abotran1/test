from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict


@dataclass
class RateLimitStatus:
    allowed: bool
    retry_after_seconds: int | None = None


class RateLimiter:
    """Simple in-memory rate limiter stub.

    Replace with Redis or API gateway policy for production usage.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list[datetime]] = {}

    def check(self, key: str) -> RateLimitStatus:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        timestamps = [ts for ts in self._requests.get(key, []) if ts >= window_start]
        if len(timestamps) >= self.max_requests:
            retry_after = int((timestamps[0] + timedelta(seconds=self.window_seconds) - now).total_seconds())
            return RateLimitStatus(allowed=False, retry_after_seconds=max(retry_after, 1))
        timestamps.append(now)
        self._requests[key] = timestamps
        return RateLimitStatus(allowed=True)
