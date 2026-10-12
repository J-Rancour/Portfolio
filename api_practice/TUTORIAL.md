# Tutorial: build a REST API from scratch, one step at a time

You'll build an **Aviation Weather Observations API** in 12 steps. Each step has:

- **Build:** the minimum code for the step. The full version is in `app/`.
- **Verify:** `python cli.py check N`, or the step's "Run checks" button in the frontend.
- **Say it out loud:** the 30-second explanation you'd give an interviewer. Practise saying it.
- **Pitfalls:** mistakes people actually make. Interviewers love asking about these.

> Work in a new folder (`my_api/`) and run your server on port 8001. Then point the checks
> at it: `python cli.py --base-url http://127.0.0.1:8001 check 1`. Copying the reference
> teaches far less than typing it yourself and fixing your own failures.

```
my_api/
  app/
    __init__.py
    main.py       # step 1
    models.py     # step 2
    storage.py    # step 2
    routes.py     # step 2
    errors.py     # step 3
    security.py   # step 5
    ratelimit.py  # step 6
    ws.py         # step 7
    wxcore.py     # step 8
    observability.py  # step 9
  native/         # step 8
  tests/          # step 11
```

---

## Before you start: HTTP in five minutes

A request is a **method** + **path** + **headers** + optional **body**. A response is a
**status code** + **headers** + optional **body**. That's all REST runs on.

```
POST /api/v1/observations HTTP/1.1          <- method, path, version
Host: 127.0.0.1:8000
Content-Type: application/json              <- headers
X-API-Key: dev-key-123

{"station": "KJFK", "visibility_sm": 10, ...}   <- body

HTTP/1.1 201 Created                         <- status
Location: /api/v1/observations/9f2c...       <- headers
Content-Type: application/json

{"id": "9f2c...", "station": "KJFK", ...}    <- body
```

| Method | Meaning | Safe? | Idempotent? | Typical success |
|---|---|---|---|---|
| GET | read | yes | yes | 200 |
| POST | create / run an action | no | **no** | 201 (+ Location), 202 for async |
| PUT | replace the whole resource | no | yes | 200 / 204 |
| PATCH | change some fields | no | not necessarily | 200 |
| DELETE | remove | no | yes | 204 |

*Safe* means it changes nothing on the server. *Idempotent* means sending it once or five
times leaves the same server state, so a client can retry it after a timeout. POST isn't
idempotent, which is why payment APIs add an `Idempotency-Key` header.

Status code families: **2xx** success, **3xx** redirect/cache, **4xx** the client's fault
(don't retry unchanged), **5xx** the server's fault (often worth retrying with backoff).

---

## Step 1: Skeleton & health check

**Build**

```bash
pip install fastapi uvicorn websockets tinydb
```

```python
# app/main.py
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Aviation Weather Observations API")

    @app.get("/health")
    async def health():
        return {"status": "ok", "time": datetime.now(UTC).isoformat()}

    # Lets the tutorial frontend (a different origin: port 5500) call this API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
        allow_methods=["*"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
        expose_headers=["Location", "Retry-After", "WWW-Authenticate", "X-Request-ID",
                        "X-Process-Time-Ms", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    return app


app = create_app()
```

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Open http://127.0.0.1:8001/docs. FastAPI generated that page from your code.

**Verify:** `python cli.py --base-url http://127.0.0.1:8001 check 1`

**Say it out loud**
- "uvicorn is the ASGI server: it handles sockets and HTTP parsing. FastAPI is the framework that routes requests to my functions and validates data."
- "The health endpoint is for load balancers and orchestrators. I keep it cheap and free of dependencies, so a slow database doesn't make every instance look dead and get restarted. Some teams add a separate *readiness* check that does test dependencies."
- "I use an app factory so tests can build a fresh app with different settings."

**CORS, briefly:** browsers block JavaScript on origin A (`127.0.0.1:5500`) from reading
responses from origin B (`127.0.0.1:8001`) unless B allows it with `Access-Control-Allow-Origin`.
For non-simple requests (custom headers like `X-API-Key`, JSON bodies), the browser first sends
an `OPTIONS` **preflight**. CORS protects users' browsers. It is **not** API security:
curl and the CLI ignore it completely.

**Pitfalls**
- `allow_origins=["*"]` together with credentials (cookies) is rejected by browsers.
- Forgetting `expose_headers`: the browser receives `Retry-After`, but `response.headers.get("Retry-After")` returns `null` in JS.

---

## Step 2: CRUD on a resource

**Build:** three pieces: the **schema** (what valid data looks like), the **storage** (where
documents live) and the **routes** (HTTP ↔ storage).

```python
# app/models.py
from datetime import datetime
from pydantic import BaseModel, Field

class ObservationCreate(BaseModel):
    station: str = Field(pattern=r"^[A-Z]{4}$")          # ICAO id, e.g. KJFK
    observed_at: datetime
    temperature_c: float = Field(ge=-90, le=60)
    dewpoint_c: float = Field(ge=-90, le=60)
    wind_dir_deg: int = Field(ge=0, le=360)
    wind_speed_kt: int = Field(ge=0, le=250)
    visibility_sm: float = Field(ge=0, le=100)
    ceiling_ft: int | None = Field(default=None, ge=0)   # None = no ceiling
    raw_metar: str | None = None

class ObservationPatch(BaseModel):                       # every field optional
    temperature_c: float | None = Field(default=None, ge=-90, le=60)
    visibility_sm: float | None = Field(default=None, ge=0, le=100)
    # ... the rest of the editable fields
```

```python
# app/storage.py: a document store behind a tiny repository class
import uuid
from pathlib import Path
from tinydb import Query, TinyDB
Obs = Query()

class ObservationRepo:
    def __init__(self, path="data/observations.json"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.table = TinyDB(path).table("observations")

    def create(self, doc):
        doc = {"id": uuid.uuid4().hex, **doc}
        self.table.insert(doc)
        return doc

    def get(self, obs_id):           return self.table.get(Obs.id == obs_id)
    def update(self, obs_id, changes):
        return self.get(obs_id) if self.table.update(changes, Obs.id == obs_id) else None
    def delete(self, obs_id):        return bool(self.table.remove(Obs.id == obs_id))
```

```python
# app/routes.py
from fastapi import APIRouter, HTTPException, Request, Response
from .models import ObservationCreate, ObservationPatch

router = APIRouter(prefix="/api/v1")

@router.post("/observations", status_code=201)
async def create(body: ObservationCreate, request: Request, response: Response):
    doc = body.model_dump(mode="json")              # datetimes -> ISO strings
    saved = request.app.state.repo.create(doc)
    response.headers["Location"] = f"/api/v1/observations/{saved['id']}"
    return saved

@router.get("/observations/{obs_id}")
async def get_one(obs_id: str, request: Request):
    doc = request.app.state.repo.get(obs_id)
    if doc is None:
        raise HTTPException(404, f"Observation {obs_id} not found")
    return doc

@router.patch("/observations/{obs_id}")
async def patch(obs_id: str, body: ObservationPatch, request: Request):
    changes = body.model_dump(exclude_unset=True)   # only fields the client sent
    doc = request.app.state.repo.update(obs_id, changes)
    if doc is None:
        raise HTTPException(404, f"Observation {obs_id} not found")
    return doc

@router.delete("/observations/{obs_id}", status_code=204)
async def delete(obs_id: str, request: Request):
    if not request.app.state.repo.delete(obs_id):
        raise HTTPException(404, f"Observation {obs_id} not found")
    return Response(status_code=204)
```

Wire it up in `create_app()`: `app.state.repo = ObservationRepo()` and `app.include_router(router)`.
You also need a list endpoint, `GET /observations?station=`. Write it now with just the
station filter; step 4 adds paging.

**Verify:** `check 2`. Then try `python cli.py req POST /api/v1/observations -d "{...}"`, or use the console tab.

**Say it out loud**
- "URLs name resources (nouns). HTTP methods are the verbs. POST returns 201 with a Location header pointing at the new resource."
- "PATCH is a partial update. I use `exclude_unset` so 'field not sent' and 'field sent as null' mean different things."
- "Routes only talk to a repository class, so moving from TinyDB to DynamoDB or MongoDB touches one file."

**Pitfalls**
- Returning 200 for creates, or 200 with `{"deleted": true}` instead of 204.
- `model_dump()` without `exclude_unset` in PATCH silently overwrites fields with `None`.
- Putting verbs in URLs (`/createObservation`). That's RPC, not REST.

---

## Step 3: Validation & consistent errors

**Build:** two things.

1. **One error envelope** for every failure (`app/errors.py`). Override FastAPI's handlers for
   `HTTPException`, `RequestValidationError` (422) and bare `Exception` (500):

```python
@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    details = [{"field": ".".join(map(str, e["loc"])), "problem": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={
        "error": {"code": "validation_error", "message": "Request failed validation", "details": details}})
```

2. **Business rules** that the type system can't express:
   - Duplicates: one report per station per timestamp. In `create`, raise `DuplicateError`
     if `station` + `observed_at` already exist. The route turns that into **409 Conflict**.
   - Cross-field validation: dewpoint can't be above temperature. Use a Pydantic
     `@model_validator(mode="after")`.
   - Normalise input: upper-case the station; convert timestamps to UTC (`...Z`). Then string
     comparison matches time order, which step 4 relies on.

**Verify:** `check 3`

**Say it out loud**
- "400 means I couldn't parse the request. 422 means it parsed but broke the rules. 404 means it doesn't exist. 409 means it conflicts with the current state, like a duplicate."
- "Every error has the same shape, so clients write one error handler. The 500 handler logs the stack trace and returns a generic message. Clients never see internals."

**Pitfalls**
- Leaking stack traces or SQL in 500 responses (a security issue).
- Check-then-insert races: two concurrent POSTs both pass the duplicate check. Single-process
  async code without an `await` between check and insert is safe. Across processes you need the
  database to enforce it: a unique index (MongoDB), `ConditionExpression="attribute_not_exists(pk)"`
  (DynamoDB) or a UNIQUE constraint (SQL).

---

## Step 4: Filtering & pagination

**Build**

```python
@router.get("/observations")
async def list_obs(request: Request,
                   station: str | None = Query(default=None, pattern=r"^[A-Za-z]{4}$"),
                   since: datetime | None = None, until: datetime | None = None,
                   limit: int = Query(default=20, ge=1, le=100),     # always cap it
                   offset: int = Query(default=0, ge=0)):
    docs, total = request.app.state.repo.list(station, since, until, limit, offset)
    return {"items": docs, "total": total, "limit": limit, "offset": offset}
```

Sort newest first, slice `[offset : offset + limit]` and return `total`.

**Verify:** `check 4`. In the frontend's Observations tab, page through seeded data.

**Say it out loud**
- "Every list endpoint has a capped limit. Unbounded lists eventually return a million rows and take the service down."
- "Offset paging is simple but gets slow on deep pages (the DB still walks the skipped rows) and skips or repeats rows when data changes between pages. For big or fast-changing data I'd use cursor (keyset) paging: return `next_cursor` = the last item's sort key, and query `WHERE observed_at < cursor`. DynamoDB works this way natively with `LastEvaluatedKey`."

**Pitfalls:** filtering in Python after loading everything (fine for TinyDB, wrong for real
databases: push filters into the query and back them with an index).

---

## Step 5: Authentication & authorization

**Build** (`app/security.py`): a FastAPI **dependency** that reads `X-API-Key`.

```python
import secrets
from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
KEYS = {"dev-key-123": "rw", "readonly-key-789": "ro"}   # real keys belong in a secrets manager

def require_write(key: str | None = Depends(api_key_header)):
    scope = next((s for k, s in KEYS.items() if key and secrets.compare_digest(k, key)), None)
    if scope is None:
        raise HTTPException(401, "Missing or invalid API key", headers={"WWW-Authenticate": "ApiKey"})
    if scope != "rw":
        raise HTTPException(403, "This API key is read-only")
```

Attach it to POST, PATCH and DELETE: `@router.post(..., dependencies=[Depends(require_write)])`.
Leave GETs public.

**Verify:** `check 5`. In the console tab, switch between "no key", "made-up key" and "read-only key".

**Say it out loud**
- "401 means you haven't proven who you are. 403 means I know who you are and you're not allowed. A 401 includes `WWW-Authenticate`."
- "API keys are simple and fine for service-to-service calls. For users I'd use OAuth2/OIDC with JWTs (short-lived, signed tokens carrying scopes), validated at the API or at API Gateway with a Cognito or Lambda authorizer. Either way, the key or token only travels over HTTPS."
- "I compare secrets in constant time and store only hashes of keys in a real system."

**Pitfalls:** keys in query strings (they end up in logs and browser history); keys committed
to git; returning 404 vs 403 inconsistently. Some APIs return 404 on purpose to hide that a
resource exists.

---

## Step 6: Rate limiting

**Build** (`app/ratelimit.py`): a token bucket per client, enforced in middleware.

```python
class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity, self.rate = capacity, rate
        self.tokens, self.updated = float(capacity), time.monotonic()

    def take(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True, 0.0
        return False, (1 - self.tokens) / self.rate     # seconds until next token
```

In an `@app.middleware("http")` function: work out the client identity (a valid API key, otherwise
the client IP), take a token, and either return **429** with `Retry-After` or call the route and
add `X-RateLimit-Limit` / `X-RateLimit-Remaining` to the response. Limits here: keyed clients get a
burst of 100 refilling at 10/s; anonymous clients a burst of 10 refilling at 1/s.

**Verify:** `check 6`, and `python cli.py burst /api/v1/observations -n 20` to watch the 429s.

**Say it out loud**
- "A token bucket allows short bursts up to the capacity, and caps the long-run rate at the refill rate. Alternatives: fixed window (simple, but allows 2× bursts at window edges), sliding window log (exact, more memory), leaky bucket (smooths output)."
- "Only valid keys get their own bucket. Otherwise an attacker sends a new fake key on every request and is never limited."
- "This in-memory version works per process. With several instances I'd keep counters in Redis (atomic INCR + EXPIRE, or a Lua script), or push limits to the edge: API Gateway usage plans and throttling, or AWS WAF rate-based rules."
- "Clients should honour `Retry-After` and use exponential backoff with jitter, so a fleet of clients doesn't retry in lockstep."

**Pitfalls:** using `time.time()` (jumps when the clock changes; use a monotonic clock);
rate-limiting `/health` (your load balancer then marks you dead); behind a proxy every client
has the proxy's IP, so you must trust `X-Forwarded-For`, but only from the proxy.

---

## Step 7: WebSockets (server push)

**Build** (`app/ws.py`): keep a set of connected sockets and broadcast on create.

```python
class Hub:
    def __init__(self):
        self.clients = set()

    async def serve(self, ws):
        await ws.accept()
        self.clients.add(ws)
        try:
            await ws.send_json({"event": "hello"})
            while True:
                await ws.receive_text()          # reading is how we notice disconnects
        except WebSocketDisconnect:
            pass
        finally:
            self.clients.discard(ws)

    async def broadcast(self, message):
        for ws in list(self.clients):
            try:
                await ws.send_json(message)
            except Exception:
                self.clients.discard(ws)         # one dead client mustn't break the rest
```

Add `@router.websocket("/ws/observations")`, and in `create` call
`await hub.broadcast({"event": "observation.created", "data": saved})`.

**Verify:** `check 7`. In the frontend's Live feed tab, click Connect and then POST from the console tab.
From a terminal: `python cli.py ws`.

**Say it out loud**
- "The handshake is an HTTP GET with `Upgrade: websocket`. The server answers `101 Switching Protocols`, and the same TCP connection becomes a two-way message channel."
- "I'd use WebSockets for live, two-way data. For one-way server→client updates, Server-Sent Events are simpler (plain HTTP, auto-reconnect). For infrequent updates, polling is fine."
- "Scaling: each instance only knows its own sockets, so broadcasts go through a pub/sub layer (Redis, SNS→SQS per instance) or a managed API Gateway WebSocket API. Load balancers need sticky or long-lived connection support; an ALB handles WebSockets."

**Pitfalls:** no heartbeat, so half-open connections pile up (send pings); blocking calls in an
async handler stall every connection; auth over a WebSocket (browsers can't set custom headers
on the handshake, so use a cookie, a short-lived token in the query string, or a first-message auth).

---

## Step 8: C++ core via ctypes

**Build:** write the computation in C++, exposed through a **C ABI**:

```cpp
// native/wxcore.h
#ifdef _WIN32
#  ifdef WXCORE_BUILD
#    define WX_API __declspec(dllexport)
#  else
#    define WX_API __declspec(dllimport)
#  endif
#else
#  define WX_API __attribute__((visibility("default")))
#endif

extern "C" {
WX_API int  wx_flight_category(double visibility_sm, double ceiling_ft);   // 0=VFR..3=LIFR
WX_API void wx_wind_components(double wind_dir, double wind_speed, double runway_heading,
                               double* headwind_kt, double* crosswind_kt);  // out-params
}
```

Flight categories (FAA): **LIFR** ceiling < 500 ft or vis < 1 sm · **IFR** 500–999 ft or 1–<3 sm
· **MVFR** 1000–3000 ft or 3–5 sm · **VFR** otherwise. The worse of the two wins.

Build it:

| Platform | Command |
|---|---|
| Windows, MSVC | `native\build.bat` (finds Visual Studio with `vswhere`, runs `cl /LD`) |
| Linux / macOS | `sh native/build.sh` (`g++ -shared -fPIC`) |
| Anywhere, CMake | `cmake -S native -B native/build && cmake --build native/build --config Release && ctest --test-dir native/build -C Release` |

Load it from Python:

```python
lib = ctypes.CDLL(str(path))
lib.wx_flight_category.argtypes = [ctypes.c_double, ctypes.c_double]
lib.wx_flight_category.restype = ctypes.c_int

head, cross = ctypes.c_double(), ctypes.c_double()
lib.wx_wind_components(270, 20, 240, ctypes.byref(head), ctypes.byref(cross))
print(head.value, cross.value)   # 17.32, 10.0
```

`app/wxcore.py` falls back to an identical Python version if the library won't load, and the
tests use that Python version as an **oracle** to check the C++ on boundary values.

**Verify:** `check 8` (needs `"engine": "cpp"` in `/health`; restart uvicorn after building).

**Say it out loud**
- "`extern \"C\"` turns off name mangling, so the symbol is just `wx_flight_category` and any language's FFI can find it. Only C types cross the boundary. C++ exceptions must never escape into Python, so catch them on the C++ side and return error codes."
- "If I forget `argtypes`, ctypes refuses Python floats outright, but passes Python ints as C ints. A function expecting doubles then reads garbage, with no error at all (every input came back LIFR when I tried it). If I forget `restype`, a returned `char*` is truncated to an int."
- "Shared library vs static: a `.so`/`.dll` is loaded at runtime and can be swapped without relinking; a static `.a`/`.lib` is copied into the binary."
- "The build pipeline is: preprocess → compile each `.cpp` to an object file → link. 'Undefined reference' is a linker error (a missing library or a missing `extern \"C\"`), not a compiler error."
- "For bigger C++ APIs I'd use pybind11 or nanobind: classes, exceptions and NumPy arrays without hand-written C wrappers."

**Pitfalls**
- **Bitness / ABI mismatch:** 64-bit Python can't load a 32-bit DLL (`[WinError 193]`). Old MinGW `g++` is 32-bit.
- Windows DLL search path: dependent DLLs must be next to the DLL, on PATH, or added with `os.add_dll_directory()`.
- Returning a pointer to a local buffer from C (it dangles once the function returns).
- Linux: forgetting `-fPIC`; `GLIBCXX_x.y not found` when building on a newer distro than you run on.

---

## Step 9: Observability

**Build** (`app/observability.py`): one middleware that

1. reads `X-Request-ID` from the request, or generates one, and stores it on `request.state`;
2. times the request with `time.perf_counter()`;
3. adds `X-Request-ID` and `X-Process-Time-Ms` to the response;
4. logs one JSON line: `{"request_id", "method", "path", "status", "ms"}`;
5. counts requests per status code for `GET /metrics`.

Put `request_id` in error bodies too (step 3's envelope).

**Middleware order matters.** In Starlette the *last* middleware added is the *outermost*. The
reference adds rate limit → observability → CORS, so the order on the way in is CORS →
observability → rate limit → route. That way even 429 responses get request IDs and CORS headers.

**Verify:** `check 9`. Watch the uvicorn terminal while you run checks.

**Say it out loud**
- "Logs say *what* happened, metrics say *how much and how fast*, and traces show *where the time went* across services. Request IDs connect a user's bug report to my logs."
- "Structured JSON logs can be queried: in CloudWatch Logs Insights, `filter status >= 500 | stats count() by path`."
- "I'd alert on symptoms users feel: error rate, p95/p99 latency, saturation. Not on every CPU blip."
- "In production: OpenTelemetry for traces, CloudWatch or Prometheus for metrics, alarms to on-call."

---

## Step 10: HTTPS & WSS

**Build**

```bash
python scripts/make_cert.py      # writes certs/cert.pem + certs/key.pem (self-signed, localhost + 127.0.0.1)
uvicorn app.main:app --host 127.0.0.1 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```

**Verify:** `python cli.py --base-url https://127.0.0.1:8443 --cafile certs/cert.pem check 10`.
Try it without `--cafile` to see the failure. For the browser, open https://127.0.0.1:8443/health
once, accept the warning, then set the frontend's base URL to `https://127.0.0.1:8443`.

> Use a different `DB_PATH` if the HTTP server is still running on the same files.

**Say it out loud**
- "TLS gives confidentiality (encryption), integrity (no tampering) and authentication (the cert proves the server's identity). The client checks the cert chains to a trusted CA and that the hostname matches the Subject Alternative Name."
- "The handshake agrees keys with asymmetric crypto (ECDHE), then switches to fast symmetric encryption (AES-GCM / ChaCha20). TLS 1.3 needs one round trip."
- "`verify=False` doesn't fix certificate errors, it turns off the protection. For a private CA, trust that CA explicitly."
- "On AWS I'd terminate TLS at the ALB or API Gateway with a free ACM certificate. Traffic from the load balancer to the containers stays inside the VPC, or is re-encrypted if compliance requires it."
- "mTLS (mutual TLS) is when the client presents a certificate too. It's common for service-to-service and government systems."

---

## Step 11: Automated tests & CI

**Build**

```python
# tests/conftest.py
@pytest.fixture
def client():
    with TestClient(create_app(Settings(db_path=":memory:"))) as c:   # fresh app + empty DB per test
        yield c

# tests/test_api.py
def test_duplicate_is_409(client):
    assert client.post("/api/v1/observations", json=obs(), headers=RW).status_code == 201
    r = client.post("/api/v1/observations", json=obs(), headers=RW)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"
```

What the reference suite covers (`tests/`): CRUD round trip, parametrized invalid bodies,
401/403/201 matrix, pagination order, UTC normalisation, rate limiting with a **fake clock**
(no `sleep` in tests), WebSocket broadcast and disconnect cleanup, C++ ⇔ Python parity on
boundary values.

CI (`.github/workflows/ci.yml`): on every push, on **Ubuntu and Windows**: build C++ with CMake
→ run the C++ tests (ctest) → `ruff` → `pytest` → assert the C++ engine loaded. Then build the
Docker image and run the CLI checks against the real container. Deploy runs only on `main`.

**Verify:** `python cli.py check 11` (runs pytest and ruff).

**Say it out loud**
- "Unit tests for logic, integration tests through the HTTP layer with TestClient, and a smoke test against the built container, because that's what actually ships."
- "Tests are isolated: each one gets a new app and an in-memory DB, so they pass in any order and in parallel."
- "Time-dependent code takes an injectable clock. Sleeping in tests makes them slow and flaky."
- "The matrix build catches platform bugs: path separators, CRLF line endings, `.dll` vs `.so`, MSVC vs GCC warnings."
- "CI means every change is built and tested automatically. Continuous *delivery* means every green build *can* be deployed; continuous *deployment* means it *is*."

---

## Step 12: Containerize & deploy (AWS)

No automated check. This step is about explaining the design on a whiteboard.

**Build:** read the `Dockerfile` (multi-stage: compile C++ in a builder, copy only `libwxcore.so`
into a slim image, run as non-root, HEALTHCHECK) and `deploy/task-definition.json`.

```bash
docker build -t wx-api .
docker run --rm -p 8000:8000 wx-api
python cli.py check 1 2 8
```

**Reference architecture to draw:**

```
            Route 53 (DNS)
                 │
        ACM cert │ HTTPS/WSS
                 ▼
   ┌──── Application Load Balancer ────┐   health checks → /health
   │   (or API Gateway: auth, quotas)  │
   └──────────────┬────────────────────┘
                  ▼
     ECS Fargate service (2+ tasks, multiple AZs, autoscaling on CPU/requests)
         │ container: uvicorn + app + libwxcore.so
         │ env vars / Secrets Manager (API keys)
         │ logs → CloudWatch Logs
         ▼
     DynamoDB table "observations"
       PK = station   SK = observed_at   (+ GSI for id lookups)
       Streams → Lambda → (fan-out to WebSocket clients / downstream consumers)

  Ingestion: data feed → S3 (raw files) → S3 event → SQS → worker (ECS/Lambda) → DynamoDB
  CI/CD: GitHub Actions → test → build image → ECR → ECS rolling / blue-green (CodeDeploy)
```

**Say it out loud**
- "Fargate for the API because it's long-running and has WebSocket connections. Lambda + API Gateway suits bursty, short request/response traffic, but has cold starts and a 15-minute limit."
- "TinyDB writes to the container's local disk, which disappears on redeploy, so in AWS that becomes DynamoDB. I design the key around the main query, 'observations for a station in a time range': partition key = station, sort key = timestamp. Hot partitions are the risk if one station gets most of the writes."
- "Rollout: ECS rolling update or CodeDeploy blue/green. The ALB health check gates traffic, so a bad build never gets traffic and can be rolled back by pointing at the previous task definition."
- "Secrets in Secrets Manager or SSM, never in the image. IAM roles per task with least privilege. GitHub assumes an IAM role through OIDC, so there are no long-lived AWS keys in CI."

---

## Stretch exercises (if time allows)

Roughly in order of interview value:

1. **Debugging drill:** do the drills in [MOCK_INTERVIEW.md](MOCK_INTERVIEW.md#part-4-hands-on-debugging-drills). Break something on purpose and diagnose it from logs and status codes alone.
2. **Cursor pagination:** add `?cursor=` + `next_cursor` to the list endpoint.
3. **Idempotency keys:** accept `Idempotency-Key` on POST; cache the first response for 24 h and return it on retries.
4. **ETag / conditional GET:** return an `ETag` hash; answer `If-None-Match` with `304 Not Modified`.
5. **Real data ingestion:** a background task that fetches live METARs from the aviationweather.gov Data API (check its current docs for the endpoint and rate limits), parses them, and stores them. Handle timeouts, retries with backoff, duplicates and partial failures.
6. **Swap the database:** implement `ObservationRepo` against DynamoDB Local (Docker) with boto3, or MongoDB with pymongo. The routes shouldn't change.
7. **Queue-based pipeline:** POST puts raw METAR text on a queue (SQS, or `asyncio.Queue` locally) and returns `202 Accepted`; a worker parses and stores. This is the same pattern JMS queues are used for.
8. **pybind11:** rewrite the C++ binding with pybind11 and compare it with ctypes.
