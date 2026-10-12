"""Tutorial CLI: verify each tutorial step against a running API, or poke it by hand.

    python cli.py steps                 list the tutorial steps
    python cli.py show 2                concepts + checks for step 2
    python cli.py check 2               run step 2's checks against the server
    python cli.py check all             run every step
    python cli.py req GET /health       send one request, pretty-print the response
    python cli.py req POST /api/v1/observations -d @sample.json
    python cli.py ws                    listen to the WebSocket feed
    python cli.py burst /api/v1/observations -n 20 --auth none
    python cli.py seed -n 10            create sample observations

Global options go before the command:
    python cli.py --base-url https://127.0.0.1:8443 --cafile certs/cert.pem check 10

The checks live in frontend/steps.json, shared with the browser UI, so the CLI
and the frontend always test the same things.
"""

import argparse
import json
import os
import random
import re
import ssl
import string
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "frontend" / "steps.json").read_text(encoding="utf-8"))
STEPS = {s["id"]: s for s in SPEC["steps"]}
VAR = re.compile(r"\{(\w+)\}")

if sys.stdout.isatty():
    if os.name == "nt":
        os.system("")  # turns on ANSI colour handling in the Windows console
    GREEN, RED, YELLOW, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"
else:
    GREEN = RED = YELLOW = DIM = BOLD = RESET = ""


# ---------------------------------------------------------------- spec helpers

def subst(value, variables):
    """Replace {name} placeholders in strings, recursively. Unknown names are left alone."""
    if isinstance(value, str):
        return VAR.sub(lambda m: str(variables.get(m.group(1), m.group(0))), value)
    if isinstance(value, dict):
        return {k: subst(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [subst(v, variables) for v in value]
    return value


def expand(body):
    """{"$template": "obs", "visibility_sm": 2} -> the template with overrides applied."""
    if isinstance(body, dict) and "$template" in body:
        overrides = {k: v for k, v in body.items() if k != "$template"}
        return {**SPEC["templates"][body["$template"]], **overrides}
    return body


def dig(obj, path):
    """dig({"a": [{"b": 1}]}, "a.0.b") -> (True, 1)"""
    for part in path.split("."):
        if isinstance(obj, list) and part.isdigit() and int(part) < len(obj):
            obj = obj[int(part)]
        elif isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return False, None
    return True, obj


def evaluate(expect, status, headers, body):
    """Compare one response with an `expect` block. Returns a list of failure messages."""
    fails = []
    want = expect.get("status")
    if want is not None and status not in (want if isinstance(want, list) else [want]):
        fails.append(f"status {status}, expected {want}")
    for name in expect.get("headers", []):
        if headers.get(name) is None:
            fails.append(f"missing header {name}")
    for name, value in expect.get("header_equals", {}).items():
        if headers.get(name) != value:
            fails.append(f"header {name} = {headers.get(name)!r}, expected {value!r}")
    for path in expect.get("json_has", []):
        if not dig(body, path)[0]:
            fails.append(f"missing JSON field {path}")
    for path, value in expect.get("json_equals", {}).items():
        found, got = dig(body, path)
        if not found or got != value:
            fails.append(f"{path} = {got!r}, expected {value!r}")
    for path, n in expect.get("json_len", {}).items():
        found, got = dig(body, path)
        if not found or not isinstance(got, list) or len(got) != n:
            fails.append(f"len({path}) = {len(got) if isinstance(got, list) else got!r}, expected {n}")
    for path, (value, tol) in expect.get("json_approx", {}).items():
        found, got = dig(body, path)
        if not found or not isinstance(got, (int, float)) or abs(got - value) > tol:
            fails.append(f"{path} = {got!r}, expected {value} +/- {tol}")
    return fails


def parse_body(response):
    if "json" in response.headers.get("content-type", ""):
        try:
            return response.json()
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------- runner

class Runner:
    def __init__(self, args):
        self.base = args.base_url.rstrip("/")
        self.ssl = ssl.create_default_context(cafile=args.cafile) if args.cafile else ssl.create_default_context()
        if args.insecure:
            self.ssl.check_hostname = False
            self.ssl.verify_mode = ssl.CERT_NONE
        self.http = httpx.Client(base_url=self.base, verify=self.ssl, timeout=10)
        self.keys = {"rw": args.key, "ro": args.ro_key, "bad": "not-a-real-key", "none": None}

    def send(self, req, variables):
        req = subst({**req, "json": expand(req.get("json"))}, variables)
        headers = dict(req.get("headers", {}))
        key = self.keys[req.get("auth", "rw")]
        if key:
            headers["X-API-Key"] = key
        # Accept "health" as well as "/health": Git Bash rewrites args that start
        # with "/" into Windows paths (C:/Program Files/Git/health).
        path = "/" + req["path"].lstrip("/")
        return self.http.request(req["method"], path, headers=headers, json=req.get("json"))

    def ws_url(self, path):
        return re.sub(r"^http", "ws", self.base) + path

    def run_check(self, check, variables):
        """Returns (passed, detail). passed is None when the check is skipped."""
        scheme = check.get("require_scheme")
        if scheme and not self.base.startswith(scheme + "://"):
            return None, f"needs a {scheme}:// --base-url (currently {self.base})"
        kind = check.get("kind", "http")
        if kind == "command":
            return self.run_command(check, variables)
        if kind == "ws":
            return self.run_ws(check, variables)

        expect = subst(check["expect"], variables)
        fails = []
        for _ in range(check.get("repeat", 1)):
            start = time.perf_counter()
            r = self.send(check["request"], variables)
            ms = (time.perf_counter() - start) * 1000
            body = parse_body(r)
            fails = evaluate(expect, r.status_code, r.headers, body)
            if not fails:
                break
        if fails:
            return False, "; ".join(fails)
        for name, source in check.get("save", {}).items():
            where, _, key = source.partition(":")
            variables[name] = r.headers.get(key) if where == "header" else dig(body, key)[1]
        return True, f"{r.status_code} in {ms:.0f} ms"

    def run_ws(self, check, variables):
        from websockets.sync.client import connect

        url = self.ws_url(check["path"])
        expect = subst(check["expect"], variables)
        with connect(url, ssl=self.ssl if url.startswith("wss") else None, open_timeout=5) as ws:
            ws.recv(timeout=5)  # the server's hello message
            r = self.send(check["request"], variables)
            if r.status_code >= 400:
                return False, f"trigger request failed with {r.status_code}"
            deadline = time.monotonic() + 5
            fails = ["no message received within 5s"]
            while fails and time.monotonic() < deadline:
                try:
                    msg = json.loads(ws.recv(timeout=max(0.1, deadline - time.monotonic())))
                except TimeoutError:
                    break
                fails = evaluate(expect, None, {}, msg) or []
        return (False, "; ".join(fails)) if fails else (True, f"pushed over {url.split(':')[0]}://")

    def run_command(self, check, variables):
        argv = subst(check["argv"], variables)
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
        return proc.returncode == 0, f"exit {proc.returncode}: {tail[0]}"


def fresh_vars():
    # A random station per run so re-running checks never collides with old data.
    return {"station": "K" + "".join(random.choices(string.ascii_uppercase, k=3)), "python": sys.executable}


# -------------------------------------------------------------------- commands

def cmd_steps(args):
    for s in SPEC["steps"]:
        n = len(s["checks"])
        print(f"{BOLD}{s['id']:>2}{RESET}  {s['title']:<34} {DIM}{n or 'no'} check{'s' if n != 1 else ''}{RESET}")
        print(f"    {DIM}{s['goal']}{RESET}")


def cmd_show(args):
    s = STEPS[args.step]
    print(f"{BOLD}Step {s['id']}: {s['title']}{RESET}\n{s['goal']}\n")
    print(f"{BOLD}Concepts{RESET}")
    for c in s["concepts"]:
        print(f"  - {c}")
    print(f"\n{BOLD}Reference files{RESET}  {', '.join(s['files'])}\n")
    print(f"{BOLD}Checks{RESET}")
    for c in s["checks"]:
        req = c.get("request", {})
        what = " ".join(c["argv"]) if c.get("kind") == "command" else f"{req.get('method', '')} {req.get('path', '')}"
        print(f"  - {c['name']}  {DIM}{what}{RESET}")
    if not s["checks"]:
        print("  (manual step, see TUTORIAL.md)")


def cmd_check(args):
    runner = Runner(args)
    ids = list(STEPS) if args.steps == ["all"] else [int(x) for x in args.steps]
    total_failed = 0
    for sid in ids:
        step = STEPS[sid]
        print(f"\n{BOLD}Step {sid}: {step['title']}{RESET}")
        if not step["checks"]:
            print(f"  {YELLOW}SKIP{RESET} manual step, nothing to check automatically")
            continue
        variables = fresh_vars()
        for check in step["checks"]:
            try:
                ok, detail = runner.run_check(check, variables)
            except (httpx.ConnectError, ConnectionRefusedError):
                raise  # server is down: stop here, main() prints how to start it
            except Exception as e:  # report and keep going; one broken check shouldn't hide the rest
                ok, detail = False, f"{type(e).__name__}: {e}"
            tag = {True: f"{GREEN}PASS", False: f"{RED}FAIL", None: f"{YELLOW}SKIP"}[ok] + RESET
            print(f"  {tag} {check['name']}  {DIM}{detail}{RESET}")
            if ok is not True and check.get("hint"):
                print(f"       {YELLOW}hint:{RESET} {check['hint']}")
            if ok is False:
                total_failed += 1
            if ok and check.get("cooldown_s"):
                print(f"       {DIM}cooling down {check['cooldown_s']}s so later checks aren't rate limited...{RESET}")
                time.sleep(check["cooldown_s"])
    print(f"\n{RED + str(total_failed) + ' check(s) failed' if total_failed else GREEN + 'All checks passed'}{RESET}")
    return 1 if total_failed else 0


def cmd_req(args):
    runner = Runner(args)
    body = None
    if args.data:
        text = Path(args.data[1:]).read_text(encoding="utf-8") if args.data.startswith("@") else args.data
        body = json.loads(text)
    headers = dict(h.split(":", 1) for h in args.header)
    req = {"method": args.method.upper(), "path": args.path, "auth": args.auth, "json": body,
           "headers": {k.strip(): v.strip() for k, v in headers.items()}}
    start = time.perf_counter()
    r = runner.send(req, {})
    ms = (time.perf_counter() - start) * 1000
    colour = GREEN if r.status_code < 400 else YELLOW if r.status_code < 500 else RED
    print(f"{colour}{r.http_version} {r.status_code} {r.reason_phrase}{RESET}  {DIM}{ms:.0f} ms{RESET}")
    for k, v in r.headers.items():
        print(f"{DIM}{k}: {v}{RESET}")
    print()
    body = parse_body(r)
    print(json.dumps(body, indent=2) if body is not None else r.text)
    return 0 if r.status_code < 400 else 1


def cmd_ws(args):
    from websockets.sync.client import connect

    runner = Runner(args)
    url = runner.ws_url(args.path)
    print(f"Connecting to {url} (Ctrl+C to stop)")
    with connect(url, ssl=runner.ssl if url.startswith("wss") else None) as ws:
        try:
            for msg in ws:
                print(json.dumps(json.loads(msg), indent=2))
        except KeyboardInterrupt:
            pass


def cmd_burst(args):
    runner = Runner(args)
    counts, retry_after = Counter(), None
    start = time.perf_counter()
    for _ in range(args.n):
        r = runner.send({"method": "GET", "path": args.path, "auth": args.auth}, {})
        counts[r.status_code] += 1
        retry_after = retry_after or r.headers.get("retry-after")
    secs = time.perf_counter() - start
    print(f"{args.n} requests in {secs:.2f}s -> " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    if retry_after:
        print(f"First Retry-After: {retry_after}s")


def cmd_seed(args):
    runner = Runner(args)
    stations = ["KJFK", "KLAX", "KORD", "KDEN", "KSEA", "KATL", "KBOS", "KSFO"]
    created = 0
    for i in range(args.n):
        body = {
            "station": random.choice(stations),
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:00Z", time.gmtime(time.time() - i * 3600)),
            "temperature_c": (temp := round(random.uniform(-5, 30), 1)),
            "dewpoint_c": round(temp - random.uniform(0, 15), 1),  # dewpoint can't exceed temperature
            "wind_dir_deg": random.randrange(0, 360, 10),
            "wind_speed_kt": random.randint(0, 30),
            "visibility_sm": random.choice([0.5, 2, 4, 7, 10]),
            "ceiling_ft": random.choice([None, 400, 900, 2500, 6000]),
        }
        r = runner.send({"method": "POST", "path": "/api/v1/observations", "json": body}, {})
        created += r.status_code == 201
    print(f"Created {created}/{args.n} observations (409s are duplicate station+time, that's fine)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument("--key", default=os.environ.get("API_KEY", "dev-key-123"), help="read-write API key")
    p.add_argument("--ro-key", default=os.environ.get("API_RO_KEY", "readonly-key-789"), help="read-only API key")
    p.add_argument("--cafile", help="trust this certificate (for the self-signed HTTPS step)")
    p.add_argument("--insecure", action="store_true", help="skip TLS verification (don't make a habit of it)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("steps", help="list tutorial steps").set_defaults(fn=cmd_steps)

    s = sub.add_parser("show", help="show one step's concepts and checks")
    s.add_argument("step", type=int, choices=list(STEPS))
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("check", help="run checks for steps (numbers or 'all')")
    s.add_argument("steps", nargs="+")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("req", help="send one request")
    s.add_argument("method")
    s.add_argument("path")
    s.add_argument("-d", "--data", help="JSON body, or @file.json")
    s.add_argument("-H", "--header", action="append", default=[], help="'Name: value' (repeatable)")
    s.add_argument("--auth", choices=["rw", "ro", "bad", "none"], default="rw")
    s.set_defaults(fn=cmd_req)

    s = sub.add_parser("ws", help="print WebSocket messages")
    s.add_argument("path", nargs="?", default="/ws/observations")
    s.set_defaults(fn=cmd_ws)

    s = sub.add_parser("burst", help="fire N quick GETs to see rate limiting")
    s.add_argument("path")
    s.add_argument("-n", type=int, default=20)
    s.add_argument("--auth", choices=["rw", "ro", "bad", "none"], default="none")
    s.set_defaults(fn=cmd_burst)

    s = sub.add_parser("seed", help="create sample observations")
    s.add_argument("-n", type=int, default=10)
    s.set_defaults(fn=cmd_seed)

    args = p.parse_args()
    if args.command == "check" and args.steps != ["all"]:
        bad = [x for x in args.steps if not x.isdigit() or int(x) not in STEPS]
        if bad:
            p.error(f"unknown step(s): {', '.join(bad)}. Use 1-{max(STEPS)} or 'all'.")
    try:
        sys.exit(args.fn(args) or 0)
    except (httpx.ConnectError, ConnectionRefusedError) as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            sys.exit(f"TLS: {args.base_url} sent a certificate we don't trust. "
                     "For the self-signed tutorial cert, add --cafile certs/cert.pem")
        sys.exit(f"Can't connect to {args.base_url}. Start the server: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
