# MyTeams Worker

Background worker that periodically syncs football data from the configured provider into the database.

## Architecture

- **RQ (Redis Queue)** for reliable task queuing.
- **Scheduler loop** (runs in main thread) enqueues tasks on a configurable interval.
- **Worker subprocess** picks up and executes queued tasks.

## Sync tasks

| Task | Default interval | Description |
|---|---|---|
| `sync_fixtures_task` | 5 min | Sync upcoming/recent fixtures for all teams |
| `sync_standings_task` | 30 min | Sync standings for all leagues |
| `sync_live_events_task` | 1 min | Sync events for in-progress fixtures |

## Running

```bash
# Via Docker (recommended)
docker compose up worker

# Locally
cd worker
pip install -e ".[dev]"
export DATABASE_URL="postgresql+asyncpg://..."
export REDIS_URL="redis://localhost:6379/0"
python -m app.main
```

## Environment variables

Inherits the same env vars as the root `.env.example`.

Key variable:

| Variable | Default | Description |
|---|---|---|
| `WORKER_SYNC_INTERVAL_SECONDS` | `300` | Base interval for scheduler checks |

## Tests

```bash
cd worker
pytest
```

