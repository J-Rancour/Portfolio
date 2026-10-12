"""App factory. Run with:  uvicorn app.main:app --reload --port 8000

A factory (create_app) instead of a module-level singleton lets tests build
an isolated app with an in-memory database and custom limits.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .errors import install_error_handlers
from .observability import install_observability
from .ratelimit import install_rate_limit
from .routes import router
from .storage import ObservationRepo
from .ws import Hub

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield  # startup work would go above this line
        app.state.repo.close()

    app = FastAPI(title="Aviation Weather Observations API", version="1.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.repo = ObservationRepo(settings.db_path)
    app.state.hub = Hub()

    install_error_handlers(app)
    app.include_router(router)

    # Middleware order matters: the LAST one added wraps all the others, so it
    # runs first on the way in and last on the way out.
    #   CORS -> observability (request id, timing) -> rate limit -> route
    install_rate_limit(app)
    install_observability(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
        # Browsers hide response headers from JavaScript unless they're listed here.
        expose_headers=[
            "Location", "Retry-After", "WWW-Authenticate", "X-Request-ID", "X-Process-Time-Ms",
            "X-RateLimit-Limit", "X-RateLimit-Remaining",
        ],
    )
    return app


app = create_app()
