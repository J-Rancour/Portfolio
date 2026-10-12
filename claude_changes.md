# Claude Changes

A log of changes Claude Code has made, newest at the bottom. Times are local (EDT).

Each entry shows the code or content as it was **before** the change, so it can be restored.

Earlier entries were logged after the fact. Their times come from file modification times, so they're accurate to the minute only where noted.

## 2026-10-11

### ~20:00 — Created global `CLAUDE.md`
- **File:** `C:\Users\jiran\.claude\CLAUDE.md` (outside this repo; applies to every project)
- Added coding guidelines: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, If You Don't Know Say It.
- **Before:** the file did not exist.

### ~20:01 — Updated global `CLAUDE.md`
- Replaced the contents with a new version: added the intro, the tradeoff note, the "never read `.env`" rule and a PR descriptions section.
- Restored section 5 ("If You Don't Know, Say It") after the replacement dropped it. *(20:01 is the file's last modification time.)*

<details>
<summary><b>Before</b>: the full first version, which the replacement overwrote</summary>

````markdown
# Global Instructions

## 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. If You Don't Know, Say It
````
</details>

**Before** restoring section 5, the end of section 4 ran straight into the PR section:

```markdown
Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## PR descriptions
```

### ~20:05 — Added `.env` deny rule to global settings
- **File:** `C:\Users\jiran\.claude\settings.json` (outside this repo)
- Added `permissions.deny: ["Read(**/.env)"]`. This blocks the Read tool from opening `.env` files. `.env.example` is still readable, and shell commands like `cat .env` are not blocked.
- *(Time approximate: the file was modified again at 20:08 by the `/effort` command, which set `effortLevel: high`.)*

**Before:**

```json
{
  "autoUpdatesChannel": "latest",
  "theme": "dark"
}
```

### 20:16 — Created `ocr` conda environment
- **Location:** `C:\Users\jiran\anaconda3\envs\ocr` (Python 3.12)
- Installed `pix2text`, `pymupdf`, `pillow` and `ipykernel`.
- Kept separate so the Anaconda base env is not touched: installing pix2text there would have upgraded numpy 1.26 → 2.x and added `opencv-python-headless` next to `opencv-python`.
- **Before:** the environment did not exist. To undo: `conda env remove -n ocr`

### 20:18 — Registered Jupyter kernel and pinned `rapidocr`
- Kernel "Python (ocr)", registered at `C:\Users\jiran\AppData\Roaming\jupyter\kernels\ocr`.
- Downgraded `rapidocr` 3.10.0 → 3.9.2 in the `ocr` env. 3.10.0 removed `resolve_model_key`, which `cnstd` (a pix2text dependency) imports, so pix2text failed to load.
- pix2text downloaded its models on first run to `C:\Users\jiran\AppData\Roaming\pix2text`.
- **Before:** no kernel; `rapidocr` 3.10.0. To undo the kernel: `jupyter kernelspec remove ocr`

### 20:20 — Added pix2text cell to `testing.ipynb`
- **File:** `educational_prompt_creator/testing.ipynb`, new cell `86f69327` after the "chatgpt version #2" cell (`915fda54`).
- OCRs page 80 with pix2text, English-only, and outputs maths as LaTeX (e.g. `$x^{2}$`). It needs the "Python (ocr)" kernel.
- The same code was tested as a standalone script; the notebook cell itself has not been run.
- **Before:** no code was changed. This is a new cell, so delete it to undo.

### 20:23 — Created this log
- **File:** `claude_changes.md` (repo root)
- Also saved a Claude memory, so future sessions keep logging here: `C:\Users\jiran\.claude\projects\C--something-professional-Portfolio\memory\change-log.md`
- **Before:** neither file existed.

### 20:24 — Added "before" content to every entry
- **Files:** this log, and the `change-log` memory, now telling future sessions to record previous code.
- **Before:** entries only described each change, without the previous code.

### 20:39 — Added fill-in-the-blank cell to `testing.ipynb`
- **File:** `educational_prompt_creator/testing.ipynb`, new cell `3b9f2a13` after the pix2text cell (`86f69327`).
- Detects the gray answer boxes on page 80 with OpenCV (mid-gray, unsaturated, square blobs: finds all 6). It then OCRs each line containing a box in pieces split at the box, and joins the pieces with `___`. It only prints those lines, not the whole page. Needs the "Python (ocr)" kernel.
- Blanks land correctly in all 6 lines, but maths in short pieces is worse than full-page OCR (e.g. `x³` → `x`, `5x²` → `5x2`).
- The cell's code was run in the `ocr` env and its output checked; it has not been run inside the notebook itself.
- **Before:** no code was changed. This is a new cell, so delete it to undo.

### 20:45 — Cleaned up output of both pix2text cells in `testing.ipynb`
- **File:** `educational_prompt_creator/testing.ipynb`, cells `86f69327` (pix2text) and `3b9f2a13` (fill in the blank).
- `86f69327`: added a `quiet()` helper that hides pix2text's download/model log spam and warnings, and a `to_markdown()` helper. `to_markdown()` turns `$$…$$` blocks into inline maths, joins digits the OCR split apart (`1 2` → `12`) and keeps line breaks. The cell now shows the result with `display(Markdown(...))` so the LaTeX renders instead of printing raw.
- `3b9f2a13`: now reuses `p2t`, `quiet` and `to_markdown` from `86f69327`, so **run that cell first**. It no longer reloads the model, wraps OCR calls in `quiet()`, escapes the blanks as `\_\_\_` so Markdown doesn't treat them as formatting, and displays all lines as one Markdown block.
- Both cells were run in order in the `ocr` env with stdout and stderr captured: no warnings, no errors. Not run inside the notebook itself.

<details>
<summary><b>Before</b>: cell <code>86f69327</code></summary>

```python
#pix2text version (needs the "Python (ocr)" kernel)
#outputs math as LaTeX, e.g. x^2 -> $x^{2}$
import pymupdf
from PIL import Image
from pix2text import Pix2Text

doc = pymupdf.open("fearons_pre_algebra.pdf")
page = doc[80]

pix = page.get_pixmap(dpi=300)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

# English only, default also includes Chinese which adds junk characters
p2t = Pix2Text.from_config(total_configs={"languages": ("en",), "text_formula": {"languages": ("en",)}})

text = p2t.recognize_text_formula(img, return_text=True)

print(text)
```
</details>

<details>
<summary><b>Before</b>: cell <code>3b9f2a13</code></summary>

```python
#fill in the blank version (needs the "Python (ocr)" kernel)
#finds the gray answer boxes, then OCRs each line in pieces split at the boxes and joins them with ___
#only prints the lines that contain a box
import cv2
import numpy as np
import pymupdf
from PIL import Image
from pix2text import Pix2Text

doc = pymupdf.open("fearons_pre_algebra.pdf")
pix = doc[80].get_pixmap(dpi=300)
rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# mid-gray and unsaturated (excludes black text and the blue border)
mask = ((gray > 70) & (gray < 200) & (hsv[..., 1] < 50)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

# size limits assume dpi=300
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
boxes = []
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    fill = cv2.countNonZero(mask[y:y + h, x:x + w]) / (w * h)
    if 40 < w < 160 and 40 < h < 160 and 0.7 < w / h < 1.4 and fill > 0.8:
        boxes.append((x, y, w, h))

p2t = Pix2Text.from_config(total_configs={"languages": ("en",), "text_formula": {"languages": ("en",)}})
mid = rgb.shape[1] // 2
pad = 45

# group boxes that share a line in the same column
lines = {}
for x, y, w, h in sorted(boxes, key=lambda b: b[0]):
    col = 0 if x < mid else 1
    key = next((k for k in lines if k[0] == col and abs(k[1] - y) < h), (col, y))
    lines.setdefault(key, []).append((x, y, w, h))

for (col, _), line_boxes in sorted(lines.items()):
    y0 = min(b[1] for b in line_boxes) - pad
    y1 = max(b[1] + b[3] for b in line_boxes) + pad
    start = 0 if col == 0 else mid
    end = mid if col == 0 else rgb.shape[1]
    parts = []
    for x, y, w, h in line_boxes:
        parts.append(rgb[y0:y1, start:x])
        start = x + w
    parts.append(rgb[y0:y1, start:end])

    texts = []
    for p in parts:
        # skip near-empty slices (just punctuation or whitespace)
        if p.shape[1] < 20 or (p < 128).mean() < 0.002:
            texts.append(" ")
            continue
        texts.append(p2t.recognize_text_formula(Image.fromarray(p), return_text=True).strip())
    print(" ___ ".join(texts))
```
</details>

### 20:55 — Merged blanks into the full-page OCR in one cell (`testing.ipynb`)
- **File:** `educational_prompt_creator/testing.ipynb`, cell `3b9f2a13` (14th cell) rewritten. Cell `86f69327` (13th) is unchanged.
- The cell is now self-contained, so it no longer needs cell 13 to run first. It:
  1. OCRs the whole page with pix2text, keeping each piece's position (`return_text=False`), so the rest of the page keeps full-page quality.
  2. Finds the gray boxes, the same way as before.
  3. Cuts any OCR piece that covers a box at the box (10 px wide of it) and re-reads the parts. Maths parts use `recognize_formula`; text parts use pix2text's single-line recogniser `text_formula_ocr.text_ocr.recognize_only`, because the normal text detector missed short words like "are". Parts get a 30 px white margin first.
  4. Rebuilds the page line by line with `\_\_\_` in place of each box and shows it as Markdown.
- Run standalone in the `ocr` env: all 6 blanks are in place, with the surrounding words and punctuation, and nothing goes to stderr. Not run inside the notebook itself.
- `recognize_only` is a pix2text internal, not public API, so it may change in a future pix2text version.

<details>
<summary><b>Before</b>: cell <code>3b9f2a13</code> (version from 20:45)</summary>

```python
#fill in the blank version (run the pix2text cell above first, it uses p2t, quiet and to_markdown)
#finds the gray answer boxes, then OCRs each line in pieces split at the boxes and joins them with ___
#only shows the lines that contain a box
import cv2
import numpy as np
import pymupdf

doc = pymupdf.open("fearons_pre_algebra.pdf")
pix = doc[80].get_pixmap(dpi=300)
rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# mid-gray and unsaturated (excludes black text and the blue border)
mask = ((gray > 70) & (gray < 200) & (hsv[..., 1] < 50)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

# size limits assume dpi=300
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
boxes = []
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    fill = cv2.countNonZero(mask[y:y + h, x:x + w]) / (w * h)
    if 40 < w < 160 and 40 < h < 160 and 0.7 < w / h < 1.4 and fill > 0.8:
        boxes.append((x, y, w, h))

mid = rgb.shape[1] // 2
pad = 45

# group boxes that share a line in the same column
lines = {}
for x, y, w, h in sorted(boxes, key=lambda b: b[0]):
    col = 0 if x < mid else 1
    key = next((k for k in lines if k[0] == col and abs(k[1] - y) < h), (col, y))
    lines.setdefault(key, []).append((x, y, w, h))

output = []
for (col, _), line_boxes in sorted(lines.items()):
    y0 = min(b[1] for b in line_boxes) - pad
    y1 = max(b[1] + b[3] for b in line_boxes) + pad
    start = 0 if col == 0 else mid
    end = mid if col == 0 else rgb.shape[1]
    parts = []
    for x, y, w, h in line_boxes:
        parts.append(rgb[y0:y1, start:x])
        start = x + w
    parts.append(rgb[y0:y1, start:end])

    texts = []
    for p in parts:
        # skip near-empty slices (just punctuation or whitespace)
        if p.shape[1] < 20 or (p < 128).mean() < 0.002:
            texts.append(" ")
            continue
        with quiet():
            texts.append(p2t.recognize_text_formula(Image.fromarray(p), return_text=True).strip())
    # underscores escaped so markdown shows them instead of treating them as formatting
    output.append(to_markdown(r" \_\_\_ ".join(texts)))

display(Markdown("  \n".join(output)))
```
</details>

### 21:08 — Created `api_practice/.venv` (interview-prep REST API tutorial)
- **Location:** `api_practice/.venv` (new virtual env, Python 3.14.3)
- Installed: fastapi 0.143.0, uvicorn 0.54.0, websockets 17.2, tinydb 4.9.0, httpx 0.28.1, pytest 9.1.1, cryptography 50.0.2, ruff 0.17.0 (plus their dependencies).
- **Before:** the env did not exist. **Undo:** delete the `api_practice/.venv` folder.

### 21:20 — Built the REST API tutorial in `api_practice/` (backend, C++ core, CLI, tests)
- **New files** (none existed before; the folder was empty):
  - `api_practice/app/` — FastAPI app: `main.py` (factory + middleware order), `config.py`, `models.py`, `storage.py` (TinyDB document store), `errors.py` (one error envelope), `security.py` (API keys, 401 vs 403), `ratelimit.py` (token bucket, 429 + Retry-After), `observability.py` (request IDs, timing, JSON logs, metrics), `ws.py` (WebSocket broadcast), `wxcore.py` (ctypes bridge to C++ with Python fallback), `routes.py`.
  - `api_practice/native/` — `wxcore.h`, `wxcore.cpp`, `test_wxcore.cpp`, `CMakeLists.txt`, `build.bat` (MSVC via vswhere), `build.sh` (gcc/clang).
  - `api_practice/cli.py` — tutorial CLI (`steps`, `show`, `check`, `req`, `ws`, `burst`, `seed`).
  - `api_practice/frontend/steps.json` — the 12 tutorial steps and their checks, shared by the CLI and the frontend.
  - `api_practice/tests/` — 35 pytest tests. `api_practice/scripts/make_cert.py` — self-signed cert for HTTPS.
  - `api_practice/requirements.txt`, `pyproject.toml` (pytest + ruff config), `.gitignore`.
- **Generated (git-ignored):** `native/build/` (MSVC build output), `certs/` (self-signed cert), `data/` (TinyDB files from test runs).
- **Before:** none of these existed. **Undo:** delete the files/folders listed above.

## 2026-10-12

### 04:14 — Finished the `api_practice/` tutorial: frontend, docs, CI/CD, Docker; small fixes
- **New files** (none existed before):
  - `api_practice/frontend/index.html`, `app.js`, `styles.css` — browser UI that runs the same checks as the CLI (reads `frontend/steps.json`), plus a request console, a WebSocket live feed and an observations table.
  - `api_practice/README.md`, `TUTORIAL.md`, `STUDY_PLAN.md`, `MOCK_INTERVIEW.md` — quick start, 12-step build guide, 2.5-day schedule, mock interview kit.
  - `api_practice/Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml` (Linux + Windows matrix, container smoke test, gated ECS deploy), `deploy/task-definition.json` (placeholder values), `requirements-dev.txt`.
- **Edits to files created earlier in this session** (no user-authored content was touched):
  - `app/models.py`: added a dewpoint ≤ temperature rule (`model_validator`); `tests/test_api.py`: 2 tests for it; `frontend/steps.json`: a matching step-3 check.
  - `app/main.py`: added `WWW-Authenticate` to CORS `expose_headers`.
  - `cli.py`: defaults to `127.0.0.1` (Windows `localhost` → IPv6 caused 2 s delays); accepts paths without a leading `/` (Git Bash path rewriting); a clearer TLS-untrusted error; skips (not fails) https-only checks on an http URL; seeds realistic dewpoints.
  - `requirements.txt`: now runtime-only (fastapi, uvicorn, websockets, tinydb); httpx, cryptography, pytest and ruff moved to `requirements-dev.txt`.
  - `app/wxcore.py`, `steps.json`, `TUTORIAL.md`, `STUDY_PLAN.md`: corrected the ctypes `argtypes` explanation (floats raise `ArgumentError`; ints give silent garbage), after testing it.
- **Deleted (generated, git-ignored):** `api_practice/data/` and `api_practice/certs/` from test runs. `native/build/` was kept.
- **`/doctor` run:** read-only. The one proposal (auto mode as the default) was declined, so no settings changed.
- **Before:** the new files did not exist. **Undo:** delete them; earlier entries cover the rest of `api_practice/`.

### 04:19 — Added `api_practice/how_to_run.md`
- New file with the three-terminal run commands (API, frontend, CLI) and a link to the README's first-time setup.
- **Before:** the file did not exist. **Undo:** delete `api_practice/how_to_run.md`.
