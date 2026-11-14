#!/usr/bin/env bash
# Daily database backup. Dumps PostgreSQL to backups/ (gzip), keeps the last N days, and
# optionally copies the dump OFF the server so a lost VPS does not lose the data
# (docs/decisions/0006-vps-resource-budget.md). Intended for a host cron job; see
# docs/runbook.md.
#
#   ./infra/scripts/backup.sh
#
# Off-server copy (optional): set BACKUP_REMOTE to an scp-style target
# (user@host:/path) or to an rclone remote written as "rclone:remote:path".
set -euo pipefail

cd "$(dirname "$0")/../.."

ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --env-file ${ENV_FILE} -f infra/docker-compose.prod.yml"
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
OUT_DIR="backups"
OUT_FILE="${OUT_DIR}/zira-${STAMP}.sql.gz"

mkdir -p "$OUT_DIR"

echo "Dumping database ${POSTGRES_DB}..."
$COMPOSE exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner \
  | gzip -9 > "$OUT_FILE"
echo "Wrote ${OUT_FILE} ($(du -h "$OUT_FILE" | cut -f1))."

echo "Pruning backups older than ${KEEP_DAYS} days..."
find "$OUT_DIR" -name 'zira-*.sql.gz' -type f -mtime "+${KEEP_DAYS}" -delete

if [ -n "${BACKUP_REMOTE:-}" ]; then
  case "$BACKUP_REMOTE" in
    rclone:*)
      dest="${BACKUP_REMOTE#rclone:}"
      echo "Copying off-server with rclone to ${dest}..."
      rclone copy "$OUT_FILE" "$dest"
      ;;
    *)
      echo "Copying off-server with scp to ${BACKUP_REMOTE}..."
      scp "$OUT_FILE" "$BACKUP_REMOTE"
      ;;
  esac
else
  echo "BACKUP_REMOTE is not set: the dump stays on this server only. Set it to copy off-server." >&2
fi
