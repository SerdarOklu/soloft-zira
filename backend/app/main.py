"""Zira API entry point.

Phase 1 adds sign-in. Routers for fields, weather, the Water Vault and the rest
arrive with their phases (docs/phases.md).
"""

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.parameters import get_config

app = FastAPI(title="Zira API", version=__version__)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/meta")
def meta() -> dict[str, object]:
    """What this deployment is running, and which parameters are not final yet."""
    config = get_config()
    return {
        "api_version": __version__,
        "model_version": config.parameters.model_version,
        "environment": get_settings().environment,
        "default_climate_profile": config.climate.default_profile,
        "crops": sorted(config.crops),
        "soils": sorted(config.soils),
        "parameters_unset": config.parameters.unset(),
        "parameters_needing_signoff": config.parameters.needing_signoff(),
    }
