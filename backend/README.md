# MyTeams Backend

FastAPI REST API with Python 3.12, SQLAlchemy 2.0, Alembic, and PostgreSQL.

## Running locally (Docker)

```bash
# From repo root
make up       # starts postgres + redis + backend + worker
make migrate  # run Alembic migrations
make seed     # load sample data
```

Backend is available at http://localhost:8000  
Docs at http://localhost:8000/docs

## Running locally (bare Python)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Set env vars
export DATABASE_URL="postgresql+asyncpg://myteams:myteams_secret@localhost:5432/myteams"
export REDIS_URL="redis://localhost:6379/0"
export APP_ENV=development

alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

## Tests

```bash
pytest                        # all tests
pytest --cov=app              # with coverage
pytest app/tests/test_health.py  # single file
```

Tests use SQLite in-memory — no Postgres needed.

## Lint / type check

```bash
ruff check .
ruff format .
mypy app
```

## Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Upgrade
alembic upgrade head

# Downgrade one step
alembic downgrade -1
```

## Project structure

```
app/
  main.py          FastAPI app factory
  api/             Route handlers (one file per domain)
  core/            config, logging, security, errors
  db/              SQLAlchemy models, session, Alembic migrations
  schemas/         Pydantic request/response models
  services/        Provider interface, MockProvider, ApiFootball adapter, sync, cache
  tests/           pytest test suite
alembic/           Alembic migration scripts
Dockerfile
pyproject.toml
```

