# Mock interview kit

- **Part 1:** a 75-minute mock interview script. Hand it to a friend, or run it alone with a timer and record yourself.
- **Part 2:** question bank with model answers, by topic.
- **Part 3:** system design: aviation weather ingestion & distribution.
- **Part 4:** hands-on debugging drills against this repo.
- **Part 5:** behavioural (STAR) prompts.
- **Part 6:** questions to ask them.

> Model answers are *outlines*, not scripts. Say them in your own words. Memorised answers
> sound memorised, and the follow-up question breaks them.

---

## Part 1: Mock interview script (75 min)

**For the interviewer:** read the questions as written. After each answer, ask one follow-up
("why?", "what if it's 100× bigger?", "how would you know it broke?"). Take notes against the
rubric at the end. Don't help unless the candidate is completely stuck for 2+ minutes.

| Min | Section | Prompts |
|---|---|---|
| 0–5 | **Intro** | "Walk me through your background and why this role." (90 s target) |
| 5–20 | **Technical rapid-fire** | A1, A3, A5, A8, B1, B3, C1, C4, F1 (about 90 s each; move on if stuck) |
| 20–40 | **Hands-on** | Live exercise 1 or 2 below. Candidate shares their screen and talks while coding |
| 40–50 | **Debugging scenario** | "A meteorologist says the simulator shows weather from 3 hours ago. The API's /health is green. Walk me through what you'd do." (see part 4, scenario S1) |
| 50–65 | **System design** | Part 3 prompt |
| 65–72 | **Behavioural** | Two prompts from part 5 |
| 72–75 | **Candidate questions** | Part 6 |

### Live exercise 1: parse a METAR wind group (20 min)

> Write `parse_wind(group: str) -> dict` for METAR wind groups. Examples:
> `"27012KT"` → `{"dir": 270, "speed": 12, "gust": None, "variable": False}`
> `"27012G20KT"` → gust 20 · `"VRB03KT"` → dir None, variable True · `"00000KT"` → calm.
> Invalid input should raise `ValueError`. Then: what tests would you write?

<details><summary>Reference solution</summary>

```python
import re

WIND = re.compile(r"^(?P<dir>\d{3}|VRB)(?P<speed>\d{2,3})(?:G(?P<gust>\d{2,3}))?KT$")

def parse_wind(group: str) -> dict:
    m = WIND.match(group.strip().upper())
    if not m:
        raise ValueError(f"not a wind group: {group!r}")
    variable = m["dir"] == "VRB"
    direction = None if variable else int(m["dir"])
    if direction is not None and direction > 360:
        raise ValueError(f"direction out of range: {direction}")
    return {
        "dir": direction,
        "speed": int(m["speed"]),
        "gust": int(m["gust"]) if m["gust"] else None,
        "variable": variable,
    }
```

Tests: each example above; 3-digit speeds (`250105KT`); lowercase input; garbage (`""`,
`"27012"`, `"ABC12KT"`, `"40012KT"`); a gust lower than the speed (should that be rejected?
**Ask the interviewer.** Asking about requirements scores points). Mention `pytest.mark.parametrize`.
</details>

### Live exercise 2: add an endpoint (20 min, in this repo)

> Add `GET /api/v1/stations/{station}/latest` that returns the newest observation for a station,
> or 404. Write a test.

<details><summary>What a good answer covers</summary>

- Reuses `repo.list(station=..., limit=1)`. No duplicated query logic.
- Validates the station format (same pattern as the list endpoint) and upper-cases it.
- 404 through `HTTPException`, so it gets the standard error envelope.
- Test: create two observations at different times → GET latest returns the newer one; unknown station → 404.
- Bonus: mentions this is DynamoDB's `Query(..., ScanIndexForward=False, Limit=1)` with station as partition key and time as sort key: one cheap read.
</details>

### Rubric (score 1–4 each)

| Area | 1 | 4 |
|---|---|---|
| Fundamentals | Vague, wrong status codes | Precise, with tradeoffs |
| Coding | Stuck or silent | Talks through it, tests edge cases, clarifies requirements |
| Debugging | Guesses randomly | Hypothesis → evidence → narrow down → fix → prevent recurrence |
| Design | Lists AWS services | Starts from requirements, sizes the problem, explains tradeoffs and failure modes |
| Communication | Rambles, or bluffs | Structured, concise, says "I don't know, but here's how I'd find out" |

---

## Part 2: Question bank with model answers

### A. REST & HTTP

**A1. What makes an API RESTful?**
Resources identified by URLs; standard methods with their standard meaning; statelessness
(each request carries everything needed, e.g. the auth token, so any server instance can handle
it); standard status codes; cacheable responses where appropriate; representations (usually JSON).
In practice "RESTful" means resource-oriented HTTP + JSON done consistently.

**A2. PUT vs PATCH vs POST?**
POST creates (server assigns the ID) and isn't idempotent. PUT replaces the whole resource at a
known URL and is idempotent. PATCH changes some fields. In my tutorial API PATCH uses
`exclude_unset` so omitted fields aren't overwritten.

**A3. 401 vs 403? 400 vs 422? When would you use 409?**
401: not authenticated (missing/invalid credentials), with `WWW-Authenticate`. 403: authenticated
but not allowed. 400: malformed request (bad JSON). 422: well-formed but fails validation.
409: conflicts with current state: duplicates, version mismatch on optimistic locking.

**A4. What's idempotency, and why does it matter?**
Repeating the request leaves the same server state. Networks fail mid-request, so clients retry,
and a retry must not double-charge or double-insert. GET/PUT/DELETE are idempotent by design;
make POST safe with an `Idempotency-Key` the server remembers.

**A5. How would you design pagination for a large collection?**
Always cap `limit`. Offset paging is simple but slow on deep pages and unstable under inserts.
Cursor/keyset paging returns an opaque `next_cursor` (the last sort key) and queries "after this
key". Stable and O(page size). Include total only if it's cheap to compute.

**A6. How do you version an API?**
URL prefix (`/v1`) is the most visible and the easiest to route. Alternatives: a header or media type.
Additive changes don't need a new version; breaking ones do, with a deprecation period, a
`Deprecation`/`Sunset` header, and usage metrics to know when v1 can be turned off.

**A7. How do you secure an API?**
TLS everywhere; authentication (API keys for services, OAuth2/OIDC + JWT for users); authorization
per resource and action (least privilege); input validation; rate limiting; no secrets in URLs or
logs; CORS configured narrowly for browsers; dependency updates; audit logging. In AWS: WAF and
API Gateway authorizers.

**A8. Explain rate limiting and how you'd implement it across multiple servers.**
Token bucket: capacity = burst, refill = sustained rate. Exceeding it → 429 + `Retry-After`. In one
process an in-memory dict works (that's what I built). Across instances the counters must be
shared: Redis with atomic operations (INCR+EXPIRE, or a Lua script for the bucket), or enforce
at the edge with API Gateway usage plans or WAF rate rules. Key on the authenticated identity,
not on spoofable inputs.

**A9. REST vs WebSockets vs SSE vs polling: when do you pick each?**
REST for request/response. Polling for infrequent changes (simple, cacheable). SSE for one-way
server→client streams over plain HTTP (auto-reconnect). WebSockets for two-way, low-latency messaging
(live feeds, control channels). WebSockets cost you sticky long-lived connections and a pub/sub
layer once you have more than one server.

**A10. Walk me through what happens when you type a URL and hit Enter.**
DNS lookup → TCP connection (3-way handshake) → TLS handshake (cert validation, key exchange) →
HTTP request → load balancer → app server → app logic/DB → response → browser renders (more requests
for assets). Mention caching at each layer, and where you'd look when something is slow.

**A11. How do you handle errors in an API?**
One error format with a machine-readable code, a human message, field details and a request ID.
Correct status codes. Never leak internals. Log server errors with the stack trace and request ID.
Clients: retry 5xx/429 with backoff, don't retry most 4xx.

**A12. How do you test an API?**
Unit tests for logic; integration tests through the HTTP layer (FastAPI TestClient with an
in-memory DB per test); contract tests against the OpenAPI spec; smoke tests against the built
container in CI; load tests (locust/k6) for capacity; monitoring as the test in production.

### B. Python

**B1. Explain the GIL. How would you speed up CPU-bound Python?**
Only one thread executes Python bytecode at a time, so threads help I/O-bound work but not CPU-bound.
For CPU work: `multiprocessing`/`ProcessPoolExecutor`, vectorised NumPy, or moving the hot loop
into C/C++ (ctypes/pybind11/Cython), which can release the GIL. Profile first (`cProfile`, `py-spy`).
Python 3.13+ also has an experimental free-threaded build.

**B2. async/await vs threads?**
asyncio runs one thread with an event loop that switches tasks at `await` points: very cheap
concurrency for many I/O waits (sockets). Threads are pre-emptive and good for blocking libraries.
The trap: one blocking call inside `async def` (e.g. `time.sleep`, `requests.get`) freezes
*every* request. Debugging drill D4 shows this.

**B3. What is a decorator? A context manager? A generator?**
A decorator is a function that takes a function and returns a wrapped one (`@app.get`, `@retry`). A context
manager guarantees setup/teardown with `with` (files, locks, DB transactions). A generator produces
values lazily with `yield`, which keeps memory constant when streaming large files.

**B4. How do you manage dependencies and environments?**
A venv per project; `requirements.txt` with pinned versions or `pyproject.toml` + a lock file
(uv/poetry/pip-tools); separate dev deps; the same versions in CI and the container; dependency
updates through automated PRs.

**B5. How do you debug a Python service that's slow or leaking memory in production?**
Metrics and logs first: which endpoint, since when, correlated with which deploy? `py-spy dump`/`top`
on the live process (no restart needed); `cProfile` on a reproduction; `tracemalloc` snapshots
compared over time for leaks (often an unbounded cache or global list, like my rate limiter's
bucket dict, which in production would need eviction).

**B6. Mutable default argument bug?**
`def f(x=[])` creates the list once when the function is defined, so it's shared across calls.
Use `x=None` and create the list inside.

### C. C / C++ and interop

**C1. How do you call C++ from Python?**
Expose a C ABI (`extern "C"`, C types only), build a shared library, load it with ctypes
(declare `argtypes`/`restype`). Or use pybind11/nanobind for richer bindings (classes,
exceptions, NumPy), or Cython, or run the C++ as a separate process. In my project I used ctypes
with a pure-Python fallback, and tests that compare both on boundary values.

**C2. What is name mangling and why does `extern "C"` matter?**
C++ encodes namespaces, classes and overloads into symbol names. `extern "C"` turns that off so the
symbol is the plain function name, which C and every FFI can find. You lose overloading for those
functions.

**C3. Static vs shared library? What's an ABI?**
Static: the code is copied into the executable at link time. Shared: loaded at runtime and
shareable/updatable without relinking. The ABI is the binary contract: calling convention, type
sizes, struct layout, name mangling, the C++ standard library version. Mismatches (32 vs 64-bit,
different MSVC runtimes, different libstdc++) fail at load time or corrupt memory silently.

**C4. Explain RAII and smart pointers.**
Resource lifetime is tied to object lifetime: acquire in the constructor, release in the destructor,
so cleanup happens even when exceptions are thrown. `unique_ptr` = sole owner (moveable, not copyable),
`shared_ptr` = reference counted, `weak_ptr` = non-owning observer that breaks cycles. In
modern C++, raw `new`/`delete` should be rare.

**C5. A C++ program crashes only in release builds. How do you debug it?**
Classic undefined behaviour: uninitialised variables, out-of-bounds access, use-after-free, or a race
the optimiser exposes. Build release with debug symbols (`-O2 -g` / `/Zi`), get a core dump or
crash dump and a backtrace, run with AddressSanitizer/UBSan (or Valgrind), turn on warnings
(`-Wall -Wextra`, `/W4`), and bisect the commits.

**C6. "Undefined reference to `foo`". What's wrong?**
A linker error: the declaration exists but no object or library provides the definition. Missing
`.cpp` in the build, missing `target_link_libraries`, library order (GCC), a C/C++ name mismatch
(missing `extern "C"`), or a Windows DLL not exporting the symbol (`dllexport`).

**C7. Stack vs heap?**
Stack: automatic, fast, limited size, freed on scope exit. Heap: dynamic size and lifetime,
explicitly managed (or through smart pointers), slower to allocate, can fragment. Returning a
pointer to a stack variable is a dangling pointer bug.

### D. CI/CD & releases

**D1. Describe a good CI/CD pipeline.**
On every push: lint → unit tests → build (C++ via CMake on every target OS, wheel, image) →
integration/smoke test the built artifact → publish to a registry tagged by commit SHA. On merge
to main: deploy to staging automatically → checks → approval → production with a rolling,
blue/green or canary rollout gated on health checks → automatic rollback on alarm. Mine runs
Linux + Windows in a matrix because the job deploys to both.

**D2. How do you make releases safe?**
Small, frequent changes; build once and promote the same artifact; feature flags; backward-compatible
DB migrations (expand/contract); health-check-gated rollouts; a rehearsed rollback; release notes;
watching dashboards after deploy.

**D3. A deploy went out and error rates jumped. What do you do?**
Mitigate first: roll back (or turn off the feature flag). Communicate on the incident channel.
Then diagnose from logs and metrics (which endpoint, which error, which version). Then fix forward
with a test that reproduces it. Then a blameless postmortem with action items (why did tests or
canary not catch it?).

**D4. What's the difference between continuous delivery and continuous deployment?**
Delivery: every green build *can* go to production (often with a manual approval). Deployment:
every green build *does* go automatically. Regulated or government environments often stop at
delivery, with a change-approval step.

### E. AWS & cloud architecture

**E1. Lambda vs ECS Fargate vs EC2 for this API?**
Lambda: spiky, short requests, pay per call, zero idle cost. But cold starts, a 15-min limit, and
WebSockets only through API Gateway. Fargate: long-running containers with no servers to manage;
good for steady APIs and WebSockets. EC2: full OS control, GPUs, legacy C++ binaries, or licensing
constraints. For a simulation platform with C++ components I'd expect a mix.

**E2. How would you make it highly available?**
At least 2 tasks/instances across availability zones behind an ALB with health checks, autoscaling,
managed multi-AZ data stores (DynamoDB is multi-AZ by default), no state on the instances, and
alarms. DR: backups, point-in-time recovery, infrastructure as code to rebuild in another region.

**E3. How do services get credentials in AWS?**
IAM roles: task roles for ECS, execution roles for Lambda, instance profiles for EC2. Temporary
credentials rotate automatically. Secrets in Secrets Manager/SSM fetched at startup. CI uses OIDC
federation instead of stored access keys.

**E4. Design an S3-triggered processing pipeline.**
Upload to S3 → event notification to SQS (buffering and retries) → workers (Lambda or ECS) process
idempotently (dedupe by object key/version) → write results → a DLQ catches poison messages →
CloudWatch alarms on DLQ depth and age of the oldest message.

**E5. Infrastructure as code?**
CloudFormation/CDK or Terraform: reviewed in PRs, reproducible environments, drift detection.
Never click-ops production.

### F. NoSQL

**F1. How would you model weather observations in DynamoDB?**
Main access pattern: "observations for station X in a time range, newest first." So partition key
`station`, sort key `observed_at` (ISO string or epoch). Query with `KeyConditionExpression` and
`ScanIndexForward=False`. Lookups by ID: a GSI on `id`, or make the ID `station#time`. Duplicates
are prevented with a conditional put. Old data expires with TTL. Watch for hot partitions if a few
stations dominate writes (spread them with a suffix if needed).

**F2. When would you choose MongoDB over DynamoDB, or a relational DB over both?**
MongoDB: flexible documents, rich ad-hoc queries and aggregation, and you want indexes on many
fields. DynamoDB: predictable single-digit-ms latency at any scale for known access patterns, fully
managed. Relational: complex joins, multi-entity transactions, reporting.

**F3. Eventual vs strong consistency?**
Eventual: a read right after a write may return stale data for a short time (cheaper, more
available). Strong: always the latest committed write. DynamoDB reads are eventually consistent by
default, strongly consistent on request (same region). Design for idempotency and tolerate brief
staleness where you can.

**F4. Embed or reference in a document DB?**
Embed what's read together and bounded in size (an observation's cloud layers). Reference what's
shared, large or unbounded (a station's full history). An unbounded array inside a document is a
classic mistake (MongoDB has a 16 MB document limit, DynamoDB 400 KB per item).

### G. Linux, Windows, builds, debugging

**G1. Your service won't start on a Linux box. Steps?**
`systemctl status` and `journalctl -u svc -n 100`; check config and env vars; `ss -ltnp` (is the
port taken?); permissions on files and directories; `df -h` (disk full?); `ldd binary` (missing
shared libs); run the command by hand as the service user.

**G2. Same code works on Windows, fails on Linux (or vice versa). Usual suspects?**
Case-sensitive paths, `\` vs `/`, CRLF line endings in scripts (`/bin/sh^M: bad interpreter`),
`.dll` vs `.so` naming and search paths, compiler differences (MSVC accepts code GCC rejects),
different default encodings, `localhost` resolving to IPv6, permissions/executable bits.

**G3. How do you approach root-cause analysis?**
Define the symptom precisely (what, since when, who's affected). Gather evidence (logs by request
ID, metrics, recent changes and deploys). Form hypotheses and test the cheapest first. Bisect
(git bisect, or half the pipeline at a time). Reproduce locally. Fix. Add a test or alert so it
can't silently recur. Write it up. Use "5 whys" to get past the trigger to the cause.

**G4. Data looks wrong at the end of a multi-stage pipeline. How do you find where?**
Check the data at each stage boundary: count records in vs out, compare samples, check
timestamps and units. Binary-search the stages. Validate at the boundaries (schemas, range checks,
freshness alarms) so the next problem is caught at the stage that causes it.

### H. Java / JMS (preferred, so a concept-level answer is enough)

**H1. What is JMS? Queue vs topic?**
Java Message Service is a standard Java API for message brokers (ActiveMQ, Artemis, IBM MQ).
**Queue** = point-to-point: each message is consumed by exactly one consumer, which gives load
balancing. **Topic** = publish/subscribe: every subscriber gets a copy. A durable subscription keeps
messages for a subscriber while it's offline. Acknowledgement modes (auto, client, transacted)
control when a message counts as processed.
*AWS analogues:* SQS ≈ queue, SNS ≈ topic, Amazon MQ = managed ActiveMQ/RabbitMQ that speaks
JMS natively. *From Python:* talk to ActiveMQ over STOMP (`stomp.py`) or AMQP.

**H2. Why use a message broker between services?**
Decoupling (producer and consumer don't need to be up at the same time), buffering bursts,
retries and dead-letter queues, fan-out to many consumers, and smoothing load into slower systems
like a simulation engine.

**H3. At-least-once vs exactly-once delivery?**
Most brokers guarantee at-least-once, so duplicates happen on redelivery. Make consumers
idempotent (dedupe by message ID or natural key, e.g. station+time). True exactly-once needs
transactions end to end and is usually not worth it.

---

## Part 3: System design: aviation weather ingestion & distribution

> **Prompt:** "We ingest weather observations and forecasts from several external feeds every few
> minutes, process them, and feed them to flight-training simulators running in different
> facilities, on Linux and Windows. Some processing is in legacy C++. Design the system. It must be
> reliable, observable, and we need to be able to replay a past weather scenario."

### How to run the 15 minutes

1. **Clarify (2 min):** data volume (how many stations, files per hour, sizes)? Latency needed
   (seconds or minutes)? How many simulators and where (cloud, on-prem, air-gapped)? Do consumers
   pull or get pushed? Retention? Compliance (export control → GovCloud?)?
2. **Sketch the core flow (5 min):**
   ```
   feeds ──► fetchers (scheduled, per source) ──► S3 raw/ (immutable, partitioned by source/date/hour)
                                                     │ S3 event
                                                     ▼
                                                SQS queue ──► processors (ECS; Python + C++ libs)
                                                     │            │ parse, validate, unit-normalise,
                                                   DLQ            │ derive (flight category, etc.)
                                                                  ▼
                                    DynamoDB (latest + recent, PK station / SK time)
                                    S3 processed/ (Parquet for history/replay)
                                                                  │ DynamoDB Streams / SNS
                                                                  ▼
                                    Distribution API (REST for queries, WebSocket/SSE for live push)
                                                                  ▼
                                                    simulators (Linux/Windows clients)
   ```
3. **Deep dives (6 min), picking what the interviewer cares about:**
   - **Reliability:** raw data is kept immutably, so you can always reprocess. Processing is idempotent (natural key = station+time). SQS retries + DLQ. Multi-AZ. Fetchers handle source outages with backoff and alert on staleness.
   - **Correctness:** schema + range validation at ingestion, units normalised once, UTC everywhere, quarantine bad records instead of dropping them silently, and C++ ⇔ Python reference tests.
   - **Replay:** a scenario = a time range plus sources. A replay service reads `processed/` for that range and republishes it on its own stream at 1× or accelerated speed. Simulators can't tell replay from live, which is great for training and for reproducing bugs.
   - **Observability:** per-stage counters (in, out, rejected), age of the newest data per source (the key alarm), queue depth and oldest-message age, p95 processing latency, request IDs carried through messages.
   - **Legacy C++:** wrap it as a library (C ABI/pybind11) or a sidecar process; build it in CI for both OSes; keep a golden-file regression suite.
   - **Deployments:** containers and IaC; blue/green for the API; processors can roll freely because the queue buffers. Version message schemas.
4. **Tradeoffs (2 min):** push vs pull for simulators (push = lower latency, harder with
   firewalls/air gaps; pull = simpler, cacheable). DynamoDB vs a time-series DB. Lambda vs ECS
   for processors (the C++ dependencies and run times favour ECS).

---

## Part 4: Hands-on debugging drills

Do these against the reference app. For each: **break it** (or have a friend break it without
telling you), look only at the **symptom**, and diagnose it from evidence: status codes, headers,
logs, `/metrics`, the CLI. Write down your hypothesis *before* opening the answer. Undo each
break with `git checkout -- <file>` (or by reverting your edit) before the next drill.

### D1: "The frontend can't see Retry-After"
**Break:** in `app/main.py`, delete `"Retry-After"` from `expose_headers`. Restart.
**Symptom:** `python cli.py burst /api/v1/observations -n 15` shows `Retry-After`, but in the
browser the rate-limit check fails with "missing header retry-after".
<details><summary>Answer</summary>
The server sends the header (curl/CLI see it), but browsers only expose CORS-safelisted response
headers to JS unless `Access-Control-Expose-Headers` lists them. Lesson: "works with curl, not in
the browser" → think CORS. The browser devtools Network tab shows the header was received.
</details>

### D2: "429 responses have no request ID"
**Break:** in `create_app()`, swap the order to `install_observability(app)` then `install_rate_limit(app)`.
**Symptom:** 429 bodies show `"request_id": null`, there's no `X-Request-ID` header, and `/metrics` stops counting 429s.
<details><summary>Answer</summary>
The last middleware added is the outermost. Rate limiting now wraps observability, so a 429 returns
before the observability middleware ever runs. Middleware order is a design decision: put
cross-cutting concerns (IDs, logging, CORS) outermost.
</details>

### D3: "Flight categories are all LIFR"
**Break:** in `app/wxcore.py`, delete the `argtypes` line for `wx_flight_category`, and in
`flight_category` pass `int(visibility_sm), int(ceiling)`.
**Symptom:** `/api/v1/tools/flight-category?visibility_sm=10` → LIFR. No errors anywhere.
<details><summary>Answer</summary>
Without `argtypes`, ctypes passes Python ints as C `int`s, but the C function reads `double`s
from the registers/stack, so it gets garbage. (Python floats would raise `ArgumentError` instead, which
is why the cast to int is needed to reproduce it.) Silent wrong answers are the worst kind of
bug, so a parity test against a reference implementation (`tests/test_wxcore.py`) catches it.
</details>

### D4: "Everything got slow, but only one endpoint changed"
**Break:** add `time.sleep(2)` (and `import time`) at the top of the `health` handler in `routes.py`.
**Symptom:** in one terminal run `python cli.py req GET /health`; at the same time, in another,
`python cli.py req GET /api/v1/observations`. The observations request also takes ~2 s.
<details><summary>Answer</summary>
`health` is `async def`, so `time.sleep` blocks the event loop, and *every* request on that worker waits.
Fix: `await asyncio.sleep`, or make it a plain `def` (FastAPI runs those in a thread pool), or
move blocking work to `asyncio.to_thread`. Diagnosis clue: latency spreads to unrelated endpoints,
and `X-Process-Time-Ms` on the victim request is small while client-side time is large (it was
waiting to be scheduled).
</details>

### D5: "Server says engine: python on the new machine"
**Break:** rename `native/build/wxcore.dll` (or `.so`) to something else. Restart.
**Symptom:** `/health` → `"engine": "python"`; step 8's first check fails.
<details><summary>Answer</summary>
Read the startup log: `C++ core not loaded from ... (FileNotFoundError/OSError ...)`. Then check
the path, the bitness (`[WinError 193]` = 32/64-bit mismatch), missing dependent DLLs (Dependencies.exe /
`ldd`), and on Linux `GLIBCXX not found` (built on a newer distro). Note the design choice:
silent fallback keeps the service up, but CI asserts `ENGINE == "cpp"` so it can't ship broken.
</details>

### D6: "Pagination returns duplicates"
**Break:** none. Think it through.
**Scenario:** a client pages with `limit=20&offset=20`, `offset=40`... while new observations
keep arriving. Users report seeing the same observation on page 2 and page 3.
<details><summary>Answer</summary>
Newest-first offset paging: each insert shifts every row down by one, so the next page repeats
items (and deletions skip items). Fix: cursor paging on a stable sort key (`observed_at`, `id`)
using "older than the cursor". Good chance to show you know the theory behind the code.
</details>

### Scenario S1 (verbal): "The simulator shows weather from 3 hours ago; /health is green"
<details><summary>A strong walkthrough</summary>

1. **Scope:** all stations or some? All simulators or one site? When did it start? Any deploys or config changes then?
2. **Check where data stops:** is the newest observation in the API 3 hours old? (`GET /observations?limit=1`.) If the API is fresh, the problem is downstream: simulator connections, the WebSocket feed, caching. If it's stale, go upstream.
3. **Upstream, stage by stage:** fetcher logs (are source fetches failing? auth expired? source format changed?), queue depth and DLQ (are processors failing on new records?), processor errors around the start time.
4. **Common root causes:** an expired credential or certificate for the source, a source format change that makes the parser reject everything (into the DLQ), a disk/quota limit, a timezone bug (local vs UTC = an exact hour offset!), a stuck consumer.
5. **Fix + prevent:** reprocess the backlog from raw storage. Add a **data freshness alarm** ("newest data older than N minutes"), because `/health` only proves the process is alive, not that it's useful. Point this out: it's the key insight.
</details>

---

## Part 5: Behavioural prompts (answer with STAR: Situation, Task, Action, Result)

Prepare 5 stories you can bend to fit most prompts: a hard bug you tracked down, a production
incident, a disagreement on a technical decision, something you delivered under time pressure,
and learning something new fast. This prep counts as that last one: "I had 2.5 days, so I built a
REST API with C++ integration and CI to get hands-on quickly."

1. Tell me about the hardest bug you've debugged.
2. Describe a time a release or deployment went wrong. What did you do?
3. Tell me about a time you disagreed with a teammate's technical approach.
4. Describe working with non-engineers (here, meteorologists) to turn a fuzzy request into software.
5. Tell me about improving the reliability or performance of an existing system.
6. Describe a time you had to learn a new technology quickly.
7. Tell me about documentation or a process you created that others used.

Keep each answer under 2 minutes. Spend most of it on **Action** (what *you* did) and end with a
measurable **Result** ("cut ingestion failures from daily to zero", "deploys went from 2 hours to 15 minutes").

---

## Part 6: Questions to ask them

- What does the system look like today: which parts are Python vs C/C++, and what's the "modernization" aiming for?
- How does weather data get into the simulation: real-time feeds, recorded scenarios, or both?
- What does a release look like today, and what would you most like to improve about it?
- What's on-call or operational support like for this role?
- How do engineers and meteorologists work together day to day?
- How much runs on AWS vs on-prem/Windows machines at training sites?
- What would success look like for this hire in the first 90 days?
- What's the hardest technical problem the team is facing right now?
