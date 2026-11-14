# Backend

FastAPI application. In Phase 0 it serves `/health` and `/api/v1/meta` and validates the
files in `../config/`. Everything else arrives phase by phase (`../docs/phases.md`).

```bash
uv sync
uv run uvicorn app.main:app --reload     # http://localhost:8000/docs
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

| Package | Will hold | PDT section |
| --- | --- | --- |
| `app/core` | Settings, configuration loading, auth | 3 |
| `app/api` | Routers | 10.1 |
| `app/models` | SQLAlchemy models for the 16 tables | 9 |
| `app/schemas` | Request and response schemas | 10.1 |
| `app/services` | NASA clients, ET0, water balance, Field Memory, rotation, card | 6 and 7 |
| `app/tasks` | Celery jobs | 10.2 |
