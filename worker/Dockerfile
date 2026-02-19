# ────────────────────────────────────────────────────────────────
# Stage: base
# ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Ensure up-to-date build tooling (fixes setuptools.backends.legacy on 3.12-slim)
RUN pip install --upgrade pip setuptools wheel

# ────────────────────────────────────────────────────────────────
# Stage: deps
# ────────────────────────────────────────────────────────────────
FROM base AS deps
COPY pyproject.toml .
RUN pip install ".[dev]"

# ────────────────────────────────────────────────────────────────
# Stage: development (source mounted via compose volume)
# ────────────────────────────────────────────────────────────────
FROM deps AS development
CMD ["python", "-m", "app.main"]

# ────────────────────────────────────────────────────────────────
# Stage: production
# ────────────────────────────────────────────────────────────────
FROM base AS production
COPY pyproject.toml .
RUN pip install "."
COPY app/ app/
CMD ["python", "-m", "app.main"]
