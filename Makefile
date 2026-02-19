.DEFAULT_GOAL := help
SHELL         := /bin/bash
DC            := docker compose

.PHONY: help up down build logs ps \
        migrate seed \
        backend-lint backend-typecheck backend-test backend-fmt \
        worker-lint worker-typecheck worker-test \
        mobile-install mobile-start mobile-typecheck mobile-test \
        ci-backend ci-worker ci-mobile \
        trivy-fs trivy-images

# ─── Formatting helpers ───────────────────────────────────────────────────────
BOLD  := $(shell tput bold 2>/dev/null || echo "")
RESET := $(shell tput sgr0 2>/dev/null || echo "")

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BOLD)%-26s$(RESET) %s\n", $$1, $$2}'

# ─── Docker Compose ──────────────────────────────────────────────────────────
up: ## Start all services (detached)
	$(DC) up -d

up-logs: ## Start all services and tail logs
	$(DC) up

down: ## Stop and remove containers
	$(DC) down

down-v: ## Stop and remove containers + volumes (data wipe)
	$(DC) down -v

build: ## Build all Docker images
	$(DC) build

build-nocache: ## Build all Docker images (no cache)
	$(DC) build --no-cache

logs: ## Tail all service logs
	$(DC) logs -f

ps: ## Show running service status
	$(DC) ps

restart: ## Restart all services
	$(DC) restart

# ─── Database ────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations inside the backend container
	$(DC) exec backend alembic upgrade head

migrate-create: ## Create a new migration (MSG="description")
	$(DC) exec backend alembic revision --autogenerate -m "$(MSG)"

seed: ## Load seed data (teams/leagues) into the database
	$(DC) exec backend python -m app.db.seed

# ─── Backend quality gates ────────────────────────────────────────────────────
backend-fmt: ## Auto-format backend with ruff
	cd backend && python -m ruff format .

backend-lint: ## Lint backend with ruff
	cd backend && python -m ruff check .

backend-typecheck: ## Type-check backend with mypy
	cd backend && python -m mypy app

backend-test: ## Run backend tests with pytest + coverage
	cd backend && python -m pytest --cov=app --cov-report=term-missing -v

backend-check: backend-lint backend-typecheck backend-test ## All backend quality gates

# ─── Worker quality gates ─────────────────────────────────────────────────────
worker-lint: ## Lint worker with ruff
	cd worker && python -m ruff check .

worker-typecheck: ## Type-check worker with mypy
	cd worker && python -m mypy app

worker-test: ## Run worker tests with pytest
	cd worker && python -m pytest -v

worker-check: worker-lint worker-typecheck worker-test ## All worker quality gates

# ─── Mobile ───────────────────────────────────────────────────────────────────
mobile-install: ## Install mobile deps
	cd mobile && npm install

mobile-start: ## Start Expo dev server
	cd mobile && npx expo start

mobile-android: ## Start on Android emulator
	cd mobile && npx expo start --android

mobile-ios: ## Start on iOS simulator
	cd mobile && npx expo start --ios

mobile-typecheck: ## TypeScript type check
	cd mobile && npx tsc --noEmit

mobile-lint: ## ESLint check
	cd mobile && npx expo lint

mobile-test: ## Run Jest tests
	cd mobile && npx jest --passWithNoTests

mobile-check: mobile-typecheck mobile-lint mobile-test ## All mobile quality gates

# ─── Security scanning ────────────────────────────────────────────────────────
trivy-fs: ## Run Trivy filesystem scan (CRITICAL=fail)
	trivy fs --exit-code 1 --severity CRITICAL --severity HIGH .

trivy-images: ## Run Trivy scan on built images
	trivy image --exit-code 1 --severity CRITICAL myteams-backend:dev
	trivy image --exit-code 1 --severity CRITICAL myteams-worker:dev

# ─── CI shortcuts ─────────────────────────────────────────────────────────────
ci-backend: backend-lint backend-typecheck backend-test ## Full backend CI run
ci-worker:  worker-lint  worker-typecheck  worker-test  ## Full worker CI run
ci-mobile:  mobile-typecheck mobile-lint mobile-test     ## Full mobile CI run

# ─── Setup quickstart ─────────────────────────────────────────────────────────
setup: ## First-time project setup (copy .env, install mobile deps, build images)
	@test -f .env || cp .env.example .env && echo "Created .env from .env.example"
	@test -f mobile/.env || cp mobile/.env.example mobile/.env && echo "Created mobile/.env"
	$(MAKE) mobile-install
	$(DC) build
	@echo ""
	@echo "$(BOLD)Setup complete!$(RESET)"
	@echo "Run 'make up' to start all services, then 'make migrate' and 'make seed'."
