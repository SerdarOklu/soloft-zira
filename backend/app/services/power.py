"""NASA POWER daily client, parser and cache (PDT section 6, decision 0007).

Everything about the request comes from ``config/parameters.yaml`` (``power_request``).
No coordinate lives here: the caller passes the location read from the Field Profile.
Values are stored exactly as POWER reports them; the units are in ``UNITS``.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.parameters import Config
from app.models import DataFetchJob, DataSource, Field, JobStatus, WeatherObservation

logger = logging.getLogger(__name__)

SOURCE = "power"
BATCH_ROWS = 1000
MAX_ATTEMPTS = 3
BACKOFF_S = 2.0
ERROR_LIMIT = 1000

# POWER parameter name -> weather_observations column.
COLUMNS: dict[str, str] = {
    "PRECTOTCORR": "precipitation_mm",
    "T2M": "temperature_avg",
    "T2M_MAX": "temperature_max",
    "T2M_MIN": "temperature_min",
    "RH2M": "humidity",
    "WS10M": "wind_speed",
    "WS2M": "wind_speed",
    "PS": "surface_pressure",
    "ALLSKY_SFC_SW_DWN": "solar_radiation",
}
# Height each wind parameter is measured at. It must match core.wind_measurement_height_m,
# because ET0 converts wind to 2 m from the height that is recorded.
WIND_HEIGHT_M: dict[str, float] = {"WS10M": 10.0, "WS2M": 2.0}
VALUE_COLUMNS = sorted(set(COLUMNS.values()))

# Units as reported by the POWER parameter metadata (API v2.10.3).
UNITS: dict[str, str] = {
    "precipitation_mm": "mm/day",
    "temperature_avg": "°C",
    "temperature_max": "°C",
    "temperature_min": "°C",
    "humidity": "%",
    "wind_speed": "m/s",
    "solar_radiation": "MJ/m²/day",
    "surface_pressure": "kPa",
}


class PowerError(RuntimeError):
    """The request failed or the answer cannot be used."""


@dataclass(frozen=True)
class PowerResult:
    rows: list[dict[str, Any]]
    elevation_m: float | None
    api_version: str | None


def _setting(config: Config, name: str) -> Any:
    return config.parameters.get("power_request", name)


def _parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def default_range(config: Config) -> tuple[date, date]:
    """The period the parameter sheet asks for (25 years)."""
    return _parse_day(str(_setting(config, "start"))), _parse_day(str(_setting(config, "end")))


def _check_parameters(config: Config) -> tuple[list[str], float]:
    names = list(_setting(config, "parameters"))
    unknown = [name for name in names if name not in COLUMNS]
    if unknown:
        raise PowerError(f"No column is defined for POWER parameters: {', '.join(unknown)}")
    winds = [name for name in names if name in WIND_HEIGHT_M]
    if len(winds) != 1:
        raise PowerError("Request exactly one wind speed parameter (WS10M or WS2M)")
    configured = float(config.parameters.get("corrections", "wind_measurement_height_m"))
    if WIND_HEIGHT_M[winds[0]] != configured:
        raise PowerError(
            f"{winds[0]} is measured at {WIND_HEIGHT_M[winds[0]]:g} m but "
            f"corrections.wind_measurement_height_m is {configured:g}"
        )
    return names, configured


def _messages(response: httpx.Response) -> str:
    try:
        return "; ".join(str(m) for m in response.json().get("messages", [])) or response.text[:200]
    except ValueError:
        return response.text[:200]


def _get_json(client: httpx.Client, url: str, params: dict[str, Any]) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(url, params=params)
        except httpx.TransportError as error:  # timeouts and connection failures
            last = error
        else:
            if response.status_code == 429 or response.status_code >= 500:
                last = PowerError(f"POWER answered HTTP {response.status_code}")
            elif response.status_code != 200:
                raise PowerError(
                    f"POWER rejected the request (HTTP {response.status_code}): "
                    f"{_messages(response)}"
                )
            else:
                try:
                    return response.json()
                except ValueError as error:
                    raise PowerError("POWER returned a body that is not JSON") from error
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S * attempt)
    raise PowerError(f"POWER is not reachable after {MAX_ATTEMPTS} attempts: {last}") from last


def parse_payload(
    payload: dict[str, Any], names: list[str], *, missing: float, wind_height: float
) -> PowerResult:
    """Turn a POWER answer into rows. The fill value becomes missing (None)."""
    try:
        series = payload["properties"]["parameter"]
    except (KeyError, TypeError) as error:
        detail = payload.get("messages") if isinstance(payload, dict) else payload
        raise PowerError(f"POWER answered without data: {detail}") from error
    absent = [name for name in names if name not in series]
    if absent:
        raise PowerError(f"POWER answer lacks parameters: {', '.join(absent)}")

    days = sorted(set().union(*(series[name].keys() for name in names)))
    if not days:
        raise PowerError("POWER returned no days")

    rows: list[dict[str, Any]] = []
    for day in days:
        row: dict[str, Any] = {"date": _parse_day(day), "wind_height_m": wind_height}
        partial = False
        for name in names:
            value = series[name].get(day)
            if value is None or float(value) == missing:
                value, partial = None, True
            row[COLUMNS[name]] = value
        row["quality_flag"] = "partial" if partial else None
        rows.append(row)

    coordinates = (payload.get("geometry") or {}).get("coordinates") or []
    elevation = float(coordinates[2]) if len(coordinates) > 2 else None
    api = (payload.get("header") or {}).get("api") or {}
    return PowerResult(rows=rows, elevation_m=elevation, api_version=api.get("version"))


def fetch_daily(
    config: Config,
    *,
    latitude: float,
    longitude: float,
    start: date,
    end: date,
    client: httpx.Client | None = None,
) -> PowerResult:
    names, wind_height = _check_parameters(config)
    params = {
        "parameters": ",".join(names),
        "community": _setting(config, "community"),
        "longitude": longitude,
        "latitude": latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": _setting(config, "format"),
        # POWER answers in local solar time unless told otherwise.
        "time-standard": _setting(config, "time_standard"),
    }
    owns_client = client is None
    http = client or httpx.Client(timeout=float(_setting(config, "timeout_s")))
    try:
        payload = _get_json(http, _setting(config, "api_url"), params)
    finally:
        if owns_client:
            http.close()
    return parse_payload(
        payload,
        names,
        missing=float(_setting(config, "missing_value")),
        wind_height=wind_height,
    )


def cached_days(session: Session, field_id: uuid.UUID, start: date, end: date) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(WeatherObservation)
            .where(
                WeatherObservation.field_id == field_id,
                WeatherObservation.source == SOURCE,
                WeatherObservation.date.between(start, end),
            )
        )
        or 0
    )


def store_rows(session: Session, field_id: uuid.UUID, rows: list[dict[str, Any]]) -> int:
    """Upsert: unique per field, day and source, so fetching again is safe."""
    for index in range(0, len(rows), BATCH_ROWS):
        chunk = rows[index : index + BATCH_ROWS]
        statement = insert(WeatherObservation).values(
            [{**row, "field_id": field_id, "source": SOURCE} for row in chunk]
        )
        update = {
            column: statement.excluded[column]
            for column in (*VALUE_COLUMNS, "wind_height_m", "quality_flag")
        }
        update["fetched_at"] = func.now()
        session.execute(
            statement.on_conflict_do_update(
                index_elements=["field_id", "date", "source"], set_=update
            )
        )
    return len(rows)


def run_fetch_job(
    session: Session,
    job_id: uuid.UUID,
    config: Config,
    *,
    force: bool = False,
    client: httpx.Client | None = None,
) -> DataFetchJob:
    """Run one fetch job and record the outcome on it. A failure is recorded, not raised."""
    job = session.get(DataFetchJob, job_id)
    if job is None:
        raise LookupError(f"No fetch job {job_id}")
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(UTC)
    session.commit()

    try:
        location = session.execute(
            select(func.ST_Y(Field.centroid), func.ST_X(Field.centroid)).where(
                Field.id == job.field_id
            )
        ).one_or_none()
        if location is None or location[0] is None:
            raise PowerError("The field has no location")
        start, end = job.date_from, job.date_to
        if start is None or end is None:
            raise PowerError("The job has no date range")

        wanted = (end - start).days + 1
        if not force and cached_days(session, job.field_id, start, end) >= wanted:
            written = 0  # the whole period is already stored
        else:
            result = fetch_daily(
                config,
                latitude=location[0],
                longitude=location[1],
                start=start,
                end=end,
                client=client,
            )
            written = store_rows(session, job.field_id, result.rows)
            field = session.get(Field, job.field_id)
            if field is not None and field.elevation_m is None and result.elevation_m is not None:
                field.elevation_m = result.elevation_m

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
        logger.exception("POWER fetch job %s failed", job_id)
        job = session.get(DataFetchJob, job_id)
        job.status = JobStatus.FAILED
        job.error_message = str(error)[:ERROR_LIMIT]
        job.finished_at = datetime.now(UTC)
        source = session.get(DataSource, job.data_source_id)
        if source is not None:
            source.status = "error"
        session.commit()
    return job
