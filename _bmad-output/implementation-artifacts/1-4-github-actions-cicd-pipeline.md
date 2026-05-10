# Story 1.4: GitHub Actions CI/CD Pipeline

**Epic:** 1 — Foundation & CI/CD Pipeline
**Story:** 1.4
**Status:** done

---

## User Story

As a developer,
I want every merge to main to automatically test, build, and push a new Docker image to GHCR,
So that code changes reach production without any manual steps on the Pi.

---

## Acceptance Criteria

**AC1 — Tests run and pass on every push:**
**Given** `.github/workflows/ci.yml` and a push to `main`
**When** the workflow runs
**Then** `pytest backend/` and `npm run test` (vitest) both execute and pass (with stub test files)
**And** `docker/build-push-action` builds `linux/arm64` and pushes `ghcr.io/{owner}/printserver:latest` to GHCR on test success

**AC2 — Failed tests block the build:**
**Given** an intentionally failing pytest test
**When** the push triggers the workflow
**Then** the build-and-push job does not execute and no new image is pushed to GHCR

**AC3 — Docker layer caching is configured:**
**Given** the CI workflow
**When** reviewed
**Then** `cache-from: type=gha` and `cache-to: type=gha,mode=max` are set on the build-push step, keeping subsequent builds under 10 minutes

---

## Pre-requisite: GitHub Repository

This story requires the project to be on GitHub. The Pi currently has a local repo (`~/printserver`) synced via scp — it needs a proper GitHub remote for CI to work.

**Steps to complete before implementing:**
1. Create a new repo at github.com (name: `printserver`, private or public)
2. From the local project directory:
   ```bash
   git remote add origin https://github.com/{YOUR_USERNAME}/printserver.git
   git push -u origin master
   ```
3. Note your GitHub username — it becomes the `GITHUB_USER` value in `.env` on the Pi

**GHCR package visibility:** After the first CI push, visit `https://github.com/{username}?tab=packages`, find `printserver`, go to Package Settings, and set visibility to **Public**. This is required so the Pi can pull the image without credentials (Watchtower, Story 1.5, needs unauthenticated pull).

---

## Files to Create

```
printserver/           ← repo root
├── .github/
│   └── workflows/
│       └── ci.yml         ← NEW — full CI/CD pipeline
└── backend/
    └── tests/
        └── test_placeholder.py  ← NEW — pytest stub (prevents exit-code 5 with 0 tests)
```

Also create a frontend stub test to prevent vitest from failing with "no test files found":
```
frontend/
└── src/
    └── lib/
        └── placeholder.test.ts  ← NEW — vitest stub
```

Also update `.env.example` to document `GITHUB_USER`.

**DO NOT modify:**
- `backend/app/main.py`
- `Dockerfile`
- `docker-compose.yml`

---

## Implementation

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install backend dependencies
        working-directory: backend
        run: |
          pip install .
          pip install -r requirements-dev.txt

      - name: Run backend tests
        run: pytest backend/

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Run frontend tests
        working-directory: frontend
        run: npm run test

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.repository_owner }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push linux/arm64 image
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/arm64
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/printserver:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### Key workflow decisions

| Decision | Reasoning |
|---|---|
| Two separate jobs (`test` + `build-and-push`) | `build-and-push` only runs if `test` passes — satisfies AC2 |
| `build-and-push` only on `push` to `main`, not PRs | PRs from forks don't have `packages: write` access to GHCR |
| `permissions: packages: write` on the job | Required for `GITHUB_TOKEN` to push to GHCR — must be explicit |
| `github.repository_owner` for image name | Automatically correct and lowercase — GHCR requires lowercase names |
| `type=gha` cache | GitHub Actions cache backend — free, no extra setup, automatic cleanup |
| `cache-to: mode=max` | Caches all intermediate layers, not just final — maximises cache hits |
| QEMU + Buildx | Required for cross-platform (`linux/arm64`) builds on `ubuntu-latest` (x86_64) |
| `npm ci` not `npm install` | Reproduces exact locked deps from `package-lock.json` |
| `pip install .` in `backend/` | Reads `pyproject.toml` and installs app deps + the package itself |

### Stub test files

**`backend/tests/test_placeholder.py`** — prevents pytest exit code 5 ("no tests collected"):
```python
def test_placeholder():
    pass
```

**`frontend/src/lib/placeholder.test.ts`** — prevents vitest "No test files found" error:
```typescript
import { describe, it, expect } from 'vitest'

describe('placeholder', () => {
  it('passes', () => {
    expect(true).toBe(true)
  })
})
```

These stubs are deleted as real tests are written in Epics 2 and 3.

### `.env.example` update

Add `GITHUB_USER` so the `docker-compose.yml` image reference is documented:

```dotenv
# GitHub username (used for GHCR image pull in docker-compose.yml)
GITHUB_USER=your-github-username
```

---

## Context from Previous Stories

### From Story 1.1 (Hardware Spike)
```
PRINTER_VENDOR_ID=0x1ba0
PRINTER_PRODUCT_ID=0x220a
PORT=9000
SYMLINK: /dev/receipt-printer (survives reboot)
```

### From Story 1.2 (Scaffolding)
- `frontend/package-lock.json` is committed → use `npm ci` in CI
- Frontend `test` script: `"test": "vitest run"` — runs once and exits (no `--watch`)
- `backend/requirements-dev.txt` contains: `pytest`, `pytest-asyncio`, `httpx`
- `backend/pyproject.toml` uses `setuptools.build_meta`; `pip install .` installs all app deps

### From Story 1.3 (Docker)
- `docker-compose.yml` image: `ghcr.io/${GITHUB_USER:-local}/printserver:latest` — the `GITHUB_USER` env var must be set in `.env` on the Pi for Story 1.5 (Watchtower)
- ARM64 build confirmed working on the Pi — CI will replicate this cross-platform

---

## Build Time Expectations

| Stage | First run | Cached run |
|---|---|---|
| pytest | ~30s | ~20s (no dep change) |
| vitest | ~45s (npm ci) | ~30s |
| Docker ARM64 build | ~8–12 min | ~2–3 min (layer cache) |
| **Total** | **~10–13 min** | **~3–5 min** |

The ARM64 build uses QEMU emulation on x86_64, which is the slow part. Layer caching (`type=gha`) drastically reduces this from run 2 onwards.

---

## Definition of Done

- [x] `.github/workflows/ci.yml` exists with two jobs: `test` and `build-and-push`
- [x] `backend/tests/test_placeholder.py` exists and `pytest backend/` passes locally (verified on Pi)
- [x] `frontend/src/lib/placeholder.test.ts` exists and `npm run test` passes in `frontend/`
- [x] `.env.example` includes `GITHUB_USER=` entry
- [x] Workflow YAML is syntactically valid (confirmed by successful CI run)
- [x] GitHub repo exists with code pushed to `main` (https://github.com/Cobaloba/printserver)
- [x] CI workflow runs on GitHub Actions and `test` job passes (green, 24s)
- [x] `build-and-push` job runs and `ghcr.io/cobaloba/printserver:latest` appears in GitHub Packages (4m43s)
- [ ] A second push confirms layer caching is working (build step is faster) *(will confirm on next story push)*
- [x] Deliberately breaking a test (`assert False` in placeholder) causes `build-and-push` to be skipped (run #25638874606)

---

## Dev Notes

_To be filled by developer during/after implementation._

---

## Dev Agent Record

### Implementation Plan

Created all CI/CD infrastructure files:
1. `.github/workflows/ci.yml` — two-job pipeline: `test` (pytest + vitest, all pushes/PRs) and `build-and-push` (ARM64 → GHCR, only on push to main with `packages: write` permission).
2. `backend/tests/test_placeholder.py` — single passing test prevents pytest exit code 5.
3. `frontend/src/lib/placeholder.test.ts` — vitest stub prevents "no test files found" failure.
4. `.env.example` — added `GITHUB_USER=` entry documenting the variable used in docker-compose.yml image reference.

### Completion Notes

- `pytest backend/` verified passing on Pi (1 test collected, 1 passed).
- `npm run test` verified passing locally (vitest v3.2.4, 1 test, 1 passed).
- CI fully verified on GitHub Actions: test job green (24s), build-and-push green (4m43s first run).
- GHCR image pushed to ghcr.io/cobaloba/printserver:latest and made public.
- Pi .env updated with GITHUB_USER=cobaloba.
- AC2 verified: intentional assert False blocked build-and-push (run #25638874606).
- Lowercase owner fix required: added `tr '[:upper:]' '[:lower:]'` step — GHCR rejects uppercase in image tags.
- `asyncio_mode` warning in pytest is benign — `pytest-asyncio` not yet installed; irrelevant until Epic 2 adds async tests.
- Node.js 20 deprecation warnings in Actions — action versions will need updating before June 2026.

### File List

- `.github/workflows/ci.yml` (new)
- `backend/tests/test_placeholder.py` (new)
- `frontend/src/lib/placeholder.test.ts` (new)
- `.env.example` (modified — added `GITHUB_USER`)

### Change Log

- 2026-05-10: Created CI/CD workflow (test + build-and-push jobs), pytest and vitest stub tests, updated .env.example with GITHUB_USER.

---

## Senior Developer Review (AI)

**Date:** 2026-05-10
**Outcome:** Changes Requested

### Action Items

- [x] [Review][Patch] GHCR `login-action` `username` uses raw `github.repository_owner` (mixed-case) while image tag uses lowercased output — FIXED: changed username to `${{ steps.owner.outputs.name }}` [.github/workflows/ci.yml]
- [x] [Review][Defer] CI builds `linux/arm64` only — anyone debugging locally on x86 will get `exec format error` [.github/workflows/ci.yml] — deferred, intentional; Pi is the only target; document in README
- [x] [Review][Defer] No post-push smoke test for ARM64 image — a broken image can be pushed and Watchtower will deploy it [.github/workflows/ci.yml] — deferred, enhancement; out of scope for Epic 1
