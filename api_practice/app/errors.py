"""One error shape for every failure, so clients only parse one format:

    {"error": {"code": "not_found", "message": "...", "details": ...}, "request_id": "..."}
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("api")

CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
}


def error_response(request: Request, status: int, message: str, details=None, headers=None) -> JSONResponse:
    body = {
        "error": {"code": CODES.get(status, "error"), "message": message, "details": details},
        "request_id": getattr(request.state, "request_id", None),
    }
    return JSONResponse(body, status_code=status, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return error_response(request, exc.status_code, str(exc.detail), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "problem": e["msg"]} for e in exc.errors()
        ]
        return error_response(request, 422, "Request failed validation", details)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # Never leak stack traces to clients; the request_id lets you find the log line.
        log.exception("unhandled error request_id=%s", getattr(request.state, "request_id", None))
        return error_response(request, 500, "Internal server error")
