"""Settings read from environment variables (12-factor style).

Nothing here is secret-safe for production: real keys belong in a secrets
manager (AWS Secrets Manager / SSM Parameter Store), not in defaults.
"""

import os
from dataclasses import dataclass, field


def _parse_keys(raw: str) -> dict[str, str]:
    """'key1:rw,key2:ro' -> {'key1': 'rw', 'key2': 'ro'}"""
    keys = {}
    for pair in filter(None, (p.strip() for p in raw.split(","))):
        key, _, scope = pair.partition(":")
        keys[key] = scope or "ro"
    return keys


@dataclass
class Settings:
    db_path: str = "data/observations.json"  # ":memory:" for tests
    api_keys: dict[str, str] = field(
        default_factory=lambda: {"dev-key-123": "rw", "readonly-key-789": "ro"}
    )
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5500", "http://127.0.0.1:5500"]
    )
    # Token bucket: `capacity` requests in a burst, refilled at `rate` per second.
    rate_capacity_keyed: int = 100
    rate_refill_keyed: float = 10.0
    rate_capacity_anon: int = 10
    rate_refill_anon: float = 1.0

    @classmethod
    def from_env(cls) -> "Settings":
        s = cls()
        env = os.environ
        if "DB_PATH" in env:
            s.db_path = env["DB_PATH"]
        if "API_KEYS" in env:
            s.api_keys = _parse_keys(env["API_KEYS"])
        if "CORS_ORIGINS" in env:
            s.cors_origins = [o.strip() for o in env["CORS_ORIGINS"].split(",") if o.strip()]
        if "RATE_CAPACITY_ANON" in env:
            s.rate_capacity_anon = int(env["RATE_CAPACITY_ANON"])
        if "RATE_REFILL_ANON" in env:
            s.rate_refill_anon = float(env["RATE_REFILL_ANON"])
        return s
