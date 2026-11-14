# Runbook: deploying and operating Zira on the VPS

How to put Zira on the Hostinger KVM 2 VPS and keep it running. The images are built in
GitHub Actions and pulled here; nothing is built on the server
([decisions/0006](decisions/0006-vps-resource-budget.md)). The stack and its memory limits
are in [`infra/docker-compose.prod.yml`](../infra/docker-compose.prod.yml).

## What runs

| Service | Image | Purpose | Published |
| --- | --- | --- | --- |
| `nginx` | `nginx:1.27-alpine` | TLS, reverse proxy, login rate limit | 80, 443 |
| `frontend` | `ghcr.io/serdaroklu/zira-frontend` | Next.js standalone server | internal only |
| `backend` | `ghcr.io/serdaroklu/zira-backend` | FastAPI | internal only |
| `worker` | `ghcr.io/serdaroklu/zira-backend` | Celery background jobs | internal only |
| `migrate` | `ghcr.io/serdaroklu/zira-backend` | Runs migrations + seed once, then exits | — |
| `postgres` | `postgis/postgis:17-3.5` | Database | internal only |
| `redis` | `redis:7-alpine` | Job queue | internal only |

Only Nginx is reachable from outside. `/api/v1` goes to the backend, everything else to
the frontend; `/api/v1/auth/login` is rate limited
([decisions/0008](decisions/0008-sign-in-and-sessions.md)).

## Prerequisites

1. A VPS with Docker Engine and the Compose plugin installed.
2. A **domain** whose DNS `A` (and `AAAA` if you use IPv6) record points at the VPS.
3. The images pushed to GHCR: a push to `main` runs the **Images** workflow
   (`.github/workflows/images.yml`), which needs the `UDS_READ_TOKEN` secret set
   ([frontend/README.md](../frontend/README.md)).
4. Read access to pull the images on the server (they are private by default): a personal
   access token with `read:packages`, or make the two packages public in GitHub.

## First deployment

```bash
# 1. Get the deployment files onto the server (infra/, scripts). config/ is already baked
#    into the backend image, so the server only needs this repository for infra/ and .env.
git clone https://github.com/SerdarOklu/soloft-zira.git
cd soloft-zira

# 2. Configuration and secrets.
cp .env.prod.example .env
#    Edit .env: set ZIRA_DOMAIN, CERTBOT_EMAIL, POSTGRES_PASSWORD, and a real SECRET_KEY:
#      openssl rand -hex 32
#    Production refuses to start with the placeholder or a secret under 32 characters.

# 3. Log in to GHCR so the server can pull the images (skip if the packages are public).
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-user> --password-stdin

# 4. Issue the HTTPS certificate (DNS must already point here). Run once.
./infra/scripts/init-letsencrypt.sh
#    Dry run against the staging CA first if unsure:  STAGING=1 ./infra/scripts/init-letsencrypt.sh

# 5. Start everything. Migrations and reference seeding run automatically (the migrate
#    service) before the backend and worker start.
./infra/scripts/deploy.sh

# 6. Create the first administrator (no self-registration).
docker compose --env-file .env -f infra/docker-compose.prod.yml run --rm \
  -e ZIRA_PASSWORD='a-strong-password' backend \
  python -m app.cli create-user --email you@example.com --name "Your Name" --role admin
```

### Verify

```bash
curl -fsS https://<your-domain>/health          # {"status":"ok"} from the backend
curl -fsSI https://<your-domain>/                # 200/redirect from the frontend, valid TLS
docker compose --env-file .env -f infra/docker-compose.prod.yml ps
```

The approval criterion for Phase 2 is that the skeleton is reachable over HTTPS on the
domain: a signed-in user sees the empty menus, served over HTTPS.

## Updates

A push to `main` builds and pushes new images. On the server:

```bash
git pull
./infra/scripts/deploy.sh            # pulls :latest, reruns migrate, restarts
```

Pin a specific build instead of `latest` for a reproducible rollout or a rollback by
setting `IMAGE_TAG` (e.g. `sha-abc1234`) in `.env`, then running `deploy.sh`.

## Certificate renewal

Let's Encrypt certificates last 90 days. Renew with a host cron entry (e.g. weekly):

```cron
0 3 * * 1 cd /path/to/soloft-zira && \
  docker compose --env-file .env -f infra/docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot && \
  docker compose --env-file .env -f infra/docker-compose.prod.yml exec nginx nginx -s reload
```

## Backups

Daily database dump, kept 14 days, optionally copied off-server
([decisions/0006](decisions/0006-vps-resource-budget.md)):

```cron
30 2 * * * cd /path/to/soloft-zira && ./infra/scripts/backup.sh >> backups/backup.log 2>&1
```

Set `BACKUP_REMOTE` in `.env` to copy each dump off the server (scp or rclone target); a
backup that only lives on the VPS is lost with the VPS. Restore with:

```bash
./infra/scripts/restore.sh backups/zira-YYYYMMDD-HHMMSS.sql.gz   # destructive; asks to confirm
```

## Day to day

```bash
C="docker compose --env-file .env -f infra/docker-compose.prod.yml"
$C ps                      # status and health
$C logs -f backend         # follow a service's logs
$C logs -f nginx
$C restart backend         # restart one service
$C down                    # stop the stack (volumes are kept)
docker stats               # live memory use against the limits in decision 0006
```

## Notes

- **Secrets** live only in `.env` on the server (git-ignored) and in GitHub Actions
  secrets. Nothing secret is committed.
- **Memory limits** come from [decisions/0006](decisions/0006-vps-resource-budget.md).
  Confirm them under real load with `docker stats` and adjust the limits in the Compose
  file if a service is killed (OOM) or starved.
- **Fonts** still load from Google Fonts until self-hosting is implemented
  ([decisions/0009](decisions/0009-self-hosted-fonts.md)); it is blocked on the same UDS
  access as the frontend image build.
