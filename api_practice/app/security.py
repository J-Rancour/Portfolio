"""API-key auth as FastAPI dependencies.

401 Unauthorized = "I don't know who you are" (missing or bad credentials).
403 Forbidden    = "I know who you are, and you can't do this" (wrong scope).
"""

import secrets

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def lookup_scope(request: Request, key: str | None) -> str | None:
    if not key:
        return None
    for known, scope in request.app.state.settings.api_keys.items():
        # Constant-time compare so response timing doesn't leak key prefixes.
        if secrets.compare_digest(known, key):
            return scope
    return None


def require_write(request: Request, key: str | None = Depends(api_key_header)) -> str:
    scope = lookup_scope(request, key)
    if scope is None:
        raise HTTPException(401, "Missing or invalid API key", headers={"WWW-Authenticate": "ApiKey"})
    if scope != "rw":
        raise HTTPException(403, "This API key is read-only")
    return key
