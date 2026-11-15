"""Regional cross-checks for a field: SMAP soil moisture, GPM IMERG rainfall, GRACE water storage.

The jobs read each source for the field's location (see ``earthdata``) and store the values in
``regional_observations``. The summaries (a correlation with NASA POWER rainfall, a storage trend)
are computed from what is stored. These are checks on the model, never inputs to it.
"""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    DataFetchJob,
    DataSource,
    Field,
    JobStatus,
    RegionalObservation,
    WeatherObservation,
)
from app.services import earthdata as ed
from app.services.power import SOURCE as POWER_SOURCE

logger = logging.getLogger(__name__)

SOURCES = ("smap", "gpm", "grace")
WINDOW_DAYS = 60  # SMAP and IMERG are read for the last days of the stored weather record
READ_WORKERS = 4
READ_ATTEMPTS = 3
MAX_FAILED_SHARE = 0.25
ERROR_LIMIT = 1000
GRACE_TREND_FROM = date(2003, 1, 1)  # whole years after the first months of the mission
UNITS = {
    "soil_moisture_am": "m3/m3",
    "soil_moisture_pm": "m3/m3",
    "precip_mm_day": "mm",
    "lwe_thickness_cm": "cm",
}

Row = tuple[str, date, float]  # variable, day, value


def window_for(session: Session, field_id: uuid.UUID) -> tuple[date, date]:
    """The last ``WINDOW_DAYS`` days of the field's weather record, or the days before today."""
    last = session.scalar(
        select(func.max(WeatherObservation.date)).where(
            WeatherObservation.field_id == field_id, WeatherObservation.source == POWER_SOURCE
        )
    )
    end = last or (datetime.now(UTC).date() - timedelta(days=5))
    return end - timedelta(days=WINDOW_DAYS - 1), end


def _read_many(items: Sequence[Any], read_one: Callable[[Any], list[Row]]) -> list[Row]:
    def safe(item: Any) -> list[Row] | None:
        for attempt in range(READ_ATTEMPTS):
            try:
                return read_one(item)
            except Exception:  # a flaky range read; try again, then give up on this file
                time.sleep(2**attempt)
        logger.warning("Could not read %s", getattr(item, "title", item))
        return None

    with ThreadPoolExecutor(max_workers=READ_WORKERS) as pool:
        results = list(pool.map(safe, items))
    failed = sum(1 for r in results if r is None)
    if items and failed / len(items) > MAX_FAILED_SHARE:
        raise ed.EarthdataError(f"{failed} of {len(items)} files could not be read")
    return [row for rows in results if rows for row in rows]


def fetch_rows(
    source: str,
    *,
    longitude: float,
    latitude: float,
    start: date,
    end: date,
    client: httpx.Client,
    token: str,
    readers: dict[str, Callable[..., list[Row]]] | None = None,
) -> list[Row]:
    """The values of one source for a point. ``readers`` replaces the file readers in tests."""
    readers = readers or {}
    if source == "smap":
        granules = ed.search_granules(
            client,
            token,
            ed.SMAP_SHORT_NAME,
            start,
            end,
            suffixes=(".h5",),
            day_from_title=ed.smap_day,
        )
        if not granules:
            raise ed.EarthdataError("NASA's catalogue has no SMAP file for this period")
        cell = ed.smap_cell(longitude, latitude)

        def read_smap(granule: ed.Granule) -> list[Row]:
            if "smap" in readers:
                return readers["smap"](granule, cell)
            with ed.open_hdf5(client, granule.url, token) as handle:
                values = ed.read_smap(handle, *cell)
            return [(name, granule.day, v) for name, v in values.items() if v is not None]

        return _read_many(granules, read_smap)

    if source == "gpm":
        # The Final run ends in September 2025; later days come from the Late run.
        for short_name in (ed.GPM_SHORT_NAME, ed.GPM_LATE_SHORT_NAME):
            granules = ed.search_granules(
                client,
                token,
                short_name,
                start,
                end,
                suffixes=(".nc4",),
                day_from_title=ed.gpm_day,
            )
            if granules:
                break
        if not granules:
            raise ed.EarthdataError("NASA's catalogue has no IMERG file for this period")
        cell = ed.gpm_cell(longitude, latitude)

        def read_gpm(granule: ed.Granule) -> list[Row]:
            if "gpm" in readers:
                return readers["gpm"](granule, cell)
            with ed.open_hdf5(client, granule.url, token) as handle:
                value = ed.read_gpm(handle, *cell)
            return [] if value is None else [("precip_mm_day", granule.day, value)]

        return _read_many(granules, read_gpm)

    if source == "grace":
        response = client.get(
            ed.CMR_URL,
            params={"short_name": ed.GRACE_SHORT_NAME, "page_size": 5},
            headers={"Authorization": f"Bearer {token}"},
            timeout=ed.TIMEOUT_S,
        )
        entries = (
            response.json().get("feed", {}).get("entry", []) if response.status_code == 200 else []
        )
        links = [
            link["href"]
            for entry in entries
            for link in entry.get("links", [])
            if link.get("rel", "").endswith("/data#") and link["href"].endswith(".nc")
        ]
        if not links:
            raise ed.EarthdataError("NASA's catalogue has no GRACE file")
        if "grace" in readers:
            return readers["grace"](links[0], (longitude, latitude))
        with ed.open_hdf5(client, links[0], token) as handle:
            series = ed.read_grace(handle, longitude, latitude)
        return [("lwe_thickness_cm", day, value) for day, value in series]

    raise ed.EarthdataError(f"Unknown source {source}")


def store_rows(session: Session, field_id: uuid.UUID, source: str, rows: Sequence[Row]) -> int:
    if not rows:
        return 0
    values = [
        {
            "field_id": field_id,
            "source": source,
            "variable": variable,
            "observed_on": day,
            "value": value,
            "unit": UNITS[variable],
        }
        for variable, day, value in rows
    ]
    for index in range(0, len(values), 2000):
        statement = insert(RegionalObservation).values(values[index : index + 2000])
        session.execute(
            statement.on_conflict_do_update(
                index_elements=["field_id", "source", "variable", "observed_on"],
                set_={"value": statement.excluded.value, "unit": statement.excluded.unit},
            )
        )
    return len(values)


def run_fetch_job(
    session: Session,
    job_id: uuid.UUID,
    *,
    client: httpx.Client | None = None,
    token: str | None = None,
    readers: dict[str, Callable[..., list[Row]]] | None = None,
) -> DataFetchJob:
    """Run one regional job (the source is the job's data source) and record the outcome."""
    job = session.get(DataFetchJob, job_id)
    if job is None:
        raise LookupError(f"No fetch job {job_id}")
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    session.commit()
    owns_client = client is None
    http = client or httpx.Client(follow_redirects=False)
    try:
        source = session.get(DataSource, job.data_source_id)
        if source is None or source.key not in SOURCES:
            raise ed.EarthdataError("The job is not for SMAP, GPM or GRACE")
        token = token or get_settings().earthdata_token
        if not token:
            raise ed.EarthdataError("EARTHDATA_TOKEN is not set on this server")
        row = session.execute(
            select(func.ST_Y(Field.centroid), func.ST_X(Field.centroid)).where(
                Field.id == job.field_id
            )
        ).one_or_none()
        if row is None or row[0] is None:
            raise ed.EarthdataError("The field has no location")
        start, end = (job.date_from, job.date_to)
        if start is None or end is None:
            start, end = window_for(session, job.field_id)
        rows = fetch_rows(
            source.key,
            longitude=row[1],
            latitude=row[0],
            start=start,
            end=end,
            client=http,
            token=token,
            readers=readers,
        )
        written = store_rows(session, job.field_id, source.key, rows)
        job.status = JobStatus.DONE
        job.rows_written = written
        job.error_message = None
        job.finished_at = datetime.now(UTC)
        source.status = "ok"
        source.last_success_at = job.finished_at
        session.commit()
    except Exception as error:  # recorded on the job; the worker must keep running
        session.rollback()
        logger.exception("Regional fetch job %s failed", job_id)
        job = session.get(DataFetchJob, job_id)
        job.status = JobStatus.FAILED
        # Never let the token reach a stored message.
        message = str(error)
        if token:
            message = message.replace(token, "***")
        job.error_message = message[:ERROR_LIMIT]
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "error"
        session.commit()
    finally:
        if owns_client:
            http.close()
    return job


# --- What the stored values say -------------------------------------------------------------------


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Pearson correlation, or None with fewer than three pairs or no spread."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return sxy / math.sqrt(sxx * syy)


def trend_per_year(
    points: Sequence[tuple[date, float]], *, since: date = GRACE_TREND_FROM
) -> float | None:
    """The least-squares slope in units per year from ``since``; None with under two years."""
    pts = [(d, v) for d, v in points if d >= since]
    if len(pts) < 24:
        return None
    xs = [(d - since).days / 365.25 for d, _ in pts]
    ys = [v for _, v in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx


def to_json(value: Any) -> str:
    return json.dumps(value, default=str)
