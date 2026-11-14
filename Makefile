# Shortcuts for common tasks. On Windows without make, run the commands directly;
# each one is listed in README.md.

COMPOSE_DEV = docker compose --env-file .env -f infra/docker-compose.dev.yml

.PHONY: dev-up dev-down dev-logs backend-install backend-test backend-lint backend-run \
        migrate seed worker frontend-install frontend-test frontend-build frontend-dev check

dev-up:            ## start PostgreSQL/PostGIS and Redis
	$(COMPOSE_DEV) up -d

dev-down:          ## stop them (data volumes are kept)
	$(COMPOSE_DEV) down

dev-logs:
	$(COMPOSE_DEV) logs -f

backend-install:
	cd backend && uv sync

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

backend-run:       ## API on http://localhost:8000
	cd backend && uv run uvicorn app.main:app --reload

migrate:           ## apply database migrations
	cd backend && uv run alembic upgrade head

seed:              ## load crops and data sources from config/
	cd backend && uv run python -m app.cli seed-reference

worker:            ## background job worker
	cd backend && uv run celery -A app.tasks.celery_app worker --loglevel INFO

frontend-install:
	cd frontend && npm ci

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build && npm run typecheck

frontend-dev:      ## web app on http://localhost:3000
	cd frontend && npm run dev

check: backend-lint backend-test frontend-test frontend-build   ## everything CI runs
