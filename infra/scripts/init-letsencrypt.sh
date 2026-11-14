#!/usr/bin/env bash
# First-time HTTPS certificate issuance. Nginx needs a certificate to start its 443
# server, but the certificate needs Nginx to answer the ACME challenge first. This breaks
# the deadlock with a throwaway self-signed certificate, then replaces it with a real one
# from Let's Encrypt. Run once, from the repository root, after DNS points at this server.
#
#   ZIRA_DOMAIN=zira.example.com [email protected] ./infra/scripts/init-letsencrypt.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

ENV_FILE="${ENV_FILE:-.env}"
# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }
COMPOSE="docker compose --env-file ${ENV_FILE} -f infra/docker-compose.prod.yml"

: "${ZIRA_DOMAIN:?Set ZIRA_DOMAIN to the domain whose DNS points at this server}"
: "${CERTBOT_EMAIL:?Set CERTBOT_EMAIL for certificate expiry notices}"
STAGING="${STAGING:-0}"   # STAGING=1 uses the Let's Encrypt staging CA for dry runs.

live="/etc/letsencrypt/live/${ZIRA_DOMAIN}"

echo "1/4 Creating a throwaway self-signed certificate so Nginx can start..."
$COMPOSE run --rm --entrypoint sh certbot -c "\
  mkdir -p '${live}' && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '${live}/privkey.pem' -out '${live}/fullchain.pem' \
    -subj '/CN=${ZIRA_DOMAIN}'"

echo "2/4 Starting Nginx (and its upstreams)..."
$COMPOSE up -d nginx

echo "3/4 Requesting the real certificate from Let's Encrypt..."
staging_arg=""
[ "$STAGING" = "1" ] && staging_arg="--staging"
$COMPOSE run --rm --entrypoint sh certbot -c "\
  rm -rf '${live}' && \
  certbot certonly --webroot -w /var/www/certbot \
    -d '${ZIRA_DOMAIN}' --email '${CERTBOT_EMAIL}' \
    --agree-tos --no-eff-email --non-interactive ${staging_arg}"

echo "4/4 Reloading Nginx with the real certificate..."
$COMPOSE exec nginx nginx -s reload

echo "Done. https://${ZIRA_DOMAIN} should now serve a valid certificate."
