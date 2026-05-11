# PrintServer — Operations Guide

Day-to-day maintenance and recovery procedures.

---

## Accessing the Pi

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25
```

The project lives at `~/printserver` on the Pi.

---

## Common procedures

### After a printer power cycle

The container holds a USB handle that goes stale when the printer is powered off. After powering it back on:

**Option A — app (preferred):**
Admin page → **Restart Service** button

**Option B — SSH:**
```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25 "docker restart printserver"
```

Wait ~10 seconds, then try printing again.

### Checking if the container is healthy

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25 "docker ps && curl -s http://localhost:9000/health"
# Should return: {"status":"ok"}
```

### Viewing live logs

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25 "docker logs printserver -f --tail 50"
```

### Restarting manually

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25 "docker restart printserver"
```

---

## Deploying updates

### Automatic (normal workflow)

Push to `main` → GitHub Actions builds and pushes to GHCR → Watchtower detects and deploys within ~15 minutes.

### Manual redeploy (from dev machine)

```bash
make redeploy
# Runs git pull + docker compose up --build -d on the Pi
```

### Manual redeploy (from Pi directly)

```bash
ssh -i ~/.ssh/pi_printserver conor@192.168.0.25
cd ~/printserver && git pull && docker compose up -d
```

---

## Managing the Telegram bot

### Enabling the bot

1. Get a token from `@BotFather` on Telegram (`/newbot`)
2. On the Pi:
```bash
echo 'TELEGRAM_BOT_TOKEN=your-token-here' >> ~/printserver/.env
cd ~/printserver && docker compose up -d
```

### Restricting who can print (allowlist)

1. Each person you want to allow messages `@userinfobot` on Telegram to get their numeric ID
2. On the Pi:
```bash
# Edit .env
nano ~/printserver/.env
# Add: TELEGRAM_ALLOWED_IDS=123456789,987654321
# Restart
cd ~/printserver && docker compose up -d
```

People not on the list are silently ignored and shown as `⊘ blocked` in the Admin page.

### Adding someone to the allowlist later

```bash
nano ~/printserver/.env
# Update TELEGRAM_ALLOWED_IDS line, save
cd ~/printserver && docker compose up -d
```

### Rotating the bot token

If you need to revoke and replace the token (e.g. it was leaked):

1. Message `@BotFather` → `/mybots` → select your bot → *API Token* → *Revoke current token*
2. Copy the new token
3. Update `TELEGRAM_BOT_TOKEN` in `.env` on the Pi
4. `docker compose up -d`

### Disabling the bot

```bash
# Remove or comment out TELEGRAM_BOT_TOKEN from .env
nano ~/printserver/.env
cd ~/printserver && docker compose up -d
```

---

## Paper roll management

### Loading a new roll

1. Load the paper
2. Open the app → Admin → **Log New Roll**
3. Enter the roll dimensions (57mm wide × 40mm diameter for standard rolls)
4. Tap **Save New Roll**

This resets the usage counter and clears the previous calibration so the gauge starts fresh.

### How the gauge works

The gauge estimates remaining paper from:
1. Bytes printed (tracked per print job)
2. Roll dimensions (set on new roll)
3. A calibration factor that starts as a rough default (`14 bytes/mm²`)

**Self-calibration:** when the printer's hardware sensor first reports "paper running low", the system back-calculates the real usage rate for this specific roll and content mix. The estimate improves automatically — no action needed.

### If the gauge is badly wrong

Re-log the roll with correct dimensions (Admin → Log New Roll). The calibration resets and will converge again after the next near-end detection.

---

## Environment variables

Full reference — edit `~/printserver/.env` on the Pi:

| Variable | Default | Description |
|---|---|---|
| `PRINTER_VENDOR_ID` | `0x1ba0` | USB vendor ID (Jolimark) |
| `PRINTER_PRODUCT_ID` | `0x220a` | USB product ID (Jolimark) |
| `PORT` | `9000` | Service port |
| `DATA_DIR` | `/app/data` | Persistent state (mounted volume) |
| `GITHUB_USER` | — | GitHub username for GHCR pull |
| `API_KEY` | *(unset)* | Optional auth header for API endpoints |
| `TELEGRAM_BOT_TOKEN` | *(unset)* | Telegram bot token (bot disabled if unset) |
| `TELEGRAM_ALLOWED_IDS` | *(unset)* | Comma-separated Telegram user IDs; unset = anyone can print |

After any `.env` change: `cd ~/printserver && docker compose up -d`

---

## Known limitations / deferred work

See [`_bmad-output/implementation-artifacts/deferred-work.md`](../_bmad-output/implementation-artifacts/deferred-work.md) for the full list. Key ones:

- **USB reconnect** — printer power cycle always requires a container restart (no auto-reconnect)
- **Frontend auth** — if `API_KEY` is set, the frontend breaks (frontend doesn't send the key)
- **Roll gauge on heavy image prints** — QR codes and raster images send many more bytes per cm of paper than text; gauge drops faster than reality until the sensor calibrates
- **No ARM64 smoke test** — CI can push a broken image; Watchtower will auto-deploy it

---

## CI/CD overview

```
git push main
  → GitHub Actions
      pytest backend/      (68 tests)
      vitest frontend/     (12 tests)
      docker buildx linux/arm64
      push to ghcr.io/cobaloba/printserver:latest
  → Watchtower on Pi (polls every 5 min)
      detects new image digest
      pulls and restarts container
```

Total time push → live: ~10–15 minutes.
