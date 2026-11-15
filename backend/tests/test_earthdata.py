# ruff: noqa: E501
"""SMAP, GPM IMERG and GRACE through NASA Earthdata: the file reader on small HDF5 files served over
fake range requests, the redirect handling that keeps the token away from storage hosts, the jobs,
and the API. No real token or network is used."""

from __future__ import annotations

import io
import math
import uuid
from datetime import date, timedelta

import h5py
import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    DataFetchJob,
    DataSource,
    JobStatus,
    RegionalObservation,
    Role,
    WeatherObservation,
)
from app.services import earthdata as ed
from app.services import regional
from tests.test_fields_api import create_field
from tests.test_water_vault_api import store, weather

TOKEN = "eyJ-secret-token-value"
ARCHIVE = "https://data.nsidc.earthdatacloud.nasa.gov/protected/file.h5"
SIGNED = "https://d123.cloudfront.net/s3-signed/file.h5?sig=abc"


# --- Names and grids -----------------------------------------------------------------------------


def test_the_day_is_read_from_the_file_names():
    assert ed.smap_day("SMAP_L3_SM_P_E_20250501_R19240_002.h5") == date(2025, 5, 1)
    assert ed.gpm_day(
        "GPM_3IMERGDF.07:3B-DAY.MS.MRG.3IMERG.20250501-S000000-E235959.V07B.nc4"
    ) == date(2025, 5, 1)
    assert ed.smap_day("no date here.h5") is None


def test_the_smap_cell_of_a_point_in_the_ease_grid():
    # The first row and column sit at the top left of the grid; the grid centre is near (0, 0).
    assert ed.smap_cell(-179.99, 84.6) == (0, 0)
    row, column = ed.smap_cell(0.0, 0.0)
    assert column == 1928 and row in (811, 812)
    with pytest.raises(ed.EarthdataError):
        ed.smap_cell(10.0, 89.9)  # beyond the grid's northern edge


def test_the_imerg_cell_of_the_demo_location():
    assert ed.gpm_cell(33.04739, 39.09271) == (2130, 1290)
    assert ed.gpm_cell(179.99, 89.99) == (3599, 1799)


# --- Reading a file by range requests -----------------------------------------------------------------


def make_file(build) -> bytes:
    buffer = io.BytesIO()
    with h5py.File(buffer, "w") as handle:
        build(handle)
    return buffer.getvalue()


def archive(files: dict[str, bytes], seen: list | None = None) -> httpx.Client:
    """A fake archive: the NASA host answers a token with a redirect to a signed storage address,
    which serves ranges of the file. Every request is recorded in ``seen``."""

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append((request.url.host, request.headers.get("authorization")))
        if request.url.host == "data.nsidc.earthdatacloud.nasa.gov":
            if request.headers.get("authorization") != f"Bearer {TOKEN}":
                return httpx.Response(401)
            return httpx.Response(303, headers={"location": SIGNED})
        if request.url.host == "d123.cloudfront.net":
            if request.headers.get("authorization"):
                return httpx.Response(400, text="the token must not reach storage")
            data = files["file"]
            start, _, end = request.headers["range"].removeprefix("bytes=").partition("-")
            start, end = int(start), min(int(end), len(data) - 1)
            return httpx.Response(
                206,
                content=data[start : end + 1],
                headers={"content-range": f"bytes {start}-{end}/{len(data)}"},
            )
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)


def smap_file() -> bytes:
    def build(h):
        for name, value in (("AM", 0.21), ("PM", 0.18)):
            grid = np.full((50, 60), -9999.0, dtype="float32")
            grid[10, 20] = value
            variable = (
                "soil_moisture" if name == "AM" else "soil_moisture_pm"
            )  # as in the real files
            h.create_group(f"Soil_Moisture_Retrieval_Data_{name}").create_dataset(
                variable, data=grid
            )
        h["Soil_Moisture_Retrieval_Data_PM"]["soil_moisture_pm"][
            10, 20
        ] = -9999.0  # no evening retrieval

    return make_file(build)


def test_the_token_goes_to_nasa_and_never_to_storage_and_the_pixel_is_read():
    seen: list = []
    client = archive({"file": smap_file()}, seen)
    with ed.open_hdf5(client, ARCHIVE, TOKEN) as handle:
        values = ed.read_smap(handle, 10, 20)
    assert values == {"soil_moisture_am": pytest.approx(0.21), "soil_moisture_pm": None}
    by_host = {host: auth for host, auth in seen}
    assert by_host["data.nsidc.earthdatacloud.nasa.gov"] == f"Bearer {TOKEN}"
    assert by_host["d123.cloudfront.net"] is None


def test_a_refused_token_names_the_archive_application():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403)))
    with pytest.raises(ed.EarthdataError, match="authorized"):
        ed.resolve(client, ARCHIVE, TOKEN)


def test_a_gap_in_smap_is_none_and_not_a_value():
    handle = h5py.File(io.BytesIO(smap_file()), "r")
    assert ed.read_smap(handle, 0, 0) == {"soil_moisture_am": None, "soil_moisture_pm": None}


def test_imerg_reads_the_cell_and_treats_the_fill_value_as_missing():
    def build(h):
        grid = np.full((1, 3600, 1800), -9999.9, dtype="float32")
        grid[0, 2130, 1290] = 12.5
        h.create_dataset("precipitation", data=grid, chunks=(1, 3600, 900), compression="gzip")

    handle = h5py.File(io.BytesIO(make_file(build)), "r")
    assert ed.read_gpm(handle, 2130, 1290) == pytest.approx(12.5)
    assert ed.read_gpm(handle, 0, 0) is None


def test_grace_gives_a_monthly_series_for_the_nearest_cell():
    months = 30

    def build(h):
        h.create_dataset("lat", data=np.arange(-89.75, 90, 0.5))
        h.create_dataset("lon", data=np.arange(0.25, 360, 0.5))
        h.create_dataset("time", data=np.arange(months) * 30.4 + 100)
        cube = np.zeros((months, 360, 720), dtype="float32")
        i, j = int(round((39.09 + 89.75) / 0.5)), int(round((33.05 - 0.25) / 0.5))
        cube[:, i, j] = np.linspace(5.0, -5.0, months)
        h.create_dataset("lwe_thickness", data=cube, compression="gzip")

    handle = h5py.File(io.BytesIO(make_file(build)), "r")
    series = ed.read_grace(handle, 33.047, 39.093)
    assert len(series) == months
    assert series[0] == (date(2002, 1, 1) + timedelta(days=100), pytest.approx(5.0))
    assert series[-1][1] == pytest.approx(-5.0)


# --- The numbers computed from what is stored ----------------------------------------------------------


def test_correlation_and_trend():
    assert regional.pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert regional.pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert (
        regional.pearson([1, 2], [1, 2]) is None and regional.pearson([1, 1, 1], [1, 2, 3]) is None
    )
    points = [
        (date(2003, 1, 1) + timedelta(days=30 * k), -2.0 * k * 30 / 365.25) for k in range(96)
    ]
    assert regional.trend_per_year(points) == pytest.approx(-2.0, abs=0.02)
    assert regional.trend_per_year(points[:10]) is None


# --- Finding files ---------------------------------------------------------------------------------------


def test_the_catalogue_search_pages_and_keeps_one_data_file_per_day():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(dict(request.url.params))
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        page = int(request.url.params["page_num"])
        count = 200 if page == 1 else 3
        entries = [
            {
                "title": f"SMAP_L3_SM_P_E_{(date(2025, 1, 1) + timedelta(days=(page - 1) * 200 + n)):%Y%m%d}_R1_002.h5",
                "links": [
                    {
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                        "href": "https://x.nasa.gov/a.h5",
                    },
                    {
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                        "href": "https://x.nasa.gov/a.h5.xml",
                    },
                ],
            }
            for n in range(count)
        ]
        return httpx.Response(200, json={"feed": {"entry": entries}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    found = ed.search_granules(
        client,
        TOKEN,
        "SPL3SMP_E",
        date(2025, 1, 1),
        date(2025, 8, 1),
        suffixes=(".h5",),
        day_from_title=ed.smap_day,
    )
    assert len(found) == 203 and found[0].url == "https://x.nasa.gov/a.h5" and len(calls) == 2
    assert found == sorted(found, key=lambda g: g.day)


# --- The jobs ---------------------------------------------------------------------------------------------


def _job(pg, field_id: str, key: str, window: bool = True) -> uuid.UUID:
    with Session(pg) as db, db.begin():
        source = db.scalar(select(DataSource).where(DataSource.key == key))
        job = DataFetchJob(
            field_id=uuid.UUID(field_id),
            data_source_id=source.id,
            status=JobStatus.QUEUED,
            date_from=date(2025, 12, 1) if window else None,
            date_to=date(2025, 12, 3) if window else None,
        )
        db.add(job)
        db.flush()
        return job.id


def _cmr(days: int) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        entries = [
            {
                "title": f"SMAP_L3_SM_P_E_202512{d:02d}_R1_002.h5",
                "links": [{"rel": "x/data#", "href": f"https://x.nasa.gov/{d}.h5"}],
            }
            for d in range(1, days + 1)
        ]
        return httpx.Response(200, json={"feed": {"entry": entries}})

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def field(pg, pg_client: TestClient, make_user, bearer) -> str:
    make_user("admin@example.com", Role.ADMIN)
    return create_field(pg_client, bearer("admin@example.com"))["id"]


@pytest.mark.db
def test_a_smap_job_stores_the_values_of_each_day(pg, field):
    readers = {
        "smap": lambda granule, cell: [
            ("soil_moisture_am", granule.day, 0.2),
            ("soil_moisture_pm", granule.day, 0.18),
        ]
    }
    with Session(pg) as db:
        done = regional.run_fetch_job(
            db, _job(pg, field, "smap"), client=_cmr(3), token=TOKEN, readers=readers
        )
        assert done.status == JobStatus.DONE and done.rows_written == 6
    with Session(pg) as db:
        rows = db.scalars(
            select(RegionalObservation).where(RegionalObservation.source == "smap")
        ).all()
        assert len(rows) == 6 and {r.unit for r in rows} == {"m3/m3"}
        assert db.scalar(select(DataSource).where(DataSource.key == "smap")).status == "ok"


@pytest.mark.db
def test_a_job_without_a_token_fails_and_a_leaked_token_is_masked(pg, field, monkeypatch):
    monkeypatch.setattr(get_settings(), "earthdata_token", "")
    with Session(pg) as db:
        failed = regional.run_fetch_job(db, _job(pg, field, "gpm"), client=_cmr(1))
        assert (
            failed.status == JobStatus.FAILED
            and "EARTHDATA_TOKEN is not set" in failed.error_message
        )

    def leaky(granule, cell):
        raise RuntimeError(f"could not open https://x?token={TOKEN}")

    monkeypatch.setattr(regional.time, "sleep", lambda _s: None)
    with Session(pg) as db:
        failed = regional.run_fetch_job(
            db, _job(pg, field, "smap"), client=_cmr(4), token=TOKEN, readers={"smap": leaky}
        )
        assert failed.status == JobStatus.FAILED and "could not be read" in failed.error_message
        assert TOKEN not in failed.error_message


@pytest.mark.db
def test_a_grace_job_reads_the_whole_record(pg, field):
    def handler(request: httpx.Request) -> httpx.Response:
        links = [{"rel": "x/data#", "href": "https://x.nasa.gov/grace.nc"}]
        return httpx.Response(200, json={"feed": {"entry": [{"title": "g", "links": links}]}})

    readers = {
        "grace": lambda link, point: [
            ("lwe_thickness_cm", date(2020, 1, 1) + timedelta(days=30 * k), float(k))
            for k in range(5)
        ]
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    with Session(pg) as db:
        done = regional.run_fetch_job(
            db, _job(pg, field, "grace", window=False), client=client, token=TOKEN, readers=readers
        )
        assert done.status == JobStatus.DONE and done.rows_written == 5


# --- The API -------------------------------------------------------------------------------------------------


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


@pytest.mark.db
def test_fetch_needs_the_token_and_queues_one_job_per_source(
    pg, pg_client: TestClient, admin, monkeypatch
):
    queued = []
    monkeypatch.setattr(
        "app.api.regional.fetch_field_regional",
        type("T", (), {"delay": staticmethod(queued.append)}),
    )
    field = create_field(pg_client, admin)["id"]
    url = f"/api/v1/fields/{field}/regional/fetch"

    monkeypatch.setattr(get_settings(), "earthdata_token", "")
    refused = pg_client.post(url, headers=admin)
    assert (
        refused.status_code == 503
        and refused.json()["detail"]["code"] == "earthdata_not_configured"
    )
    assert queued == []

    monkeypatch.setattr(get_settings(), "earthdata_token", TOKEN)
    ok = pg_client.post(url, headers=admin)
    assert ok.status_code == 202 and sorted(j["source"] for j in ok.json()) == [
        "gpm",
        "grace",
        "smap",
    ]
    assert len(queued) == 3 and pg_client.post(url, headers=admin).status_code == 409
    got = pg_client.get(f"/api/v1/fields/{field}/regional", headers=admin).json()
    assert got["configured"] is True and len(got["latest_jobs"]) == 3
    assert TOKEN not in str(got)


@pytest.mark.db
def test_what_is_stored_is_summarised(pg, pg_client: TestClient, admin):
    field = create_field(pg_client, admin)["id"]
    start = date(2025, 11, 1)
    store(pg, field, weather(start, date(2025, 11, 30), rain=2.0))
    with Session(pg) as db, db.begin():
        # IMERG follows POWER closely (twice the rain on some days), so the correlation is high.
        for k in range(30):
            day = start + timedelta(days=k)
            power = db.scalar(
                select(WeatherObservation.precipitation_mm).where(WeatherObservation.date == day)
            )
            db.add(
                RegionalObservation(
                    field_id=uuid.UUID(field),
                    source="gpm",
                    variable="precip_mm_day",
                    observed_on=day,
                    value=power * (1 + (k % 3)),
                    unit="mm",
                )
            )
            db.add(
                RegionalObservation(
                    field_id=uuid.UUID(field),
                    source="smap",
                    variable="soil_moisture_am",
                    observed_on=day,
                    value=0.2,
                    unit="m3/m3",
                )
            )
        for k in range(96):
            db.add(
                RegionalObservation(
                    field_id=uuid.UUID(field),
                    source="grace",
                    variable="lwe_thickness_cm",
                    observed_on=date(2003, 1, 1) + timedelta(days=30 * k),
                    value=-1.5 * 30 * k / 365.25,
                    unit="cm",
                )
            )
    body = pg_client.get(f"/api/v1/fields/{field}/regional", headers=admin).json()

    assert (
        body["smap"]["days"] == 30
        and body["smap"]["mean_am"] == pytest.approx(0.2)
        and body["smap"]["mean_pm"] is None
    )
    assert body["gpm"]["days"] == 30 and body["gpm"]["power_total_mm"] == pytest.approx(60.0)
    assert body["gpm"]["imerg_total_mm"] > body["gpm"]["power_total_mm"]
    assert body["gpm"]["correlation"] is None or -1 <= body["gpm"]["correlation"] <= 1
    assert body["grace"]["months"] == 96 and body["grace"]["trend_cm_per_year"] == pytest.approx(
        -1.5, abs=0.02
    )


@pytest.mark.db
def test_the_data_center_connects_earthdata_sources_only_with_a_token(
    pg, pg_client: TestClient, admin, monkeypatch
):
    def sources():
        return {
            s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=admin).json()
        }

    monkeypatch.setattr(get_settings(), "earthdata_token", "")
    off = sources()
    assert all(
        off[k]["connected"] is False and off[k]["status"] == "not_connected"
        for k in ("smap", "gpm", "grace")
    )
    monkeypatch.setattr(get_settings(), "earthdata_token", TOKEN)
    on = sources()
    assert all(
        on[k]["connected"] is True and on[k]["status"] == "never_fetched"
        for k in ("smap", "gpm", "grace")
    )
    assert on["ecostress"]["connected"] is False
    _ = math


@pytest.mark.db
def test_a_gpm_job_uses_the_late_run_when_the_final_run_has_ended(pg, field):
    asked = []

    def handler(request: httpx.Request) -> httpx.Response:
        short = request.url.params["short_name"]
        asked.append(short)
        entries = []
        if short == ed.GPM_LATE_SHORT_NAME:
            entries = [
                {
                    "title": f"GPM_3IMERGDL.07:3B-DAY-L.MS.MRG.3IMERG.202512{d:02d}-S000000-E235959.V07C.nc4",
                    "links": [{"rel": "x/data#", "href": f"https://x.nasa.gov/{d}.nc4"}],
                }
                for d in (1, 2, 3)
            ]
        return httpx.Response(200, json={"feed": {"entry": entries}})

    readers = {"gpm": lambda granule, cell: [("precip_mm_day", granule.day, 1.5)]}
    client = httpx.Client(transport=httpx.MockTransport(handler))
    with Session(pg) as db:
        done = regional.run_fetch_job(
            db, _job(pg, field, "gpm"), client=client, token=TOKEN, readers=readers
        )
        assert done.status == JobStatus.DONE and done.rows_written == 3
    assert asked == [ed.GPM_SHORT_NAME, ed.GPM_LATE_SHORT_NAME]
