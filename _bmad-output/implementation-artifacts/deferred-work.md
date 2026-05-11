# Deferred Work

## Deferred from: code review of 1-2-monorepo-scaffolding (2026-05-10)

- `PrinterError` has no structured fields (`backend/app/exceptions.py`) — add message/code fields when first used in Story 2.1
- `/health` returns `ok` unconditionally — full status-aware health check is Story 2.5
- `asyncio_mode = "auto"` but `anyio` not pinned in `requirements-dev.txt` — anyio is transitive via httpx; add explicit pin if test flakiness appears
- `PRINTER_VENDOR_ID`/`PRODUCT_ID` crash on non-hex env var strings — add input validation when env var documentation is formalised
- `PORT` accepts out-of-range values (0, -1, >65535) silently — add range check; low priority for single-user homelab
- `DATA_DIR` stored raw without path normalisation — use `pathlib.Path` at callsites rather than string concatenation
- `backend/app/data/*.json` gitignore pattern does not recurse into subdirectories — architecture only writes files at root of `data/`; revisit if subdirs are introduced
- `ssr = false` + `vite-plugin-pwa` autoUpdate can serve stale shell after deploy — known PWA limitation; address in Story 3.9 PWA configuration

## Deferred from: code review of Epic 1 stories 1.3, 1.4, 1.5 (2026-05-10)

- `make redeploy` uses `--build` (builds from source on Pi) instead of pulling the CI-tested GHCR image — spec-compliant per 1.5 AC3; consider a separate `make pull-deploy` target using `docker compose pull && docker compose up -d`
- `/dev/receipt-printer` device absence causes container start failure with no fallback — known hardware dependency; handled by Story 1.1 udev symlink
- CI builds `linux/arm64` only — `exec format error` on x86 dev machines; add a note to README or add `linux/amd64` to platforms
- No post-push smoke test for ARM64 image — broken image can be pushed and Watchtower will auto-deploy; consider a `docker run --rm --platform linux/arm64` health check step in the workflow
- `~/.bashrc` alias on Pi not versioned in repo — new Pi setup requires manual step; consider `make setup-pi` target or `scripts/setup-pi.sh`
- Makefile hardcodes `PI_HOST`/`PI_KEY` — correct for single-developer project; consider reading from env vars with hardcoded defaults for portability
- `Makefile test` has no dependency install step — fails on clean environment; consider adding a `make install` prerequisite
- No image digest pinning for `containrrr/watchtower`, `node:20-alpine`, `python:3.12-slim-bookworm` — floating tags expose to upstream breaking changes; pin digests when stability becomes critical

## Deferred from: code review of Epic 3 frontend (2026-05-11)

- Float imprecision in receipt item prices — `parseFloat` stores raw float; backend `f'£{price:.2f}'` rounds at print time so output is correct, but raw value sent to API has potential imprecision. Address if backend arithmetic ever changes.
- Overlapping `getStatus` poll calls if one takes >5 seconds — backend status endpoint reads from in-memory cache (<200ms), so probability is negligible; revisit if backend latency degrades.
- No runtime schema validation on API responses — `res.json()` cast directly to TypeScript types with no Zod/runtime check; silent field mismatches possible if API shape changes. Consider adding Zod in V2.
- Empty `store` field on receipt — backend accepts empty string; printer prints a blank centred store name line. Design decision: no enforcement added.
- Backend: `paper_near_end` not cleared in status cache on poll failure — only `printer_online` is set to False; stale paper warning can persist. Fix in backend status_cache.py `_poll_loop`.
- Backend: Printer USB singleton has no reconnection path — USB disconnect/reconnect requires container restart; no `reset_printer()` endpoint. Add reconnection logic in a future backend story.
