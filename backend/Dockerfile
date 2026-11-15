# syntax=docker/dockerfile:1
#
# Backend image: FastAPI, the Celery worker and the Alembic migrations share it.
# Built in GitHub Actions and pulled on the VPS, never built on the server
# (docs/decisions/0006-vps-resource-budget.md).
#
# The build context is the repository ROOT, because the backend reads model values
# from config/ at the repository root (app.core.config, CONFIG_DIR). Build with:
#   docker build -f backend/Dockerfile -t zira-backend .

ARG PYTHON_VERSION=3.12

# --- Builder: resolve dependencies into a virtual environment with uv ---
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first so this layer is cached until the lock file changes.
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Then the application itself.
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# --- Runtime: a slim image with the virtual environment, the app and the config ---
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    CONFIG_DIR=/app/config \
    ENVIRONMENT=production

WORKDIR /app

# rasterio (MODIS NDVI) needs libexpat, which the slim image does not carry.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

# The virtual environment installs the app as editable, pointing at /app/app, so the
# source must live at the same path here as in the builder.
COPY --from=builder /app/.venv /app/.venv
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini
COPY config ./config

USER app
EXPOSE 8000

# The worker and the one-off migrate step override this command in the Compose file.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
