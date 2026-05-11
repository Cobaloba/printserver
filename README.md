# PrintServer

A self-hosted thermal receipt printer controller running on a Raspberry Pi. Exposes a mobile-first PWA and a Telegram bot for printing from anywhere on your home network.

**Live at:** `http://192.168.0.25:9000` (on the local network)
**Telegram bot:** `@CobaPrinty_bot`

---

## What it does

- Print todo lists, fake receipts, free text, QR codes, and goatse from a phone browser
- Live printer status indicator and paper roll gauge in the app header
- Telegram bot: friends text `print: Hello world` → it prints
- PWA-installable — add to phone home screen, works offline (cached shell)
- Till roll tracking with self-calibrating paper remaining estimate

---

## Architecture

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.12), Pydantic v2, python-escpos |
| Frontend | SvelteKit 2 + Svelte 5, Tailwind CSS v4, vite-plugin-pwa |
| Printer | Jolimark USB thermal, `/dev/receipt-printer` via udev symlink |
| Deploy | Docker (linux/arm64), GitHub Actions → GHCR → Watchtower |
| Port | 9000 (avoids PiHole on 80/443 and Octoprint on 5000) |

Full architecture decisions: [`_bmad-output/planning-artifacts/architecture.md`](_bmad-output/planning-artifacts/architecture.md)

---

## Setup

### Prerequisites

- Raspberry Pi 4 with Docker and Docker Compose installed
- Jolimark USB thermal printer connected and udev symlink configured
- GitHub account (for GHCR image pull)

### 1. Clone and configure

```bash
git clone https://github.com/Cobaloba/printserver.git ~/printserver
cd ~/printserver
cp .env.example .env
nano .env
```

### 2. Environment variables

Edit `.env` with your values:

| Variable | Required | Description |
|---|---|---|
| `PRINTER_VENDOR_ID` | Yes | USB vendor ID from `lsusb` (default: `0x1ba0`) |
| `PRINTER_PRODUCT_ID` | Yes | USB product ID from `lsusb` (default: `0x220a`) |
| `PORT` | Yes | Service port (default: `9000`) |
| `DATA_DIR` | Yes | Persistent state directory (default: `/app/data`) |
| `GITHUB_USER` | Yes | Your GitHub username for GHCR image pull |
| `API_KEY` | No | Optional auth key for print/admin endpoints. Leave unset for open LAN access |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token from `@BotFather`. Leave unset to disable the bot |
| `TELEGRAM_ALLOWED_IDS` | No | Comma-separated Telegram user IDs allowed to trigger prints. Leave unset to allow anyone |

### 3. Start

```bash
docker compose up -d
```

The container pulls from GHCR automatically. Watchtower keeps it updated on every push to `main`.

---

## Telegram Bot

### Setting up

1. Message `@BotFather` on Telegram → `/newbot` → follow prompts → copy the token
2. Add `TELEGRAM_BOT_TOKEN=your-token` to `.env` on the Pi
3. `docker compose up -d`

### Commands

```
print: Hello world                       → prints "Hello world" (medium font)
print todo: Shopping | Milk | Bread      → prints a todo list
```

Anything else → the bot replies with help text.

### Restricting who can print (allowlist)

By default the bot responds to anyone who messages it. To restrict to specific people:

1. Each person messages `@userinfobot` on Telegram to get their numeric ID
2. Add to `.env`: `TELEGRAM_ALLOWED_IDS=123456789,987654321`
3. `cd ~/printserver && docker compose up -d`

People not on the list are silently ignored. Their attempts appear in the Admin page under **Printy — Bot Messages** with status `⊘ blocked`.

To add someone later: update `TELEGRAM_ALLOWED_IDS` and restart the container.

### Message history

Every message Printy receives is stored permanently in `/app/data/bot_messages.db` (SQLite, on the Docker volume). The Admin page shows the last 20; to browse the full history:

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25
sqlite3 ~/printserver/data/bot_messages.db

# Useful queries:
SELECT timestamp, sender_name, text, status FROM bot_messages ORDER BY id DESC LIMIT 20;
SELECT sender_name, COUNT(*) FROM bot_messages WHERE status='printed' GROUP BY sender_name;
SELECT * FROM bot_messages WHERE status='not_allowed';
.quit
```

---

## Development

### Local dev (no Pi required)

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 9000

# Terminal 2 — frontend
cd frontend && npm run dev    # Vite on :5173, proxies /api/ → localhost:9000
```

### Tests

```bash
make test
# or individually:
pytest backend/
cd frontend && npm run test
```

### Deploy to Pi

```bash
git push origin main
# GitHub Actions: pytest → vitest → docker buildx linux/arm64 → push GHCR
# Watchtower: detects new image → pulls → restarts container (~10 min total)
```

### Manual redeploy

```bash
make redeploy
# Runs: ssh pi 'cd ~/printserver && git pull && docker compose up --build -d'
```

### SSH to Pi

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25
```

---

## Adding a new print type

Exactly two files:

1. `backend/app/services/print_service.py` — add `def print_shopping_list(printer, ...)`
2. `backend/app/routers/print.py` — add `@router.post("/shopping-list")`
3. `backend/app/models/print_models.py` — add `ShoppingListRequest`
4. `frontend/src/routes/shopping-list/+page.svelte` — add the UI
5. `frontend/src/lib/api.ts` — add `printShoppingList()`
6. `frontend/src/routes/+page.svelte` — add a `PrintCard` to the home grid

---

## Project structure

```
printserver/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app, lifespan, router registration
│       ├── routers/             # print, status, admin, health
│       ├── services/            # printer, print_service, status_cache, roll_tracker, telegram_bot
│       └── models/              # Pydantic request/response schemas
├── frontend/
│   └── src/
│       ├── routes/              # One SvelteKit route per print type
│       └── lib/                 # api.ts, stores.ts, polling.ts, types.ts, components/
├── Makefile                     # make test, make redeploy
├── Dockerfile                   # Multi-stage: node build → python runtime
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── user-guide.md            # How to use the app (for non-developers)
│   └── operations.md            # Maintenance procedures
└── _bmad-output/
    ├── planning-artifacts/      # PRD, architecture, epics
    └── implementation-artifacts/ # Story files, sprint status, retrospectives
```

---

## Further reading

- [User Guide](docs/user-guide.md) — Using the PWA and Telegram bot
- [Operations Guide](docs/operations.md) — Maintenance and troubleshooting
- [Architecture](/_bmad-output/planning-artifacts/architecture.md) — Technical decisions
- [Deferred Work](_bmad-output/implementation-artifacts/deferred-work.md) — Known limitations
