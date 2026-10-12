// Tutorial frontend. Runs the same checks as `python cli.py check` (both read
// steps.json), plus a request console, a WebSocket viewer and a data table.
// Plain browser JS, no build step.

"use strict";

const $ = (sel) => document.querySelector(sel);
const DEFAULTS = { baseUrl: "http://127.0.0.1:8000", rwKey: "dev-key-123", roKey: "readonly-key-789" };
let SPEC = null;
let current = 1;
let progress = load("progress", {});        // { stepId: "pass" | "fail" }
const settings = { ...DEFAULTS, ...load("settings", {}) };

// ------------------------------------------------------------- small helpers

function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem("wxtut." + key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem("wxtut." + key, JSON.stringify(value)); } catch { /* storage blocked: fine */ }
}

// Build DOM nodes without innerHTML, so server data can never inject markup.
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v !== undefined && v !== null && v !== false) node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat(Infinity)) if (c !== null && c !== undefined) node.append(c instanceof Node ? c : String(c));
  return node;
}

const base = () => settings.baseUrl.replace(/\/+$/, "");
const wsBase = () => base().replace(/^http/, "ws");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pretty = (v) => (typeof v === "string" ? v : JSON.stringify(v, null, 2));

// ------------------------------------------------- check engine (mirrors cli.py)

function subst(value, vars) {
  if (typeof value === "string") return value.replace(/\{(\w+)\}/g, (m, name) => (name in vars ? String(vars[name]) : m));
  if (Array.isArray(value)) return value.map((v) => subst(v, vars));
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, subst(v, vars)]));
  return value;
}

function expand(body) {
  if (body && typeof body === "object" && "$template" in body) {
    const { $template, ...overrides } = body;
    return { ...SPEC.templates[$template], ...overrides };
  }
  return body;
}

function dig(obj, path) {
  for (const part of path.split(".")) {
    if (Array.isArray(obj) && /^\d+$/.test(part) && Number(part) < obj.length) obj = obj[Number(part)];
    else if (obj && typeof obj === "object" && !Array.isArray(obj) && part in obj) obj = obj[part];
    else return [false, undefined];
  }
  return [true, obj];
}

function evaluate(expect, status, headers, body) {
  const fails = [];
  const want = expect.status;
  if (want !== undefined && !(Array.isArray(want) ? want : [want]).includes(status)) fails.push(`status ${status}, expected ${want}`);
  for (const name of expect.headers || []) if (headers.get(name) === null) fails.push(`missing header ${name}`);
  for (const [name, value] of Object.entries(expect.header_equals || {})) {
    if (headers.get(name) !== value) fails.push(`header ${name} = ${JSON.stringify(headers.get(name))}, expected ${JSON.stringify(value)}`);
  }
  for (const path of expect.json_has || []) if (!dig(body, path)[0]) fails.push(`missing JSON field ${path}`);
  for (const [path, value] of Object.entries(expect.json_equals || {})) {
    const [found, got] = dig(body, path);
    if (!found || got !== value) fails.push(`${path} = ${JSON.stringify(got)}, expected ${JSON.stringify(value)}`);
  }
  for (const [path, n] of Object.entries(expect.json_len || {})) {
    const [found, got] = dig(body, path);
    if (!found || !Array.isArray(got) || got.length !== n) fails.push(`len(${path}) = ${Array.isArray(got) ? got.length : JSON.stringify(got)}, expected ${n}`);
  }
  for (const [path, [value, tol]] of Object.entries(expect.json_approx || {})) {
    const [found, got] = dig(body, path);
    if (!found || typeof got !== "number" || Math.abs(got - value) > tol) fails.push(`${path} = ${JSON.stringify(got)}, expected ${value} ± ${tol}`);
  }
  return fails;
}

const KEYS = () => ({ rw: settings.rwKey, ro: settings.roKey, bad: "not-a-real-key", none: null });

// Sends one request; returns {status, headers, body, ms, method, url, sentHeaders, sentBody}.
async function send(req, vars = {}) {
  req = subst({ ...req, json: expand(req.json) }, vars);
  const headers = { ...(req.headers || {}) };
  const key = KEYS()[req.auth || "rw"];
  if (key) headers["X-API-Key"] = key;
  let payload;
  if (req.json !== undefined && req.json !== null) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(req.json);
  }
  const url = base() + "/" + req.path.replace(/^\/+/, "");
  const start = performance.now();
  let res;
  try {
    res = await fetch(url, { method: req.method, headers, body: payload });
  } catch (e) {
    // fetch only throws for network-level failures. The browser hides the reason
    // on purpose, so the console is where the real error (CORS, refused...) shows.
    throw new Error(`Network error reaching ${url}: server down, wrong URL, untrusted HTTPS cert, or blocked by CORS (see browser console)`);
  }
  const ms = performance.now() - start;
  const text = await res.text();
  let body = null;
  if ((res.headers.get("content-type") || "").includes("json")) { try { body = JSON.parse(text); } catch { body = text; } }
  else if (text) body = text;
  return { status: res.status, statusText: res.statusText, headers: res.headers, body, ms, method: req.method, url, sentHeaders: headers, sentBody: req.json };
}

function wsCheck(check, vars) {
  return new Promise((resolve) => {
    const url = wsBase() + check.path;
    const expect = subst(check.expect, vars);
    let ws;
    let triggered = false;
    let last = "no message received within 5s";
    const done = (ok, detail) => { clearTimeout(timer); try { ws.close(); } catch { /* already closed */ } resolve({ ok, detail }); };
    const timer = setTimeout(() => done(false, last), 5000);
    try { ws = new WebSocket(url); } catch (e) { return done(false, e.message); }
    ws.onerror = () => done(false, `could not open ${url}`);
    ws.onmessage = async (ev) => {
      const msg = JSON.parse(ev.data);
      if (!triggered) {      // first message is the server's hello; now cause an event
        triggered = true;
        try {
          const r = await send(check.request, vars);
          if (r.status >= 400) done(false, `trigger request failed with ${r.status}`);
        } catch (e) { done(false, e.message); }
        return;
      }
      const fails = evaluate(expect, undefined, new Headers(), msg);
      if (!fails.length) done(true, `pushed over ${url.split(":")[0]}://`, msg);
      else last = fails.join("; ");
    };
  });
}

async function runCheck(check, vars) {
  if (check.require_scheme && !base().startsWith(check.require_scheme + "://")) {
    return { ok: null, detail: `needs a ${check.require_scheme}:// API base URL` };
  }
  const kind = check.kind || "http";
  if (kind === "command") return { ok: null, detail: `CLI only: run  ${subst(check.argv, { python: "python" }).join(" ")}` };
  if (kind === "ws") return wsCheck(check, vars);

  const expect = subst(check.expect, vars);
  let r, fails;
  for (let i = 0; i < (check.repeat || 1); i++) {
    r = await send(check.request, vars);
    fails = evaluate(expect, r.status, r.headers, r.body);
    if (!fails.length) break;
  }
  if (fails.length) return { ok: false, detail: fails.join("; "), response: r };
  for (const [name, source] of Object.entries(check.save || {})) {
    const [where, key] = source.split(/:(.*)/);
    vars[name] = where === "header" ? r.headers.get(key) : dig(r.body, key)[1];
  }
  return { ok: true, detail: `${r.status} in ${r.ms.toFixed(0)} ms`, response: r };
}

function freshVars() {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  let station = "K";
  for (let i = 0; i < 3; i++) station += letters[Math.floor(Math.random() * 26)];
  return { station };
}

// ------------------------------------------------------------- step list + view

function renderStepList() {
  const list = $("#stepList");
  list.replaceChildren(...SPEC.steps.map((s) => {
    const state = s.checks.length ? progress[s.id] || "" : "manual";
    return el("li", {},
      el("button", { class: s.id === current ? "active" : "", onclick: () => selectStep(s.id) },
        el("span", { class: `num ${state}` }, state === "pass" ? "✓" : state === "fail" ? "!" : s.id),
        s.title));
  }));
}

function selectStep(id) {
  current = id;
  save("current", id);
  renderStepList();
  renderStep();
}

function renderStep(results = null) {
  const s = SPEC.steps.find((x) => x.id === current);
  const view = $("#stepView");
  const cliCmd = `python cli.py check ${s.id}`;
  view.replaceChildren(
    el("div", { class: "step-head" },
      el("div", {}, el("span", { class: "muted" }, `Step ${s.id} of ${SPEC.steps.length}`), el("h2", {}, s.title)),
      s.checks.length ? el("button", { class: "btn primary", id: "runStep", onclick: () => runStep(s) }, "Run checks") : null),
    el("p", { class: "goal" }, s.goal),
    el("ul", { class: "concepts" }, s.concepts.map((c) => el("li", {}, c))),
    el("div", { class: "meta" },
      el("span", {}, "Reference: ", s.files.map((f, i) => [i ? ", " : "", el("code", {}, f)])),
      s.checks.length ? el("span", {}, "Terminal: ",
        el("code", { class: "copy", title: "Click to copy", onclick: (e) => copy(cliCmd, e.target) }, cliCmd)) : null),
    s.checks.length
      ? el("ol", { class: "checks" }, s.checks.map((c, i) => renderCheck(c, results ? results[i] : undefined)))
      : el("p", { class: "muted" }, "No automated checks for this step. Work through it in TUTORIAL.md."),
  );
}

function renderCheck(check, result) {
  const state = result === undefined ? "" : result === "running" ? "running" : result.ok === true ? "pass" : result.ok === false ? "fail" : "skip";
  const label = { "": "····", running: "RUN…", pass: "PASS", fail: "FAIL", skip: "SKIP" }[state];
  const req = check.request || {};
  const what = check.kind === "command" ? check.argv.join(" ") : `${check.kind === "ws" ? "WS " + check.path + " + " : ""}${req.method} ${req.path}`;
  const body = el("div", { class: "body" },
    typeof result === "object" && result.ok !== true && check.hint ? el("p", { class: "hint" }, "Hint: " + check.hint) : null,
    el("div", {}, el("code", {}, what), req.auth ? el("span", { class: "muted" }, `  (key: ${req.auth})`) : null),
    result && result.response ? responseView(result.response) : null);
  return el("li", {},
    el("details", { class: `check ${state}`, open: state === "fail" },
      el("summary", {},
        el("span", { class: "badge" }, label),
        el("span", {}, check.name),
        result && result.detail ? el("span", { class: "detail" }, result.detail) : null),
      body));
}

async function runStep(step) {
  const btn = $("#runStep");
  if (btn) btn.disabled = true;
  const vars = freshVars();
  const results = step.checks.map(() => undefined);
  let failed = false, passed = false;
  for (let i = 0; i < step.checks.length; i++) {
    results[i] = "running";
    if (step.id === current) renderStep(results);
    try {
      results[i] = await runCheck(step.checks[i], vars);
    } catch (e) {
      results[i] = { ok: false, detail: e.message };
    }
    if (results[i].ok === false) failed = true;
    if (results[i].ok === true) passed = true;
    if (step.id === current) renderStep(results);
    if (results[i].ok && step.checks[i].cooldown_s) {
      results[i].detail += ` · cooling down ${step.checks[i].cooldown_s}s`;
      if (step.id === current) renderStep(results);
      await sleep(step.checks[i].cooldown_s * 1000);
    }
  }
  // All-skipped steps (HTTPS on an http:// URL, CLI-only checks) stay unmarked.
  if (failed || passed) progress[step.id] = failed ? "fail" : "pass";
  else delete progress[step.id];
  save("progress", progress);
  renderStepList();
  return !failed;
}

async function runAll() {
  const btn = $("#runAll");
  btn.disabled = true;
  for (const s of SPEC.steps.filter((x) => x.checks.length)) {
    selectStep(s.id);
    await runStep(s);
  }
  btn.disabled = false;
}

function copy(text, node) {
  navigator.clipboard?.writeText(text).then(() => {
    const old = node.textContent;
    node.textContent = "copied!";
    setTimeout(() => (node.textContent = old), 900);
  }).catch(() => {});
}

// --------------------------------------------------------------- response view

function responseView(r) {
  const cls = r.status < 300 ? "ok" : r.status < 500 ? "warn" : "err";
  const headerLines = [...r.headers.entries()].map(([k, v]) => `${k}: ${v}`).join("\n");
  return el("div", {},
    el("div", { class: `status-line ${cls}` }, `${r.method} ${r.url.replace(base(), "")} → ${r.status} ${r.statusText}  (${r.ms.toFixed(0)} ms)`),
    el("details", {}, el("summary", { class: "muted" }, "Request sent"),
      el("pre", {}, Object.entries(r.sentHeaders).map(([k, v]) => `${k}: ${v}`).join("\n") + (r.sentBody ? "\n\n" + pretty(r.sentBody) : ""))),
    el("details", {}, el("summary", { class: "muted" }, "Response headers (only CORS-exposed ones are visible to JS)"),
      el("pre", { class: "headers" }, headerLines || "(none)")),
    r.body !== null ? el("pre", {}, pretty(r.body)) : el("p", { class: "muted" }, "(empty body)"));
}

// ------------------------------------------------------------- request console

const SAMPLE = () => ({
  station: "KDEN",
  observed_at: new Date().toISOString().slice(0, 16) + ":00Z",
  temperature_c: 12.5, dewpoint_c: 3.0, wind_dir_deg: 250, wind_speed_kt: 14,
  visibility_sm: 6, ceiling_ft: 2500, raw_metar: "KDEN 111853Z 25014KT 6SM BKN025 13/03 A3002",
});
const PRESETS = {
  health: ["GET", "/health", "rw", ""],
  create: ["POST", "/api/v1/observations", "rw", () => pretty(SAMPLE())],
  invalid: ["POST", "/api/v1/observations", "rw", pretty({ station: "TOOLONG", wind_dir_deg: 999 })],
  category: ["GET", "/api/v1/tools/flight-category?visibility_sm=2&ceiling_ft=1500", "none", ""],
  wind: ["GET", "/api/v1/tools/wind-components?wind_dir=270&wind_speed=20&runway_heading=240", "none", ""],
  metrics: ["GET", "/metrics", "none", ""],
};

async function sendConsole(e) {
  e.preventDefault();
  const out = $("#cResponse");
  const headers = {};
  for (const line of $("#cHeaders").value.split("\n")) {
    const i = line.indexOf(":");
    if (i > 0) headers[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  let json;
  const raw = $("#cBody").value.trim();
  if (raw) {
    try { json = JSON.parse(raw); } catch (err) {
      out.className = "response";
      out.replaceChildren(el("div", { class: "status-line err" }, "Body is not valid JSON: " + err.message));
      return;
    }
  }
  out.className = "response";
  out.replaceChildren(el("span", { class: "muted" }, "Sending…"));
  try {
    const r = await send({ method: $("#cMethod").value, path: $("#cPath").value, auth: $("#cAuth").value, headers, json });
    out.replaceChildren(responseView(r));
  } catch (err) {
    out.replaceChildren(el("div", { class: "status-line err" }, err.message));
  }
}

// ------------------------------------------------------------------ live feed

let socket = null;

function wsLog(text, cls = "") {
  const t = new Date().toLocaleTimeString();
  $("#wsLog").prepend(el("li", { class: cls }, el("time", {}, t), text));
}

function toggleSocket() {
  if (socket) { socket.close(); return; }
  const url = wsBase() + "/ws/observations";
  $("#wsState").textContent = "connecting to " + url;
  socket = new WebSocket(url);
  socket.onopen = () => {
    $("#wsState").textContent = "connected: " + url;
    $("#wsToggle").textContent = "Disconnect";
    $("#wsPing").disabled = false;
  };
  socket.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.event === "observation.created") {
      const d = msg.data;
      wsLog(`${msg.event}  ${d.station} ${d.observed_at}  ${d.flight_category}  vis ${d.visibility_sm}sm`);
    } else wsLog(JSON.stringify(msg));
  };
  socket.onerror = () => wsLog("error (is the server running? wss:// needs a trusted cert)");
  socket.onclose = (ev) => {
    $("#wsState").textContent = `disconnected (code ${ev.code})`;
    $("#wsToggle").textContent = "Connect";
    $("#wsPing").disabled = true;
    socket = null;
  };
}

// ----------------------------------------------------------------- data table

let offset = 0;
const PAGE = 10;

async function loadData(e) {
  if (e) { e.preventDefault(); offset = 0; }
  const station = $("#dStation").value.trim().toUpperCase();
  const qs = new URLSearchParams({ limit: PAGE, offset });
  if (station) qs.set("station", station);
  const rows = $("#dRows");
  try {
    const r = await send({ method: "GET", path: "/api/v1/observations?" + qs });
    if (r.status !== 200) {
      rows.replaceChildren(el("tr", {}, el("td", { colspan: 8 }, `${r.status}: ${r.body?.error?.message || pretty(r.body)}`)));
      return;
    }
    const { items, total } = r.body;
    $("#dInfo").textContent = total ? `${offset + 1}–${offset + items.length} of ${total}` : "no observations yet (try python cli.py seed)";
    $("#dPrev").disabled = offset === 0;
    $("#dNext").disabled = offset + PAGE >= total;
    rows.replaceChildren(...items.map((o) => el("tr", {},
      el("td", {}, el("strong", {}, o.station)),
      el("td", {}, o.observed_at.replace("T", " ").replace("Z", "")),
      el("td", {}, `${o.temperature_c} / ${o.dewpoint_c}`),
      el("td", {}, `${String(o.wind_dir_deg).padStart(3, "0")}° @ ${o.wind_speed_kt} kt`),
      el("td", {}, o.visibility_sm),
      el("td", {}, o.ceiling_ft ?? "—"),
      el("td", {}, el("span", { class: `cat ${o.flight_category}` }, o.flight_category)),
      el("td", {}, el("button", { class: "btn small", title: "DELETE with the read-write key", onclick: () => deleteObs(o.id) }, "Delete")))));
    if (!items.length) rows.replaceChildren(el("tr", {}, el("td", { colspan: 8, class: "muted" }, "Nothing here.")));
  } catch (err) {
    rows.replaceChildren(el("tr", {}, el("td", { colspan: 8 }, err.message)));
  }
}

async function deleteObs(id) {
  const r = await send({ method: "DELETE", path: `/api/v1/observations/${id}` });
  if (r.status !== 204) alert(`${r.status}: ${r.body?.error?.message || ""}`);
  loadData();
}

// ------------------------------------------------------------ health + settings

async function pollHealth() {
  const box = $("#health");
  try {
    const res = await fetch(base() + "/health");
    const body = await res.json();
    box.className = "health up";
    $("#healthText").textContent = `up · engine: ${body.engine ?? "?"}`;
  } catch {
    box.className = "health down";
    $("#healthText").textContent = "unreachable";
  }
}

function bindSettings() {
  for (const id of ["baseUrl", "rwKey", "roKey"]) {
    const input = $("#" + id);
    input.value = settings[id];
    input.addEventListener("change", () => {
      settings[id] = input.value.trim() || DEFAULTS[id];
      input.value = settings[id];
      save("settings", settings);
      $("#docsLink").href = base() + "/docs";
      pollHealth();
    });
  }
  $("#docsLink").href = base() + "/docs";
}

// ---------------------------------------------------------------------- boot

async function boot() {
  bindSettings();
  pollHealth();
  setInterval(pollHealth, 5000);

  document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("active", x === b));
    document.querySelectorAll(".tab-panel").forEach((p) => (p.hidden = p.id !== "tab-" + b.dataset.tab));
  }));
  document.querySelectorAll("[data-preset]").forEach((b) => b.addEventListener("click", () => {
    const [method, path, auth, body] = PRESETS[b.dataset.preset];
    $("#cMethod").value = method;
    $("#cPath").value = path;
    $("#cAuth").value = auth;
    $("#cBody").value = typeof body === "function" ? body() : body;
  }));
  $("#consoleForm").addEventListener("submit", sendConsole);
  $("#wsToggle").addEventListener("click", toggleSocket);
  $("#wsPing").addEventListener("click", () => socket?.send("ping"));
  $("#wsClear").addEventListener("click", () => $("#wsLog").replaceChildren());
  $("#dataForm").addEventListener("submit", loadData);
  $("#dPrev").addEventListener("click", () => { offset = Math.max(0, offset - PAGE); loadData(); });
  $("#dNext").addEventListener("click", () => { offset += PAGE; loadData(); });
  $("#runAll").addEventListener("click", runAll);
  $("#resetProgress").addEventListener("click", () => { progress = {}; save("progress", progress); renderStepList(); renderStep(); });

  try {
    SPEC = await (await fetch("steps.json", { cache: "no-store" })).json();
  } catch {
    $("#stepView").replaceChildren(el("p", {}, "Couldn't load steps.json. Serve this folder over HTTP: python -m http.server 5500 --bind 127.0.0.1 --directory frontend"));
    return;
  }
  current = load("current", 1);
  if (!SPEC.steps.some((s) => s.id === current)) current = 1;
  renderStepList();
  renderStep();
}

boot();
