# Zira

Zira is a decision-support platform that tells an agronomist, before sowing, which crop
rotation a specific field's water can carry. It combines NASA Earth observations with the
field's own soil, crop and farmer data. It supports the agronomist's and farmer's judgment
and does not replace it.

Built for the NASA Space Apps 2026 challenge "Field Shift: Adapting Farms with NASA Data"
and continued as a product by Soloft Industries.

**Status: Phase 1, base infrastructure.** Sign-in with three roles, the database schema
and the six-menu interface frame are in place; the screens have no content yet. The plan
and the approval gate for each phase are in [docs/phases.md](docs/phases.md).

## What is here

| Path | Contents |
| --- | --- |
| [`docs/PDT.md`](docs/PDT.md) | The Project Defining Document: scope, architecture, calculation specification, data model, API |
| [`docs/phases.md`](docs/phases.md) | Development phases, what each delivers, and its approval criterion |
| [`docs/decisions/`](docs/decisions/) | Architecture decisions and the ones still open |
| [`config/`](config/) | Model parameters, crops, soils, climate profiles and data sources |
| [`backend/`](backend/) | FastAPI application: API, calculation engine, background jobs |
| [`frontend/`](frontend/) | Next.js web application, built on the Soloft UDS design system from Phase 1 |
| [`simulator/`](simulator/) | Sensor simulator (Phase 7) |
| [`infra/`](infra/) | Docker Compose files; production stack for the VPS from Phase 2 |

## Requirements

- Docker with Compose
- Python 3.12 or newer and [uv](https://docs.astral.sh/uv/)
- Node.js 22.12 or newer
- Read access to the private `SerdarOklu/soloft-uds` repository
  (see [frontend/README.md](frontend/README.md))

## Quick start

```bash
cp .env.example .env

# 1. database and job queue
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# 2. backend
cd backend
uv sync
uv run alembic upgrade head                 # create the tables
uv run python -m app.cli seed-reference     # crops and data sources from config/
uv run python -m app.cli create-user --email you@example.com --name "Your Name" --role admin
uv run uvicorn app.main:app --reload        # http://localhost:8000/docs

# 3. frontend, in a second terminal
cd frontend
npm ci
npm run dev                                 # http://localhost:3000

# 4. job worker, in a third terminal (not needed until Phase 3)
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel INFO
```

Open http://localhost:3000 and sign in with the account you created.

With `make` installed: `make dev-up`, `make migrate`, `make seed`, `make backend-run`,
`make frontend-dev`, `make worker`.

## Checks

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest
cd frontend && npm test && npm run build && npm run typecheck
```

`make check` runs all of them; CI runs the same commands on every push and pull request.
Backend tests that need PostgreSQL or Redis are skipped locally when those are not
running, and are never allowed to skip in CI.

## Parameters

The parameter sheet is the source of truth for every model value. The files in `config/`
mirror it, and the backend refuses to load them if their shape or ranges are wrong.
`GET /api/v1/meta` lists the parameters that are still unset or waiting for agronomist
sign-off. See [config/README.md](config/README.md).

## NASA data

NASA POWER (daily climate), Landsat 8 and 9 (field history), GPM IMERG (precipitation),
SMAP (regional surface soil moisture), MODIS (vegetation time series) and GRACE / GRACE-FO
(basin water storage context). Roles, resolutions and scale warnings are in
[config/data_sources.yaml](config/data_sources.yaml) and PDT section 6.

## Design system

The interface is built on `@soloft/uds`, Soloft's private design system. Installing the
frontend from Phase 1 on needs read access to that repository; see
[docs/decisions/0005-repository-visibility-and-uds.md](docs/decisions/0005-repository-visibility-and-uds.md).

## License

Not decided yet.
