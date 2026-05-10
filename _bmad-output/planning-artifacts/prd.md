---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation-skipped', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
releaseMode: phased
inputDocuments: []
workflowType: 'prd'
classification:
  projectType: 'web_app_api_backend'
  domain: 'general_homelab'
  complexity: 'medium'
  projectContext: 'brownfield'
briefCount: 0
researchCount: 0
brainstormingCount: 0
projectDocsCount: 1
---

# Product Requirements Document — PrintServer

**Author:** Conor
**Date:** 2026-05-07

## Executive Summary

PrintServer is a self-hosted, Dockerized print server on a Raspberry Pi 4, delivering a mobile-first web interface and REST API for sending formatted output to a USB thermal receipt printer. The platform serves a single user — its developer/owner — enabling instant physical output of tasks, receipts, QR codes, and free text from any device on the home network, without a computer.

The target user is a developer who values both daily utility (checkable task lists, physical reminders) and social creativity (prank receipts, shareable novelties). V1 establishes the core platform; future versions add integrations with home automation systems, messaging platforms, and third-party webhooks.

### What Makes This Special

Most tools output to screens — notifications dismissed, lists ignored, information lost in the scroll. PrintServer outputs to paper: physical, tactile, present. A to-do list checked off with a pen. A receipt slipped into a gift. A QR code handed to someone.

The differentiator is threefold:
1. **Immediacy** — three taps from phone to printer, no desktop required
2. **Personality** — a curated set of print types balancing utility and delight, from daily chores to pranks
3. **Extensibility** — a developer-owned REST API where adding a new print type or wiring an external trigger takes minutes, not hours

## Project Classification

- **Project Type:** Self-hosted Web Application + REST API Backend
- **Domain:** Personal Homelab / Home Automation
- **Complexity:** Medium — brownfield Python print logic, Docker on ARM64, USB device passthrough, existing multi-service Pi environment
- **Project Context:** Brownfield — `printertest.py` provides proven print logic (python-escpos, todo/receipt/goatse) to be refactored into the API layer
- **Deployment Target:** Raspberry Pi 4 Model B, alongside PiHole and Octoprint (Docker Compose)

## Success Criteria

### User Success

- Print job submitted from phone reaches physical paper within 3 seconds of tap
- Printer status (online/offline) visible on home screen before submitting any job
- Toast notification confirms success or describes failure on every print attempt — no silent failures
- Till roll indicator provides a "getting low" warning before paper runs out
- PWA installable on phone home screen, launches full-screen without browser chrome

### Personal / Developer Success

- System runs without manual intervention — auto-restarts on error, no SSH required
- Any new print type live in production within 5 minutes of merging to main
- Adding new functionality remains enjoyable and frictionless — the process is part of the value
- Platform actively used and extended 6+ months post-launch

### Technical Success

- Docker container stable across reboots on Pi 4 ARM64 with USB printer passthrough
- `restart: unless-stopped` + health check endpoint ensures auto-recovery without manual intervention
- GitHub Actions pipeline: automated tests + ARM64 image build + GHCR push + Watchtower deploy — zero manual steps after merge to main
- No port conflicts with PiHole (80/443) or Octoprint (5000)
- All print operations complete end-to-end within 3 seconds under normal conditions

### Measurable Outcomes

- Zero manual SSH restarts required after initial setup
- < 5 minutes from `git push` to live production
- All V1 print types verified on real Pi + printer hardware before release

## User Journeys

### Journey 1: Conor — The Morning List (Primary User, Happy Path)

It's 8:30am. Conor is having coffee, mentally running through the day. He picks up his phone and taps the PrintServer icon — it opens instantly, full-screen, dark interface, the printer status dot pulsing green. He taps "Todo List", types tasks one by one — each appearing as a row below the input — hits Print. A spinner for half a second, then a green toast: "Sent to printer ✓". He tears off the strip and leaves it on his desk. By 6pm, every item is crossed off in pen.

**Capabilities revealed:** PWA home screen install, card navigation, todo dynamic list, print submission, success/failure toasts, printer status indicator.

---

### Journey 2: Conor — The Prank Receipt (Primary User, Social/Delight Path)

Conor is wrapping a birthday gift — a £20 book. He opens PrintServer, taps "Fake Receipt". A mini-ledger: store name at top ("Harrods"), two-column row builder with a running total updating live. He prices the book at £340.00, adds a few luxury items. Total: £892.50. He hits Print. A receipt slides out — date, receipt number, total, "Thank you for your visit." He tucks it in the gift bag. His friend's reaction is worth every line of code.

**Capabilities revealed:** Multi-item receipt form builder, live running total, formatted receipt output with store name / date / receipt number.

---

### Journey 3: Conor — Printer Offline (Primary User, Error Recovery)

Conor opens PrintServer to print a QR code. The status dot is flat grey — "Printer Offline". He walks over: it's unplugged after moving furniture. He plugs it in. Within seconds the dot pulses green. He pastes the URL, sees the QR preview render in real time, hits Print. Green toast. Paper out.

**Capabilities revealed:** Continuous status polling, offline state on home screen before any form interaction, graceful API error responses.

---

### Journey 4: Conor as Admin — New Roll Loaded

The till roll arc gauge shows red. Conor loads a fresh 57×40mm roll, taps the gear icon, hits "New Roll Loaded", confirms the size (pre-filled from last time), taps Save. The gauge resets to full. No SSH, no config editing, no terminal.

**Capabilities revealed:** Admin section, "New Roll Loaded" with size input + pre-fill, arc gauge state update, no-SSH maintenance flow.

---

### Journey 5: Conor as Developer — Shipping a New Print Type

Conor adds a "Shopping List" type: one new function in the print module, one FastAPI route, one test. He pushes, opens a PR, merges to main. GitHub Actions runs tests, builds the ARM64 image, pushes to GHCR. Watchtower restarts the container. He opens PrintServer on his phone — "Shopping List" is on the home screen. It works. Time from idea to production: under 30 minutes.

**Capabilities revealed:** Modular print type architecture, CI/CD pipeline, Watchtower auto-deploy, `/health` endpoint, developer ergonomics.

---

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---|---|
| Morning List | PWA install, card home screen, todo dynamic list, print submission, toasts, status dot |
| Prank Receipt | Multi-item form builder, live total, formatted receipt output |
| Printer Offline | Status polling, offline state UI, pre-form error surfacing, graceful API errors |
| Admin — New Roll | Admin section, roll reset + size input, arc gauge, no-SSH maintenance |
| Developer — New Type | Modular API/frontend architecture, GitHub Actions CI/CD, Watchtower, `/health` endpoint |

## Domain-Specific Requirements

### Network & Security

- V1: No authentication — access restricted to home LAN by network topology only
- Accepted risk: any device on the home network can trigger prints
- V2: Authentication layer to be added; architecture must not assume permanently open access

### Hardware Reliability

- Printer USB path stable across Pi reboots via udev persistent symlink (`/dev/receipt-printer`)
- API handles printer offline, out-of-paper, and mid-job disconnect gracefully — returns clear error, never crashes
- Docker Compose `restart: unless-stopped` + `/health` endpoint for automatic recovery without SSH

### Data Persistence

- Till roll state (`bytes_printed`, `roll_size`, `last_reset`) stored in a volume-mounted file (SQLite or JSON)
- State survives container restarts and image updates
- Volume defined in Docker Compose; never stored inside the container image

### Deployment Safety

- Watchtower auto-deploys on new GHCR image — no staging environment
- CI test suite is the only gate between a push and production
- Tests must cover all print type logic to catch regressions before image build

## API & Frontend Specification

### Overview

PrintServer is a single-page application (Svelte) served as static files by a FastAPI backend, accessed from mobile browsers on the home network. The REST API uses a `/api/v1/` prefix. The frontend is a PWA installable to the phone home screen. No SEO, no multi-tenancy, no rate limiting — single user, local network only.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/print/todo` | Print a to-do list |
| `POST` | `/api/v1/print/receipt` | Print a fake receipt |
| `POST` | `/api/v1/print/free-text` | Print free text |
| `POST` | `/api/v1/print/qr` | Print a QR code from URL |
| `POST` | `/api/v1/print/goatse` | Print goatse ASCII art |
| `GET` | `/api/v1/status` | Get printer status + roll state |
| `POST` | `/api/v1/admin/roll` | Log new roll loaded (resets counter) |
| `GET` | `/api/v1/admin/roll` | Get current roll state |
| `GET` | `/health` | Docker/Watchtower health check |

### Request Schemas

**`POST /api/v1/print/todo`**
```json
{ "title": "string (optional, default: 'TO DO')", "items": ["string"] }
```

**`POST /api/v1/print/receipt`**
```json
{
  "store": "string",
  "address": "string (optional)",
  "phone": "string (optional)",
  "items": [{ "name": "string", "price": "number" }],
  "tax_pct": "number (optional, default: 0)"
}
```

**`POST /api/v1/print/free-text`**
```json
{ "text": "string", "font_size": "'small'|'medium'|'large' (optional, default: 'medium')" }
```

**`POST /api/v1/print/qr`**
```json
{ "url": "string (valid URL)" }
```

**`POST /api/v1/admin/roll`**
```json
{ "width_mm": "number (default: 57)", "diameter_mm": "number (default: 40)" }
```

**Standard response envelope:**
```json
{ "success": true, "message": "string (optional)" }
```

**`GET /api/v1/status` response:**
```json
{
  "printer_online": true,
  "paper_near_end": false,
  "paper_out": false,
  "estimated_remaining_pct": 72
}
```

### Auth Model

- **V1:** No authentication. Network-level access control only (home LAN).
- **V2:** Authentication to be designed; API must not hardcode unauthenticated assumptions.

### Error Codes

| Code | Meaning |
|---|---|
| `200 OK` | Success |
| `400 Bad Request` | Missing or invalid input |
| `422 Unprocessable Entity` | Pydantic validation failure |
| `503 Service Unavailable` | Printer offline, out of paper, or USB error |

All error responses include a `detail` field surfaced in the frontend toast.

### PWA & Frontend

- `manifest.json`: `display: standalone`, dark theme, app name "PrintServer", icons at 192×192 and 512×512
- Service worker caches app shell — UI loads and shows offline state even when Pi is unreachable
- iOS: `apple-mobile-web-app-capable` and status bar meta tags
- Minimum viewport: 375px; touch targets: minimum 44×44px; dark mode default

### Printer Status Polling

- Frontend calls `GET /api/v1/status` every 5 seconds
- Status dot: green (online), grey (offline), amber (paper near end)
- No WebSocket required; polling is sufficient for local network latency

### Implementation Notes

- All print logic isolated in `print_service` module — one function per print type, independently testable
- FastAPI serves compiled Svelte output from `static/` at root (`/`)
- Pydantic models enforce validation — no manual input checking in route handlers
- Print jobs execute synchronously (single-threaded; no job queue required for V1)
- `python-escpos` `Usb(idVendor, idProduct)` backend — vendor/product ID confirmed via `lsusb` on Pi at setup

## Product Scope

### Philosophy

Platform foundation MVP — V1 establishes a working, extensible print server with the core print type set, full CI/CD pipeline, and reliable hardware integration. The goal is developer ergonomics that make every future addition fast and enjoyable. Single developer, personal project time.

### V1 — Must-Have

- FastAPI REST API (`/api/v1/`) — 5 print endpoints + status + admin + health
- Svelte + Tailwind PWA: dark mode, card home screen, per-type input UIs, printer status dot, toaster notifications, till roll arc gauge, admin section
- USB printer via `python-escpos` `Usb()` backend + udev persistent symlink (`/dev/receipt-printer`)
- Docker (`python:3.12-slim-bookworm` ARM64), `restart: unless-stopped`, volume-mounted state file
- GitHub Actions: test → build ARM64 → push to GHCR → Watchtower auto-deploy on merge to main
- Till roll tracking: `get_status()` hardware polling + byte-count estimation, "New Roll Loaded" reset

### V1.1 — Nice-to-Have

- QR code live preview as you type
- Camera QR scan input
- Drag-to-reorder todo items

### V2 — Growth

- Image printing (upload → resize to 384 dots → Floyd-Steinberg dither → print)
- Banner printing (rotated large text via Pillow image rendering)
- QR code arbitrary text input
- Authentication and access control
- Print history log

### Vision — Future

- Event-driven integrations: Octoprint job complete → auto-print summary; LinkedIn / messaging triggers
- Scheduled prints (morning briefing, daily task auto-print)
- Custom print templates
- Multi-printer support

### Risk Register

| Risk | Mitigation |
|---|---|
| USB passthrough on Docker ARM64 | Hardware spike first: `lsusb` → `Usb()` connection test → udev symlink reboot test. All architecture depends on this passing. |
| python-escpos QR native command unsupported | Test `printer.qr()` on hardware; Pillow raster fallback ready if native command absent. |
| Scope overrun in spare time | Deliver CI/CD + Free Text + Todo first — platform works with one print type. |
| Watchtower deploys broken code | CI test suite must cover all print logic before image build; enable Watchtower only after tests are solid. |

## Functional Requirements

### Print Operations

- **FR1:** User can submit a to-do list (title + one or more items) for printing
- **FR2:** User can submit a fake receipt (store name, optional address/phone, line items with prices, optional tax) for printing
- **FR3:** User can submit free text for printing with a choice of font size
- **FR4:** User can submit a URL for QR code generation and printing
- **FR5:** User can trigger goatse ASCII art printing
- **FR6:** System executes each print type as a discrete, independent operation
- **FR7:** System formats each print type according to its defined layout (line widths, alignment, headers, totals)
- **FR8:** System reports print job outcome — success or a specific failure reason — to the caller

### Printer Status & Monitoring

- **FR9:** System detects whether the printer is reachable and online
- **FR10:** System detects paper-near-end and paper-out conditions where hardware supports it
- **FR11:** User can view current printer status (online / offline / paper warning) before submitting a print job
- **FR12:** System periodically refreshes printer status and reflects changes in the interface without user action

### Till Roll Management

- **FR13:** User can log when a new paper roll has been loaded
- **FR14:** User can specify roll dimensions (width and diameter) when logging a new roll
- **FR15:** System pre-fills the last used roll dimensions when the user opens the new roll form
- **FR16:** System tracks cumulative paper usage since the last roll change
- **FR17:** System estimates the percentage of paper remaining on the current roll
- **FR18:** User can view estimated paper remaining from the home screen without navigating to settings

### Frontend Experience

- **FR19:** User can navigate to any available print type from a single home screen
- **FR20:** Each print type presents a tailored input interface suited to its content structure
- **FR21:** User receives immediate visual confirmation (success or failure) after every print submission
- **FR22:** User can access the admin section from the main interface
- **FR23:** User can install the application to their mobile device home screen as a standalone PWA
- **FR24:** Application displays its interface and communicates server status even when the Pi is unreachable
- **FR25:** User can see printer status and estimated paper level on the home screen without navigating away

### System Reliability & Operations

- **FR26:** System automatically restarts the print service after a crash or unhandled error without manual intervention
- **FR27:** System exposes a health check endpoint for container orchestration and uptime monitoring
- **FR28:** System handles printer disconnection, power loss, or paper errors gracefully — returns a clear error without crashing
- **FR29:** System persists till roll tracking state across container restarts and image updates
- **FR30:** System maintains a stable, consistent path to the printer device across host reboots

### API & Integration

- **FR31:** System exposes all print operations as versioned REST API endpoints callable by any HTTP client on the network
- **FR32:** System validates all API request inputs and returns structured, human-readable error responses for invalid requests
- **FR33:** System exposes printer status and roll state via a dedicated API endpoint
- **FR34:** System returns a health status response suitable for automated monitoring tools

### Developer Operations

- **FR35:** Developer can add a new print type by implementing a single module function and registering a single API route
- **FR36:** System automatically tests, builds, and deploys changes to production on merge to the main branch
- **FR37:** System runs automated tests against all print type logic before building a deployment image
- **FR38:** Developer can trigger a manual redeploy from any machine with SSH access using a single command

## Non-Functional Requirements

### Performance

- **NFR1:** Print job API requests complete end-to-end within 3 seconds under normal operating conditions
- **NFR2:** Printer status API responses return within 200ms
- **NFR3:** Frontend initial load completes within 2 seconds on the local WiFi network
- **NFR4:** Health check endpoint responds within 100ms
- **NFR5:** Frontend renders status poll updates and print submission responses within 500ms on devices with 2GB+ RAM

### Reliability & Availability

- **NFR6:** Service recovers automatically from application crashes within 30 seconds without manual intervention
- **NFR7:** Service starts automatically on Pi reboot via Docker restart policy
- **NFR8:** Printer disconnection or power loss does not crash or hang the service — returns a clear error and remains available
- **NFR9:** Till roll tracking state survives container restarts and image updates without data loss
- **NFR10:** Printer USB device path is stable across Pi reboots

### Maintainability

- **NFR11:** Adding a new print type requires changes to no more than 2 files (print module + API routes)
- **NFR12:** Project builds successfully from a clean clone with a single command
- **NFR13:** All print type logic is unit-testable without a physical printer connected
- **NFR14:** Full deployment cycle (code push → live production) completes within 10 minutes

### Security

- **NFR15:** The API does not log or persist user-submitted print content beyond the current request
- **NFR16:** Service binds to the local network interface only — no public internet exposure by default
- **NFR17:** No credentials, tokens, or secrets stored in the Docker image or source code — environment variables or Docker secrets used instead

### Compatibility

- **NFR18:** Docker image runs on `linux/arm64` (Raspberry Pi 4 Model B)
- **NFR19:** Frontend functions correctly on mobile Chrome (Android) and mobile Safari (iOS) at minimum 375px viewport
- **NFR20:** Service operates on a port that does not conflict with PiHole (80/443) or Octoprint (5000)

### Accessibility

- **NFR21:** All interactive elements have a minimum touch target size of 44×44px
- **NFR22:** Text and UI elements meet WCAG 2.1 AA contrast ratio requirements in dark mode
- **NFR23:** All form inputs have associated labels accessible to screen readers
