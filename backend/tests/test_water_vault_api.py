"""The Water Vault on PostgreSQL: usable water on a decision day, its range, and the reasons it
refuses. The weather is inserted directly, so every expected number can be worked out by hand.

Loam, winter wheat: soil 155 mm/m (range 130 to 180), maximum root depth 1.8 m, so
TAW = 279 mm (low 234, high 324). Fallow efficiency is 0.25 (low 0.15, high 0.35), the warm-up
is 365 days and the soil starts at half of TAW. With 1 mm of rain every day:
    middle: 139.5 + 365 * 0.25 = 230.75   low: 117 + 365 * 0.15 = 171.75
    high:   162   + 365 * 0.35 = 289.75
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Role
from app.services.power import store_rows
from tests.test_fields_api import create_field

pytestmark = pytest.mark.db

FIRST_DAY = date(2023, 1, 1)
LAST_DAY = date(2025, 12, 31)


def weather(start: date, end: date, *, rain: float = 1.0) -> list[dict]:
    return [
        {
            "date": start + timedelta(days=offset),
            "wind_height_m": 10.0,
            "precipitation_mm": rain,
            "temperature_avg": 15.0,
            "temperature_max": 22.0,
            "temperature_min": 8.0,
            "humidity": 60.0,
            "wind_speed": 3.0,
            "solar_radiation": 15.0,
            "surface_pressure": 90.0,
            "quality_flag": None,
        }
        for offset in range((end - start).days + 1)
    ]


def store(pg, field_id: str, rows: list[dict]) -> None:
    with Session(pg) as db, db.begin():
        store_rows(db, uuid.UUID(field_id), rows)


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


@pytest.fixture
def field(pg_client: TestClient, admin, pg) -> str:
    """A loam field with three years of weather at 1 mm of rain a day."""
    created = create_field(pg_client, admin)
    store(pg, created["id"], weather(FIRST_DAY, LAST_DAY))
    return created["id"]


def vault(client: TestClient, headers, field_id: str, crop: str = "winter_wheat", **params):
    query = {"crop": crop} | params
    return client.get(f"/api/v1/fields/{field_id}/water-vault", params=query, headers=headers)


def error_code(response) -> str:
    assert response.status_code == 422, response.text
    return response.json()["detail"]["code"]


# --- The number on the decision day ------------------------------------------------------


def test_the_decision_day_water_and_its_range(pg_client: TestClient, admin, field):
    response = vault(pg_client, admin, field)
    assert response.status_code == 200, response.text
    body = response.json()

    decision = body["decision"]
    assert decision["storage_mm"] == pytest.approx(230.75)
    assert decision["low_mm"] == pytest.approx(171.75)
    assert decision["high_mm"] == pytest.approx(289.75)
    assert decision["taw_mm"] == pytest.approx(279.0)
    assert decision["taw_low_mm"] == pytest.approx(234.0)
    assert decision["taw_high_mm"] == pytest.approx(324.0)
    assert decision["fill_fraction"] == pytest.approx(230.75 / 279.0)
    assert decision["low_mm"] <= decision["storage_mm"] <= decision["high_mm"]


def test_without_a_date_the_latest_decision_day_of_the_season_is_used(
    pg_client: TestClient, admin, field
):
    body = vault(pg_client, admin, field).json()
    # Winter crops are decided on 1 October (config); the data ends on 31 December 2025.
    assert body["date"] == "2025-10-01"
    assert body["date_is_default"] is True
    assert body["window"] == {
        "start": "2024-10-02",
        "end": "2025-10-01",
        "days": 365,
        "missing_days": 0,
    }
    assert len(body["daily"]) == 365
    assert body["daily"][-1]["storage_mm"] == pytest.approx(230.75)
    assert body["daily"][0]["storage_mm"] == pytest.approx(139.5 + 0.25)


def test_the_water_on_any_past_date_can_be_read(pg_client: TestClient, admin, field):
    body = vault(pg_client, admin, field, date="2025-06-15").json()
    assert body["date"] == "2025-06-15"
    assert body["date_is_default"] is False
    assert body["window"]["end"] == "2025-06-15"
    assert body["decision"]["storage_mm"] == pytest.approx(230.75)


def test_a_wet_year_fills_the_root_zone_and_no_more(pg_client: TestClient, admin, pg):
    wet = create_field(pg_client, admin, name="Islak")
    store(pg, wet["id"], weather(FIRST_DAY, LAST_DAY, rain=3.0))
    decision = vault(pg_client, admin, wet["id"]).json()["decision"]
    assert decision["storage_mm"] == pytest.approx(279.0)  # 139.5 + 365 * 0.75 would be 413
    assert decision["fill_fraction"] == pytest.approx(1.0)


def test_a_few_missing_days_are_counted_as_no_rain_and_reported(
    pg_client: TestClient, admin, field, pg
):
    with Session(pg) as db, db.begin():
        db.execute(
            text(
                "DELETE FROM weather_observations WHERE date BETWEEN '2025-03-01' AND '2025-03-05'"
            )
        )
    body = vault(pg_client, admin, field).json()
    assert body["window"]["missing_days"] == 5
    assert body["decision"]["storage_mm"] == pytest.approx(139.5 + 360 * 0.25)


def test_a_calibrated_soil_has_one_capacity(pg_client: TestClient, admin, field, pg):
    with Session(pg) as db, db.begin():
        db.execute(text("UPDATE soil_profiles SET is_calibrated = true, taw_mm_per_m = 100"))
    body = vault(pg_client, admin, field).json()
    decision = body["decision"]
    assert body["soil_calibrated"] is True
    assert decision["taw_mm"] == decision["taw_low_mm"] == decision["taw_high_mm"] == 180.0


# --- What it says about itself -----------------------------------------------------------


def test_it_lists_what_still_waits_for_an_agronomist(pg_client: TestClient, admin, field):
    default = vault(pg_client, admin, field).json()
    assert {
        "decision_date",
        "fallow_efficiency",
        "initial_storage_frac",
        "spinup_seasons",
        "uncertainty_rain_delta",
        "min_valid_day_share",
    } <= set(default["needs_signoff"])
    # A date the user chose does not depend on the sheet's decision date.
    chosen = vault(pg_client, admin, field, date="2025-06-15").json()
    assert "decision_date" not in chosen["needs_signoff"]
    assert "fallow_efficiency" in chosen["needs_signoff"]


def test_it_states_what_the_number_rests_on(pg_client: TestClient, admin, field):
    body = vault(pg_client, admin, field).json()
    assert body["assumptions"] == [
        "fallow_before_the_day",
        "regional_weather",
        "no_sensor",
        "range_from_soil_and_fallow_efficiency",
    ]
    assert body["parameters"] == {
        "fallow_efficiency": 0.25,
        "initial_storage_frac": 0.5,
        "spinup_days": 365,
        "uncertainty_delta": 0.1,
    }


def test_the_crop_season_is_not_run_until_the_agronomist_sets_the_stage_lengths(
    pg_client: TestClient, admin, field
):
    crop = vault(pg_client, admin, field).json()["crop"]
    assert crop["key"] == "winter_wheat"
    assert crop["root_depth_m"] == 1.8
    assert crop["season_ready"] is False
    assert crop["season_blocker"] == "stage_lengths_not_set"


# --- Evapotranspiration ------------------------------------------------------------------


def test_et0_needs_the_elevation_which_the_nasa_fetch_provides(pg_client: TestClient, admin, field):
    body = vault(pg_client, admin, field).json()
    assert body["et0_days"] == 0
    assert body["et0_blocker"] == "no_elevation"
    assert all(day["et0_mm"] is None for day in body["daily"])


def test_et0_is_computed_for_every_day_with_complete_weather(
    pg_client: TestClient, admin, field, pg
):
    with Session(pg) as db, db.begin():
        db.execute(text("UPDATE fields SET elevation_m = 1000"))
    body = vault(pg_client, admin, field).json()
    assert body["et0_blocker"] is None
    assert body["et0_days"] == 365
    values = [day["et0_mm"] for day in body["daily"]]
    assert all(0.5 < value < 10 for value in values)
    # The same weather on a day in summer and one in winter: more sun, more evaporation.
    by_date = {day["date"]: day["et0_mm"] for day in body["daily"]}
    assert by_date["2025-06-21"] > by_date["2024-12-21"]


# --- Why it refuses ----------------------------------------------------------------------


def test_an_unknown_crop_is_refused(pg_client: TestClient, admin, field):
    assert error_code(vault(pg_client, admin, field, crop="marble")) == "unknown_crop"


def test_a_field_without_weather_cannot_be_read(pg_client: TestClient, admin):
    empty = create_field(pg_client, admin, name="Verisiz")
    assert error_code(vault(pg_client, admin, empty["id"])) == "no_weather_data"


def test_a_crop_without_a_season_type_needs_a_date(pg_client: TestClient, admin, field):
    assert error_code(vault(pg_client, admin, field, crop="barley")) == "season_type_not_set"
    chosen = vault(pg_client, admin, field, crop="barley", date="2025-06-15")
    assert chosen.status_code == 200
    assert chosen.json()["decision"]["taw_mm"] == pytest.approx(155.0 * 1.5)  # barley, 1.5 m


def test_a_date_after_the_data_is_refused_and_says_where_the_data_ends(
    pg_client: TestClient, admin, field
):
    response = vault(pg_client, admin, field, date="2026-06-01")
    assert error_code(response) == "date_after_data"
    assert response.json()["detail"]["last_date"] == "2025-12-31"


def test_a_date_without_a_warm_up_behind_it_is_refused(pg_client: TestClient, admin, field):
    response = vault(pg_client, admin, field, date="2023-06-01")
    assert error_code(response) == "not_enough_history"
    detail = response.json()["detail"]
    assert detail["first_date"] == "2023-01-01"
    assert detail["earliest_date"] == "2023-12-31"


def test_too_many_missing_days_are_refused(pg_client: TestClient, admin, field, pg):
    with Session(pg) as db, db.begin():
        db.execute(
            text(
                "DELETE FROM weather_observations WHERE date BETWEEN '2025-01-01' AND '2025-06-30'"
            )
        )
    response = vault(pg_client, admin, field)
    assert error_code(response) == "too_many_gaps"
    assert response.json()["detail"]["missing_days"] == 181


# --- Access ------------------------------------------------------------------------------


def test_the_water_vault_needs_a_signed_in_user(pg_client: TestClient, field):
    assert vault(pg_client, {}, field).status_code == 401


def test_another_organizations_field_is_not_found(pg_client: TestClient, make_user, bearer):
    make_user("a@coop-a.local", Role.COOPERATIVE_USER, organization="Kooperatif A")
    make_user("b@coop-b.local", Role.COOPERATIVE_USER, organization="Kooperatif B")
    mine = create_field(pg_client, bearer("a@coop-a.local"))
    assert vault(pg_client, bearer("b@coop-b.local"), mine["id"]).status_code == 404


def test_the_crop_list_says_which_seasons_can_run(pg_client: TestClient, admin):
    crops = pg_client.get("/api/v1/reference/crops", headers=admin).json()
    by_key = {crop["key"]: crop for crop in crops}
    assert len(crops) == 8
    assert by_key["winter_wheat"]["root_depth_m"] == 1.8
    assert by_key["winter_wheat"]["season_type"] == "winter"
    assert by_key["barley"]["season_type"] is None
    assert not any(crop["season_ready"] for crop in crops)
    assert pg_client.get("/api/v1/reference/crops").status_code == 401
