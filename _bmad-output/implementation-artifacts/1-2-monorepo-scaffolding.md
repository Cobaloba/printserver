# Story 1.2: Monorepo Scaffolding

**Epic:** 1 — Foundation & CI/CD Pipeline
**Story:** 1.2
**Status:** done

---

## User Story

As a developer,
I want the project repository structure initialised with both frontend and backend codebases,
So that development can begin in a clean, reproducible environment.

---

## Acceptance Criteria

**AC1 — SvelteKit scaffolded:**
**Given** an empty GitHub repository
**When** `npm create svelte@latest frontend` is run (SvelteKit minimal, TypeScript, ESLint + Prettier, Vitest)
**Then** `frontend/` exists with `svelte.config.js`, `vite.config.ts`, `tsconfig.json`, and passing `npm run build`

**AC2 — Frontend deps installed:**
**Given** the SvelteKit app is scaffolded
**When** `npm install tailwindcss @tailwindcss/vite svelte-sonner` and `npm install -D vite-plugin-pwa` are run
**Then** all deps appear in `package.json` with correct runtime vs devDependency placement

**AC3 — Backend directory structure created:**
**Given** the frontend is scaffolded
**When** `backend/app/` directory structure is created manually (routers/, services/, models/, data/.gitkeep, main.py, config.py, exceptions.py) with `pyproject.toml` listing FastAPI + uvicorn + python-escpos + pydantic
**Then** `cd backend && python -c "import app.main"` succeeds with no import errors

**AC4 — .env.example committed, .gitignore correct:**
**Given** the repo root
**When** `.env.example` containing `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PORT=9000`, `DATA_DIR=/app/data` is committed and `.gitignore` excludes `.env` and `backend/app/data/*.json`
**Then** `git status` shows neither `.env` nor any `.json` state files as tracked

---

## Dev Context & Implementation Guide

### Hardware Facts from Story 1.1 (carry forward to all stories)

These values were validated on the physical Pi. Use them verbatim in `.env.example`:

```
PRINTER_VENDOR_ID=0x1ba0
PRINTER_PRODUCT_ID=0x220a
PORT=9000
DATA_DIR=/app/data
```

**Critical deviation for Story 2.1:** The Jolimark printer exposes `paper_status()` (not `get_status()`). `paper_status()` returns `2` for paper OK. Document this in the story 2.1 dev notes — the `PrinterInterface.get_status()` method must call `paper_status()` internally on the `EscposPrinter` implementation.

---

### Existing File to Be Aware Of

`printertest.py` exists at the project root — this is legacy brownfield code (working print logic for todo, receipt, goatse). **Do not delete or modify it.** It uses `Serial(devfile='COM9', ...)` which was Windows development code; the production code will use `Usb()` via the PrinterInterface. Story 2.2 will refactor this logic into `backend/app/services/print_service.py`.

---

### Directory Structure to Create

After this story the repo must look like this (partial — only what story 1.2 creates):

```
printserver/                      ← repo root (already exists as project dir)
├── .gitignore
├── .env.example
├── printertest.py                ← existing, do not touch
├── frontend/                     ← created by npm create svelte@latest
│   ├── src/
│   ├── static/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   └── tsconfig.json
└── backend/
    ├── pyproject.toml
    ├── requirements-dev.txt
    ├── .python-version
    └── app/
        ├── __init__.py
        ├── main.py
        ├── config.py
        ├── exceptions.py
        ├── routers/
        │   └── __init__.py
        ├── services/
        │   └── __init__.py
        ├── models/
        │   └── __init__.py
        └── data/
            └── .gitkeep
```

Everything in `backend/app/routers/`, `backend/app/services/`, `backend/app/models/` is empty scaffolding at this stage — just `__init__.py` files. The real implementations come in Epics 1.3–2.x.

---

### Step-by-Step Implementation

#### Step 1: Initialise Git (if not already done)

```bash
git init
git remote add origin <github-remote-url>
```

#### Step 2: Scaffold SvelteKit

Run from the project root:

```bash
npm create svelte@latest frontend
```

At the prompts, select:
- **Template:** SvelteKit minimal (not demo app)
- **Type checking:** TypeScript
- **Linting:** ESLint
- **Formatting:** Prettier
- **Testing:** Vitest

Then:

```bash
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite svelte-sonner
npm install -D vite-plugin-pwa
cd ..
```

**Dependency placement rules (enforced by architecture):**
- `tailwindcss`, `@tailwindcss/vite`, `svelte-sonner` → `dependencies` (runtime)
- `vite-plugin-pwa` → `devDependencies`

Verify in `frontend/package.json` after install.

#### Step 3: Create Backend Structure

Create these files manually from the project root:

```bash
mkdir -p backend/app/routers
mkdir -p backend/app/services
mkdir -p backend/app/models
mkdir -p backend/app/data
mkdir -p backend/tests/services
mkdir -p backend/tests/routers
```

#### Step 4: Create `backend/pyproject.toml`

```toml
[project]
name = "printserver"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.27.0",
    "python-escpos>=3.1",
    "pydantic>=2.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"
```

#### Step 5: Create `backend/requirements-dev.txt`

```
pytest
pytest-asyncio
httpx
```

#### Step 6: Create `backend/.python-version`

```
3.12
```

#### Step 7: Create `backend/app/__init__.py` (empty)

```python
```

Create identical empty `__init__.py` files in:
- `backend/app/routers/__init__.py`
- `backend/app/services/__init__.py`
- `backend/app/models/__init__.py`
- `backend/tests/__init__.py`
- `backend/tests/services/__init__.py`
- `backend/tests/routers/__init__.py`

#### Step 8: Create `backend/app/main.py`

**CRITICAL: This is scaffolding only.** Do NOT implement lifespan, static mount, status cache, or router registration here — those come in Stories 1.3 and 2.4. The only requirement at this stage is that `import app.main` succeeds.

```python
from fastapi import FastAPI

app = FastAPI(title="PrintServer")


@app.get("/health")
def health():
    return {"status": "ok"}
```

#### Step 9: Create `backend/app/config.py`

```python
import os

PRINTER_VENDOR_ID = int(os.getenv("PRINTER_VENDOR_ID", "0x1ba0"), 16)
PRINTER_PRODUCT_ID = int(os.getenv("PRINTER_PRODUCT_ID", "0x220a"), 16)
PORT = int(os.getenv("PORT", "9000"))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
```

#### Step 10: Create `backend/app/exceptions.py`

```python
class PrinterError(Exception):
    pass
```

#### Step 11: Create `backend/app/data/.gitkeep`

Empty file — keeps the `data/` directory tracked in git. `roll_state.json` (created at runtime) is gitignored.

#### Step 12: Create `.env.example` at repo root

```
# Printer Hardware (confirmed via lsusb on Pi)
PRINTER_VENDOR_ID=0x1ba0
PRINTER_PRODUCT_ID=0x220a

# Service Configuration
PORT=9000

# Paths (used in Docker)
DATA_DIR=/app/data
```

#### Step 13: Create `.gitignore` at repo root

```gitignore
# Environment
.env

# Backend state files
backend/app/data/*.json

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/
build/

# Node / Frontend
node_modules/
frontend/build/
frontend/.svelte-kit/
.svelte-kit/

# OS
.DS_Store
Thumbs.db
```

#### Step 14: Verify

From the `backend/` directory:

```bash
cd backend
pip install -e ".[dev]"  # or: pip install fastapi uvicorn pydantic python-escpos
python -c "import app.main; print('OK')"
```

Should print `OK` with no errors.

From the `frontend/` directory:

```bash
cd frontend
npm run build
```

Should complete without errors and produce `frontend/build/`.

---

### Anti-Patterns to Avoid in This Story

| ❌ Don't | ✅ Do instead |
|---|---|
| Use `python:3.12-alpine` in Dockerfile (if started) | Use `python:3.12-slim-bookworm` — Alpine's musl libc breaks python-escpos USB backend |
| Add business logic to `main.py` | Keep `main.py` minimal; full wiring in Stories 1.3 and 2.4 |
| Create `tailwind.config.js` | Tailwind v4 uses `@tailwindcss/vite` plugin only — no config file |
| Put `vite-plugin-pwa` in `dependencies` | It's a devDependency (build-time only) |
| Delete or modify `printertest.py` | Legacy brownfield — leave it alone until Story 2.2 |
| Create `requirements.txt` | Use `pyproject.toml` as the source of truth for deps |
| Use `adapter-node` in `svelte.config.js` | Use `adapter-static` with `fallback: 'index.html'` — required for SPA routing |

---

### Critical Architecture Rules (carry forward to all stories)

- **`escpos` import boundary:** `from escpos.printer import Usb` must only ever appear in `backend/app/services/printer.py` (Story 2.1). Never import it anywhere else.
- **JSON field naming:** All JSON fields are `snake_case` throughout — `paper_near_end`, `bytes_printed`, `roll_width_mm`. No camelCase layer.
- **Router registration order:** In `main.py` (Story 2.4), API routers (`/api/v1/`) MUST be registered BEFORE the `StaticFiles` mount — otherwise the SPA catch-all intercepts API calls.
- **Atomic JSON writes:** `roll_state.json` must be written via temp file + `os.replace()` rename — never a direct write.

---

## Definition of Done

- [ ] `frontend/` directory exists with SvelteKit 2 + Svelte 5 scaffold
- [ ] `frontend/package.json` shows `tailwindcss`, `@tailwindcss/vite`, `svelte-sonner` in `dependencies` and `vite-plugin-pwa` in `devDependencies`
- [ ] `cd frontend && npm run build` completes without errors
- [ ] `backend/app/` directory structure exists with all `__init__.py` files
- [ ] `backend/pyproject.toml` exists with FastAPI, uvicorn, python-escpos, pydantic dependencies
- [ ] `backend/app/main.py` exists (minimal FastAPI app)
- [ ] `backend/app/config.py` exists with env var reads
- [ ] `backend/app/exceptions.py` exists with `PrinterError`
- [ ] `backend/app/data/.gitkeep` exists
- [ ] `cd backend && python -c "import app.main"` succeeds with no errors
- [ ] `.env.example` at repo root contains all 4 required vars with correct Jolimark values
- [ ] `.gitignore` excludes `.env` and `backend/app/data/*.json`
- [ ] `git status` shows `.env` is NOT tracked (if `.env` was created locally for testing)
- [ ] No `__pycache__` or `node_modules` directories committed

---

## Dev Notes

```
Implemented: 2026-05-10

PACKAGE_JSON_TYPE: "type": "module" required in frontend/package.json — SvelteKit
  is ESM-only and vite.config.ts fails to load without it.

VITE_PLUGIN_SVELTE_VERSION: @sveltejs/vite-plugin-svelte@^4 only supports Vite 5.
  Must use ^5.0.0 for Vite 6 compatibility. package.json has ^5.0.0.

SVELTE_KIT_TSCONFIG: tsconfig.json extends .svelte-kit/tsconfig.json which is
  generated at build time by svelte-kit sync. The "Cannot find base config file"
  warning on first build is expected and harmless — it resolves on subsequent builds.

BUILD_VERIFIED: cd frontend && npm run build → success, build/ produced.
IMPORT_VERIFIED: cd backend && python -c "import app.main" → OK.
GITIGNORE_VERIFIED: .env and backend/app/data/*.json excluded.
COMMIT: 751c299 feat: story 1.2 — monorepo scaffolding
```
