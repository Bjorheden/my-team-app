# ────────────────────────────────────────────────────────────────
# Stage: base — shared Python layer
# ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure up-to-date build tooling (fixes setuptools.backends.legacy on 3.12-slim)
RUN pip install --upgrade pip setuptools wheel

# ────────────────────────────────────────────────────────────────
# Stage: deps — install Python packages
# ────────────────────────────────────────────────────────────────
FROM base AS deps

COPY pyproject.toml .
RUN pip install ".[dev]"

# ────────────────────────────────────────────────────────────────
# Stage: development — hot-reload, source mounted at runtime
# ────────────────────────────────────────────────────────────────
FROM deps AS development

# Source is mounted via docker compose volume; nothing to COPY here.
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ────────────────────────────────────────────────────────────────
# Stage: production — baked-in source, no devDeps
# ────────────────────────────────────────────────────────────────
FROM base AS production

COPY pyproject.toml .
RUN pip install "."

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
