#!/usr/bin/env bash
# Pull the images built by GitHub Actions and (re)start the stack. Migrations and
# reference seeding run automatically as the one-off "migrate" service before the
# backend and worker start. Run from the repository root on the VPS.
#
#   ./infra/scripts/deploy.sh            # deploy :latest
#   IMAGE_TAG=sha-abc1234 ./infra/scripts/deploy.sh   # pin a specific build
set -euo pipefail

cd "$(dirname "$0")/../.."

ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --env-file ${ENV_FILE} -f infra/docker-compose.prod.yml"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing ${ENV_FILE}. Copy .env.prod.example and fill it in first." >&2
  exit 1
fi

echo "Validating the Compose file..."
$COMPOSE config --quiet

echo "Pulling images (IMAGE_TAG=${IMAGE_TAG:-latest})..."
$COMPOSE pull

echo "Starting the stack..."
$COMPOSE up -d --remove-orphans

# Nginx resolves the backend and frontend addresses when it starts. A recreated container
# can get a new address, so make Nginx look them up again.
$COMPOSE exec -T nginx nginx -s reload || echo "Nginx was not running; nothing to reload."

echo "Current state:"
$COMPOSE ps
