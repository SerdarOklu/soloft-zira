# syntax=docker/dockerfile:1
#
# Frontend image: the Next.js standalone server. Built in GitHub Actions and pulled on
# the VPS (docs/decisions/0006-vps-resource-budget.md).
#
# @soloft/uds is a private git dependency, so the build needs read access to
# SerdarOklu/soloft-uds. The token is passed as a BuildKit secret (id=uds_token) and
# never written into an image layer. See frontend/README.md. Build with:
#   docker build --secret id=uds_token,env=UDS_READ_TOKEN -t zira-frontend frontend

ARG NODE_VERSION=22

# --- Dependencies: install npm packages, including the private design system ---
FROM node:${NODE_VERSION}-bookworm-slim AS deps
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./

# The lock file records @soloft/uds as a git dependency. Fetch it over HTTPS with the
# token, exactly as CI does, then remove the credential helper in the same layer.
RUN --mount=type=secret,id=uds_token \
    UDS_READ_TOKEN="$(cat /run/secrets/uds_token 2>/dev/null || true)"; \
    if [ -z "$UDS_READ_TOKEN" ]; then \
      echo "::error:: the uds_token build secret is empty; the frontend needs read access to SerdarOklu/soloft-uds (frontend/README.md)." >&2; \
      exit 1; \
    fi; \
    AUTH="https://x-access-token:${UDS_READ_TOKEN}@github.com/"; \
    git config --global url."$AUTH".insteadOf "ssh://git@github.com/"; \
    git config --global --add url."$AUTH".insteadOf "git@github.com:"; \
    git config --global --add url."$AUTH".insteadOf "https://github.com/"; \
    npm ci; \
    rm -f /root/.gitconfig

# --- Build: produce the standalone output (next.config.ts sets output: 'standalone') ---
FROM node:${NODE_VERSION}-bookworm-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- Runtime: the self-contained server, nothing else ---
FROM node:${NODE_VERSION}-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN groupadd --system nodejs && useradd --system --gid nodejs --home-dir /app nextjs

# Standalone server, static assets and the public directory.
COPY --from=build --chown=nextjs:nodejs /app/public ./public
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

# BACKEND_URL is supplied at runtime; the browser never talks to the backend directly.
CMD ["node", "server.js"]
