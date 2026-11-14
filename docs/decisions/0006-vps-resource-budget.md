# 0006: Memory budget on the VPS

**Status:** Proposed. Confirmed or adjusted in Phase 2 with measurements.

## Server

One Hostinger KVM 2 VPS, dedicated to Zira: 2 vCPU (shared), 8 GB RAM, 100 GB NVMe,
8 TB bandwidth.

## Proposed container limits

| Service | Memory limit | Note |
| --- | --- | --- |
| PostgreSQL with PostGIS | 1.5 GB | |
| Celery worker | 1.5 GB | Concurrency 1 to 2; raster processing runs in Earth Engine, not here |
| FastAPI backend | 768 MB | 2 workers |
| Next.js frontend | 512 MB | Standalone output |
| Redis | 256 MB | |
| Nginx | 128 MB | |
| System and headroom | about 3 GB | |

These are limits to configure, not measurements.

## Consequences

- Images are built in GitHub Actions and pulled on the server. A Next.js build on 2 shared
  vCPUs would starve the running services.
- Long jobs (25 years of data, 25-season simulations) run in the worker, never in a request.
- Daily database dumps are copied off the server.
