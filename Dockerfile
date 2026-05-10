# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python runtime ──────────────────────────────────────────────────
FROM python:3.12-slim-bookworm
WORKDIR /app

# Install curl for HEALTHCHECK — must be explicit, not in base image
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately from app code (layer cache optimisation:
# pyproject.toml changes rarely; app code changes often)
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.27.0" \
    "python-escpos>=3.1" \
    "pydantic>=2.0"

# Copy application source
COPY backend/app/ ./app/

# Copy compiled frontend into the FastAPI static serving directory
# Story 2.4 mounts app/static/ at "/" — this is where the SPA lives in the container
COPY --from=frontend-builder /build/build/ ./app/static/

# Create the data directory at the volume mount point
RUN mkdir -p /app/data

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

EXPOSE 9000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
