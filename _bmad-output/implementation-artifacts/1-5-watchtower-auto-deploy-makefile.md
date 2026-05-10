# Story 1.5: Watchtower Auto-Deploy + Makefile

**Epic:** 1 — Foundation & CI/CD Pipeline
**Story:** 1.5
**Status:** ready-for-dev

---

## User Story

As a developer,
I want Watchtower to automatically deploy new images on the Pi and a Makefile to simplify common commands,
So that `git push` → merge results in automatic production deployment within minutes.

---

## Acceptance Criteria

**AC1 — Watchtower auto-deploys within 5 minutes:**
**Given** Watchtower running on the Pi polling GHCR every 5 minutes
**When** a new `latest` image digest is pushed to GHCR after a successful CI run
**Then** Watchtower pulls the new image and restarts the `printserver` container within 5 minutes

**AC2 — `make test` runs both test suites:**
**Given** the `Makefile` at the repo root
**When** `make test` is run
**Then** both `pytest backend/` and `cd frontend && npm run test` execute

**AC3 — `make redeploy` triggers Pi rebuild:**
**Given** the `Makefile`
**When** `make redeploy` is run from any machine with SSH access to the Pi
**Then** the Pi runs `git pull && docker compose up --build -d` and the container is rebuilt

**AC4 — `redeploy` alias works on the Pi:**
**Given** `alias redeploy='cd ~/printserver && git pull && docker compose up --build -d'` in `~/.bashrc`
**When** `ssh pi 'redeploy'` is run (or logged in and running `redeploy`)
**Then** the container rebuilds and restarts without error

---

## Files to Create / Modify

```
printserver/        ← repo root
├── Makefile        ← NEW
└── docker-compose.yml  ← UPDATE (add Watchtower service + container_name)
```

Pi host changes (not in repo):
- `~/.bashrc` — append `redeploy` alias
- `~/printserver/` — replace scp copy with proper `git clone`

---

## Implementation

### `docker-compose.yml` updates

Two changes:
1. Add `container_name: printserver` to the printserver service so Watchtower can target it by name
2. Add `watchtower` service

```yaml
services:
  printserver:
    container_name: printserver
    image: ghcr.io/${GITHUB_USER:-local}/printserver:latest
    build: .
    restart: unless-stopped
    ports:
      - "9000:9000"
    env_file: .env
    devices:
      - /dev/receipt-printer:/dev/receipt-printer
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  watchtower:
    image: containrrr/watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300 printserver
```

**Notes:**
- `container_name: printserver` — gives the container a stable name so Watchtower's `printserver` argument targets it correctly
- `command: --interval 300 printserver` — polls every 300s (5 min); the `printserver` arg limits Watchtower to only that container, leaving PiHole and Octoprint alone
- Watchtower mounts the Docker socket to control the Docker daemon
- Since the GHCR image is public, no credentials needed for Watchtower to pull

### `Makefile` (repo root)

```makefile
PI_HOST = conor@192.168.0.25
PI_KEY  = ~/.ssh/pi_printserver

.PHONY: test redeploy

test:
	pytest backend/
	cd frontend && npm run test

redeploy:
	ssh -i $(PI_KEY) $(PI_HOST) 'cd ~/printserver && git pull && docker compose up --build -d'
```

**Notes:**
- `make test` requires `pytest` and `node/npm` to be available on the dev machine
- `make redeploy` SSHes to the Pi using the same key from Story 1.1; requires Pi's `~/printserver` to be a git clone (see Pi setup below)
- On Windows, run via Git Bash or WSL where `make` is available

### Pi host setup — convert scp copy to git clone

The Pi's `~/printserver` was copied via scp and is not a git repo. Converting it:

```bash
# Save .env (not in git)
cp ~/printserver/.env /tmp/printserver.env

# Stop running container
cd ~/printserver && docker compose down

# Replace with git clone
cd ~
rm -rf printserver
git clone https://github.com/Cobaloba/printserver.git printserver

# Restore .env
cp /tmp/printserver.env ~/printserver/.env

# Restart
cd ~/printserver && docker compose up -d
```

### Pi `~/.bashrc` — add redeploy alias

Append to `~/.bashrc` on the Pi:
```bash
alias redeploy='cd ~/printserver && git pull && docker compose up --build -d'
```

---

## Context from Previous Stories

### From Story 1.3 (Docker)
- `docker-compose.yml` already has `restart: unless-stopped`, device passthrough, volume, env_file
- The Pi currently runs the container from a locally-built image

### From Story 1.4 (CI/CD)
- GHCR image: `ghcr.io/cobaloba/printserver:latest` — public, no auth needed for pull
- Pi `.env` has `GITHUB_USER=cobaloba`
- Pi's `~/printserver` is an scp copy, not a git clone — must be converted as part of this story

---

## Definition of Done

- [ ] `Makefile` exists at repo root with `test` and `redeploy` targets
- [ ] `make test` runs both `pytest backend/` and `npm run test` in `frontend/`
- [ ] `docker-compose.yml` has `container_name: printserver` and `watchtower` service
- [ ] Pi's `~/printserver` is a proper `git clone` of `https://github.com/Cobaloba/printserver`
- [ ] `docker compose up -d` on Pi starts both `printserver` and `watchtower` containers
- [ ] `redeploy` alias exists in `~/.bashrc` on Pi
- [ ] `make redeploy` from local machine triggers Pi to pull and rebuild (AC3)
- [ ] Watchtower detects a new GHCR image and restarts printserver within 5 minutes (AC1 — verified by pushing a commit and watching)

---

## Dev Notes

_To be filled by developer during/after implementation._
