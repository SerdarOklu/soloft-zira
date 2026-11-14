# 0001: One repository and the base stack

**Status:** Accepted, 14 November 2026

## Decision

Backend, frontend, sensor simulator, configuration and infrastructure live in one
repository. The stack is the one recommended in the VPS architecture report:

- Backend: Python, FastAPI
- Database: PostgreSQL with PostGIS
- Job queue: Redis with Celery workers
- Remote sensing: Google Earth Engine
- Deployment: Docker Compose behind Nginx with HTTPS

Python dependencies are locked with uv (`backend/uv.lock`); Node dependencies with npm
(`frontend/package-lock.json`).

## Why

Six people work on one product with one release. A single repository keeps the API, the
interface and the parameter files in step, and one pull request can change all three.

## Consequences

- CI runs backend and frontend checks on every pull request.
- The frontend and backend are deployed together from one tag.
