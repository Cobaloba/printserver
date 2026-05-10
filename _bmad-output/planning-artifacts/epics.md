---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
---

# PrintServer - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for PrintServer, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: User can submit a to-do list (title + one or more items) for printing
FR2: User can submit a fake receipt (store name, optional address/phone, line items with prices, optional tax) for printing
FR3: User can submit free text for printing with a choice of font size
FR4: User can submit a URL for QR code generation and printing
FR5: User can trigger goatse ASCII art printing
FR6: System executes each print type as a discrete, independent operation
FR7: System formats each print type according to its defined layout (line widths, alignment, headers, totals)
FR8: System reports print job outcome — success or a specific failure reason — to the caller
FR9: System detects whether the printer is reachable and online
FR10: System detects paper-near-end and paper-out conditions where hardware supports it
FR11: User can view current printer status (online / offline / paper warning) before submitting a print job
FR12: System periodically refreshes printer status and reflects changes in the interface without user action
FR13: User can log when a new paper roll has been loaded
FR14: User can specify roll dimensions (width and diameter) when logging a new roll
FR15: System pre-fills the last used roll dimensions when the user opens the new roll form
FR16: System tracks cumulative paper usage since the last roll change
FR17: System estimates the percentage of paper remaining on the current roll
FR18: User can view estimated paper remaining from the home screen without navigating to settings
FR19: User can navigate to any available print type from a single home screen
FR20: Each print type presents a tailored input interface suited to its content structure
FR21: User receives immediate visual confirmation (success or failure) after every print submission
FR22: User can access the admin section from the main interface
FR23: User can install the application to their mobile device home screen as a standalone PWA
FR24: Application displays its interface and communicates server status even when the Pi is unreachable
FR25: User can see printer status and estimated paper level on the home screen without navigating away
FR26: System automatically restarts the print service after a crash or unhandled error without manual intervention
FR27: System exposes a health check endpoint for container orchestration and uptime monitoring
FR28: System handles printer disconnection, power loss, or paper errors gracefully — returns a clear error without crashing
FR29: System persists till roll tracking state across container restarts and image updates
FR30: System maintains a stable, consistent path to the printer device across host reboots
FR31: System exposes all print operations as versioned REST API endpoints callable by any HTTP client on the network
FR32: System validates all API request inputs and returns structured, human-readable error responses for invalid requests
FR33: System exposes printer status and roll state via a dedicated API endpoint
FR34: System returns a health status response suitable for automated monitoring tools
FR35: Developer can add a new print type by implementing a single module function and registering a single API route
FR36: System automatically tests, builds, and deploys changes to production on merge to the main branch
FR37: System runs automated tests against all print type logic before building a deployment image
FR38: Developer can trigger a manual redeploy from any machine with SSH access using a single command

### NonFunctional Requirements

NFR1: Print job API requests complete end-to-end within 3 seconds under normal operating conditions
NFR2: Printer status API responses return within 200ms
NFR3: Frontend initial load completes within 2 seconds on the local WiFi network
NFR4: Health check endpoint responds within 100ms
NFR5: Frontend renders status poll updates and print submission responses within 500ms on devices with 2GB+ RAM
NFR6: Service recovers automatically from application crashes within 30 seconds without manual intervention
NFR7: Service starts automatically on Pi reboot via Docker restart policy
NFR8: Printer disconnection or power loss does not crash or hang the service — returns a clear error and remains available
NFR9: Till roll tracking state survives container restarts and image updates without data loss
NFR10: Printer USB device path is stable across Pi reboots
NFR11: Adding a new print type requires changes to no more than 2 files (print module + API routes)
NFR12: Project builds successfully from a clean clone with a single command
NFR13: All print type logic is unit-testable without a physical printer connected
NFR14: Full deployment cycle (code push → live production) completes within 10 minutes
NFR15: The API does not log or persist user-submitted print content beyond the current request
NFR16: Service binds to the local network interface only — no public internet exposure by default
NFR17: No credentials, tokens, or secrets stored in the Docker image or source code — environment variables or Docker secrets used instead
NFR18: Docker image runs on linux/arm64 (Raspberry Pi 4 Model B)
NFR19: Frontend functions correctly on mobile Chrome (Android) and mobile Safari (iOS) at minimum 375px viewport
NFR20: Service operates on a port that does not conflict with PiHole (80/443) or Octoprint (5000)
NFR21: All interactive elements have a minimum touch target size of 44×44px
NFR22: Text and UI elements meet WCAG 2.1 AA contrast ratio requirements in dark mode
NFR23: All form inputs have associated labels accessible to screen readers

### Additional Requirements

- **Pre-dev spike**: Hardware validation — connect printer to Pi via USB, run `lsusb` to get vendor/product ID, confirm `python-escpos Usb()` connects, test `get_status()` for paper sensor capability, validate udev symlink `/dev/receipt-printer` survives reboot
- **Pre-dev spike**: PiHole port check — SSH into Pi, run `docker ps` / `netstat -tlnp`, confirm port 9000 is free
- **PrinterInterface ABC**: `EscposPrinter` + `MockPrinter` implementations required before any other backend work; `escpos` imported only in `printer.py`
- **Status cache**: Background `threading.Thread` started via FastAPI `lifespan`; initialises to `printer_online: false`; polls every 5s; must not crash if printer unavailable at startup
- **Atomic state writes**: `roll_state.json` written via temp file + atomic rename (never direct write)
- **udev rule**: Pi host requires udev rule assigning stable symlink `/dev/receipt-printer` keyed on USB vendor/product ID
- **Multi-stage Dockerfile**: Stage 1 Node build (`npm run build`) → Stage 2 Python runtime; copies `frontend/build/` to `app/static/`; installs `curl` for HEALTHCHECK
- **Router registration order**: API routers (`/api/v1/`) must be registered in `main.py` BEFORE `StaticFiles` mount
- **GitHub Actions CI/CD**: pytest → vitest → `docker/build-push-action` (`linux/arm64`) → push to GHCR on merge to main
- **Watchtower**: Deployed on Pi to auto-pull new GHCR images and restart container
- **SvelteKit adapter-static**: `fallback: 'index.html'` for SPA routing
- **Frontend deps**: `svelte-sonner` (runtime) + `vite-plugin-pwa` (devDep) must be in `package.json`
- **Makefile**: `make test`, `make build`, `make redeploy` targets
- **`.env` file**: `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PORT=9000`, `DATA_DIR=/app/data`
- **docker-compose.yml**: `restart: unless-stopped`, `devices: ["/dev/receipt-printer:/dev/receipt-printer"]`, `volumes: ["./data:/app/data"]`, `env_file: .env`

### UX Design Requirements

No UX Design document exists. UX requirements are captured in the PRD (API & Frontend Specification section) and Architecture (Frontend Architecture decisions section).

Key UX implementation notes derived from PRD/Architecture:
- Dark mode default; Tailwind v4 `@theme {}` tokens in `app.css`
- `svelte-sonner` for toast notifications (success green / failure red)
- `StatusDot.svelte`: pulsing green (online) / flat grey (offline) / amber (paper near end)
- `RollGauge.svelte`: arc gauge showing `estimated_remaining_pct`
- `PrintCard.svelte`: home screen card grid with icon, name, description
- `PrintButton.svelte`: full-width, accepts `loading` prop, shows spinner when loading
- Minimum 44×44px touch targets; 375px minimum viewport
- PWA: `manifest.webmanifest` in `static/`, `vite-plugin-pwa` service worker caching app shell

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR1 | Epic 2+3 | Todo print — backend + UI |
| FR2 | Epic 2+3 | Receipt print — backend + UI |
| FR3 | Epic 2+3 | Free text print — backend + UI |
| FR4 | Epic 2+3 | QR code print — backend + UI |
| FR5 | Epic 2+3 | Goatse print — backend + UI |
| FR6 | Epic 2 | Discrete operations via service layer |
| FR7 | Epic 2 | Formatting in `print_service.py` |
| FR8 | Epic 2+3 | Outcome reporting — API response + toast |
| FR9 | Epic 2 | Printer online detection in `status_cache` |
| FR10 | Epic 2 | Paper sensor in `get_status()` |
| FR11 | Epic 3 | Status dot in `+layout.svelte` |
| FR12 | Epic 3 | 5s polling via `polling.ts` |
| FR13–FR15 | Epic 2+3 | Roll logging — backend tracker + admin UI |
| FR16–FR18 | Epic 2+3 | Roll estimation — tracker + gauge display |
| FR19 | Epic 3 | Card grid home screen |
| FR20 | Epic 3 | Per-type input pages |
| FR21 | Epic 3 | svelte-sonner toasts |
| FR22 | Epic 3 | Admin route |
| FR23 | Epic 3 | PWA manifest + installability |
| FR24 | Epic 3 | Service worker offline shell |
| FR25 | Epic 3 | Status + gauge in layout |
| FR26 | Epic 1 | `restart: unless-stopped` |
| FR27 | Epic 1 | `health.py` route |
| FR28 | Epic 2 | `PrinterError` → 503 chain |
| FR29 | Epic 2 | Volume mount + atomic write |
| FR30 | Epic 1 | udev symlink spike |
| FR31 | Epic 2 | `/api/v1/` versioned endpoints |
| FR32 | Epic 2 | Pydantic v2 validation |
| FR33 | Epic 2 | `/api/v1/status` endpoint |
| FR34 | Epic 1 | `/health` endpoint |
| FR35 | Epic 2 | 2-file pattern via PrinterInterface + service module |
| FR36 | Epic 1 | GitHub Actions workflow |
| FR37 | Epic 1+2 | CI runs tests; Epic 2 writes the tests |
| FR38 | Epic 1 | `make redeploy` + SSH alias |

## Epic List

### Epic 1: Foundation & CI/CD Pipeline
The project skeleton exists on the Pi, deploys automatically, and every push to main triggers a working test → build → deploy cycle. The developer can make a change and have it live without touching the Pi.
**FRs covered:** FR26, FR27, FR30, FR34, FR36, FR37, FR38

### Epic 2: Complete Backend API
The entire print server API is functional and fully tested — all 5 print types, printer status, till roll tracking, admin endpoints, and health check. A developer can print anything via `curl`.
**FRs covered:** FR1–FR10, FR13–FR18, FR28–FR29, FR31–FR35

### Epic 3: Frontend PWA
The complete mobile-first progressive web app — installable on the phone home screen, all print type UIs, live printer status, till roll gauge, admin panel, and graceful offline handling.
**FRs covered:** FR11–FR12, FR19–FR25 + frontend sides of FR1–FR5, FR13–FR18

## Epic 1: Foundation & CI/CD Pipeline

The project skeleton exists on the Pi, deploys automatically, and every push to main triggers a working test → build → deploy cycle. The developer can make a change and have it live without touching the Pi.

### Story 1.1: Hardware & Port Validation Spikes

As a developer,
I want to validate that the printer connects via USB to the Pi and that port 9000 is available,
So that all architecture decisions are confirmed before any code is written.

**Acceptance Criteria:**

**Given** the printer is connected to the Pi via USB
**When** `lsusb` is run on the Pi
**Then** the printer vendor ID and product ID are identified and documented in `.env.example`

**Given** the vendor ID and product ID from lsusb
**When** `python -c "from escpos.printer import Usb; p = Usb(VENDOR, PRODUCT); print('connected')"` is run
**Then** the printer connects without error

**Given** a udev rule created at `/etc/udev/rules.d/99-receipt-printer.rules` using the printer's vendor/product IDs
**When** the Pi is rebooted with the printer connected
**Then** `/dev/receipt-printer` symlink exists and points to the correct device

**Given** the Pi is running PiHole and Octoprint
**When** `docker ps` and `netstat -tlnp` are run
**Then** port 9000 is confirmed free and `.env.example` `PORT=9000` is verified correct

### Story 1.2: Monorepo Scaffolding

As a developer,
I want the project repository structure initialised with both frontend and backend codebases,
So that development can begin in a clean, reproducible environment.

**Acceptance Criteria:**

**Given** an empty GitHub repository
**When** `npm create svelte@latest frontend` is run (SvelteKit minimal, TypeScript, ESLint + Prettier, Vitest)
**Then** `frontend/` exists with `svelte.config.js`, `vite.config.ts`, `tsconfig.json`, and passing `npm run build`

**Given** the SvelteKit app is scaffolded
**When** `npm install tailwindcss @tailwindcss/vite svelte-sonner` and `npm install -D vite-plugin-pwa` are run
**Then** all deps appear in `package.json` with correct runtime vs devDependency placement

**Given** the frontend is scaffolded
**When** `backend/app/` directory structure is created manually (routers/, services/, models/, data/.gitkeep, main.py, config.py, exceptions.py) with `pyproject.toml` listing FastAPI + uvicorn + python-escpos + pydantic
**Then** `cd backend && python -c "import app.main"` succeeds with no import errors

**Given** the repo root
**When** `.env.example` containing `PRINTER_VENDOR_ID`, `PRINTER_PRODUCT_ID`, `PORT=9000`, `DATA_DIR=/app/data` is committed and `.gitignore` excludes `.env` and `backend/app/data/*.json`
**Then** `git status` shows neither `.env` nor any `.json` state files as tracked

### Story 1.3: Multi-stage Dockerfile + Docker Compose

As a developer,
I want the project containerised with a working Docker setup on the Pi,
So that the app runs reliably as a managed service alongside PiHole and Octoprint.

**Acceptance Criteria:**

**Given** the monorepo with a multi-stage Dockerfile (Stage 1: `node:20-alpine` builds frontend; Stage 2: `python:3.12-slim-bookworm` runs API + copies `frontend/build/` to `app/static/`)
**When** `docker build --platform linux/arm64 -t printserver .` completes
**Then** the image exists, contains `app/static/index.html`, and the `HEALTHCHECK` is configured with `curl -f http://localhost:9000/health`

**Given** the Docker image includes `RUN apt-get install -y --no-install-recommends curl`
**When** `docker run --env-file .env -p 9000:9000 printserver`
**Then** `curl http://localhost:9000/health` returns `{"status": "ok"}` with HTTP 200

**Given** `docker-compose.yml` with `restart: unless-stopped`, `devices: ["/dev/receipt-printer:/dev/receipt-printer"]`, `volumes: ["./data:/app/data"]`, `env_file: .env`
**When** `docker compose up -d` is run on the Pi
**Then** the container starts, health check passes, and `./data/` is mounted correctly

**Given** the running container
**When** `docker compose down` followed by `docker compose up -d`
**Then** any files previously written to `./data/` are still present after restart

### Story 1.4: GitHub Actions CI/CD Pipeline

As a developer,
I want every merge to main to automatically test, build, and push a new Docker image to GHCR,
So that code changes reach production without any manual steps on the Pi.

**Acceptance Criteria:**

**Given** `.github/workflows/ci.yml` and a push to `main`
**When** the workflow runs
**Then** `pytest backend/` and `cd frontend && npm run test -- --run` both execute (passing with empty/stub test files)
**And** `docker/build-push-action` builds `linux/arm64` and pushes `ghcr.io/{user}/printserver:latest` to GHCR on test success

**Given** an intentionally failing pytest test
**When** the push triggers the workflow
**Then** the build stage does not execute and no new image is pushed to GHCR

**Given** the CI workflow
**When** reviewed
**Then** Docker layer caching is configured (`cache-from: type=gha`, `cache-to: type=gha,mode=max`) to keep subsequent builds under 10 minutes

### Story 1.5: Watchtower Auto-Deploy + Makefile

As a developer,
I want Watchtower to automatically deploy new images on the Pi and a Makefile to simplify common commands,
So that `git push` → merge results in automatic production deployment within minutes.

**Acceptance Criteria:**

**Given** Watchtower configured in `docker-compose.yml` (or standalone) polling GHCR every 5 minutes
**When** a new `latest` image digest is pushed to GHCR after a successful CI run
**Then** Watchtower pulls the new image and restarts the `printserver` container on the Pi within 5 minutes

**Given** the `Makefile` at the repo root
**When** `make test` is run
**Then** both `pytest backend/` and `cd frontend && npm run test -- --run` execute

**Given** the `Makefile`
**When** `make redeploy` is run from any machine with SSH access to the Pi
**Then** the Pi runs `git pull && docker compose up --build -d` and the container is rebuilt

**Given** `alias redeploy='cd ~/printserver && git pull && docker compose up --build -d'` in `~/.bashrc` on the Pi
**When** `ssh pi 'redeploy'` is run
**Then** the container rebuilds and restarts without error

## Epic 2: Complete Backend API

The entire print server API is functional and fully tested — all 5 print types, printer status, till roll tracking, admin endpoints, and health check. A developer can print anything via `curl`.

### Story 2.1: PrinterInterface + EscposPrinter + MockPrinter

As a developer,
I want a clean printer abstraction layer with a real and mock implementation,
So that all print logic is testable without hardware and the escpos driver is isolated to one file.

**Acceptance Criteria:**

**Given** `backend/app/services/printer.py`
**When** reviewed
**Then** `PrinterInterface` ABC defines abstract methods `print_todo`, `print_receipt`, `print_free_text`, `print_qr`, `print_goatse`, `get_status`, `get_bytes_for_job`; `EscposPrinter` implements all methods using `python-escpos Usb()`; `MockPrinter` implements all methods recording calls without hardware interaction

**Given** `EscposPrinter` initialised with vendor/product IDs from config
**When** the physical printer is connected to the Pi via `/dev/receipt-printer`
**Then** the connection succeeds without error

**Given** `MockPrinter` and a call to any print method
**When** `mock.get_bytes_for_job()` is called after the print
**Then** a positive integer is returned representing simulated bytes sent

**Given** `backend/app/exceptions.py`
**When** reviewed
**Then** `PrinterError(Exception)` is defined; given `EscposPrinter` encounters a USB error, when a print method is called, then `PrinterError` is raised with a descriptive message

**Given** `backend/tests/conftest.py`
**When** pytest runs
**Then** a `mock_printer` fixture provides a fresh `MockPrinter` instance and a `tmp_roll_state` fixture provides a temporary JSON file path via `tmp_path`

### Story 2.2: Print Service — Todo, Receipt, Goatse

As a developer,
I want the three original print types implemented in the print service module, refactored from printertest.py,
So that existing proven print logic is available through the clean architecture.

**Acceptance Criteria:**

**Given** `backend/app/services/print_service.py`
**When** reviewed
**Then** `print_todo(printer, title, items)`, `print_receipt(printer, store, items, address, phone, tax_pct)`, and `print_goatse(printer)` exist, each accepting `PrinterInterface` as first argument and containing no `escpos` imports

**Given** `MockPrinter` and `print_todo(printer, "TO DO", ["Buy milk", "Call Bob"])`
**When** called
**Then** `mock.get_bytes_for_job()` returns a positive integer and no exception is raised

**Given** `MockPrinter` and `print_receipt(printer, "Harrods", [("Gold watch", 340.00)], None, None, 20)`
**When** called
**Then** the mock records calls and no exception is raised; the function does not catch `PrinterError` internally

**Given** `pytest backend/tests/services/test_print_service.py` using `mock_printer` fixture
**When** run
**Then** all tests pass; `PrinterError` propagation is verified by configuring `MockPrinter` to raise and asserting it re-raises

### Story 2.3: Print Service — Free Text, QR Code

As a developer,
I want free text and QR code print types added to the print service,
So that all 5 V1 print types are available from the service layer.

**Acceptance Criteria:**

**Given** `print_service.py` after this story
**When** reviewed
**Then** `print_free_text(printer, text, font_size)` and `print_qr(printer, url)` exist

**Given** `font_size` values `"small"`, `"medium"`, `"large"`
**When** `print_free_text` is called with each
**Then** `MockPrinter` records different height/width multiplier calls for each size

**Given** `print_qr(printer, "https://example.com")`
**When** `MockPrinter`'s `qr` method raises (simulating unsupported native QR command)
**Then** `print_qr` falls back to rendering the QR code as a Pillow raster image and calls the printer's image method instead

**Given** all 5 print service functions
**When** `pytest backend/tests/services/test_print_service.py` runs
**Then** all tests pass with `MockPrinter`

### Story 2.4: FastAPI Application — Routers, Models, Static Mount

As a developer,
I want the full FastAPI application wired together with all API routes, Pydantic validation, and static file serving,
So that every endpoint is reachable, validates inputs, and the frontend SPA is served from the same origin.

**Acceptance Criteria:**

**Given** `backend/app/main.py`
**When** reviewed
**Then** all API routers (`/api/v1/print/*`, `/api/v1/status`, `/api/v1/admin/*`, `/health`) are registered **before** the `StaticFiles` mount at `/`

**Given** `POST /api/v1/print/todo` with `{"title": "My List", "items": ["item1"]}`
**When** processed with `MockPrinter` injected
**Then** `{"success": true}` is returned with HTTP 200

**Given** `POST /api/v1/print/todo` with `{"items": []}` (empty items)
**When** processed
**Then** HTTP 422 is returned with a validation error detail (no print call made)

**Given** a `PrinterError` raised by the injected `MockPrinter`
**When** any print endpoint handles it
**Then** HTTP 503 is returned with `{"detail": "<message>"}` — not 500

**Given** `GET /health`
**When** called
**Then** `{"status": "ok"}` is returned with HTTP 200

**Given** `FastAPI TestClient` in `backend/tests/routers/test_print_routes.py`
**When** all 5 print endpoints are tested with valid inputs, empty/invalid inputs, and `PrinterError` conditions
**Then** all tests pass

### Story 2.5: Status Cache — Background Polling Thread

As a developer,
I want a background thread that polls the printer every 5 seconds and caches the result,
So that status requests return instantly without blocking on hardware I/O.

**Acceptance Criteria:**

**Given** `backend/app/services/status_cache.py`
**When** reviewed
**Then** `StatusCache` has `start(printer)` launching a daemon thread, `get_cached()` returning the last known status dict, and initial state `{"printer_online": false, "paper_near_end": false, "paper_out": false, "estimated_remaining_pct": 0}`

**Given** `StatusCache` started with a `MockPrinter` configured to return `printer_online: true`
**When** 6 seconds elapse
**Then** `get_cached()["printer_online"]` is `true`

**Given** `MockPrinter` raises on `get_status()` (simulating unavailable printer at startup)
**When** `StatusCache.start()` is called
**Then** no exception propagates to the caller and `get_cached()` returns the initial offline state

**Given** `GET /api/v1/status` while the background thread is running
**When** response time is measured
**Then** it is under 200ms (reading from cache, not polling hardware)

**Given** `status_cache` wired into `main.py` lifespan
**When** the container starts
**Then** the background polling thread begins automatically with no manual invocation required

### Story 2.6: Till Roll Tracker

As a developer,
I want a roll tracker service that persists paper usage and estimates remaining paper,
So that the API can report paper level and the state survives container restarts.

**Acceptance Criteria:**

**Given** `backend/app/services/roll_tracker.py`
**When** reviewed
**Then** `RollTracker` has `load(path)`, `save()` (atomic rename), `add_bytes(n)`, `reset(width_mm, diameter_mm)`, and `estimate_remaining() -> int` (0–100)

**Given** `roll_state.json` does not exist
**When** `RollTracker.load(path)` is called
**Then** a default state file is created: `bytes_printed=0`, `roll_width_mm=57`, `roll_diameter_mm=40`, `last_reset=<now ISO>`, `hardware_paper_sensor_available=null`

**Given** `add_bytes(500)` is called
**When** `roll_state.json` is read directly from disk
**Then** `bytes_printed` equals 500, confirming the atomic write completed

**Given** the volume is mounted and a previous state was saved
**When** a new `RollTracker.load()` is called (simulating container restart)
**Then** the previously saved `bytes_printed` value is recovered intact

**Given** `pytest backend/tests/services/test_roll_tracker.py` using `tmp_path`
**When** all tests run
**Then** all pass without accessing real filesystem paths outside `tmp_path`

### Story 2.7: Admin Endpoints + Full Test Suite

As a developer,
I want the admin endpoints for roll management and a complete passing test suite,
So that till roll operations are API-accessible and every backend component has verified coverage.

**Acceptance Criteria:**

**Given** `POST /api/v1/admin/roll` with `{"width_mm": 57, "diameter_mm": 40}`
**When** processed
**Then** `RollTracker.reset()` is called, state is updated, and `{"success": true}` is returned

**Given** `GET /api/v1/admin/roll`
**When** called
**Then** a JSON object with `bytes_printed`, `roll_width_mm`, `roll_diameter_mm`, `last_reset`, and `estimated_remaining_pct` is returned

**Given** `POST /api/v1/admin/roll` with missing required fields
**When** processed
**Then** HTTP 422 is returned

**Given** `pytest backend/` run across the full test suite
**When** all tests execute
**Then** all pass; every test touching print operations uses `MockPrinter`; no test imports `escpos` directly

**Given** `backend/tests/routers/test_admin_routes.py`
**When** run
**Then** both admin endpoints are covered with valid inputs, missing fields, and a reset-then-verify flow

## Epic 3: Frontend PWA

The complete mobile-first progressive web app — installable on the phone home screen, all print type UIs, live printer status, till roll gauge, admin panel, and graceful offline handling.

### Story 3.1: SvelteKit Foundation

As a developer,
I want the SvelteKit frontend configured with Tailwind v4, PWA tooling, and the Vite API proxy,
So that the development environment matches production configuration exactly.

**Acceptance Criteria:**

**Given** `frontend/svelte.config.js`
**When** reviewed
**Then** `@sveltejs/adapter-static` is configured with `fallback: 'index.html'` and `ssr: false`

**Given** `frontend/vite.config.ts`
**When** reviewed
**Then** it includes `tailwindcss()` from `@tailwindcss/vite`, `sveltekit()`, `VitePWA({...})`, and a server proxy rule forwarding `/api` to `http://localhost:9000`

**Given** `frontend/src/app.css`
**When** reviewed
**Then** it contains `@import "tailwindcss";` and a `@theme {}` block defining at minimum dark background, card surface, and accent colour tokens

**Given** `cd frontend && npm run build`
**When** executed
**Then** `frontend/build/` is produced without errors and `frontend/build/index.html` exists

**Given** `cd frontend && npm run dev`
**When** the dev server starts on port 5173
**Then** the page loads without console errors and requests to `/api/*` are proxied to port 9000

### Story 3.2: API Client, Stores, and Polling

As a developer,
I want typed API wrappers, Svelte stores for shared state, and a polling loop,
So that all components consume the API consistently and printer status updates reactively.

**Acceptance Criteria:**

**Given** `frontend/src/lib/types.ts`
**When** reviewed
**Then** `PrinterStatus` and `RollState` TypeScript interfaces are defined with `snake_case` field names matching the API schemas exactly (e.g. `printer_online`, `estimated_remaining_pct`)

**Given** `frontend/src/lib/api.ts`
**When** reviewed
**Then** `printTodo`, `printReceipt`, `printFreeText`, `printQr`, `printGoatse`, `getStatus`, `getAdminRoll`, `postAdminRoll` are all exported; each uses `snake_case` in request bodies; each throws `Error(err.detail)` on non-2xx responses

**Given** `frontend/src/lib/stores.ts`
**When** reviewed
**Then** `printerStatus` (writable `PrinterStatus`) and `rollState` (writable `RollState | null`) are exported with sensible defaults

**Given** `frontend/src/lib/polling.ts`
**When** reviewed
**Then** `startPolling()` calls `getStatus()` every 5 seconds and calls `printerStatus.set(result)`; `stopPolling()` cancels the interval; errors from `getStatus()` update `printerStatus` to offline state rather than crashing

**Given** a Vitest test mocking `fetch` to return a 503 with `{"detail": "Printer offline"}`
**When** any `api.ts` print function is called
**Then** it throws `Error("Printer offline")`

### Story 3.3: Shared Components

As a developer,
I want the four shared UI components built and visually verified,
So that every print page and the layout can use them without duplicating code.

**Acceptance Criteria:**

**Given** `StatusDot.svelte` accepting `status: PrinterStatus`
**When** `printer_online=true`, `printer_online=false`, and `paper_near_end=true` are each rendered
**Then** a pulsing green dot, flat grey dot, and amber dot are shown respectively; each has a minimum 8×8px visible size

**Given** `RollGauge.svelte` accepting `pct: number` (0–100)
**When** rendered at 0%, 50%, and 100%
**Then** the SVG arc fills proportionally; when `pct < 15`, the arc renders in a warning colour (red or amber)

**Given** `PrintButton.svelte` accepting `loading: boolean`
**When** `loading=true`
**Then** a spinner is shown and the button is `disabled`; when `loading=false`, the button shows its slot content and is interactive

**Given** `PrintCard.svelte` accepting `title`, `description`, and `href`
**When** rendered and tapped
**Then** navigation to `href` occurs; the card has a minimum bounding box of 44×44px

### Story 3.4: Root Layout + Home Screen

As a developer,
I want the root layout to show printer status and roll level at all times, and the home screen to list all print types as cards,
So that users can see printer state before choosing what to print.

**Acceptance Criteria:**

**Given** `frontend/src/routes/+layout.svelte`
**When** reviewed
**Then** it calls `startPolling()` in `onMount` and `stopPolling()` in `onDestroy`; renders `<StatusDot />` bound to `$printerStatus`; renders `<RollGauge pct={$printerStatus.estimated_remaining_pct} />`; renders `<Toaster />` from svelte-sonner

**Given** `frontend/src/routes/+page.svelte` (home screen)
**When** rendered
**Then** it shows 6 `PrintCard` components — Free Text, QR Code, Todo, Receipt, Goatse, Admin — each linking to the correct route

**Given** a 375px viewport in dark mode
**When** the home screen renders
**Then** all 6 cards are visible without horizontal scrolling; the status bar with dot and gauge is visible at the top

**Given** the printer transitions to offline (polling returns `printer_online=false`)
**When** the next poll fires
**Then** the `StatusDot` updates to grey within 6 seconds

### Story 3.5: Todo and Free Text Print Pages

As a developer,
I want the todo list and free text print UIs implemented end-to-end,
So that users can make their first successful phone-to-paper prints.

**Acceptance Criteria:**

**Given** `frontend/src/routes/todo/+page.svelte`
**When** rendered
**Then** it shows a text input, "Add item" button, a list of added items (each with a remove button), and a full-width `<PrintButton>`

**Given** 2 items added and Print tapped
**When** `api.printTodo(title, items)` succeeds
**Then** `toast.success('Sent to printer ✓')` fires; `loading` resets to `false` in a `finally` block

**Given** Print tapped when the printer is offline (API returns 503)
**When** the error is caught
**Then** `toast.error('Printer offline')` (or the returned `detail`) fires within 3 seconds

**Given** `frontend/src/routes/free-text/+page.svelte`
**When** rendered
**Then** it shows a `<textarea>`, a font size selector with options Small / Medium / Large, and a `<PrintButton>`; on print success/failure, the appropriate toast fires

### Story 3.6: Receipt Print Page

As a developer,
I want the fake receipt print UI with its mini-ledger builder implemented,
So that users can construct a receipt line by line and print it.

**Acceptance Criteria:**

**Given** `frontend/src/routes/receipt/+page.svelte`
**When** rendered
**Then** it shows: store name input; optional address and phone inputs; a row builder (item name + price, "Add row" button); a live-updating running total; a tax percentage input; and a `<PrintButton>`

**Given** 2 items added (Coffee £2.50, Cake £3.00) with 20% tax
**When** the totals area is inspected before printing
**Then** subtotal shows £5.50, tax shows £1.10, and total shows £6.60, all updating reactively

**Given** no items added
**When** Print is tapped
**Then** the button is disabled or a client-side validation message appears — no API call is made

**Given** a completed receipt form
**When** Print is tapped and succeeds
**Then** `api.printReceipt({store, address, phone, items, tax_pct})` is called with `snake_case` field names and the success toast fires

### Story 3.7: QR Code + Goatse Pages

As a developer,
I want the QR code and Goatse print pages implemented,
So that users can print QR codes from URLs and trigger the goatse print.

**Acceptance Criteria:**

**Given** `frontend/src/routes/qr-code/+page.svelte`
**When** a valid URL is typed
**Then** a live QR code preview renders below the input using a client-side QR library; when the input is cleared, the preview disappears

**Given** an invalid URL (missing `https://` prefix)
**When** Print is tapped
**Then** client-side validation prevents submission and shows an inline error message; no API call is made

**Given** a valid URL and Print tapped
**When** `api.printQr(url)` completes
**Then** the appropriate success or failure toast fires and `loading` resets

**Given** `frontend/src/routes/goatse/+page.svelte`
**When** rendered
**Then** it shows a single full-width `<PrintButton>` with no other input; on tap, `api.printGoatse()` is called and the appropriate toast fires

### Story 3.8: Admin Page — Till Roll Management

As a developer,
I want the admin page to display current roll state and let users log a new roll,
So that till roll tracking can be reset and monitored without SSH.

**Acceptance Criteria:**

**Given** `frontend/src/routes/admin/+page.svelte`
**When** loaded
**Then** `GET /api/v1/admin/roll` is called and the response populates current `bytes_printed`, `estimated_remaining_pct`, and `last_reset`; the New Roll form pre-fills `width_mm` and `diameter_mm` from the retrieved values

**Given** the user changes `diameter_mm` to 35 and taps Save
**When** `api.postAdminRoll({width_mm: 57, diameter_mm: 35})` succeeds
**Then** `toast.success('Roll updated')` fires and the displayed roll state refreshes

**Given** the Save button is tapped and the API returns an error
**When** the error is caught
**Then** `toast.error(detail)` fires and the form values remain unchanged

**Given** the Admin card on the home screen
**When** tapped
**Then** navigation to `/admin` occurs

### Story 3.9: PWA Configuration

As a developer,
I want the app configured as a full PWA with service worker caching the app shell,
So that users can install it on their home screen and the UI loads even when the Pi is briefly unreachable.

**Acceptance Criteria:**

**Given** `frontend/static/manifest.webmanifest`
**When** reviewed
**Then** it contains `name: "PrintServer"`, `short_name: "Print"`, `display: "standalone"`, dark `background_color` and `theme_color`, and `icons` array with 192×192 and 512×512 entries

**Given** `VitePWA` configured in `vite.config.ts` with `registerType: 'autoUpdate'` and `workbox.globPatterns` covering `**/*.{js,css,html,svg,png,ico}`
**When** `npm run build` runs
**Then** a service worker file is generated in `frontend/build/`

**Given** the built PWA is served and visited in Chrome on Android
**When** "Add to Home Screen" is triggered
**Then** the app installs and launches full-screen without browser chrome

**Given** the Pi backend is stopped (simulating unreachable server)
**When** the installed PWA is opened
**Then** the app shell loads (home screen visible) and shows the offline/grey printer status — no browser network error page

### Story 3.10: Accessibility Polish

As a developer,
I want all interactive elements to meet minimum accessibility standards,
So that the app is usable on any device and meets WCAG 2.1 AA requirements in dark mode.

**Acceptance Criteria:**

**Given** all interactive elements in the app (buttons, inputs, cards)
**When** inspected with browser DevTools
**Then** every element has a minimum bounding box of 44×44px

**Given** all form inputs (`<input>`, `<textarea>`)
**When** reviewed
**Then** each has a corresponding `<label for="...">` or `aria-label` attribute

**Given** the dark mode colour palette defined in `app.css @theme {}`
**When** text/background combinations are checked with a WCAG contrast checker
**Then** all body text and interactive element labels meet the 4.5:1 minimum contrast ratio

**Given** svelte-sonner toast notifications rendering success and error messages
**When** a toast appears
**Then** it uses appropriate ARIA roles (`role="status"` for success, `role="alert"` for errors)

**Given** `npm run build` followed by `npm run preview` tested on a real mobile device
**When** all pages are visited
**Then** no console errors appear and all touch interactions respond within 500ms
