# MyTeams — Personalized Football Hub

[![Backend CI](https://github.com/YOUR_ORG/my-team-app/actions/workflows/backend.yml/badge.svg)](https://github.com/YOUR_ORG/my-team-app/actions/workflows/backend.yml)
[![Worker CI](https://github.com/YOUR_ORG/my-team-app/actions/workflows/worker.yml/badge.svg)](https://github.com/YOUR_ORG/my-team-app/actions/workflows/worker.yml)
[![Mobile CI](https://github.com/YOUR_ORG/my-team-app/actions/workflows/mobile.yml/badge.svg)](https://github.com/YOUR_ORG/my-team-app/actions/workflows/mobile.yml)
[![Security Scan](https://github.com/YOUR_ORG/my-team-app/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_ORG/my-team-app/actions/workflows/security.yml)

MyTeams lets football fans follow their favourite clubs and get a personalised feed of upcoming fixtures, live scores, and league standings — all in a cross-platform mobile app (iOS & Android).

---

## Monorepo layout

```
my-team-app/
├── backend/          # FastAPI REST API (Python 3.12)
├── worker/           # RQ background worker (Python 3.12)
├── mobile/           # Expo / React Native app (TypeScript)
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Architecture overview

```
┌──────────────────────────────────────────────────────────┐
│  Mobile app (Expo / React Native)                        │
│  Expo Router · Tanstack Query · Zustand · axios          │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTPS / JSON
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI backend  (uvicorn + asyncio)                     │
│  JWT auth · CORS · structlog · Pydantic v2               │
│  /v1/auth  /v1/me  /v1/catalog  /v1/fixtures             │
│  /v1/standings  /v1/admin  /healthz  /readyz             │
└────┬──────────────────┬────────────────────────┬─────────┘
     │                  │                        │
┌────▼────┐   ┌─────────▼──────────┐   ┌────────▼────────┐
│ Postgres│   │   Redis (cache +   │   │  Football API   │
│  15     │   │   RQ queues)       │   │  (api-football  │
└─────────┘   └─────────┬──────────┘   │   or MockProv.) │
                        │              └─────────────────-┘
              ┌─────────▼──────────┐
              │  RQ Worker         │
              │  sync_fixtures     │
              │  sync_standings    │
              │  sync_live_events  │
              └────────────────────┘
```

---

## Quick start (Docker)

### 1. Clone & configure

```bash
git clone https://github.com/YOUR_ORG/my-team-app.git
cd my-team-app
cp .env.example .env          # edit values as needed
```

### 2. Start all services

```bash
make up
# or: docker compose up --build
```

This will:
- Start PostgreSQL 15 and Redis 7
- Run `alembic upgrade head` + seed data on first boot
- Start the FastAPI dev server with hot-reload at http://localhost:8000
- Start the RQ worker with hot-reload

### 3. Explore the API

- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc
- Health:      http://localhost:8000/healthz

### 4. Dev login (no email provider needed)

```bash
curl -X POST http://localhost:8000/v1/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com"}'
```

Returns a JWT you can use as `Authorization: Bearer <token>`.

---

## Environment variables

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` \| `staging` \| `production` |
| `SECRET_KEY` | *required* | JWT signing secret (min 32 chars) |
| `DATABASE_URL` | postgres://… | Async SQLAlchemy URL |
| `REDIS_URL` | redis://redis:6379/0 | Redis connection URL |
| `PROVIDER_NAME` | `mock` | `mock` \| `api_football` |
| `API_FOOTBALL_KEY` | — | api-football.com API key |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `REDIS_CACHE_TTL_SECONDS` | `300` | Dashboard / standings cache TTL |

When `PROVIDER_NAME=api_football` but `API_FOOTBALL_KEY` is blank, the backend automatically falls back to `mock`.

---

## Makefile targets

```
make setup           Install all deps locally (pip + npm)
make up              docker compose up --build -d
make down            docker compose down
make down-v          docker compose down -v  (destroys DB volume)
make migrate         Run alembic upgrade head inside container
make seed            Run db seed inside container
make backend-check   ruff + mypy + pytest in backend/
make worker-check    ruff + mypy + pytest in worker/
make mobile-check    tsc + expo lint + jest in mobile/
make trivy-fs        Trivy filesystem scan
make trivy-images    Build images then Trivy scan both
make ci-backend      Full backend quality gate (local)
make ci-worker       Full worker quality gate (local)
make ci-mobile       Full mobile quality gate (local)
```

---

## Database migrations

```bash
# Create a new migration (auto-generate from model changes)
docker compose exec backend alembic revision --autogenerate -m "add_column_x"

# Apply pending migrations
make migrate

# Downgrade one step
docker compose exec backend alembic downgrade -1
```

---

## Running tests locally

```bash
# Backend (SQLite in-memory — no Postgres required)
cd backend
pip install -e ".[dev]"
pytest -v

# Worker
cd worker
pip install -e ".[dev]"
pip install -e "../backend"   # shared models
pytest -v

# Mobile
cd mobile
npm ci
npx jest
```

---

## GitHub Actions CI

| Workflow | Triggers | Jobs |
|---|---|---|
| `backend.yml` | push/PR on `backend/**` | lint · typecheck · pytest · docker build · Trivy |
| `worker.yml` | push/PR on `worker/**` | lint · typecheck · pytest · docker build · Trivy |
| `mobile.yml` | push/PR on `mobile/**` | install · tsc · expo lint · jest |
| `security.yml` | push/PR to main + weekly | Trivy FS scan · backend image · worker image |

SARIF results are uploaded to GitHub Code Scanning.

---

## Mobile networking

When running the Expo development client on a physical device, set `EXPO_PUBLIC_API_URL` in `mobile/.env.local` to your machine's LAN IP:

```
EXPO_PUBLIC_API_URL=http://192.168.1.x:8000/v1
```

For the Android emulator use `http://10.0.2.2:8000/v1`.

---

## Key assumptions

1. **Magic-link auth is stubbed** — the `/v1/auth/request-link` endpoint logs the token to stdout instead of sending an email. Wire up an email provider (SendGrid, Resend, etc.) in `backend/app/api/auth.py` for production.
2. **Push notifications are stubbed** — `PushToken` models are persisted but no delivery logic is implemented. Add Expo Push Notifications or FCM/APNs in a separate service.
3. **api-football.com is the default external provider** — free tier is limited to 100 requests/day. The `MockProvider` is used when no API key is set.
4. **Single-region deployment assumed** — no multi-region cache invalidation is built in.
5. **No rate limiting** — add `slowapi` or a reverse-proxy rule before going to production.
