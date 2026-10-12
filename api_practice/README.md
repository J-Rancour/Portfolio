# Aviation Weather Observations API: interview prep kit

A small but complete REST API, built in 12 steps, for preparing for a backend role
that is mostly Python, with some C/C++, AWS, NoSQL and CI/CD. The domain is aviation
weather (METAR-style observations and flight categories), which matches the job.

| File | What it's for |
|---|---|
| [STUDY_PLAN.md](STUDY_PLAN.md) | The 2.5-day schedule: what to study, build and rehearse, hour by hour |
| [TUTORIAL.md](TUTORIAL.md) | Builds the API from an empty folder, one verifiable step at a time |
| [MOCK_INTERVIEW.md](MOCK_INTERVIEW.md) | Mock interview script, question bank with model answers, debugging drills, system design |
| `frontend/` | Browser UI: tutorial steps with one-click checks, request console, live WebSocket feed, data table |
| `cli.py` | Terminal version of the same checks, plus `req`, `ws`, `burst`, `seed` helpers |
| `app/` | Reference implementation (FastAPI) |
| `native/` | C++ library (flight category, wind components) called from Python with ctypes |
| `tests/` | pytest suite (37 tests) |
| `.github/workflows/ci.yml`, `Dockerfile`, `deploy/` | CI/CD: Linux + Windows matrix, container build, ECS deploy |

## What it covers

- REST resource design, status codes, validation, one error format
- Filtering and pagination
- API-key auth (401 vs 403)
- Token-bucket rate limiting (429 + Retry-After)
- WebSockets (server push)
- HTTPS/WSS with a self-signed cert
- Python ↔ C++ through a C ABI (ctypes)
- Observability: request IDs, structured logs, metrics
- Testing, CI on Linux + Windows, Docker, and AWS deployment

## Quick start

Needs Python 3.12+ (tested with 3.14).

**Windows (PowerShell)**
```powershell
cd api_practice
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
native\build.bat                       # optional: builds the C++ DLL with MSVC (needs VS Build Tools)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Linux / macOS**
```bash
cd api_practice
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
sh native/build.sh                     # optional: builds libwxcore.so / .dylib with g++/clang
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API runs without the C++ library. It falls back to Python and `/health` reports `"engine": "python"`.
Step 8 of the tutorial is where you build it.

Once it's running:

- **Swagger UI:** http://127.0.0.1:8000/docs (generated from the code)
- **Frontend:** in a second terminal, run
  `python -m http.server 5500 --bind 127.0.0.1 --directory frontend`
  and open http://127.0.0.1:5500
- **CLI:** in a third terminal, run
  ```
  python cli.py steps          # list the steps
  python cli.py check all      # verify everything
  python cli.py seed -n 20     # sample data for the frontend's Observations tab
  python cli.py req GET /api/v1/observations?limit=2
  python cli.py burst /api/v1/observations -n 20   # watch 429s appear
  python cli.py ws             # live feed; create data in another terminal
  ```

API keys (dev only): `dev-key-123` (read-write) and `readonly-key-789` (read-only).
Change them with `API_KEYS="key1:rw,key2:ro"`.

## Building your own copy (recommended)

Reading the reference code isn't the same as having built an API. For the real practice:

1. Make an empty folder, e.g. `my_api/`, and follow [TUTORIAL.md](TUTORIAL.md).
2. Run your server on a different port: `uvicorn app.main:app --reload --port 8001`.
3. From this folder, check your work after every step:
   `python cli.py --base-url http://127.0.0.1:8001 check 2`.
   You can also set the frontend's "API base URL" box to `http://127.0.0.1:8001`.
4. If you get stuck, compare with the matching file in `app/`.

## Troubleshooting (each of these is also a good interview story)

| Symptom | Cause | Fix |
|---|---|---|
| First request to `localhost` takes ~2 s on Windows | `localhost` resolves to IPv6 `::1` first, uvicorn only listens on IPv4, so the client waits for the IPv6 attempt to time out | Point clients at `127.0.0.1` instead of `localhost` |
| `python cli.py req GET /health` → 404 in **Git Bash** | MSYS rewrites args starting with `/` into Windows paths (`C:/Program Files/Git/health`) | Drop the leading slash (`req GET health`) or set `MSYS_NO_PATHCONV=1` |
| `/health` says `"engine": "python"` | The C++ library isn't built, or doesn't match Python's bitness (`[WinError 193]` in the server log) | Run `native\build.bat` (it uses 64-bit MSVC). A 32-bit MinGW `g++` can't produce a DLL that 64-bit Python can load |
| Frontend: "Network error … blocked by CORS" | The page's origin isn't in `CORS_ORIGINS`, or the server is down | Serve the frontend from `127.0.0.1:5500` or `localhost:5500`, or set `CORS_ORIGINS` |
| Frontend can't read `Retry-After` / `Location` | Browsers hide response headers from JS unless the server lists them in `Access-Control-Expose-Headers` | See `expose_headers` in `app/main.py` |
| HTTPS step: CLI says the certificate isn't trusted | Self-signed cert | `--cafile certs/cert.pem`. In the browser, open `https://127.0.0.1:8443/health` once and accept the warning |
| Data looks corrupted after running two servers | Both processes write the same TinyDB JSON file, with no locking between processes | One writer per file: `DB_PATH=data/other.json` for the second server |

## Reset

Stop the server and delete `data/`. To start fresh in the frontend, use "Reset progress".
