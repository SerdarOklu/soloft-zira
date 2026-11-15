"""MODIS NDVI for a field polygon (PDT section 6, phase 5).

The data is NASA's MOD13Q1 (Terra) and MYD13Q1 (Aqua) version 061 vegetation index, 250 m,
16-day composites, which together give a sample about every eight days. It is read from the
cloud-optimised GeoTIFFs of the public Microsoft Planetary Computer STAC catalogue, so no
account or Earth Engine project is needed. A job takes the pixels inside the field polygon and
keeps the ones the product marks as good or marginal (pixel reliability 0 or 1); snow, cloud and
fill values are left out and counted (the polygon-interior statistics the scale warning asks for).

Runs in the worker, never inside a request.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, Field, JobStatus, SatelliteObservation

logger = logging.getLogger(__name__)

SOURCE = "modis"
COLLECTION = "modis-13Q1-061"
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/modiseuwest/modis-061-cogs"
NDVI_ASSET = "250m_16_days_NDVI"
RELIABILITY_ASSET = "250m_16_days_pixel_reliability"

SCALE = 0.0001  # stored as integers; NDVI = value * 0.0001
GOOD_RELIABILITY = (0, 1)  # 0 good data, 1 marginal data; 2 snow or ice, 3 cloudy
PARTIAL_CLOUD_FRACTION = 0.5
SEARCH_LIMIT = 1000
READ_WORKERS = 6
READ_ATTEMPTS = 3
TIMEOUT_S = 60.0
MAX_FAILED_SHARE = 0.2
ERROR_LIMIT = 1000


class ModisError(RuntimeError):
    """The MODIS fetch failed; the text is stored on the job and shown in the Data Center."""


@dataclass(frozen=True)
class Observation:
    scene_id: str
    image_date: date
    ndvi_mean: float | None
    ndvi_median: float | None
    valid_pixel_count: int
    cloud_fraction: float | None
    quality_flag: str  # ok, partial (mostly cloud) or cloudy (nothing usable)


Reader = Callable[[dict[str, Any], str, dict[str, Any]], Observation]


def default_range(today: date, history_years: int) -> tuple[date, date]:
    """From 1 September before the first of ``history_years`` seasons to today.

    A season is the March to September window of its harvest year (see field_memory)."""
    last_harvest = today.year if today >= date(today.year, 9, 30) else today.year - 1
    return date(last_harvest - history_years, 9, 1), today


def stats_from_arrays(
    ndvi: np.ndarray, reliability: np.ndarray, inside: np.ndarray, nodata: float | None
) -> tuple[float | None, float | None, int, float | None, str]:
    """Mean and median NDVI of the usable pixels inside the polygon, how many there were, the
    share of polygon pixels that were not usable, and a quality flag."""
    total = int(inside.sum())
    if total == 0:
        return None, None, 0, None, "cloudy"
    usable = inside & np.isin(reliability, GOOD_RELIABILITY)
    if nodata is not None:
        usable &= ndvi != nodata
    count = int(usable.sum())
    cloud_fraction = 1.0 - count / total
    if count == 0:
        return None, None, 0, cloud_fraction, "cloudy"
    values = ndvi[usable].astype("float64") * SCALE
    flag = "partial" if cloud_fraction >= PARTIAL_CLOUD_FRACTION else "ok"
    return float(values.mean()), float(np.median(values)), count, cloud_fraction, flag


def read_polygon(item: dict[str, Any], token: str, geometry: dict[str, Any]) -> Observation:
    """Read one composite for the polygon. Imports rasterio here so the rest of the module
    (and the tests that fake the reader) do not need GDAL."""

    return read_rasters(
        f"{item['assets'][NDVI_ASSET]['href']}?{token}",
        f"{item['assets'][RELIABILITY_ASSET]['href']}?{token}",
        geometry,
        scene_id=item["id"],
        image_date=_item_date(item),
    )


def read_rasters(
    ndvi_path: str,
    reliability_path: str,
    geometry: dict[str, Any],
    *,
    scene_id: str,
    image_date: date,
) -> Observation:
    """The polygon statistics of one NDVI raster and its pixel-reliability raster (any path or
    URL GDAL can open; the tests use small local files in the MODIS sinusoidal projection)."""
    import rasterio
    from rasterio import features
    from rasterio.warp import transform_geom
    from rasterio.windows import Window, from_bounds

    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"):
        with rasterio.open(ndvi_path) as ndvi_ds:
            projected = transform_geom("EPSG:4326", ndvi_ds.crs, geometry)
            xs = [point[0] for point in projected["coordinates"][0]]
            ys = [point[1] for point in projected["coordinates"][0]]
            window = from_bounds(min(xs), min(ys), max(xs), max(ys), ndvi_ds.transform)
            window = window.round_offsets().round_lengths()
            window = Window(
                window.col_off, window.row_off, max(1, window.width), max(1, window.height)
            )
            ndvi = ndvi_ds.read(1, window=window)
            transform = ndvi_ds.window_transform(window)
            nodata = ndvi_ds.nodata
        with rasterio.open(reliability_path) as reliability_ds:
            reliability = reliability_ds.read(1, window=window)
    # all_touched keeps a field smaller than one pixel from vanishing.
    inside = features.geometry_mask(
        [projected], out_shape=ndvi.shape, transform=transform, invert=True, all_touched=True
    )
    mean, median, count, cloud, flag = stats_from_arrays(ndvi, reliability, inside, nodata)
    return Observation(
        scene_id=scene_id,
        image_date=image_date,
        ndvi_mean=mean,
        ndvi_median=median,
        valid_pixel_count=count,
        cloud_fraction=cloud,
        quality_flag=flag,
    )


def _item_date(item: dict[str, Any]) -> date:
    properties = item["properties"]
    stamp = properties.get("start_datetime") or properties.get("datetime")
    return date.fromisoformat(stamp[:10])


def _request(client: httpx.Client, method: str, url: str, **kwargs: Any) -> httpx.Response:
    last: Exception | None = None
    for attempt in range(READ_ATTEMPTS):
        try:
            response = client.request(method, url, timeout=TIMEOUT_S, **kwargs)
            if response.status_code < 500 and response.status_code != 429:
                return response
            last = ModisError(f"{url} answered {response.status_code}")
        except httpx.HTTPError as error:
            last = error
        time.sleep(2**attempt)
    raise ModisError(f"The MODIS catalogue could not be reached ({last})")


def search_items(
    client: httpx.Client, *, longitude: float, latitude: float, start: date, end: date
) -> list[dict[str, Any]]:
    response = _request(
        client,
        "POST",
        STAC_URL,
        json={
            "collections": [COLLECTION],
            "intersects": {"type": "Point", "coordinates": [longitude, latitude]},
            "datetime": f"{start.isoformat()}/{end.isoformat()}",
            "limit": SEARCH_LIMIT,
        },
    )
    if response.status_code != 200:
        raise ModisError(f"The MODIS catalogue answered {response.status_code}")
    items = response.json().get("features", [])
    return sorted(items, key=_item_date)


def sas_token(client: httpx.Client) -> str:
    response = _request(client, "GET", SAS_URL)
    token = response.json().get("token") if response.status_code == 200 else None
    if not token:
        raise ModisError("The MODIS storage did not give an access token")
    return token


def fetch_observations(
    *,
    geometry: dict[str, Any],
    longitude: float,
    latitude: float,
    start: date,
    end: date,
    client: httpx.Client | None = None,
    reader: Reader = read_polygon,
) -> list[Observation]:
    """One observation per composite in the period. A composite that cannot be read is skipped;
    too many skipped ones fail the job."""
    owns_client = client is None
    http = client or httpx.Client()
    try:
        items = search_items(http, longitude=longitude, latitude=latitude, start=start, end=end)
        if not items:
            raise ModisError("The catalogue has no MODIS composite for this place and period")
        token = sas_token(http)
    finally:
        if owns_client:
            http.close()

    def read_one(item: dict[str, Any]) -> Observation | None:
        for attempt in range(READ_ATTEMPTS):
            try:
                return reader(item, token, geometry)
            except Exception:  # a flaky range request; try again, then give up on this scene
                time.sleep(2**attempt)
        logger.warning("MODIS scene %s could not be read", item.get("id"))
        return None

    with ThreadPoolExecutor(max_workers=READ_WORKERS) as pool:
        results = list(pool.map(read_one, items))
    observations = [r for r in results if r is not None]
    failed = len(results) - len(observations)
    if failed / len(results) > MAX_FAILED_SHARE:
        raise ModisError(f"{failed} of {len(results)} MODIS composites could not be read")
    return observations


def store_observations(
    session: Session, field_id: uuid.UUID, observations: list[Observation]
) -> int:
    """Upsert: unique per field, source and scene, so fetching again is safe."""
    if not observations:
        return 0
    statement = insert(SatelliteObservation).values(
        [
            {
                "field_id": field_id,
                "source": SOURCE,
                "image_date": o.image_date,
                "scene_id": o.scene_id,
                "ndvi_mean": o.ndvi_mean,
                "ndvi_median": o.ndvi_median,
                "valid_pixel_count": o.valid_pixel_count,
                "cloud_fraction": o.cloud_fraction,
                "quality_flag": o.quality_flag,
            }
            for o in observations
        ]
    )
    update = {
        column: statement.excluded[column]
        for column in (
            "image_date",
            "ndvi_mean",
            "ndvi_median",
            "valid_pixel_count",
            "cloud_fraction",
            "quality_flag",
        )
    }
    update["fetched_at"] = func.now()
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["field_id", "source", "scene_id"], set_=update
        )
    )
    return len(observations)


def run_fetch_job(
    session: Session,
    job_id: uuid.UUID,
    *,
    client: httpx.Client | None = None,
    reader: Reader = read_polygon,
) -> DataFetchJob:
    """Run one MODIS job and record the outcome on it. A failure is recorded, not raised."""
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
        if job.date_from is None or job.date_to is None:
            raise ModisError("The job has no date range")
        import json

        observations = fetch_observations(
            geometry=json.loads(row[0]),
            longitude=row[2],
            latitude=row[1],
            start=job.date_from,
            end=job.date_to,
            client=client,
            reader=reader,
        )
        written = store_observations(session, job.field_id, observations)
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
        logger.exception("MODIS fetch job %s failed", job_id)
        job = session.get(DataFetchJob, job_id)
        job.status = JobStatus.FAILED
        job.error_message = str(error)[:ERROR_LIMIT]
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "error"
        session.commit()
    return job
