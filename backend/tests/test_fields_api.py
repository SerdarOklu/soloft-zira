"""Fields, the NASA POWER fetch job, the Data Center and the overview, on PostgreSQL.

The application runs for real (PostGIS geometry, migrations, the Celery task run inline);
only the call to NASA is replaced, and the tests record what it was asked for.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.models import Role
from app.services import power
from app.services.power import PowerError, PowerResult

pytestmark = pytest.mark.db

# About 0.01 degrees on each side near Konya: roughly 97 ha.
SQUARE = [[32.50, 37.90], [32.51, 37.90], [32.51, 37.91], [32.50, 37.91], [32.50, 37.90]]


def field_body(**overrides):
    body = {
        "name": "Konya test tarlası",
        "region": "Konya",
        "water_regime": "rainfed",
        "soil_texture": "loam",
        "geometry": {"type": "Polygon", "coordinates": [SQUARE]},
    }
    return body | overrides


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


class Recorder(list):
    """The calls made to NASA, plus a switch that makes the next call fail."""

    def __init__(self) -> None:
        super().__init__()
        self.outcome: dict = {"error": None}


@pytest.fixture
def nasa(monkeypatch: pytest.MonkeyPatch, eager):
    """Replace the NASA call with a recorder that returns one day per requested date."""
    calls = Recorder()
    outcome = calls.outcome

    def fake_fetch(config, *, latitude, longitude, start, end, client=None):
        calls.append({"latitude": latitude, "longitude": longitude, "start": start, "end": end})
        if outcome["error"]:
            raise outcome["error"]
        rows = [
            {
                "date": start + timedelta(days=offset),
                "wind_height_m": 10.0,
                "precipitation_mm": 2.0,
                "temperature_avg": 10.0,
                "temperature_max": 15.0,
                "temperature_min": 5.0,
                "humidity": 60.0,
                "wind_speed": 3.0,
                "solar_radiation": 15.0,
                "surface_pressure": 90.0,
                "quality_flag": None,
            }
            for offset in range((end - start).days + 1)
        ]
        return PowerResult(rows=rows, elevation_m=1215.6, api_version="test")

    monkeypatch.setattr(power, "fetch_daily", fake_fetch)
    return calls


def create_field(client: TestClient, headers, **overrides) -> dict:
    response = client.post("/api/v1/fields", json=field_body(**overrides), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


# --- creating and reading fields -------------------------------------------------------


def test_a_field_gets_its_area_and_centroid_from_the_polygon(pg_client: TestClient, admin):
    field = create_field(pg_client, admin)
    assert field["code"].startswith("ZR-")
    assert field["soil_texture"] == "loam"
    assert field["water_regime"] == "rainfed"
    assert 90 < field["area_ha"] < 105
    assert field["centroid"]["lon"] == pytest.approx(32.505)
    assert field["centroid"]["lat"] == pytest.approx(37.905)
    assert field["geometry"]["type"] == "Polygon"
    assert field["weather_days"] == 0
    assert field["elevation_m"] is None


def test_an_open_ring_is_closed(pg_client: TestClient, admin):
    open_ring = SQUARE[:-1]
    field = create_field(pg_client, admin, geometry={"type": "Polygon", "coordinates": [open_ring]})
    assert field["geometry"]["coordinates"][0][0] == field["geometry"]["coordinates"][0][-1]


def test_the_soil_default_comes_from_the_configuration(pg_client: TestClient, admin, pg):
    from sqlalchemy import text

    from app.core.parameters import get_config

    create_field(pg_client, admin)
    with pg.connect() as connection:
        taw, source, calibrated = connection.execute(
            text("SELECT taw_mm_per_m, source, is_calibrated FROM soil_profiles")
        ).one()
    assert taw == get_config().soils["loam"].taw_mid
    assert (source, calibrated) == ("config_default", False)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],  # a bow tie
                }
            },
            "edges must not cross",
        ),
        ({"soil_texture": "marble"}, "Unknown soil texture"),
    ],
)
def test_an_invalid_field_is_refused(pg_client: TestClient, admin, overrides, message):
    response = pg_client.post("/api/v1/fields", json=field_body(**overrides), headers=admin)
    assert response.status_code == 422
    assert message in response.text


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]},  # too few corners
        {"type": "Polygon", "coordinates": [[[200, 0], [201, 0], [201, 1], [200, 0]]]},  # lon
        {"type": "Polygon", "coordinates": [[[0, 95], [1, 95], [1, 96], [0, 95]]]},  # lat
        {"type": "Polygon", "coordinates": [SQUARE, SQUARE]},  # a hole
        {"type": "Point", "coordinates": [32.5, 37.9]},
    ],
)
def test_a_malformed_geometry_is_refused(pg_client: TestClient, admin, geometry):
    response = pg_client.post("/api/v1/fields", json=field_body(geometry=geometry), headers=admin)
    assert response.status_code == 422


def test_a_duplicate_code_is_a_conflict(pg_client: TestClient, admin):
    create_field(pg_client, admin, code="TARLA-1")
    response = pg_client.post("/api/v1/fields", json=field_body(code="TARLA-1"), headers=admin)
    assert response.status_code == 409


def test_fields_need_a_signed_in_user(pg_client: TestClient):
    assert pg_client.get("/api/v1/fields").status_code == 401
    assert pg_client.post("/api/v1/fields", json=field_body()).status_code == 401


def test_a_cooperative_user_only_sees_their_own_organization(
    pg_client: TestClient, make_user, bearer
):
    make_user("a@coop-a.local", Role.COOPERATIVE_USER, organization="Kooperatif A")
    make_user("b@coop-b.local", Role.COOPERATIVE_USER, organization="Kooperatif B")
    make_user("ayse@example.com", Role.AGRONOMIST)
    a, b, agronomist = (
        bearer("a@coop-a.local"),
        bearer("b@coop-b.local"),
        bearer("ayse@example.com"),
    )

    mine = create_field(pg_client, a, name="A tarlası")
    create_field(pg_client, b, name="B tarlası")

    assert [f["name"] for f in pg_client.get("/api/v1/fields", headers=a).json()] == ["A tarlası"]
    assert [f["name"] for f in pg_client.get("/api/v1/fields", headers=b).json()] == ["B tarlası"]
    assert len(pg_client.get("/api/v1/fields", headers=agronomist).json()) == 2

    assert pg_client.get(f"/api/v1/fields/{mine['id']}", headers=a).status_code == 200
    # Another organization's field does not exist as far as this user can tell.
    assert pg_client.get(f"/api/v1/fields/{mine['id']}", headers=b).status_code == 404
    assert (
        pg_client.post(f"/api/v1/fields/{mine['id']}/weather/fetch", json={}, headers=b).status_code
        == 404
    )


def test_only_an_admin_deletes_a_field(pg_client: TestClient, admin, make_user, bearer):
    make_user("ayse@example.com", Role.AGRONOMIST)
    field = create_field(pg_client, admin)
    url = f"/api/v1/fields/{field['id']}"

    assert pg_client.delete(url, headers=bearer("ayse@example.com")).status_code == 403
    assert pg_client.delete(url, headers=admin).status_code == 204
    assert pg_client.get(url, headers=admin).status_code == 404


def test_the_soil_list_is_the_configuration(pg_client: TestClient, admin):
    from app.core.parameters import get_config

    soils = pg_client.get("/api/v1/reference/soils", headers=admin).json()
    assert [s["key"] for s in soils] == list(get_config().soils)
    loam = next(s for s in soils if s["key"] == "loam")
    assert loam["taw_mm_per_m"] == [130, 180]
    assert pg_client.get("/api/v1/reference/soils").status_code == 401


# --- fetching NASA POWER weather -------------------------------------------------------


def fetch(client: TestClient, headers, field_id: str, **body):
    return client.post(f"/api/v1/fields/{field_id}/weather/fetch", json=body, headers=headers)


def test_a_fetch_reads_the_location_from_the_field_and_stores_the_days(
    pg_client: TestClient, admin, nasa
):
    field = create_field(pg_client, admin)
    response = fetch(pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-31")

    assert response.status_code == 202
    job = response.json()
    assert (job["status"], job["rows_written"], job["source"]) == ("done", 31, "power")

    (call,) = nasa
    assert call["latitude"] == pytest.approx(37.905)
    assert call["longitude"] == pytest.approx(32.505)
    assert (str(call["start"]), str(call["end"])) == ("2024-01-01", "2024-01-31")

    summary = pg_client.get(f"/api/v1/fields/{field['id']}/weather/summary", headers=admin).json()
    assert summary["days"] == 31
    assert (summary["first_date"], summary["last_date"]) == ("2024-01-01", "2024-01-31")
    assert summary["units"]["precipitation_mm"] == "mm/day"
    assert summary["wind_height_m"] == 10.0
    assert len(summary["recent"]) == 14
    assert summary["recent"][0]["date"] == "2024-01-31"
    assert summary["years"] == [
        {
            "year": 2024,
            "days": 31,
            "precipitation_mm": 62.0,
            "temperature_avg": 10.0,
            "temperature_min": 5.0,
            "temperature_max": 15.0,
        }
    ]
    assert summary["latest_job"]["status"] == "done"

    refreshed = pg_client.get(f"/api/v1/fields/{field['id']}", headers=admin).json()
    assert refreshed["weather_days"] == 31
    assert refreshed["elevation_m"] == pytest.approx(1215.6)  # taken from POWER


def test_the_default_period_is_the_twenty_five_years_of_the_sheet(
    pg_client: TestClient, admin, nasa
):
    field = create_field(pg_client, admin)
    job = fetch(pg_client, admin, field["id"]).json()
    assert (job["date_from"], job["date_to"]) == ("2001-01-01", "2025-12-31")
    assert job["rows_written"] == 9131


def test_a_period_that_is_already_stored_is_not_fetched_again(pg_client: TestClient, admin, nasa):
    field = create_field(pg_client, admin)
    span = {"date_from": "2024-01-01", "date_to": "2024-01-10"}

    assert fetch(pg_client, admin, field["id"], **span).json()["rows_written"] == 10
    again = fetch(pg_client, admin, field["id"], **span).json()
    assert (again["status"], again["rows_written"]) == ("done", 0)  # served from the cache
    assert len(nasa) == 1

    forced = fetch(pg_client, admin, field["id"], force=True, **span).json()
    assert forced["rows_written"] == 10
    assert len(nasa) == 2

    # A wider period is not covered, so it is fetched; the days already stored are overwritten.
    wider = fetch(
        pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-20"
    ).json()
    assert wider["rows_written"] == 20
    summary = pg_client.get(f"/api/v1/fields/{field['id']}/weather/summary", headers=admin).json()
    assert summary["days"] == 20


def test_a_failed_fetch_is_recorded_and_shown(pg_client: TestClient, admin, nasa):
    field = create_field(pg_client, admin)
    nasa.outcome["error"] = PowerError("POWER is not reachable after 3 attempts")

    job = fetch(pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-05").json()
    assert job["status"] == "failed"
    assert "not reachable" in job["error_message"]
    assert job["rows_written"] is None

    sources = {
        s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=admin).json()
    }
    assert sources["power"]["status"] == "error"
    assert sources["power"]["jobs"]["failed"] == 1

    # Trying again after the outage works and clears the error.
    nasa.outcome["error"] = None
    ok = fetch(pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-05").json()
    assert ok["status"] == "done"
    sources = {
        s["key"]: s for s in pg_client.get("/api/v1/data-center/sources", headers=admin).json()
    }
    assert sources["power"]["status"] == "ok"


@pytest.mark.parametrize(
    "span",
    [
        {"date_from": "2024-02-01", "date_to": "2024-01-01"},
        {"date_from": "2024-01-01", "date_to": "2999-01-01"},
    ],
)
def test_a_bad_period_is_refused_before_a_job_exists(pg_client: TestClient, admin, nasa, span):
    field = create_field(pg_client, admin)
    assert fetch(pg_client, admin, field["id"], **span).status_code == 422
    assert pg_client.get("/api/v1/data-center/jobs", headers=admin).json() == []
    assert nasa == []


def test_the_weather_of_an_unknown_field_is_not_found(pg_client: TestClient, admin):
    missing = "00000000-0000-0000-0000-000000000000"
    assert (
        pg_client.get(f"/api/v1/fields/{missing}/weather/summary", headers=admin).status_code == 404
    )
    assert fetch(pg_client, admin, missing).status_code == 404


# --- Data Center -----------------------------------------------------------------------


def test_the_data_center_lists_every_source_and_what_arrived(pg_client: TestClient, admin, nasa):
    field = create_field(pg_client, admin)
    fetch(pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-31")

    sources = pg_client.get("/api/v1/data-center/sources", headers=admin).json()
    assert [s["key"] for s in sources] == [
        "power",
        "landsat8",
        "landsat9",
        "gpm",
        "smap",
        "modis",
        "grace",
        "ecostress",
        "srtm",
    ]
    by_key = {s["key"]: s for s in sources}
    power_source = by_key["power"]
    assert power_source["connected"] is True
    assert power_source["status"] == "ok"
    assert power_source["observations"] == 31
    assert power_source["jobs"] == {"queued": 0, "running": 0, "done": 1, "failed": 0}
    assert power_source["last_success_at"] is not None
    # MODIS is read from the public STAC catalogue (phase 5): connected, but nothing fetched yet.
    assert by_key["modis"]["connected"] is True
    assert by_key["modis"]["status"] == "never_fetched"
    assert by_key["modis"]["collection_id"] == "modis-13Q1-061"
    assert by_key["landsat8"]["connected"] and by_key["landsat9"]["connected"]
    # The Earth Engine sources are not set up and are reported as not connected, not as healthy.
    for key in ("gpm", "smap", "grace"):
        assert by_key[key]["connected"] is False
        assert by_key[key]["status"] == "not_connected"
        assert by_key[key]["observations"] == 0
    assert by_key["landsat8"]["collection_id"] == "landsat-c2-l2"


def test_the_data_center_lists_recent_jobs_with_their_field(pg_client: TestClient, admin, nasa):
    field = create_field(pg_client, admin, code="TARLA-9", name="Dokuzuncu")
    fetch(pg_client, admin, field["id"], date_from="2024-01-01", date_to="2024-01-03")

    (job,) = pg_client.get("/api/v1/data-center/jobs", headers=admin).json()
    assert (job["field_code"], job["field_name"], job["source"]) == (
        "TARLA-9",
        "Dokuzuncu",
        "power",
    )
    assert (job["status"], job["rows_written"]) == ("done", 3)
    assert pg_client.get("/api/v1/data-center/jobs?limit=0", headers=admin).status_code == 422


def test_the_data_center_is_for_admins_and_agronomists(pg_client: TestClient, make_user, bearer):
    make_user("ayse@example.com", Role.AGRONOMIST)
    make_user("kemal@coop.local", Role.COOPERATIVE_USER, organization="Kooperatif A")
    assert (
        pg_client.get("/api/v1/data-center/sources", headers=bearer("ayse@example.com")).status_code
        == 200
    )
    for path in ("sources", "jobs"):
        response = pg_client.get(f"/api/v1/data-center/{path}", headers=bearer("kemal@coop.local"))
        assert response.status_code == 403


# --- Overview --------------------------------------------------------------------------


def test_the_overview_counts_fields_and_flags_the_ones_without_data(
    pg_client: TestClient, admin, nasa
):
    empty = pg_client.get("/api/v1/dashboard/summary", headers=admin).json()
    assert empty["field_count"] == 0
    assert empty["markers"] == []
    assert empty["last_weather_update"] is None

    with_data = create_field(pg_client, admin, name="Verili")
    create_field(pg_client, admin, name="Verisiz")
    fetch(pg_client, admin, with_data["id"], date_from="2024-01-01", date_to="2024-01-03")

    summary = pg_client.get("/api/v1/dashboard/summary", headers=admin).json()
    assert summary["field_count"] == 2
    assert summary["fields_with_weather"] == 1
    assert [f["name"] for f in summary["fields_missing_weather"]] == ["Verisiz"]
    assert summary["jobs"] == {"queued": 0, "running": 0, "done": 1, "failed": 0}
    assert summary["last_weather_update"] is not None
    assert {m["name"]: m["has_weather"] for m in summary["markers"]} == {
        "Verili": True,
        "Verisiz": False,
    }
    assert summary["markers"][0]["lat"] == pytest.approx(37.905)


def test_the_overview_is_scoped_like_the_field_list(pg_client: TestClient, make_user, bearer):
    make_user("a@coop-a.local", Role.COOPERATIVE_USER, organization="Kooperatif A")
    make_user("b@coop-b.local", Role.COOPERATIVE_USER, organization="Kooperatif B")
    create_field(pg_client, bearer("a@coop-a.local"))
    summary = pg_client.get("/api/v1/dashboard/summary", headers=bearer("b@coop-b.local")).json()
    assert summary["field_count"] == 0
