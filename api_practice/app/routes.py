"""HTTP + WebSocket endpoints.

Resource design: nouns in the URL, verbs are the HTTP methods.
    GET    /api/v1/observations        list (filter + paginate)
    POST   /api/v1/observations        create   -> 201 + Location header
    GET    /api/v1/observations/{id}   read     -> 200 / 404
    PATCH  /api/v1/observations/{id}   partial update
    DELETE /api/v1/observations/{id}   delete   -> 204, no body
The /v1 prefix lets a breaking v2 live next to v1 while clients migrate.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, WebSocket
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from . import wxcore
from .models import Observation, ObservationCreate, ObservationPage, ObservationPatch
from .security import require_write
from .storage import DuplicateError

router = APIRouter()


def iso_utc(dt: datetime) -> str:
    """Store one canonical form so string comparison == time comparison."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)  # treat naive timestamps as UTC (METARs are always Zulu)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def present(doc: dict) -> dict:
    """Stored document -> API representation (adds computed fields)."""
    return {**doc, "flight_category": wxcore.flight_category(doc["visibility_sm"], doc.get("ceiling_ft"))}


def repo(request: Request):
    return request.app.state.repo


@router.get("/health", tags=["ops"])
async def health():
    # Liveness check for load balancers / ECS. Keep it cheap and dependency-free.
    return {"status": "ok", "engine": wxcore.ENGINE, "time": iso_utc(datetime.now(UTC))}


@router.get("/metrics", tags=["ops"])
async def metrics(request: Request):
    m = request.app.state.metrics
    return {
        "requests_total": m["requests_total"],
        "by_status": {k.removeprefix("status_"): v for k, v in m.items() if k.startswith("status_")},
        "ws_clients": len(request.app.state.hub.clients),
        "engine": wxcore.ENGINE,
    }


# Note: these handlers are `async` but TinyDB does blocking file I/O. That's fine
# for a tiny local file; with a real database you'd use an async driver (motor,
# aioboto3) or plain `def` handlers, which FastAPI runs in a thread pool.


@router.get("/api/v1/observations", response_model=ObservationPage, tags=["observations"])
async def list_observations(
    request: Request,
    station: str | None = Query(default=None, pattern=r"^[A-Za-z]{4}$"),
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    docs, total = repo(request).list(
        station=station.upper() if station else None,
        since=iso_utc(since) if since else None,
        until=iso_utc(until) if until else None,
        limit=limit,
        offset=offset,
    )
    return {"items": [present(d) for d in docs], "total": total, "limit": limit, "offset": offset}


@router.post(
    "/api/v1/observations",
    status_code=201,
    response_model=Observation,
    tags=["observations"],
    dependencies=[Depends(require_write)],
)
async def create_observation(body: ObservationCreate, request: Request, response: Response):
    doc = body.model_dump()
    doc["observed_at"] = iso_utc(body.observed_at)
    try:
        saved = repo(request).create(doc)
    except DuplicateError as e:
        raise HTTPException(409, str(e))
    response.headers["Location"] = f"/api/v1/observations/{saved['id']}"
    out = present(saved)
    await request.app.state.hub.broadcast({"event": "observation.created", "data": out})
    return out


@router.get("/api/v1/observations/{obs_id}", response_model=Observation, tags=["observations"])
async def get_observation(obs_id: str, request: Request):
    doc = repo(request).get(obs_id)
    if doc is None:
        raise HTTPException(404, f"Observation {obs_id} not found")
    return present(doc)


@router.patch(
    "/api/v1/observations/{obs_id}",
    response_model=Observation,
    tags=["observations"],
    dependencies=[Depends(require_write)],
)
async def patch_observation(obs_id: str, body: ObservationPatch, request: Request):
    current = repo(request).get(obs_id)
    if current is None:
        raise HTTPException(404, f"Observation {obs_id} not found")
    # exclude_unset: only fields the client actually sent, so omitted != null.
    changes = body.model_dump(exclude_unset=True)
    try:
        # Re-validate the merged document, e.g. reject {"temperature_c": null}.
        ObservationCreate.model_validate({**current, **changes})
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    return present(repo(request).update(obs_id, changes))


@router.delete(
    "/api/v1/observations/{obs_id}",
    status_code=204,
    tags=["observations"],
    dependencies=[Depends(require_write)],
)
async def delete_observation(obs_id: str, request: Request):
    if not repo(request).delete(obs_id):
        raise HTTPException(404, f"Observation {obs_id} not found")
    return Response(status_code=204)


@router.get("/api/v1/tools/flight-category", tags=["tools"])
async def flight_category(
    visibility_sm: float = Query(ge=0), ceiling_ft: float | None = Query(default=None, ge=0)
):
    return {"category": wxcore.flight_category(visibility_sm, ceiling_ft), "engine": wxcore.ENGINE}


@router.get("/api/v1/tools/wind-components", tags=["tools"])
async def wind_components(
    wind_dir: float = Query(ge=0, le=360),
    wind_speed: float = Query(ge=0),
    runway_heading: float = Query(ge=0, le=360),
):
    head, cross = wxcore.wind_components(wind_dir, wind_speed, runway_heading)
    return {"headwind_kt": round(head, 1), "crosswind_kt": round(cross, 1), "engine": wxcore.ENGINE}


@router.websocket("/ws/observations")
async def observations_feed(ws: WebSocket):
    await ws.app.state.hub.serve(ws)
