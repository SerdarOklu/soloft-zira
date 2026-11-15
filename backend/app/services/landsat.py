"""Landsat 8 and 9 NDVI for a field polygon (PDT section 6, phase 8).

NASA and USGS Landsat Collection 2 Level-2 surface reflectance, 30 m, read from the
cloud-optimised GeoTIFFs of the public Microsoft Planetary Computer STAC catalogue (the same
route as MODIS, so no account or Earth Engine project is needed). For each scene the job takes the
pixels inside the field polygon, keeps the ones the quality band marks as clear (no fill, cloud,
cirrus, shadow or snow), converts the red and near-infrared bands to surface reflectance
(SR = DN * 0.0000275 - 0.2) and stores the mean and median NDVI = (NIR - Red) / (NIR + Red).

At 30 m a field of a few hectares holds dozens of pixels, which is why Landsat is the better source
for Field Memory than MODIS; MODIS stays as the fallback and as a long, dense series.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from typing import Any

import httpx
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, Field, JobStatus
from app.services import modis
from app.services.modis import ModisError, Observation, store_observations

logger = logging.getLogger(__name__)

COLLECTION = "landsat-c2-l2"
STAC_URL = modis.STAC_URL
SAS_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/landsateuwest/landsat-c2"
PLATFORMS = {"landsat8": "landsat-8", "landsat9": "landsat-9"}
MAX_SCENE_CLOUD = 70  # percent; the pixel quality band does the real work inside the polygon
SR_SCALE, SR_OFFSET = 0.0000275, -0.2
# QA_PIXEL bits: 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow, 5 snow.
BAD_QA_BITS = 0b111111
PARTIAL_CLOUD_FRACTION = modis.PARTIAL_CLOUD_FRACTION
READ_WORKERS = 6
READ_ATTEMPTS = modis.READ_ATTEMPTS
MAX_FAILED_SHARE = modis.MAX_FAILED_SHARE
ERROR_LIMIT = modis.ERROR_LIMIT

Reader = Any  # (item, token, geometry) -> Observation


def default_range(today: date, history_years: int) -> tuple[date, date]:
    return modis.default_range(today, history_years)


def stats_from_arrays(
    red: np.ndarray, nir: np.ndarray, qa: np.ndarray, inside: np.ndarray
) -> tuple[float | None, float | None, int, float | None, str]:
    """Mean and median NDVI of the clear pixels inside the polygon, how many there were, the share
    of polygon pixels left out, and a quality flag (ok, partial or cloudy)."""
    total = int(inside.sum())
    if total == 0:
        return None, None, 0, None, "cloudy"
    red_sr = red.astype("float64") * SR_SCALE + SR_OFFSET
    nir_sr = nir.astype("float64") * SR_SCALE + SR_OFFSET
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir_sr - red_sr) / (nir_sr + red_sr)
    clear = (
        inside
        & ((qa & BAD_QA_BITS) == 0)
        & (red > 0)
        & (nir > 0)
        & np.isfinite(ndvi)
        & (ndvi >= -1.0)
        & (ndvi <= 1.0)
    )
    count = int(clear.sum())
    cloud_fraction = 1.0 - count / total
    if count == 0:
        return None, None, 0, cloud_fraction, "cloudy"
    values = ndvi[clear]
    flag = "partial" if cloud_fraction >= PARTIAL_CLOUD_FRACTION else "ok"
    return float(values.mean()), float(np.median(values)), count, cloud_fraction, flag


def read_rasters(
    red_path: str,
    nir_path: str,
    qa_path: str,
    geometry: dict[str, Any],
    *,
    scene_id: str,
    image_date: date,
) -> Observation:
    """The polygon statistics of one scene's red, near-infrared and quality rasters (any path or
    URL GDAL can open). Imports rasterio here so the rest of the module needs no GDAL."""
    import rasterio
    from rasterio import features
    from rasterio.warp import transform_geom
    from rasterio.windows import Window, from_bounds

    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"):
        with rasterio.open(red_path) as red_ds:
            if red_ds.crs is None or red_ds.transform.is_identity:
                raise ModisError("The raster came back without georeferencing")
            projected = transform_geom("EPSG:4326", red_ds.crs, geometry)
            xs = [p[0] for p in projected["coordinates"][0]]
            ys = [p[1] for p in projected["coordinates"][0]]
            window = from_bounds(min(xs), min(ys), max(xs), max(ys), red_ds.transform)
            window = window.round_offsets().round_lengths()
            window = Window(
                window.col_off, window.row_off, max(1, window.width), max(1, window.height)
            )
            red = red_ds.read(1, window=window)
            transform = red_ds.window_transform(window)
        with rasterio.open(nir_path) as nir_ds:
            nir = nir_ds.read(1, window=window)
        with rasterio.open(qa_path) as qa_ds:
            qa = qa_ds.read(1, window=window)
    if not (red.shape == nir.shape == qa.shape):
        raise ModisError("The Landsat rasters do not line up")
    inside = features.geometry_mask(
        [projected], out_shape=red.shape, transform=transform, invert=True, all_touched=True
    )
    mean, median, count, cloud, flag = stats_from_arrays(red, nir, qa, inside)
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
    return date.fromisoformat(item["properties"]["datetime"][:10])


def read_polygon(item: dict[str, Any], token: str, geometry: dict[str, Any]) -> Observation:
    assets = item["assets"]
    return read_rasters(
        f"{assets['red']['href']}?{token}",
        f"{assets['nir08']['href']}?{token}",
        f"{assets['qa_pixel']['href']}?{token}",
        geometry,
        scene_id=item["id"],
        image_date=_item_date(item),
    )


def search_items(
    client: httpx.Client,
    *,
    platform: str,
    longitude: float,
    latitude: float,
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    response = modis._request(
        client,
        "POST",
        STAC_URL,
        json={
            "collections": [COLLECTION],
            "intersects": {"type": "Point", "coordinates": [longitude, latitude]},
            "datetime": f"{start.isoformat()}/{end.isoformat()}",
            "limit": modis.SEARCH_LIMIT,
            "query": {
                "platform": {"eq": platform},
                "eo:cloud_cover": {"lt": MAX_SCENE_CLOUD},
            },
        },
    )
    if response.status_code != 200:
        raise ModisError(f"The Landsat catalogue answered {response.status_code}")
    return sorted(response.json().get("features", []), key=_item_date)


def sas_token(client: httpx.Client) -> str:
    response = modis._request(client, "GET", SAS_URL)
    token = response.json().get("token") if response.status_code == 200 else None
    if not token:
        raise ModisError("The Landsat storage did not give an access token")
    return token


def fetch_observations(
    *,
    platform: str,
    geometry: dict[str, Any],
    longitude: float,
    latitude: float,
    start: date,
    end: date,
    client: httpx.Client | None = None,
    reader: Reader = read_polygon,
) -> list[Observation]:
    """One observation per scene. A scene that cannot be read is skipped; too many fail the job."""
    owns_client = client is None
    http = client or httpx.Client()
    try:
        items = search_items(
            http, platform=platform, longitude=longitude, latitude=latitude, start=start, end=end
        )
        if not items:
            return []  # for example Landsat 9 before 2022: nothing to read, not an error
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
        logger.warning("Landsat scene %s could not be read", item.get("id"))
        return None

    with ThreadPoolExecutor(max_workers=READ_WORKERS) as pool:
        results = list(pool.map(read_one, items))
    observations = [r for r in results if r is not None]
    failed = len(results) - len(observations)
    if failed / len(results) > MAX_FAILED_SHARE:
        raise ModisError(f"{failed} of {len(results)} Landsat scenes could not be read")
    return observations


def run_fetch_job(
    session: Session,
    job_id: uuid.UUID,
    *,
    client: httpx.Client | None = None,
    reader: Reader = read_polygon,
) -> DataFetchJob:
    """Run one Landsat job (one platform, named by the job's data source) and record the outcome."""
    job = session.get(DataFetchJob, job_id)
    if job is None:
        raise LookupError(f"No fetch job {job_id}")
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    session.commit()

    try:
        source = session.get(DataSource, job.data_source_id)
        if source is None or source.key not in PLATFORMS:
            raise ModisError("The job is not for Landsat 8 or 9")
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
        observations = fetch_observations(
            platform=PLATFORMS[source.key],
            geometry=json.loads(row[0]),
            longitude=row[2],
            latitude=row[1],
            start=job.date_from,
            end=job.date_to,
            client=client,
            reader=reader,
        )
        written = store_observations(session, job.field_id, observations, source=source.key)
        job.status = JobStatus.DONE
        job.rows_written = written
        job.error_message = None
        job.finished_at = datetime.now(UTC)
        source.status = "ok"
        source.last_success_at = job.finished_at
        session.commit()
    except Exception as error:  # recorded on the job; the worker must keep running
        session.rollback()
        logger.exception("Landsat fetch job %s failed", job_id)
        job = session.get(DataFetchJob, job_id)
        job.status = JobStatus.FAILED
        job.error_message = str(error)[:ERROR_LIMIT]
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "error"
        session.commit()
    return job
