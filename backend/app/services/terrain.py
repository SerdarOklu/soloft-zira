"""Terrain of a field from NASADEM, NASA's reprocessing of the SRTM elevation data (phase 8).

NASADEM (30 m, one arc-second) is read from the cloud-optimised GeoTIFFs of the public Microsoft
Planetary Computer STAC catalogue, like the vegetation data. For the pixels inside the field polygon
the job stores the mean, lowest and highest elevation and the mean slope. Elevation is a property of
the land, not of a day, so each value is stored once, dated with the end of the SRTM mission.

Runs in the worker, never inside a request.
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, Field, JobStatus, RegionalObservation
from app.services import modis
from app.services.modis import ModisError

logger = logging.getLogger(__name__)

SOURCE = "srtm"
COLLECTION = "nasadem"
STAC_URL = modis.STAC_URL
SAS_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/nasademeuwest/nasadem-cog"
SRTM_DATE = date(2000, 2, 22)  # the end of the Shuttle Radar Topography Mission
METRES_PER_DEGREE_LAT = 110_574.0
METRES_PER_DEGREE_LON_AT_EQUATOR = 111_320.0
ERROR_LIMIT = modis.ERROR_LIMIT

# variable name -> unit
VARIABLES = {
    "elevation_m": "m",
    "elevation_min_m": "m",
    "elevation_max_m": "m",
    "slope_deg": "degree",
}


@dataclass(frozen=True)
class Terrain:
    elevation_m: float
    elevation_min_m: float
    elevation_max_m: float
    slope_deg: float
    pixels: int

    def as_values(self) -> dict[str, float]:
        return {
            "elevation_m": self.elevation_m,
            "elevation_min_m": self.elevation_min_m,
            "elevation_max_m": self.elevation_max_m,
            "slope_deg": self.slope_deg,
        }


def slope_degrees(
    elevation: np.ndarray, *, pixel_deg_x: float, pixel_deg_y: float, latitude: float
) -> np.ndarray:
    """The slope in degrees of every pixel, from the elevation grid and its size in degrees."""
    dx = METRES_PER_DEGREE_LON_AT_EQUATOR * math.cos(math.radians(latitude)) * abs(pixel_deg_x)
    dy = METRES_PER_DEGREE_LAT * abs(pixel_deg_y)
    d_row, d_col = np.gradient(elevation.astype("float64"), dy, dx)
    return np.degrees(np.arctan(np.hypot(d_row, d_col)))


def stats_from_arrays(
    elevation: np.ndarray,
    inside: np.ndarray,
    nodata: float | None,
    *,
    pixel_deg_x: float,
    pixel_deg_y: float,
    latitude: float,
) -> Terrain | None:
    """Elevation and slope statistics of the pixels inside the polygon, or None with no valid pixel.

    ``elevation`` should reach one pixel beyond the polygon so the slope at its edge is real.
    """
    valid = inside & np.isfinite(elevation)
    if nodata is not None:
        valid &= elevation != nodata
    if not valid.any():
        return None
    grid = np.where(elevation == nodata, np.nan, elevation) if nodata is not None else elevation
    slope = slope_degrees(
        np.nan_to_num(grid, nan=float(np.nanmean(grid[valid]))),
        pixel_deg_x=pixel_deg_x,
        pixel_deg_y=pixel_deg_y,
        latitude=latitude,
    )
    values = elevation[valid].astype("float64")
    return Terrain(
        elevation_m=float(values.mean()),
        elevation_min_m=float(values.min()),
        elevation_max_m=float(values.max()),
        slope_deg=float(slope[valid].mean()),
        pixels=int(valid.sum()),
    )


def read_terrain(path: str, geometry: dict[str, Any], *, latitude: float) -> Terrain:
    """Read the polygon (plus one pixel around it) from a NASADEM raster; any path GDAL can open."""
    import rasterio
    from rasterio import features
    from rasterio.windows import Window, from_bounds

    with (
        rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"),
        rasterio.open(path) as dataset,
    ):
        if dataset.crs is None or dataset.transform.is_identity:
            raise ModisError("The raster came back without georeferencing")
        xs = [p[0] for p in geometry["coordinates"][0]]
        ys = [p[1] for p in geometry["coordinates"][0]]
        window = from_bounds(min(xs), min(ys), max(xs), max(ys), dataset.transform)
        window = window.round_offsets().round_lengths()
        window = Window(
            max(0, window.col_off - 1),
            max(0, window.row_off - 1),
            window.width + 2,
            window.height + 2,
        )
        elevation = dataset.read(1, window=window, boundless=False).astype("float64")
        transform = dataset.window_transform(window)
        nodata = dataset.nodata
        pixel_x, pixel_y = dataset.res
    inside = features.geometry_mask(
        [geometry], out_shape=elevation.shape, transform=transform, invert=True, all_touched=True
    )
    result = stats_from_arrays(
        elevation, inside, nodata, pixel_deg_x=pixel_x, pixel_deg_y=pixel_y, latitude=latitude
    )
    if result is None:
        raise ModisError("The polygon has no valid elevation pixel")
    return result


def fetch_terrain(
    *,
    geometry: dict[str, Any],
    longitude: float,
    latitude: float,
    client: httpx.Client | None = None,
    reader: Any = read_terrain,
) -> Terrain:
    owns_client = client is None
    http = client or httpx.Client()
    try:
        response = modis._request(
            http,
            "POST",
            STAC_URL,
            json={
                "collections": [COLLECTION],
                "intersects": {"type": "Point", "coordinates": [longitude, latitude]},
                "limit": 1,
            },
        )
        items = response.json().get("features", []) if response.status_code == 200 else []
        if not items:
            raise ModisError("The catalogue has no NASADEM tile for this place")
        tokens = modis._request(http, "GET", SAS_URL)
        token = tokens.json().get("token") if tokens.status_code == 200 else None
        if not token:
            raise ModisError("The NASADEM storage did not give an access token")
    finally:
        if owns_client:
            http.close()
    href = items[0]["assets"]["elevation"]["href"]
    return reader(f"{href}?{token}", geometry, latitude=latitude)


def store_terrain(session: Session, field_id: uuid.UUID, terrain: Terrain) -> int:
    rows = [
        {
            "field_id": field_id,
            "source": SOURCE,
            "variable": name,
            "observed_on": SRTM_DATE,
            "value": value,
            "unit": VARIABLES[name],
        }
        for name, value in terrain.as_values().items()
    ]
    statement = insert(RegionalObservation).values(rows)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["field_id", "source", "variable", "observed_on"],
            set_={"value": statement.excluded.value, "unit": statement.excluded.unit},
        )
    )
    return len(rows)


def run_fetch_job(
    session: Session,
    job_id: uuid.UUID,
    *,
    client: httpx.Client | None = None,
    reader: Any = read_terrain,
) -> DataFetchJob:
    """Run one terrain job and record the outcome on it. A failure is recorded, not raised."""
    job = session.get(DataFetchJob, job_id)
    if job is None:
        raise LookupError(f"No fetch job {job_id}")
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    session.commit()

    try:
        row = session.execute(
            select(
                func.ST_AsGeoJSON(Field.geom),
                func.ST_Y(Field.centroid),
                func.ST_X(Field.centroid),
            ).where(Field.id == job.field_id)
        ).one_or_none()
        if row is None or row[0] is None or row[1] is None:
            raise ModisError("The field has no polygon")
        terrain = fetch_terrain(
            geometry=json.loads(row[0]),
            longitude=row[2],
            latitude=row[1],
            client=client,
            reader=reader,
        )
        written = store_terrain(session, job.field_id, terrain)
        field = session.get(Field, job.field_id)
        if field is not None and field.elevation_m is None:
            field.elevation_m = terrain.elevation_m  # POWER's value, if any, is kept
        job.status = JobStatus.DONE
        job.rows_written = written
        job.error_message = None
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "ok"
            source.last_success_at = job.finished_at
        session.commit()
    except Exception as error:  # recorded on the job; the worker must keep running
        session.rollback()
        logger.exception("Terrain fetch job %s failed", job_id)
        job = session.get(DataFetchJob, job_id)
        job.status = JobStatus.FAILED
        job.error_message = str(error)[:ERROR_LIMIT]
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "error"
        session.commit()
    return job
