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
