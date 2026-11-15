"""Field Memory: MODIS polygon statistics, the cropped or fallow call, and its confirmation.

The raster tests build small GeoTIFFs in the MODIS sinusoidal projection, so the polygon window,
the mask and the quality rule run for real without a network. The API tests insert NDVI rows
directly, and the job test replaces the catalogue and the pixel reader.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import numpy as np
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import DataFetchJob, DataSource, JobStatus, Role, SatelliteObservation
from app.services import field_memory as memory
from app.services import modis
from tests.test_fields_api import create_field
from tests.test_water_vault_api import store, weather

SINUSOIDAL = "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs"
PIXEL = 231.65635826395834
LON, LAT = 32.505, 37.905


# --- Polygon statistics -------------------------------------------------------------------


def test_only_clear_pixels_inside_the_polygon_count():
    ndvi = np.array([[5000, 6000, -3000], [7000, 2000, 3000], [4000, 4000, 4000]], dtype="int16")
    reliability = np.array([[0, 1, 0], [0, 3, 2], [0, 0, 1]], dtype="int8")
    inside = np.ones((3, 3), dtype=bool)
    mean, median, count, cloud, flag = modis.stats_from_arrays(ndvi, reliability, inside, -3000.0)
    # Left out: the fill value, the cloudy pixel (3) and the snow pixel (2).
    assert count == 6
    assert mean == pytest.approx(0.5)
    assert median == pytest.approx(0.45)
    assert cloud == pytest.approx(1 - 6 / 9)
    assert flag == "ok"


def test_a_mostly_cloudy_polygon_is_partial_and_a_covered_one_is_cloudy():
    ndvi = np.full((2, 2), 5000, dtype="int16")
    inside = np.ones((2, 2), dtype=bool)
    partial = modis.stats_from_arrays(ndvi, np.array([[0, 3], [3, 3]]), inside, -3000.0)
    assert partial[2] == 1 and partial[4] == "partial"
    cloudy = modis.stats_from_arrays(ndvi, np.full((2, 2), 3), inside, -3000.0)
    assert cloudy[0] is None and cloudy[2] == 0 and cloudy[4] == "cloudy"
    assert (
        modis.stats_from_arrays(ndvi, np.zeros((2, 2)), np.zeros((2, 2), bool), None)[4] == "cloudy"
    )


def _raster(tmp_path, name: str, array: np.ndarray, *, nodata=None) -> str:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_origin
    from rasterio.warp import transform

    crs = CRS.from_string(SINUSOIDAL)
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
        nodata=nodata,
    ) as dataset:
        dataset.write(array, 1)
    return path


def square(lon: float, half_lon: float = 0.006, half_lat: float = 0.004) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon - half_lon, LAT - half_lat],
                [lon + half_lon, LAT - half_lat],
                [lon + half_lon, LAT + half_lat],
                [lon - half_lon, LAT + half_lat],
                [lon - half_lon, LAT - half_lat],
            ]
        ],
    }


@pytest.fixture
def rasters(tmp_path):
    ndvi = np.full((20, 20), 2000, dtype="int16")
    ndvi[:, :10] = 6000  # the west half is green, the east half is bare
    ndvi_path = _raster(tmp_path, "ndvi.tif", ndvi, nodata=-3000)
    reliability_path = _raster(tmp_path, "rel.tif", np.zeros((20, 20), dtype="int8"))
    return ndvi_path, reliability_path


def test_a_polygon_in_the_green_half_reads_that_value(rasters):
    observation = modis.read_rasters(
        *rasters, square(LON - 0.02), scene_id="s1", image_date=date(2025, 5, 1)
    )
    assert observation.ndvi_mean == pytest.approx(0.6)
    assert observation.valid_pixel_count > 4
    assert observation.quality_flag == "ok"
    assert observation.scene_id == "s1"


def test_a_polygon_across_both_halves_lands_in_between(rasters):
    observation = modis.read_rasters(
        *rasters, square(LON), scene_id="s2", image_date=date(2025, 5, 1)
    )
    assert 0.2 < observation.ndvi_mean < 0.6


def test_a_tiny_field_still_reads_the_pixel_it_touches(rasters):
    observation = modis.read_rasters(
        *rasters, square(LON - 0.02, 0.0002, 0.0002), scene_id="s3", image_date=date(2025, 5, 1)
    )
    assert observation.valid_pixel_count >= 1
    assert observation.ndvi_mean == pytest.approx(0.6)


# --- The cropped or fallow call --------------------------------------------------------------


TODAY = date(2026, 11, 15)


def series(harvest_year: int, peak: float, *, every: int = 8) -> list[memory.Obs]:
    """Composites from March to September rising to ``peak`` in the middle of the window."""
    start, end = date(harvest_year, 3, 1), date(harvest_year, 9, 30)
    days = [start + timedelta(days=offset) for offset in range(0, (end - start).days + 1, every)]
    middle = (len(days) - 1) / 2  # an odd count puts a composite exactly at the peak
    return [
        memory.Obs(day, 0.1 + (peak - 0.1) * max(0.0, 1 - abs(i - middle) / middle), 10)
        for i, day in enumerate(days)
    ]


def test_the_last_ten_finished_seasons():
    assert memory.harvest_years(TODAY, 10) == list(range(2017, 2027))
    assert memory.harvest_years(date(2026, 6, 1), 10) == list(range(2016, 2026))
    assert memory.season_name(2026) == "2025-2026"
    assert modis.default_range(TODAY, 10) == (date(2016, 9, 1), TODAY)


def test_a_high_peak_is_cropped_and_a_low_one_is_fallow():
    obs = series(2024, 0.75) + series(2025, 0.2)
    by_year = {
        s.harvest_year: s for s in memory.detect(obs, threshold=0.4, history_years=10, today=TODAY)
    }
    cropped, fallow = by_year[2024], by_year[2025]
    assert cropped.state == memory.CROPPED and cropped.peak_ndvi == pytest.approx(0.75, abs=0.02)
    assert fallow.state == memory.FALLOW
    assert cropped.season == "2023-2024"
    # A clear margin and plenty of clear composites give full confidence.
    assert cropped.confidence == pytest.approx(1.0)
    assert memory.confidence_level(cropped.confidence) == "high"


def test_a_peak_near_the_threshold_is_less_certain():
    obs = series(2024, 0.45)
    season = next(
        s
        for s in memory.detect(obs, threshold=0.4, history_years=10, today=TODAY)
        if s.harvest_year == 2024
    )
    assert season.state == memory.CROPPED
    assert season.confidence == pytest.approx(0.25, abs=0.03)
    assert memory.confidence_level(season.confidence) == "low"


def test_too_few_clear_composites_leave_the_season_unknown():
    cloudy = [memory.Obs(o.day, None, 0) for o in series(2024, 0.8)]
    few = series(2025, 0.8, every=40)[:3]
    result = {
        s.harvest_year: s
        for s in memory.detect(cloudy + few, threshold=0.4, history_years=10, today=TODAY)
    }
    assert result[2024].state == memory.UNKNOWN and result[2024].confidence is None
    assert result[2025].state == memory.UNKNOWN
    assert result[2023].state == memory.UNKNOWN  # no data at all


def test_a_confirmed_history_becomes_strategy_a():
    assert memory.rotation_from_history(["cropped", "fallow", "cropped"]) == [
        "winter_wheat",
        None,
        "winter_wheat",
    ]


# --- The job ---------------------------------------------------------------------------------

pytestmark_db = pytest.mark.db


def _catalogue(items: list[dict]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"features": items})
        return httpx.Response(200, json={"token": "sv=x"})

    return httpx.Client(transport=httpx.MockTransport(handler))


def _items(count: int) -> list[dict]:
    return [
        {
            "id": f"MOD13Q1.A2025{100 + i * 8:03d}.h20v05",
            "properties": {
                "start_datetime": f"2025-{4 + i // 4:02d}-{1 + (i % 4) * 7:02d}T00:00:00Z"
            },
            "assets": {},
        }
        for i in range(count)
    ]


def _reader(item, token, geometry):
    day = modis._item_date(item)
    return modis.Observation(item["id"], day, 0.55, 0.54, 12, 0.1, "ok")


@pytest.mark.db
def test_a_fetch_job_stores_one_row_per_composite_and_is_safe_to_repeat(
    pg, pg_client, make_user, bearer
):
    make_user("admin@example.com", Role.ADMIN)
    created = create_field(pg_client, bearer("admin@example.com"))
    field_id = uuid.UUID(created["id"])
    with Session(pg) as db, db.begin():
        source = db.scalar(select(DataSource).where(DataSource.key == "modis"))
        job = DataFetchJob(
            field_id=field_id,
            data_source_id=source.id,
            date_from=date(2025, 3, 1),
            date_to=date(2025, 9, 30),
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        job_id = job.id

    for _ in range(2):
        with Session(pg) as db:
            finished = modis.run_fetch_job(db, job_id, client=_catalogue(_items(6)), reader=_reader)
            assert finished.status == JobStatus.DONE and finished.rows_written == 6
    with Session(pg) as db:
        assert db.query(SatelliteObservation).filter_by(field_id=field_id).count() == 6
        source = db.scalar(select(DataSource).where(DataSource.key == "modis"))
        assert source.status == "ok" and source.last_success_at is not None


@pytest.mark.db
def test_a_job_that_cannot_read_the_scenes_fails_with_a_reason(
    pg, pg_client, make_user, bearer, monkeypatch
):
    monkeypatch.setattr(modis.time, "sleep", lambda _s: None)
    make_user("admin@example.com", Role.ADMIN)
    created = create_field(pg_client, bearer("admin@example.com"))

    def broken(item, token, geometry):
        raise OSError("range request failed")

    with Session(pg) as db, db.begin():
        source = db.scalar(select(DataSource).where(DataSource.key == "modis"))
        job = DataFetchJob(
            field_id=uuid.UUID(created["id"]),
            data_source_id=source.id,
            date_from=date(2025, 3, 1),
            date_to=date(2025, 9, 30),
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        job_id = job.id
    with Session(pg) as db:
        finished = modis.run_fetch_job(db, job_id, client=_catalogue(_items(5)), reader=broken)
        assert finished.status == JobStatus.FAILED
        assert "could not be read" in finished.error_message
        assert db.scalar(select(DataSource).where(DataSource.key == "modis")).status == "error"


# --- The API -------------------------------------------------------------------------------------


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


def seed_ndvi(pg, field_id: str) -> None:
    """Alternating peaks for the ten seasons: cropped, fallow, cropped, ..."""
    today = datetime.now(UTC).date()
    rows = []
    for index, year in enumerate(memory.harvest_years(today, 10)):
        for obs in series(year, 0.75 if index % 2 == 0 else 0.2):
            rows.append(
                SatelliteObservation(
                    field_id=uuid.UUID(field_id),
                    source="modis",
                    image_date=obs.day,
                    scene_id=f"s-{obs.day.isoformat()}",
                    ndvi_mean=obs.ndvi,
                    valid_pixel_count=obs.valid_pixels,
                    cloud_fraction=0.0,
                    quality_flag="ok",
                )
            )
    with Session(pg) as db, db.begin():
        db.add_all(rows)


@pytest.mark.db
def test_the_history_is_detected_from_the_stored_ndvi(pg, pg_client, admin):
    field = create_field(pg_client, admin)["id"]
    seed_ndvi(pg, field)
    body = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=admin).json()
    assert body["provisional"] is True and body["threshold"] == 0.4
    assert len(body["seasons"]) == 10 and body["confirmed_count"] == 0
    states = [s["detected_state"] for s in body["seasons"]]
    assert states == ["cropped", "fallow"] * 5
    assert body["seasons"][0]["confidence_level"] == "high"
    assert body["coverage"]["good"] > 100 and body["series"]


@pytest.mark.db
def test_a_person_confirms_the_history_and_can_change_a_call(pg, pg_client, admin):
    field = create_field(pg_client, admin)["id"]
    seed_ndvi(pg, field)
    seasons = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=admin).json()["seasons"]
    payload = {"seasons": [{"season": s["season"], "state": s["detected_state"]} for s in seasons]}
    payload["seasons"][1]["state"] = "cropped"  # the farmer says it was cropped after all
    body = pg_client.post(
        f"/api/v1/fields/{field}/field-memory/confirm", json=payload, headers=admin
    ).json()
    assert body["confirmed_count"] == 10
    assert body["seasons"][1]["detected_state"] == "fallow"
    assert body["seasons"][1]["confirmed_state"] == "cropped"
    assert body["seasons"][1]["confirmed_by"] == "agronomist"
    bad = pg_client.post(
        f"/api/v1/fields/{field}/field-memory/confirm",
        json={"seasons": [{"season": "1999-2000", "state": "fallow"}]},
        headers=admin,
    )
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "unknown_season"


@pytest.mark.db
def test_a_cooperative_user_is_recorded_as_the_user(pg, pg_client, admin, make_user, bearer):
    make_user("coop@example.com", Role.COOPERATIVE_USER, "Koop")
    coop = bearer("coop@example.com")
    field = create_field(pg_client, coop)["id"]
    seed_ndvi(pg, field)
    seasons = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=coop).json()["seasons"]
    body = pg_client.post(
        f"/api/v1/fields/{field}/field-memory/confirm",
        json={"seasons": [{"season": seasons[0]["season"], "state": "cropped"}]},
        headers=coop,
    ).json()
    assert body["seasons"][0]["confirmed_by"] == "user"
    # Another person's field is not visible.
    other = create_field(pg_client, admin, name="Baska")["id"]
    assert pg_client.get(f"/api/v1/fields/{other}/field-memory", headers=coop).status_code == 404


@pytest.mark.db
def test_a_fetch_is_queued_once_at_a_time(pg, pg_client, admin, monkeypatch):
    queued = []
    recorder = type("T", (), {"delay": staticmethod(queued.append)})
    monkeypatch.setattr("app.api.field_memory.fetch_modis", recorder)
    monkeypatch.setattr("app.api.field_memory.fetch_landsat", recorder)
    field = create_field(pg_client, admin)["id"]
    url = f"/api/v1/fields/{field}/field-memory/fetch"

    first = pg_client.post(url, params={"source": "modis"}, headers=admin)
    assert first.status_code == 202 and [j["source"] for j in first.json()] == ["modis"]
    assert first.json()[0]["status"] == "queued" and len(queued) == 1
    assert pg_client.post(url, params={"source": "modis"}, headers=admin).status_code == 409
    latest = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=admin).json()
    assert latest["latest_job"]["status"] == "queued"

    # Landsat is a separate source, so it can be queued while MODIS is still waiting; "all"
    # then refuses because one of its sources is busy.
    both = pg_client.post(url, params={"source": "landsat"}, headers=admin)
    assert both.status_code == 202
    assert sorted(j["source"] for j in both.json()) == ["landsat8", "landsat9"]
    assert pg_client.post(url, headers=admin).status_code == 409


@pytest.mark.db
def test_all_sources_are_queued_by_default(pg, pg_client, admin, monkeypatch):
    queued = []
    recorder = type("T", (), {"delay": staticmethod(queued.append)})
    monkeypatch.setattr("app.api.field_memory.fetch_modis", recorder)
    monkeypatch.setattr("app.api.field_memory.fetch_landsat", recorder)
    field = create_field(pg_client, admin)["id"]
    response = pg_client.post(f"/api/v1/fields/{field}/field-memory/fetch", headers=admin)
    assert response.status_code == 202 and len(queued) == 3
    assert sorted(j["source"] for j in response.json()) == ["landsat8", "landsat9", "modis"]


@pytest.mark.db
def test_the_confirmed_history_drives_strategy_a(pg, pg_client, admin):
    field = create_field(pg_client, admin)["id"]
    with pg.begin() as connection:
        connection.execute(
            text("UPDATE fields SET elevation_m = 1000 WHERE id = :id"), {"id": field}
        )
    store(pg, field, weather(date(2001, 1, 1), date(2025, 12, 31), rain=3.0))
    seed_ndvi(pg, field)

    refused = pg_client.get(
        f"/api/v1/fields/{field}/rotation", params={"rotation": "history"}, headers=admin
    )
    assert (
        refused.status_code == 422 and refused.json()["detail"]["code"] == "history_not_confirmed"
    )

    seasons = pg_client.get(f"/api/v1/fields/{field}/field-memory", headers=admin).json()["seasons"]
    pg_client.post(
        f"/api/v1/fields/{field}/field-memory/confirm",
        json={"seasons": [{"season": s["season"], "state": s["detected_state"]} for s in seasons]},
        headers=admin,
    )
    body = pg_client.get(
        f"/api/v1/fields/{field}/rotation", params={"rotation": "history"}, headers=admin
    ).json()
    assert body["rotation"] == ["winter_wheat", None] * 5
    assert [s["key"] for s in body["strategies"]] == ["A", "B", "C"]


@pytest.mark.db
def test_the_data_center_shows_modis_as_connected(pg, pg_client, admin):
    field = create_field(pg_client, admin)["id"]
    sources = {
        s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=admin).json()
    }
    assert sources["modis"]["connected"] is True and sources["modis"]["status"] == "never_fetched"
    assert sources["landsat8"]["connected"] and sources["landsat9"]["connected"]
    assert sources["landsat8"]["status"] == "never_fetched"
    seed_ndvi(pg, field)
    sources = {
        s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=admin).json()
    }
    assert sources["modis"]["observations"] > 100


def test_a_raster_without_georeferencing_is_refused(tmp_path):
    import rasterio

    path = str(tmp_path / "bare.tif")
    with rasterio.open(
        path, "w", driver="GTiff", height=4, width=4, count=1, dtype="int16"
    ) as dataset:
        dataset.write(np.full((4, 4), 5000, dtype="int16"), 1)
    with pytest.raises(modis.ModisError, match="georeferencing"):
        modis.read_rasters(path, path, square(LON), scene_id="bare", image_date=date(2025, 5, 1))
