"""Landsat 8 and 9 NDVI: the arithmetic, a real raster read (small local GeoTIFFs in UTM), the job,
and Field Memory choosing Landsat over MODIS when it covers enough seasons."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, JobStatus, Role, SatelliteObservation
from app.services import field_memory as memory
from app.services import landsat
from tests.test_field_memory import series
from tests.test_fields_api import create_field

LON, LAT = 33.04739, 39.09271
PIXEL = 30.0


def dn(reflectance: float) -> int:
    return round((reflectance + 0.2) / landsat.SR_SCALE)


# --- The arithmetic ---------------------------------------------------------------------------


def test_ndvi_comes_from_surface_reflectance_of_clear_pixels():
    red = np.array([[dn(0.05), dn(0.10), 0], [dn(0.05), dn(0.05), dn(0.05)]], dtype="uint16")
    nir = np.array([[dn(0.55), dn(0.30), 0], [dn(0.55), dn(0.55), dn(0.55)]], dtype="uint16")
    qa = np.zeros((2, 3), dtype="uint16")
    qa[1, 0] = 1 << 3  # cloud
    qa[1, 1] = 1 << 4  # cloud shadow
    qa[1, 2] = 1 << 5  # snow
    inside = np.ones((2, 3), dtype=bool)
    mean, median, count, cloud, flag = landsat.stats_from_arrays(red, nir, qa, inside)
    # Clear: the first two pixels only (the third is fill, the others are cloud, shadow and snow).
    first = (0.55 - 0.05) / (0.55 + 0.05)
    second = (0.30 - 0.10) / (0.30 + 0.10)
    assert count == 2
    assert mean == pytest.approx((first + second) / 2, abs=1e-3)
    assert median == pytest.approx((first + second) / 2, abs=1e-3)
    assert cloud == pytest.approx(1 - 2 / 6)
    assert flag == "partial"  # two thirds of the polygon was not usable


def test_a_mostly_cloudy_polygon_is_partial_and_a_covered_one_is_cloudy():
    red = np.full((2, 2), dn(0.05), dtype="uint16")
    nir = np.full((2, 2), dn(0.5), dtype="uint16")
    inside = np.ones((2, 2), dtype=bool)
    qa = np.array([[0, 8], [8, 8]], dtype="uint16")
    assert landsat.stats_from_arrays(red, nir, qa, inside)[4] == "partial"
    assert landsat.stats_from_arrays(red, nir, np.full((2, 2), 8, "uint16"), inside)[4] == "cloudy"
    assert landsat.stats_from_arrays(red, nir, qa, np.zeros((2, 2), bool))[4] == "cloudy"


# --- A real raster read -----------------------------------------------------------------------


def _utm_raster(tmp_path, name: str, array: np.ndarray) -> str:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_origin
    from rasterio.warp import transform

    crs = CRS.from_epsg(32636)
    x, y = transform("EPSG:4326", crs, [LON], [LAT])
    rows, cols = array.shape
    origin = from_origin(x[0] - cols / 2 * PIXEL, y[0] + rows / 2 * PIXEL, PIXEL, PIXEL)
    path = str(tmp_path / name)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype=array.dtype,
        crs=crs,
        transform=origin,
    ) as dataset:
        dataset.write(array, 1)
    return path


def square(half_lon: float = 0.003, half_lat: float = 0.002) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [LON - half_lon, LAT - half_lat],
                [LON + half_lon, LAT - half_lat],
                [LON + half_lon, LAT + half_lat],
                [LON - half_lon, LAT + half_lat],
                [LON - half_lon, LAT - half_lat],
            ]
        ],
    }


@pytest.fixture
def scene(tmp_path):
    shape = (40, 40)
    red = _utm_raster(tmp_path, "red.tif", np.full(shape, dn(0.05), dtype="uint16"))
    nir = _utm_raster(tmp_path, "nir.tif", np.full(shape, dn(0.55), dtype="uint16"))
    qa_array = np.zeros(shape, dtype="uint16")
    qa = _utm_raster(tmp_path, "qa.tif", qa_array)
    return red, nir, qa, tmp_path, shape


def test_the_polygon_is_read_from_all_three_rasters(scene):
    red, nir, qa, _, _ = scene
    observation = landsat.read_rasters(
        red, nir, qa, square(), scene_id="LC08_x", image_date=date(2025, 5, 1)
    )
    assert observation.ndvi_mean == pytest.approx((0.55 - 0.05) / 0.60, abs=1e-3)
    assert observation.valid_pixel_count > 20  # about 18 by 15 pixels of 30 m
    assert observation.quality_flag == "ok" and observation.cloud_fraction == 0.0


def test_cloud_in_the_quality_band_removes_those_pixels(scene):
    red, nir, _, tmp_path, shape = scene
    cloudy = np.zeros(shape, dtype="uint16")
    cloudy[:, : shape[1] // 2] = 1 << 3  # the west half is cloud
    qa = _utm_raster(tmp_path, "qa_cloud.tif", cloudy)
    clear = landsat.read_rasters(
        red,
        nir,
        _utm_raster(tmp_path, "qa_clear.tif", np.zeros(shape, "uint16")),
        square(),
        scene_id="a",
        image_date=date(2025, 5, 1),
    )
    half = landsat.read_rasters(red, nir, qa, square(), scene_id="b", image_date=date(2025, 5, 1))
    assert 0.3 < half.cloud_fraction < 0.7
    assert half.valid_pixel_count < clear.valid_pixel_count


def test_a_raster_without_georeferencing_is_refused(tmp_path):
    import rasterio

    path = str(tmp_path / "bare.tif")
    with rasterio.open(path, "w", driver="GTiff", height=4, width=4, count=1, dtype="uint16") as ds:
        ds.write(np.full((4, 4), 9000, dtype="uint16"), 1)
    with pytest.raises(landsat.ModisError, match="georeferencing"):
        landsat.read_rasters(path, path, path, square(), scene_id="x", image_date=date(2025, 5, 1))


# --- The job ----------------------------------------------------------------------------------


def _catalogue(by_platform: dict[str, int]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            platform = json.loads(request.content)["query"]["platform"]["eq"]
            items = [
                {
                    "id": f"{platform}-{i}",
                    "properties": {"datetime": f"2025-0{4 + i // 3}-{10 + (i % 3) * 5}T08:00:00Z"},
                    "assets": {},
                }
                for i in range(by_platform.get(platform, 0))
            ]
            return httpx.Response(200, json={"features": items})
        return httpx.Response(200, json={"token": "sv=x"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _reader(item, token, geometry):
    return landsat.Observation(item["id"], landsat._item_date(item), 0.62, 0.6, 40, 0.05, "ok")


def _job(pg, field_id: str, key: str) -> uuid.UUID:
    with Session(pg) as db, db.begin():
        source = db.scalar(select(DataSource).where(DataSource.key == key))
        job = DataFetchJob(
            field_id=uuid.UUID(field_id),
            data_source_id=source.id,
            date_from=date(2025, 3, 1),
            date_to=date(2025, 9, 30),
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        return job.id


@pytest.mark.db
def test_each_platform_is_stored_under_its_own_source(pg, pg_client, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    field = create_field(pg_client, bearer("admin@example.com"))["id"]
    client = _catalogue({"landsat-8": 5, "landsat-9": 0})

    with Session(pg) as db:
        done = landsat.run_fetch_job(db, _job(pg, field, "landsat8"), client=client, reader=_reader)
        assert done.status == JobStatus.DONE and done.rows_written == 5
    with Session(pg) as db:
        # Landsat 9 has no scene for the period: nothing to read, which is not a failure.
        done = landsat.run_fetch_job(db, _job(pg, field, "landsat9"), client=client, reader=_reader)
        assert done.status == JobStatus.DONE and done.rows_written == 0
    with Session(pg) as db:
        rows = db.scalars(
            select(SatelliteObservation).where(SatelliteObservation.field_id == uuid.UUID(field))
        ).all()
        assert {r.source for r in rows} == {"landsat8"} and len(rows) == 5
        assert db.scalar(select(DataSource).where(DataSource.key == "landsat8")).status == "ok"


@pytest.mark.db
def test_a_job_for_the_wrong_source_fails_with_a_reason(pg, pg_client, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    field = create_field(pg_client, bearer("admin@example.com"))["id"]
    with Session(pg) as db:
        failed = landsat.run_fetch_job(
            db, _job(pg, field, "modis"), client=_catalogue({}), reader=_reader
        )
        assert failed.status == JobStatus.FAILED and "not for Landsat" in failed.error_message


# --- Field Memory prefers Landsat when it covers the seasons ----------------------------------


def _seed(pg, field_id: str, source: str, years_and_peaks: list[tuple[int, float]], every: int):
    rows = []
    for year, peak in years_and_peaks:
        for obs in series(year, peak, every=every):
            rows.append(
                SatelliteObservation(
                    field_id=uuid.UUID(field_id),
                    source=source,
                    image_date=obs.day,
                    scene_id=f"{source}-{obs.day.isoformat()}",
                    ndvi_mean=obs.ndvi,
                    valid_pixel_count=obs.valid_pixels,
                    cloud_fraction=0.0,
                    quality_flag="ok",
                )
            )
    with Session(pg) as db, db.begin():
        db.add_all(rows)


@pytest.mark.db
def test_landsat_is_used_when_it_covers_enough_seasons(pg, pg_client, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    headers = bearer("admin@example.com")
    field = create_field(pg_client, headers)["id"]
    years = memory.harvest_years(datetime.now(UTC).date(), 10)
    # MODIS says fallow every season; Landsat (every 16 days) alternates cropped and fallow.
    _seed(pg, field, "modis", [(y, 0.2) for y in years], every=8)
    _seed(
        pg,
        field,
        "landsat8",
        [(y, 0.75 if i % 2 == 0 else 0.2) for i, y in enumerate(years)],
        every=16,
    )

    auto = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=headers).json()
    assert auto["source"] == "landsat"
    assert [s["detected_state"] for s in auto["seasons"]] == ["cropped", "fallow"] * 5
    assert auto["available_sources"]["landsat"] > 50 and auto["available_sources"]["modis"] > 100

    modis_only = pg_client.get(
        f"/api/v1/fields/{field}/field-memory", params={"source": "modis"}, headers=headers
    ).json()
    assert modis_only["source"] == "modis"
    assert {s["detected_state"] for s in modis_only["seasons"]} == {"fallow"}


@pytest.mark.db
def test_a_thin_landsat_record_falls_back_to_modis(pg, pg_client, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    headers = bearer("admin@example.com")
    field = create_field(pg_client, headers)["id"]
    years = memory.harvest_years(datetime.now(UTC).date(), 10)
    _seed(
        pg, field, "modis", [(y, 0.75 if i % 2 == 0 else 0.2) for i, y in enumerate(years)], every=8
    )
    _seed(pg, field, "landsat9", [(years[-1], 0.7)], every=16)  # one season only
    body = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=headers).json()
    assert body["source"] == "modis"
    assert body["available_sources"]["landsat"] > 0


@pytest.mark.db
def test_a_field_with_no_satellite_data_still_answers(pg, pg_client, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    headers = bearer("admin@example.com")
    field = create_field(pg_client, headers)["id"]
    body = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=headers).json()
    assert body["source"] == "modis" and body["available_sources"] == {"modis": 0, "landsat": 0}
    assert {s["detected_state"] for s in body["seasons"]} == {"unknown"}
    _ = TestClient
