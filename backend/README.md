# Backend

FastAPI application. Phase 1 provides sign-in with roles, the database schema for the
16 tables of the PDT, and the job queue. Everything else arrives phase by phase
(`../docs/phases.md`).

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.cli seed-reference
uv run uvicorn app.main:app --reload     # http://localhost:8000/docs
```

## Accounts

There is no self-registration. Staff create accounts:

```bash
uv run python -m app.cli create-user --email ayse@example.com --name "Ayşe" --role agronomist
```

Roles: `admin`, `agronomist`, `cooperative_user`. The command asks for the password; set
`ZIRA_PASSWORD` to pass it non-interactively. It is never taken from the command line.

## Endpoints so far

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Liveness |
| `GET /api/v1/meta` | Versions, and the parameters still unset or awaiting sign-off |
| `POST /api/v1/auth/login` | Email and password in, access token and user out |
| `GET /api/v1/auth/me` | The signed-in user (`Authorization: Bearer <token>`) |
| `GET /api/v1/reference/soils` | Soil textures from `config/soils.yaml`, with the water they hold |
| `GET /api/v1/fields` | The fields the user may see (all for admin and agronomist; the organization's for a cooperative user) |
| `POST /api/v1/fields` | Add a field from a GeoJSON polygon; PostGIS derives the centroid and the area |
| `GET /api/v1/fields/{id}` | One field with its geometry |
| `DELETE /api/v1/fields/{id}` | Delete a field and its data (admin) |
| `POST /api/v1/fields/{id}/weather/fetch` | Queue a NASA POWER fetch (default: the 25 years of the parameter sheet); answers 202 with the job |
| `GET /api/v1/fields/{id}/weather/summary` | Coverage, yearly totals, the latest days and the latest job |
| `GET /api/v1/data-center/sources` | Every NASA source: connected or not, last success, rows, jobs (admin, agronomist) |
| `GET /api/v1/data-center/jobs` | The latest fetch jobs with their outcome (admin, agronomist) |
| `GET /api/v1/dashboard/summary` | Field and job counts, fields without data, map markers |
| `GET /api/v1/reference/crops` | Crops of `config/crops.yaml` and whether their season can run yet |
| `GET /api/v1/fields/{id}/water-vault?crop=...&date=...` | Usable water in the root zone on a day, in mm, with a low to high range, the daily series and what it rests on |
| `GET /api/v1/fields/{id}/field-memory` | MODIS NDVI series, the cropped or fallow call per season with confidence, and what a person confirmed |
| `POST /api/v1/fields/{id}/field-memory/fetch`, `.../confirm` | Queue a MODIS NDVI fetch (202 with the job); confirm the history season by season |
| `GET /api/v1/fields/{id}/rotation?rotation=winter_wheat,fallow` (or `history`) | Strategies A, B and C over the stored record: sufficient seasons with a range, stress days, deficit, irrigation need, per-season results (provisional values, see decision 0012) |
| `POST /api/v1/fields/{id}/messages/generate` | Write WhatsApp drafts for the events of one season (admin, agronomist) |
| `GET /api/v1/messages`, `GET /api/v1/messages/gateway` | The draft queue; whether the WhatsApp gateway is configured |
| `PATCH /api/v1/messages/{id}`, `POST .../approve`, `.../reject`, `.../send` | Edit, approve (sends when configured), reject, retry (admin, agronomist) |

## Water Vault

`app/services/water/` holds the FAO-56 engine as pure functions: `et0.py` (Penman-Monteith),
`crop.py` (Kc curve, Kc mid correction, TAW, RAW, p, Ks) and `balance.py` (the daily balance).
`vault.py` joins them to a field. The tests (`tests/test_water_et0.py`, `test_water_balance.py`)
reproduce the worked examples printed in FAO Irrigation and Drainage Paper 56, including the full
ET0 calculation of Example 18 and the ten-day stress table of Example 37. What the Water Vault
assumes, and what waits for an agronomist, is in
[../docs/decisions/0011-water-vault-version-1.md](../docs/decisions/0011-water-vault-version-1.md).

## WhatsApp

Drafts are approved by an agronomist before anything is sent. Sending uses Green API: set
`GREEN_API_INSTANCE_ID` and `GREEN_API_TOKEN` in `.env` (see `.env.example`). Without them
approved drafts wait. Wording and thresholds: `config/message_templates.yaml`.

## NASA POWER

The fetch runs in the Celery worker, never in a request. The request is built from
`power_request` in `config/parameters.yaml` and the location is read from the field's centroid.
It asks for UTC explicitly (POWER answers in local solar time otherwise), turns the fill value
into missing, retries transient failures, and upserts into `weather_observations` (unique per
field, day and source). A period that is already stored is served from the cache unless the
request sets `force`. A failure is recorded on the job and shown in the Data Center.

```bash
uv run celery -A app.tasks.celery_app worker --loglevel INFO   # on Windows add: --pool=solo
```

## Database migrations

```bash
uv run alembic upgrade head                          # apply
uv run alembic revision --autogenerate -m "message"  # after changing a model
uv run alembic check                                 # fails if models and migrations differ
```

Review every autogenerated migration before committing it. CI runs `alembic check`, so a
model change without a migration fails the build.

## Tests

```bash
uv run pytest            # unit tests; db and queue tests skip if their service is down
uv run pytest -m db      # needs PostgreSQL with PostGIS at TEST_DATABASE_URL
uv run pytest -m queue   # needs Redis at REDIS_URL
uv run ruff check . && uv run ruff format --check .
```

The db tests drop and rebuild the schema of the database at `TEST_DATABASE_URL`. It
defaults to `zira_test`, which the development Compose file creates on a new volume; never
point it at a database you want to keep.

## Layout

| Package | Holds | PDT section |
| --- | --- | --- |
| `app/core` | Settings, configuration loading, database session, security | 3 |
| `app/api` | Routers and request dependencies (current user, role checks) | 10.1 |
| `app/models` | SQLAlchemy models for the 16 tables | 9 |
| `app/schemas` | Request and response schemas | 10.1 |
| `app/services` | NASA clients, ET0, water balance, Field Memory, rotation, card (from Phase 3) | 6 and 7 |
| `app/tasks` | Celery application and jobs | 10.2 |
| `app/cli.py` | Administrative commands | |
| `migrations/` | Alembic migrations | 9 |
