# Infrastructure

| File | Purpose | Phase |
| --- | --- | --- |
| `docker-compose.dev.yml` | PostgreSQL with PostGIS and Redis for local development | 0 |
| `postgres/init/` | Creates the `zira_test` database on a new data volume | 1 |
| `docker-compose.prod.yml` | Full stack for the VPS: Nginx, frontend, backend, worker, database, Redis, with memory limits | 2 |
| `nginx/` | Reverse proxy and HTTPS configuration | 2 |
| `scripts/` | Backup and deployment scripts | 2 |

## Development services

```bash
cp .env.example .env    # once, from the repository root
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d
docker compose --env-file .env -f infra/docker-compose.dev.yml ps
docker compose --env-file .env -f infra/docker-compose.dev.yml down      # keeps data
docker compose --env-file .env -f infra/docker-compose.dev.yml down -v   # deletes data
```

The `zira_test` database for backend tests is created only when the data volume is new.
On a volume from Phase 0, create it once:

```bash
docker compose --env-file .env -f infra/docker-compose.dev.yml exec postgres \
  psql -U zira -d zira -c "CREATE DATABASE zira_test OWNER zira;"
```

PostgreSQL listens on `localhost:5432` and Redis on `localhost:6379`; change
`POSTGRES_PORT` or `REDIS_PORT` in `.env` if those are taken.

The target server and its memory budget are described in
[../docs/decisions/0006-vps-resource-budget.md](../docs/decisions/0006-vps-resource-budget.md).
