# Zira

Zira is a decision-support platform that tells an agronomist, before sowing, which crop
rotation a specific field's water can carry. It combines NASA Earth observations with the
field's own soil, crop and farmer data. It supports the agronomist's and farmer's judgment
and does not replace it.

Built for the NASA Space Apps 2026 challenge "Field Shift: Adapting Farms with NASA Data"
and continued as a product by Soloft Industries.

**Status: Phase 0, repository skeleton.** There is no business logic yet. The plan and the
approval gate for each phase are in [docs/phases.md](docs/phases.md).

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

## Quick start

```bash
cp .env.example .env

# database and job queue
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# backend: http://localhost:8000/health and /api/v1/meta
cd backend
uv sync
uv run uvicorn app.main:app --reload

# frontend: http://localhost:3000
cd frontend
npm ci
npm run dev
```

With `make` installed, `make dev-up`, `make backend-run` and `make frontend-dev` do the same.

## Checks

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest
cd frontend && npm run build && npm run typecheck
```

`make check` runs all of them; CI runs the same commands on every push and pull request.

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
