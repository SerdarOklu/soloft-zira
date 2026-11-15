"""Sensors, the Water Vault correction, and the cooperative panel and farmer view (phase 7).

Loam, winter wheat, three years of weather at 1 mm of rain a day: the model says 230.75 mm of the
279 mm capacity on 1 October 2025 (see test_water_vault_api). A calibrated sensor with a wilting
point of 0.15 and field capacity of 0.31 that reads 0.23 at every depth says half of the capacity:
139.5 mm.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import MessageDraft, Role
from app.services import sensors as service
from tests.test_fields_api import create_field
from tests.test_water_vault_api import FIRST_DAY, LAST_DAY, store, weather

KEY = "test-sensor-key"
DECISION = datetime(2025, 10, 1, 9, 0, tzinfo=UTC)
CALIBRATION = {"slope": 1.0, "intercept": 0.0, "theta_wp": 0.15, "theta_fc": 0.31}


# --- The arithmetic ------------------------------------------------------------------------


def test_each_sensor_stands_for_the_layer_around_it():
    assert service.layer_thicknesses([10, 30, 60, 100]) == {10: 20.0, 30: 25.0, 60: 35.0, 100: 40.0}


def test_the_available_fraction_is_weighted_by_layer_thickness():
    # Only the top layer (20 of 120 cm) is at field capacity; the rest is at the wilting point.
    values = {10: 0.31, 30: 0.15, 60: 0.15, 100: 0.15}
    assert service.available_fraction(values, theta_wp=0.15, theta_fc=0.31) == pytest.approx(
        20 / 120
    )
    # Above field capacity or below the wilting point is clipped, not extrapolated.
    wet = {10: 0.50, 30: 0.05}
    # Two sensors: each stands for 20 cm, so the clipped 1.0 and 0.0 average to one half.
    assert service.available_fraction(wet, theta_wp=0.15, theta_fc=0.31) == pytest.approx(0.5)


def test_a_reading_is_calibrated_by_a_line():
    class Cal:
        slope, intercept = 0.9, 0.02

    assert service.calibrate(0.25, Cal()) == pytest.approx(0.245)
    assert service.calibrate(0.25, None) is None


# --- The API ---------------------------------------------------------------------------------


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


@pytest.fixture(autouse=True)
def ingest_key(pg):
    settings = get_settings()
    previous = settings.sensor_ingest_key
    settings.sensor_ingest_key = KEY
    yield
    settings.sensor_ingest_key = previous


@pytest.fixture
def field(pg_client: TestClient, admin, pg) -> str:
    created = create_field(pg_client, admin)
    store(pg, created["id"], weather(FIRST_DAY, LAST_DAY))
    return created["id"]


def post_readings(
    client,
    field_id,
    node="NODE_001",
    when=DECISION,
    vwc=0.23,
    depths=(10, 30, 60, 100),
    key=KEY,
    **extra,
):
    body = {
        "field_id": field_id,
        "measured_at": when.isoformat(),
        "is_simulated": True,
        "battery_v": 3.9,
        "readings": [{"depth_cm": depth, "vwc_raw": vwc} for depth in depths],
    } | extra
    headers = {"X-Sensor-Key": key} if key is not None else {}
    return client.post(f"/api/v1/sensors/{node}/readings", json=body, headers=headers)


def vault(client, headers, field_id) -> dict:
    response = client.get(
        f"/api/v1/fields/{field_id}/water-vault", params={"crop": "winter_wheat"}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def calibrate(client, headers, field_id, **changes):
    return client.put(
        f"/api/v1/fields/{field_id}/sensor-calibration", json=CALIBRATION | changes, headers=headers
    )


def test_ingest_needs_the_shared_key(pg_client: TestClient, field):
    assert post_readings(pg_client, field, key=None).status_code == 401
    assert post_readings(pg_client, field, key="wrong").status_code == 401
    ok = post_readings(pg_client, field)
    assert ok.status_code == 200 and ok.json() == {"stored": 4, "calibrated": False}


def test_a_wrong_key_is_refused_before_the_body_is_looked_at(pg_client: TestClient):
    response = pg_client.post(
        "/api/v1/sensors/NODE_001/readings", json={}, headers={"X-Sensor-Key": "wrong"}
    )
    assert response.status_code == 401


def test_ingest_is_off_without_a_key_on_the_server(pg_client: TestClient, field):
    get_settings().sensor_ingest_key = ""
    response = post_readings(pg_client, field)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "ingest_disabled"


def test_ingest_refuses_bad_readings(pg_client: TestClient, field):
    assert post_readings(pg_client, str(uuid.uuid4())).status_code == 404
    assert post_readings(pg_client, field, node="bad node").status_code in (404, 422)
    future = datetime.now(UTC) + timedelta(days=2)
    assert (
        post_readings(pg_client, field, when=future).json()["detail"]["code"]
        == "reading_in_the_future"
    )
    assert post_readings(pg_client, field, vwc=1.7).status_code == 422
    assert post_readings(pg_client, field, depths=(10, 10)).status_code == 422
    assert post_readings(pg_client, field, when=datetime(2025, 10, 1, 9, 0)).status_code == 422


def test_a_node_belongs_to_one_field_and_a_repeat_overwrites(pg_client: TestClient, admin, field):
    assert post_readings(pg_client, field).status_code == 200
    assert post_readings(pg_client, field, vwc=0.2).json()["stored"] == 4  # same time: updated
    status = pg_client.get(f"/api/v1/fields/{field}/sensors", headers=admin).json()
    assert len(status["nodes"]) == 1
    assert {r["vwc_raw"] for r in status["nodes"][0]["readings"]} == {0.2}
    other = create_field(pg_client, admin, name="Baska")["id"]
    conflict = post_readings(pg_client, other)
    assert (
        conflict.status_code == 409
        and conflict.json()["detail"]["code"] == "node_belongs_to_another_field"
    )


def test_only_an_agronomist_or_admin_records_the_calibration(
    pg_client: TestClient, admin, field, make_user, bearer
):
    bad = calibrate(pg_client, admin, field, theta_wp=0.4, theta_fc=0.3)
    assert bad.status_code == 422
    assert calibrate(pg_client, admin, field).status_code == 200
    read = pg_client.get(f"/api/v1/fields/{field}/sensor-calibration", headers=admin).json()
    assert read["theta_wp"] == 0.15 and read["theta_fc"] == 0.31
    make_user("coop@example.com", Role.COOPERATIVE_USER, "Koop")
    assert calibrate(pg_client, bearer("coop@example.com"), field).status_code == 403


def test_without_a_calibration_the_sensor_is_not_trusted(pg_client: TestClient, admin, field):
    post_readings(pg_client, field)
    body = vault(pg_client, admin, field)
    assert body["mode"] == "satellite" and body["sensor"] is None
    assert body["decision"]["storage_mm"] == pytest.approx(230.75)


def test_a_calibrated_sensor_corrects_the_decision_day(pg_client: TestClient, admin, field):
    calibrate(pg_client, admin, field)
    for node in ("NODE_001", "NODE_002", "NODE_003"):
        assert post_readings(pg_client, field, node=node).json()["calibrated"] is True
    body = vault(pg_client, admin, field)

    assert body["mode"] == "sensor"
    decision = body["decision"]
    assert decision["storage_mm"] == pytest.approx(139.5)  # half of 279 mm
    assert decision["fill_fraction"] == pytest.approx(0.5)
    # The band is narrower than the soil range: 10 % of the capacity each way.
    assert decision["low_mm"] == pytest.approx(139.5 - 27.9)
    assert decision["high_mm"] == pytest.approx(139.5 + 27.9)
    assert decision["taw_low_mm"] == decision["taw_high_mm"] == pytest.approx(279.0)

    sensor = body["sensor"]
    assert sensor["model_mm"] == pytest.approx(230.75)
    assert sensor["sensor_mm"] == pytest.approx(139.5)
    assert sensor["difference_mm"] == pytest.approx(139.5 - 230.75)
    assert sensor["nodes"] == 3 and sensor["depths_cm"] == [10, 30, 60, 100]
    assert "sensor_corrects_decision_day" in body["assumptions"]
    assert "no_sensor" not in body["assumptions"]
    assert "sensor_silence_h" in body["needs_signoff"]


def test_a_silent_sensor_returns_the_field_to_satellite_mode(pg_client: TestClient, admin, field):
    calibrate(pg_client, admin, field)
    # The silence limit counts back from the end of the chosen day (1 October, 23:59 UTC).
    end = datetime(2025, 10, 1, 23, 59, tzinfo=UTC)
    post_readings(pg_client, field, when=end - timedelta(hours=49))  # older than 48 h
    assert vault(pg_client, admin, field)["mode"] == "satellite"
    post_readings(pg_client, field, when=end - timedelta(hours=47))  # just inside
    assert vault(pg_client, admin, field)["mode"] == "sensor"


def test_one_depth_is_not_enough_to_say_how_wet_the_root_zone_is(
    pg_client: TestClient, admin, field
):
    calibrate(pg_client, admin, field)
    post_readings(pg_client, field, depths=(10,))
    assert vault(pg_client, admin, field)["mode"] == "satellite"


def test_the_sensor_calibration_changes_what_a_reading_means(pg_client: TestClient, admin, field):
    post_readings(pg_client, field, vwc=0.20)
    calibrate(pg_client, admin, field, slope=1.0, intercept=0.03)  # reads 0.23 once calibrated
    assert vault(pg_client, admin, field)["decision"]["storage_mm"] == pytest.approx(139.5)


def test_the_status_lists_nodes_and_marks_a_silent_one(pg_client: TestClient, admin, field):
    calibrate(pg_client, admin, field)
    post_readings(pg_client, field, node="OLD_NODE", when=datetime.now(UTC) - timedelta(days=3))
    post_readings(pg_client, field, node="NEW_NODE", when=datetime.now(UTC) - timedelta(hours=1))
    body = pg_client.get(f"/api/v1/fields/{field}/sensors", headers=admin).json()
    by_id = {n["node_id"]: n for n in body["nodes"]}
    assert by_id["OLD_NODE"]["status"] == "silent" and by_id["NEW_NODE"]["status"] == "active"
    assert by_id["NEW_NODE"]["is_simulated"] is True and by_id["NEW_NODE"]["battery_v"] == 3.9
    assert by_id["NEW_NODE"]["readings"][0]["vwc_calibrated"] == pytest.approx(0.23)
    # One node is still talking, but the model date is 2025, so "now" has no usable reading set
    # for two depths in common only if the active node reports them: it does.
    assert body["silence_h"] == 48 and body["mode"] == "sensor"


# --- Cooperative panel and farmer view -----------------------------------------------------------


@pytest.fixture
def coop(make_user, bearer):
    make_user("coop@example.com", Role.COOPERATIVE_USER, "Koop")
    return bearer("coop@example.com")


def new_user(client, headers, email, role="farmer", **extra):
    return client.post(
        "/api/v1/users",
        json={"email": email, "name": "Ali Çiftçi", "password": "uzun-bir-sifre-1", "role": role}
        | extra,
        headers=headers,
    )


def test_a_cooperative_user_creates_farmers_in_their_own_organization(
    pg_client: TestClient, admin, coop
):
    made = new_user(pg_client, coop, "ali@example.com")
    assert made.status_code == 201 and made.json()["role"] == "farmer"
    org = made.json()["organization_id"]
    assert org is not None
    assert new_user(pg_client, coop, "ali@example.com").json()["detail"]["code"] == "email_taken"
    assert new_user(pg_client, coop, "x@example.com", role="agronomist").status_code == 403
    assert new_user(pg_client, coop, "short@example.com", password="kisa").status_code == 422

    listed = pg_client.get("/api/v1/users", headers=coop).json()
    assert [u["email"] for u in listed] == ["ali@example.com"]
    everyone = pg_client.get("/api/v1/users", headers=admin).json()
    assert {"admin@example.com", "coop@example.com", "ali@example.com"} <= {
        u["email"] for u in everyone
    }
    unknown = new_user(pg_client, admin, "veli@example.com", organization_id=str(uuid.uuid4()))
    assert unknown.status_code == 422 and unknown.json()["detail"]["code"] == "unknown_organization"
    # A farmer of another organization is invisible to this cooperative user.


def test_a_farmer_can_be_deactivated_and_signs_in_no_more(pg_client: TestClient, coop):
    made = new_user(pg_client, coop, "ali@example.com").json()
    login = {"email": "ali@example.com", "password": "uzun-bir-sifre-1"}
    assert pg_client.post("/api/v1/auth/login", json=login).status_code == 200
    changed = pg_client.patch(
        f"/api/v1/users/{made['id']}", json={"is_active": False}, headers=coop
    )
    assert changed.json()["is_active"] is False
    assert pg_client.post("/api/v1/auth/login", json=login).status_code == 401


def farmer_headers(client, email="ali@example.com", password="uzun-bir-sifre-1"):
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_a_farmer_sees_only_their_own_field_and_sent_messages(
    pg_client: TestClient, admin, coop, pg
):
    farmer = new_user(pg_client, coop, "ali@example.com").json()
    mine = create_field(pg_client, coop, name="Benim tarlam")["id"]
    theirs = create_field(pg_client, admin, name="Baskasi")["id"]
    store(pg, mine, weather(FIRST_DAY, LAST_DAY))

    linked = pg_client.patch(
        f"/api/v1/fields/{mine}/farmer", json={"farmer_user_id": farmer["id"]}, headers=coop
    )
    assert linked.status_code == 200
    # A cooperative user cannot link a field outside their reach, nor a non-farmer.
    assert (
        pg_client.patch(
            f"/api/v1/fields/{theirs}/farmer", json={"farmer_user_id": farmer["id"]}, headers=coop
        ).status_code
        == 404
    )

    with Session(pg) as db, db.begin():
        for state, kind in (
            ("sent", "heavy_rain"),
            ("pending", "decision"),
            ("rejected", "leaching"),
        ):
            db.add(
                MessageDraft(
                    field_id=uuid.UUID(mine),
                    event_type=kind,
                    event_date=date(2025, 10, 1),
                    body=f"{state} text",
                    status=state,
                    sent_at=datetime.now(UTC) if state == "sent" else None,
                )
            )
    headers = farmer_headers(pg_client)
    summary = pg_client.get("/api/v1/farmer/summary", headers=headers).json()
    assert summary["name"] == "Ali Çiftçi"
    assert [f["name"] for f in summary["fields"]] == ["Benim tarlam"]
    water = summary["fields"][0]["water"]
    assert (
        water["storage_mm"] == pytest.approx(230.75) and summary["fields"][0]["mode"] == "satellite"
    )
    assert [m["body"] for m in summary["messages"]] == ["sent text"]

    # A farmer reads only the fields linked to them; another field does not exist for them.
    own = pg_client.get("/api/v1/fields", headers=headers)
    assert own.status_code == 200 and [f["name"] for f in own.json()] == ["Benim tarlam"]
    assert pg_client.get(f"/api/v1/fields/{mine}", headers=headers).status_code == 200
    for path in (
        f"/api/v1/fields/{theirs}",
        f"/api/v1/fields/{theirs}/field-memory",
        f"/api/v1/fields/{theirs}/rotation",
        f"/api/v1/fields/{theirs}/sensors",
        f"/api/v1/fields/{theirs}/water-vault?crop=winter_wheat",
    ):
        assert pg_client.get(path, headers=headers).status_code == 404, path
    for path in (
        f"/api/v1/fields/{mine}/field-memory",
        f"/api/v1/fields/{mine}/sensors",
        "/api/v1/reference/crops",
    ):
        assert pg_client.get(path, headers=headers).status_code == 200, path
    # The rotation is allowed; this test field has too little weather to compare (422, not 403/404).
    rotation = pg_client.get(
        f"/api/v1/fields/{mine}/rotation?rotation=winter_wheat,fallow", headers=headers
    )
    assert rotation.status_code not in (401, 403, 404)

    # Writes and staff-only data stay closed to a farmer.
    assert pg_client.post("/api/v1/fields", json={}, headers=headers).status_code == 403
    assert (
        pg_client.post(f"/api/v1/fields/{mine}/field-memory/fetch", headers=headers).status_code
        == 403
    )
    assert (
        pg_client.post(
            f"/api/v1/fields/{mine}/field-memory/confirm", json={}, headers=headers
        ).status_code
        == 403
    )
    assert pg_client.get(f"/api/v1/fields/{mine}/regional", headers=headers).status_code == 403
    assert pg_client.get("/api/v1/data-center/sources", headers=headers).status_code == 403
    assert pg_client.get("/api/v1/users", headers=headers).status_code == 403
    assert (
        pg_client.post(
            f"/api/v1/fields/{mine}/messages/generate", json={"season_year": 2024}, headers=headers
        ).status_code
        == 403
    )
    listed = pg_client.get("/api/v1/messages", headers=headers).json()
    assert [m["status"] for m in listed] == ["sent"]
    # Staff cannot read the farmer summary.
    assert pg_client.get("/api/v1/farmer/summary", headers=coop).status_code == 403


def test_a_farmer_whose_field_has_no_data_is_told_why(pg_client: TestClient, admin, coop):
    farmer = new_user(pg_client, coop, "ali@example.com").json()
    mine = create_field(pg_client, coop)["id"]
    pg_client.patch(
        f"/api/v1/fields/{mine}/farmer", json={"farmer_user_id": farmer["id"]}, headers=coop
    )
    field_card = pg_client.get("/api/v1/farmer/summary", headers=farmer_headers(pg_client)).json()[
        "fields"
    ][0]
    assert field_card["water"] is None and field_card["water_problem"] == "no_weather_data"
