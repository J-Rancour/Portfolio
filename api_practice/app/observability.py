"""Request IDs, timing, structured logs and a tiny metrics counter.

The request ID is the thread you pull when debugging: the client sees it in the
X-Request-ID header and error bodies, and every log line carries it. If a caller
sends their own X-Request-ID we reuse it, so one ID can follow a request across
several services.
"""

import json
import logging
import time
import uuid
from collections import Counter

from fastapi import FastAPI, Request

log = logging.getLogger("api")


def install_observability(app: FastAPI) -> None:
    app.state.metrics = Counter()

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
        app.state.metrics["requests_total"] += 1
        app.state.metrics[f"status_{response.status_code}"] += 1
        # One JSON object per line: easy to grep locally, and CloudWatch Logs
        # Insights / ELK can query the fields directly.
        log.info(json.dumps({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": round(elapsed_ms, 1),
        }))
        return response
