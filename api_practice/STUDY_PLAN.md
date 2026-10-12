# 2.5-day study plan: Backend Software Engineer (Python + C/C++, aviation weather simulation)

## Read this first: what the job is testing

The posting asks for 5+ years of experience. You can't fake that in 2.5 days, so don't try.
What you **can** do is:

1. **Talk fluently about the core topics.** REST, HTTP, debugging, CI/CD, AWS and NoSQL come up in almost every question.
2. **Have built something real recently.** This kit gives you a working API with C++ integration, tests and a pipeline. Being able to say "I built this last weekend to sharpen my API skills, here's what I learned about rate limiting" beats a vague claim every time.
3. **Show a debugging method.** "Troubleshoot, diagnose, root-cause" appears four times in the posting, so expect a debugging question. A calm, structured approach scores very well.
4. **Be honest about gaps.** "I haven't run JMS in production, but I understand queues vs topics and I've used the same pattern with SQS" is a strong answer. Bluffing that gets caught ends the interview.

Map of what they listed to where it's covered:

| Posting says | Where you practise it |
|---|---|
| RESTful APIs, backend services | Tutorial steps 1–9, mock interview part 2A |
| Python (strong) | Whole kit; part 2B (Python internals) |
| C and/or C++ | Step 8 (`native/`), part 2C, C++ refresher below |
| AWS, cloud architecture | Step 12, part 2E, part 3 (system design) |
| NoSQL / document DBs | Steps 2–4 (TinyDB), part 2F |
| Linux + Windows, build/compile/deploy across OSes | Step 8 build scripts, step 11 CI matrix, part 2G |
| Debugging, troubleshooting, root cause | Part 4 drills, README troubleshooting table |
| Release processes, CI/CD, automated testing | Step 11, `ci.yml`, part 2D |
| Data ingestion/processing pipelines, monitoring | Steps 7 + 9, stretch exercise 5, part 3 |
| Java / JMS (preferred) | Part 2H (concept level is enough) |
| Aviation weather interest (preferred) | Domain primer below |

---

## Schedule

The plan assumes ~9 focused hours on days 1–2 and a half day before the interview. Every
block ends with something you can **check** (a CLI check passing, or an answer said out loud).
Take a 10-minute break every hour; you'll retain more.

### Day 1: HTTP, REST and building the API (tutorial steps 1–6)

| Time | Block | Done when |
|---|---|---|
| 0:00–0:30 | **Setup.** Follow the README quick start. Run the reference API, the frontend and `python cli.py check all`. Click around `/docs`. | All checks green; you've sent a request from the frontend console |
| 0:30–1:30 | **HTTP fundamentals.** Read "HTTP in five minutes" in TUTORIAL.md and the cheat sheet below. In the console, send each preset and read the status codes and headers. | You can explain methods, idempotency and status code families without notes |
| 1:30–2:30 | **Step 1: skeleton.** Create `my_api/` and build step 1 from TUTORIAL.md yourself. Run on port 8001. | `python cli.py --base-url http://127.0.0.1:8001 check 1` passes |
| 2:30–4:30 | **Step 2: CRUD.** Models, repository, routes. This is the biggest step, so take your time. | `check 2` passes on your server |
| 4:30–5:00 | Break + **say it out loud**: explain your CRUD design to an imaginary interviewer for 2 minutes. Record yourself on your phone if you can. | |
| 5:00–6:00 | **Step 3: validation & errors.** | `check 3` passes |
| 6:00–6:45 | **Step 4: filtering & pagination.** | `check 4` passes |
| 6:45–7:45 | **Step 5: auth.** | `check 5` passes |
| 7:45–8:45 | **Step 6: rate limiting.** Implement the token bucket, then run `python cli.py burst ...` and watch the 429s. | `check 6` passes |
| 8:45–9:15 | **Review:** answer mock-interview questions A1–A12 out loud. Mark the ones you stumble on. | |

### Day 2: realtime, C++, ops, cloud (steps 7–12 + concepts)

| Time | Block | Done when |
|---|---|---|
| 0:00–0:20 | Warm-up: redo the stumbled questions from yesterday. | |
| 0:20–1:20 | **Step 7: WebSockets.** Watch the live feed in the frontend while running `python cli.py seed`. | `check 7` passes |
| 1:20–3:00 | **Step 8: C++ via ctypes.** Read `native/wxcore.h` and `.cpp` line by line. Build with `native\build.bat`. Break it on purpose: remove `extern "C"` and watch the load fail; remove `argtypes` and call it with ints (`10` instead of `10.0`) to watch the results turn to garbage. Then fix it. | `check 8` passes; you can explain name mangling and ABI |
| 3:00–3:45 | **C++ refresher** (list below). Answer part 2C out loud. | |
| 3:45–4:30 | **Step 9: observability.** Find one request's log line by its X-Request-ID. | `check 9` passes |
| 4:30–5:15 | **Step 10: HTTPS.** Make the cert and run TLS. Try without `--cafile` and read the error. | `check 10` passes over https |
| 5:15–6:15 | **Step 11: tests & CI.** Read `tests/` and `ci.yml`. Write 2 tests of your own (e.g. the PATCH-404 path). | `check 11` passes |
| 6:15–7:15 | **AWS + NoSQL concepts** (cheat sheet below). Draw step 12's architecture from memory on paper. | You can draw it in 5 min |
| 7:15–8:15 | **Debugging drills** 1–4 (MOCK_INTERVIEW.md part 4). | |
| 8:15–9:00 | **Questions:** parts 2D–2H out loud. | |

### Day 3 (half day): rehearse

| Time | Block |
|---|---|
| 0:00–1:15 | **Full mock interview** (MOCK_INTERVIEW.md part 1) with a friend reading the script, or alone with a timer and a recording. |
| 1:15–1:45 | Review the recording: where did you ramble, freeze or bluff? Rework those answers. |
| 1:45–2:30 | **System design rehearsal** (part 3): talk through the weather ingestion design out loud, drawing as you go. |
| 2:30–3:15 | **Behavioural stories** (part 5): write 5 STAR stories as bullet points and say each one in under 2 minutes. |
| 3:15–3:45 | **Prepare your questions** for them (part 6) and look up the company and the program (public info only). |
| 3:45–4:00 | Stop. Rest. Don't cram the night before. |

**If you fall behind:** cut in this order: step 10 → step 12 hands-on (keep the concepts) →
step 7 hands-on. **Never cut** steps 2, 3, 5 and 8, the debugging drills, or the Day 3 mock.

---

## Cheat sheets

### HTTP / REST: must know cold

- **Status codes:** 200 OK · 201 Created · 202 Accepted (queued for async work) · 204 No Content ·
  301/308 permanent redirect · 304 Not Modified · 400 Bad Request · 401 Unauthorized ·
  403 Forbidden · 404 Not Found · 405 Method Not Allowed · 409 Conflict · 412 Precondition Failed ·
  415 Unsupported Media Type · 422 Unprocessable · 429 Too Many Requests · 500 Internal ·
  502 Bad Gateway (upstream sent garbage / died) · 503 Unavailable (overloaded/maintenance) ·
  504 Gateway Timeout (upstream too slow).
- **Idempotent:** GET, PUT, DELETE, HEAD, OPTIONS. **Not:** POST (use an Idempotency-Key), PATCH (usually).
- **Headers to know:** Content-Type, Accept, Authorization, Location, Cache-Control, ETag / If-None-Match,
  Retry-After, X-Request-ID, the CORS family (Origin, Access-Control-Allow-*), Upgrade/Connection (WebSocket).
- **REST design:** plural nouns (`/observations`), nesting only for real ownership (`/stations/KJFK/observations`),
  versioning (`/v1`), filtering through query params, paging always, one error format, no verbs in URLs.
- **Versioning without breaking clients:** adding fields is safe. Removing or renaming fields, or changing types or meanings, is breaking, so it needs `/v2` and a deprecation window.
- **Timeouts and retries:** every outbound call needs a timeout. Retry only idempotent operations, with exponential backoff + jitter and a retry cap. Circuit breakers stop you hammering a dead dependency.
- **HTTP/1.1 vs 2 vs 3:** 1.1 handles one request at a time per connection (keep-alive helps). HTTP/2 multiplexes many streams over one TCP connection and compresses headers. HTTP/3 runs over QUIC (UDP), so one lost packet no longer stalls every stream.

### Python: likely deep-dive topics

- **GIL:** one thread runs Python bytecode at a time, so threads help for I/O-bound work, not CPU-bound. For CPU work use `multiprocessing`, or C/C++ extensions (which can release the GIL). Python 3.13+ has an optional free-threaded build.
- **asyncio:** a single-threaded event loop. `await` hands control back while waiting on I/O. Never block inside `async def` (use `asyncio.to_thread` or a `def` endpoint). FastAPI runs `def` endpoints in a thread pool.
- **Generators/iterators**, **context managers** (`with`, `__enter__`/`__exit__`, `contextlib`), **decorators**, **dataclasses vs Pydantic** (plain data container vs runtime validation).
- **Typing:** type hints aren't enforced at runtime (Pydantic enforces them for models); mypy/pyright check them statically.
- **Packaging:** venvs, `pip`, `pyproject.toml`, pinning versions; wheels vs sdists (pre-built vs compiled on install, which matters for C extensions).
- **Profiling and debugging:** `cProfile`, `py-spy` (attaches to a running process), `pdb`/`breakpoint()`, `logging` (not `print`), `tracemalloc` for memory.
- **Mutable default argument** gotcha (`def f(x=[])`), `is` vs `==`, late-binding closures in loops.

### C / C++ refresher (step 8 covers the interop part)

- **Memory:** stack vs heap; `new`/`delete` vs **RAII** (resource freed in the destructor, so cleanup is automatic); smart pointers: `unique_ptr` (single owner), `shared_ptr` (ref-counted), `weak_ptr` (breaks cycles). Rule of 0/3/5.
- **References vs pointers**, `const` correctness, pass-by-value vs `const&`, move semantics (`std::move` transfers resources instead of copying).
- **Undefined behaviour:** out-of-bounds access, use-after-free, dangling pointers, signed overflow, uninitialised reads, data races. It may "work" in debug builds and crash in release.
- **Build pipeline:** preprocessor → compiler (`.o`/`.obj`) → linker. "Undefined reference/unresolved external" is a **link** error: a missing library, a name-mangling mismatch, or a missing definition.
- **Static vs shared libraries:** `.a`/`.lib` copied into the binary vs `.so`/`.dll` loaded at runtime. On Windows a DLL has an import `.lib` and needs `__declspec(dllexport)`.
- **Tools:** `gdb`/`lldb` (backtrace with `bt`), Visual Studio debugger, `valgrind` and AddressSanitizer (`-fsanitize=address`) for memory bugs, ThreadSanitizer for data races, core dumps (`ulimit -c unlimited`), `-g -O0` for debuggable builds.
- **CMake:** `add_library`, `add_executable`, `target_link_libraries`, `target_include_directories`, out-of-source builds (`-B build`), multi-config generators (Visual Studio) vs single-config (Make/Ninja).
- **Virtual functions:** dynamic dispatch through a vtable; always give a base class with virtual methods a virtual destructor.
- **Legacy C code** (likely in a "long-standing" platform): `malloc`/`free`, buffer sizes passed alongside pointers, `strncpy` pitfalls, global state, `#ifdef` per platform.

### AWS: services to be able to name and place

| Need | Service | One-liner |
|---|---|---|
| Run containers | **ECS on Fargate** (or EKS) | No servers to manage; tasks behind an ALB |
| Run functions | **Lambda** | Event-driven, pay per call, 15-min max, cold starts |
| HTTP front door | **API Gateway** / **ALB** | API GW: auth, throttling, usage plans. ALB: cheap L7 load balancing, WebSockets |
| Object storage | **S3** | Raw data files, data lake, static sites; events trigger processing |
| Queues / pub-sub | **SQS** / **SNS** / **EventBridge** / **Amazon MQ** | SQS = queue (at-least-once delivery, use a DLQ). SNS = fan-out. Amazon MQ = managed ActiveMQ (speaks JMS!) |
| NoSQL | **DynamoDB** / **DocumentDB** | Key-value/document at any scale vs MongoDB-compatible |
| Observability | **CloudWatch** (Logs, Metrics, Alarms), **X-Ray** | Logs Insights queries, alarms → SNS → on-call |
| Identity | **IAM** | Roles for services, least privilege, no long-lived keys |
| Secrets | **Secrets Manager** / **SSM Parameter Store** | Never in code or images |
| Images | **ECR** | Container registry |
| Network | **VPC**, subnets, security groups, NAT | Private subnets for apps/DBs; SG = stateful firewall |
| Compute (classic) | **EC2** + Auto Scaling Groups | When you need the OS (e.g. legacy C++ simulation binaries) |
| Govt workloads | **GovCloud (US)** | Separate isolated regions for ITAR/export-controlled data. Relevant here! |

### NoSQL / document databases

- **Document model:** store data the way it's read. Embed data that's read together; reference data that's large or shared.
- **DynamoDB:** design the keys from the access patterns *first*. Partition key spreads the load, sort key orders within a partition (`station` + `observed_at`). GSIs serve other access patterns. Avoid hot partitions. `Query` (by key) is efficient; `Scan` reads the whole table, so avoid it. Conditional writes prevent duplicates. Reads are eventually consistent by default (strong consistency is optional). Use TTL to expire old data.
- **MongoDB:** collections of BSON documents, rich queries, indexes (compound, TTL), aggregation pipeline, replica sets (HA), sharding (scale-out). Read/write concerns tune consistency.
- **When NOT to use NoSQL:** heavy ad-hoc joins, cross-entity transactions, or reporting with unknown queries. Those fit relational better.
- **CAP, briefly:** during a network partition you choose consistency or availability. Most NoSQL stores lean toward availability, with tunable consistency.

### CI/CD & release management

- **Pipeline:** lint → unit → build artifacts (wheel, binaries, image) → integration/smoke → publish → deploy to staging → (approval) → production → post-deploy checks.
- **Build once, promote the same artifact** (tagged by commit SHA) through environments. Never rebuild for prod.
- **Deployment strategies:** rolling, blue/green (instant switch and instant rollback), canary (1% → 10% → 100% while watching metrics), feature flags (separate deploying code from releasing a feature).
- **Rollback plan:** previous task definition or image tag; database migrations that are backward-compatible (expand → migrate → contract).
- **Versioning:** SemVer (MAJOR.MINOR.PATCH), git tags, release branches or trunk-based development, changelogs.
- **Release checklist mindset:** what changed, how do we know it works (tests + monitoring), how do we undo it, who needs to know.

### Linux & Windows operations

- **Linux:** `systemctl status|restart`, `journalctl -u svc -f`, `tail -f`, `grep -r`, `less`, `top`/`htop`, `df -h`/`du -sh` (disk full is a classic outage), `free -m`, `ss -ltnp` (who listens on which port), `lsof -p PID`, `strace -p PID`, `ps aux`, `kill -TERM` vs `-KILL`, permissions (`chmod`/`chown`), `ldd` (shared-lib dependencies), `nm -D` (exported symbols), cron.
- **Windows:** Event Viewer, Services (`services.msc`, `sc query`), Task Manager / Resource Monitor / Process Explorer, `netstat -ano`, PowerShell (`Get-Process`, `Get-NetTCPConnection`, `Get-Content -Wait` as `tail -f`), `dumpbin /exports` (DLL symbols), Dependencies.exe (missing DLLs), Task Scheduler.
- **Cross-platform gotchas:** path separators, CRLF vs LF, case-sensitive filesystems on Linux, `.so` vs `.dll`, `PATH` vs `LD_LIBRARY_PATH` for loading libraries, MSVC vs GCC flags and warnings, `localhost` → IPv6 (you hit this in setup!).

### Aviation weather domain primer (shows genuine interest)

- **METAR:** routine surface observation, usually hourly. `KJFK 111851Z 27012G20KT 10SM FEW050 BKN250 18/10 A3002 RMK AO2` = station, day/time (Z = UTC), wind 270° at 12 kt gusting 20, 10 statute miles visibility, few clouds at 5,000 ft, broken at 25,000 ft, temperature 18 °C / dewpoint 10 °C, altimeter 30.02 inHg, automated station.
- **SPECI:** a special, unscheduled METAR issued when conditions change significantly.
- **TAF:** terminal aerodrome forecast (24–30 h, per airport).
- **PIREP:** pilot report (turbulence, icing). **SIGMET / AIRMET:** advisories for hazardous weather over areas.
- **Ceiling:** the lowest broken (BKN) or overcast (OVC) layer. FEW and SCT layers don't count.
- **Flight categories:** VFR / MVFR / IFR / LIFR, from ceiling and visibility (step 8 implements them).
- **Data sources:** NOAA/NWS, the Aviation Weather Center (aviationweather.gov, with a public data API). Gridded model data (GFS, HRRR) comes as **GRIB2** files, and NetCDF is common in research. A "weather simulation platform" for training (e.g. flight simulators or ATC training) likely ingests real or synthetic data like this, transforms it, and feeds it to simulators in real time. Expect questions on data correctness, timeliness and validation.
- **Why correctness matters:** a wrong visibility value could train someone on the wrong procedure. Talk about validating input ranges, units (statute vs nautical miles, °C vs °F, inHg vs hPa), UTC everywhere, and monitoring data freshness ("no new observations in 90 minutes" should alert).
