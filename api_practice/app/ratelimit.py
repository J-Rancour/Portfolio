"""Token-bucket rate limiting.

Each client gets a bucket holding up to `capacity` tokens that refills at
`rate` tokens/second. A request spends one token; an empty bucket means 429.
Bursts up to `capacity` are allowed, the long-run average is capped at `rate`.

Limits: buckets live in this process's memory, so they reset on restart and
aren't shared between instances. Behind a load balancer you'd keep them in
Redis/ElastiCache, or let API Gateway usage plans do it.
"""

import math
import time

from fastapi import FastAPI, Request

from .errors import error_response
from .security import lookup_scope


class TokenBucket:
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity
        self.rate = rate
        self.tokens = float(capacity)
        self.updated = time.monotonic()  # monotonic: immune to wall-clock jumps

    def take(self) -> tuple[bool, float]:
        """Returns (allowed, seconds until a token is available)."""
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True, 0.0
        return False, (1 - self.tokens) / self.rate


def install_rate_limit(app: FastAPI) -> None:
    buckets: dict[str, TokenBucket] = {}

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        s = request.app.state.settings
        key = request.headers.get("x-api-key")
        # Only *valid* keys get their own bucket. Otherwise a client could dodge
        # the limit by sending a different made-up key on every request.
        if lookup_scope(request, key):
            identity, capacity, rate = f"key:{key}", s.rate_capacity_keyed, s.rate_refill_keyed
        else:
            host = request.client.host if request.client else "unknown"
            identity, capacity, rate = f"ip:{host}", s.rate_capacity_anon, s.rate_refill_anon

        bucket = buckets.setdefault(identity, TokenBucket(capacity, rate))
        allowed, wait = bucket.take()
        headers = {
            "X-RateLimit-Limit": str(capacity),
            "X-RateLimit-Remaining": str(int(bucket.tokens)),
        }
        if not allowed:
            headers["Retry-After"] = str(math.ceil(wait))
            return error_response(request, 429, "Too many requests, slow down", headers=headers)

        response = await call_next(request)
        response.headers.update(headers)
        return response
