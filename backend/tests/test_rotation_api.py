"""The rotation comparison on PostgreSQL. The weather is inserted directly (constant, so each
case can be reasoned about): wet weather fills the soil and every sown season has enough water;
dry weather leaves the current rotation short."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.models import Role
from tests.test_fields_api import create_field
from tests.test_water_vault_api import store, weather

pytestmark = pytest.mark.db


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


def make_field(pg_client: TestClient, admin, pg, *, rain: float, name: str = "Tarla") -> str:
    created = create_field(pg_client, admin, name=name)
    with pg.begin() as connection:
        connection.execute(
            text("UPDATE fields SET elevation_m = 1000 WHERE id = :id"), {"id": created["id"]}
        )
    store(pg, created["id"], weather(date(2001, 1, 1), date(2025, 12, 31), rain=rain))
    return created["id"]


def compare(client: TestClient, headers, field_id: str, **params):
    return client.get(f"/api/v1/fields/{field_id}/rotation", params=params, headers=headers)


def test_requires_sign_in(pg_client: TestClient):
    assert (
        pg_client.get(f"/api/v1/fields/{'0' * 8}-0000-0000-0000-{'0' * 12}/rotation").status_code
        == 401
    )


def test_three_strategies_on_the_same_seasons(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=3.0)
    response = compare(pg_client, admin, field)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["provisional"] is True
    assert body["seasons"] == 24  # sown 2001 to 2024; the 2025 season would end after the record
    assert body["rotation"] == ["winter_wheat", None]
    assert [s["key"] for s in body["strategies"]] == ["A", "B", "C"]
    years = [[season["year"] for season in s["seasons"]] for s in body["strategies"]]
    assert years[0] == years[1] == years[2] == list(range(2001, 2025))
    assert body["strategies"][0]["difference"] is None


def test_wet_weather_gives_enough_water_in_every_sown_season(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=3.0)
    a, b, c = compare(pg_client, admin, field).json()["strategies"]

    assert a["metrics"]["sown"] == 12 and a["metrics"]["fallow"] == 12
    assert a["metrics"]["share"] == pytest.approx(1.0)
    assert a["metrics"]["sufficient"] == 12
    # B follows A's crop years and the soil is full on every decision day, so it sows them all.
    assert b["metrics"]["sown"] == 12
    # C adds a lentil to every second fallow season of A: 12 fallow seasons, 6 legumes.
    assert c["metrics"]["sown"] == 18
    assert sorted(c["crops"]) == ["lentil", "winter_wheat"]
    assert c["difference"]["sufficient"] == 6


def test_dry_weather_leaves_the_current_rotation_short(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=0.0, name="Kuru")
    a = compare(pg_client, admin, field).json()["strategies"][0]
    assert a["metrics"]["sown"] == 12
    assert a["metrics"]["sufficient"] == 0
    assert a["metrics"]["share"] == pytest.approx(0.0)
    assert a["metrics"]["deficit_mean_mm"] > 0
    assert a["metrics"]["irrigation_need_mean_mm"] > a["metrics"]["deficit_mean_mm"]
    assert all(season["stress_days"] > 0 for season in a["seasons"] if season["crop"])


def test_the_range_brackets_the_middle(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=1.0, name="Orta")
    for strategy in compare(pg_client, admin, field).json()["strategies"]:
        m = strategy["metrics"]
        assert m["sufficient_low"] <= m["sufficient"] <= m["sufficient_high"]


def test_the_rotation_can_be_chosen(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=3.0, name="Rotasyon")
    body = compare(pg_client, admin, field, rotation="winter_wheat").json()
    assert body["rotation"] == ["winter_wheat"]
    assert body["strategies"][0]["metrics"]["sown"] == 24
    assert body["strategies"][0]["metrics"]["fallow"] == 0


def test_refusals_say_why(pg_client: TestClient, admin, pg):
    field = make_field(pg_client, admin, pg, rain=1.0, name="Ret")
    assert compare(pg_client, admin, field, rotation="fallow").json()["detail"]["code"] == (
        "rotation_without_crop"
    )
    unknown = compare(pg_client, admin, field, rotation="nonsense")
    assert unknown.status_code == 422 and unknown.json()["detail"]["code"] == "unknown_crop"
    # Barley is in crops.yaml, but has no season values yet.
    barley = compare(pg_client, admin, field, rotation="barley")
    assert barley.json()["detail"]["code"] == "season_values_missing"

    empty = create_field(pg_client, admin, name="Bos")
    assert compare(pg_client, admin, empty["id"]).status_code == 422
