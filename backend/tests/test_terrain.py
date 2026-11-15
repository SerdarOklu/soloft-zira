"""Terrain from NASADEM: slope arithmetic, a real raster read, the job, and the API."""

from __future__ import annotations

import math
import uuid

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, Field, JobStatus, RegionalObservation, Role
from app.services import terrain
from tests.test_fields_api import create_field

LON, LAT = 33.04739, 39.09271
# 30 m pixels in degrees at this latitude.
PIXEL_X = 30.0 / (111_320.0 * math.cos(math.radians(LAT)))
PIXEL_Y = 30.0 / 110_574.0


def test_a_plane_rising_three_metres_per_pixel_has_a_known_slope():
    grid = 1000.0 + 3.0 * np.tile(np.arange(10.0), (10, 1))
    slope = terrain.slope_degrees(grid, pixel_deg_x=PIXEL_X, pixel_deg_y=PIXEL_Y, latitude=LAT)
    assert slope[5, 5] == pytest.approx(math.degrees(math.atan(3 / 30)), abs=0.01)  # 5.71 degrees


def test_the_fill_value_is_left_out_of_the_statistics():
    grid = np.array([[100.0, 100.0, 100.0], [100.0, -32768.0, 110.0], [100.0, 110.0, 110.0]])
    inside = np.ones((3, 3), dtype=bool)
    result = terrain.stats_from_arrays(
        grid, inside, -32768.0, pixel_deg_x=PIXEL_X, pixel_deg_y=PIXEL_Y, latitude=LAT
    )
    assert (
        result.pixels == 8 and result.elevation_min_m == 100.0 and result.elevation_max_m == 110.0
    )
    assert result.elevation_m == pytest.approx((100 * 5 + 110 * 3) / 8)
    nothing = terrain.stats_from_arrays(
        grid,
        np.zeros((3, 3), bool),
        -32768.0,
        pixel_deg_x=PIXEL_X,
        pixel_deg_y=PIXEL_Y,
        latitude=LAT,
    )
    assert nothing is None


@pytest.fixture
def dem(tmp_path):
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_origin

    rows = cols = 60
    elevation = (1000.0 + 3.0 * np.tile(np.arange(cols), (rows, 1))).astype("int16")
    path = str(tmp_path / "dem.tif")
    origin = from_origin(LON - cols / 2 * PIXEL_X, LAT + rows / 2 * PIXEL_Y, PIXEL_X, PIXEL_Y)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="int16",
        crs=CRS.from_epsg(4326),
        transform=origin,
        nodata=-32768,
    ) as dataset:
        dataset.write(elevation, 1)
    return path


def polygon(half_lon: float = 0.003, half_lat: float = 0.002) -> dict:
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


def test_the_polygon_gives_elevation_and_slope(dem):
    result = terrain.read_terrain(dem, polygon(), latitude=LAT)
    # The centre column is 30, so the plane there is about 1000 + 3 * 30 = 1090 m.
    assert 1080 < result.elevation_m < 1100
    assert result.elevation_min_m < result.elevation_m < result.elevation_max_m
    assert result.slope_deg == pytest.approx(5.71, abs=0.1)
    assert result.pixels > 20


def test_a_raster_without_georeferencing_is_refused(tmp_path):
    import rasterio

    path = str(tmp_path / "bare.tif")
    with rasterio.open(path, "w", driver="GTiff", height=4, width=4, count=1, dtype="int16") as ds:
        ds.write(np.full((4, 4), 900, dtype="int16"), 1)
    with pytest.raises(terrain.ModisError, match="georeferencing"):
        terrain.read_terrain(path, polygon(), latitude=LAT)


def _catalogue(empty: bool = False) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            items = (
                []
                if empty
                else [
                    {
                        "id": "NASADEM_HGT_n39e033",
                        "assets": {"elevation": {"href": "https://x/y.tif"}},
                    }
                ]
            )
            return httpx.Response(200, json={"features": items})
        return httpx.Response(200, json={"token": "sv=x"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _fake_reader(path, geometry, *, latitude):
    return terrain.Terrain(1090.0, 1060.0, 1120.0, 5.7, 24)


def _job(pg, field_id: str) -> uuid.UUID:
    with Session(pg) as db, db.begin():
        source = db.scalar(select(DataSource).where(DataSource.key == "srtm"))
        job = DataFetchJob(
            field_id=uuid.UUID(field_id), data_source_id=source.id, status=JobStatus.QUEUED
        )
        db.add(job)
        db.flush()
        return job.id


@pytest.mark.db
def test_the_job_stores_four_values_and_fills_a_missing_elevation(
    pg, pg_client: TestClient, make_user, bearer
):
    make_user("admin@example.com", Role.ADMIN)
    field = create_field(pg_client, bearer("admin@example.com"))["id"]
    for _ in range(2):  # safe to repeat
        with Session(pg) as db:
            done = terrain.run_fetch_job(
                db, _job(pg, field), client=_catalogue(), reader=_fake_reader
            )
            assert done.status == JobStatus.DONE and done.rows_written == 4
    with Session(pg) as db:
        rows = db.scalars(
            select(RegionalObservation).where(RegionalObservation.field_id == uuid.UUID(field))
        ).all()
        assert {r.variable: r.value for r in rows} == {
            "elevation_m": 1090.0,
            "elevation_min_m": 1060.0,
            "elevation_max_m": 1120.0,
            "slope_deg": 5.7,
        }
        assert db.get(Field, uuid.UUID(field)).elevation_m == 1090.0  # none from POWER yet


@pytest.mark.db
def test_a_power_elevation_is_not_overwritten(pg, pg_client: TestClient, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    field = create_field(pg_client, bearer("admin@example.com"))["id"]
    with Session(pg) as db, db.begin():
        db.get(Field, uuid.UUID(field)).elevation_m = 1215.6
    with Session(pg) as db:
        terrain.run_fetch_job(db, _job(pg, field), client=_catalogue(), reader=_fake_reader)
        assert db.get(Field, uuid.UUID(field)).elevation_m == 1215.6


@pytest.mark.db
def test_a_place_without_a_tile_fails_with_a_reason(pg, pg_client: TestClient, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    field = create_field(pg_client, bearer("admin@example.com"))["id"]
    with Session(pg) as db:
        failed = terrain.run_fetch_job(
            db, _job(pg, field), client=_catalogue(empty=True), reader=_fake_reader
        )
        assert failed.status == JobStatus.FAILED and "NASADEM tile" in failed.error_message


@pytest.mark.db
def test_the_api_queues_once_and_reads_back(
    pg, pg_client: TestClient, make_user, bearer, monkeypatch
):
    queued = []
    monkeypatch.setattr(
        "app.api.terrain.fetch_field_terrain", type("T", (), {"delay": staticmethod(queued.append)})
    )
    make_user("admin@example.com", Role.ADMIN)
    headers = bearer("admin@example.com")
    field = create_field(pg_client, headers)["id"]
    empty = pg_client.get(f"/api/v1/fields/{field}/terrain", headers=headers).json()
    assert empty["available"] is False and empty["elevation_m"] is None

    first = pg_client.post(f"/api/v1/fields/{field}/terrain/fetch", headers=headers)
    assert first.status_code == 202 and first.json()["source"] == "srtm" and len(queued) == 1
    assert (
        pg_client.post(f"/api/v1/fields/{field}/terrain/fetch", headers=headers).status_code == 409
    )

    with Session(pg) as db:
        job_id = db.scalar(select(DataFetchJob.id).where(DataFetchJob.field_id == uuid.UUID(field)))
        terrain.run_fetch_job(db, job_id, client=_catalogue(), reader=_fake_reader)
    body = pg_client.get(f"/api/v1/fields/{field}/terrain", headers=headers).json()
    assert body["available"] and body["elevation_m"] == 1090.0 and body["slope_deg"] == 5.7
    assert body["latest_job"]["status"] == "done"
    sources = {
        s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=headers).json()
    }
    assert sources["srtm"]["connected"] is True and sources["srtm"]["observations"] == 4
    assert (
        pg_client.get(f"/api/v1/fields/{uuid.uuid4()}/terrain", headers=headers).status_code == 404
    )
