#!/usr/bin/env bash
# Restore the database from a dump produced by backup.sh. Destructive: it overwrites the
# current data. Run from the repository root.
#
#   ./infra/scripts/restore.sh backups/zira-20261115-030000.sql.gz
set -euo pipefail

cd "$(dirname "$0")/../.."

DUMP="${1:-}"
if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
  echo "Usage: $0 <path-to-dump.sql.gz>" >&2
  exit 1
fi

ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --env-file ${ENV_FILE} -f infra/docker-compose.prod.yml"
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

printf 'This overwrites the data in database %s. Type the database name to confirm: ' "$POSTGRES_DB"
read -r reply
[ "$reply" = "$POSTGRES_DB" ] || { echo "Aborted."; exit 1; }

echo "Restoring from ${DUMP}..."
gunzip -c "$DUMP" | $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
echo "Done."
