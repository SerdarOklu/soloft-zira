"""WhatsApp drafts: events from the model, the approval step, and the gateway.

The weather is constant and wet, with one 25 mm day in March 2024, so the events of the season
sown in autumn 2023 are known: the October decision, the heavy rain and the water that leaves
the root zone that day, and the harvest summary. No real message is ever sent: the gateway is
replaced by a recorder.
"""

from __future__ import annotations

from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.messages import get_gateway
from app.core.config import Settings
from app.core.parameters import get_config
from app.main import app
from app.models import Role
from app.services.messaging.events import Event
from app.services.messaging.greenapi import (
    GatewayError,
    GreenApiClient,
    NotConfigured,
    normalise_phone,
)
from app.services.messaging.texts import render
from tests.test_fields_api import create_field
from tests.test_water_vault_api import store, weather

pytestmark = pytest.mark.db

PHONE = "+90 532 123 45 67"


class Recorder:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str]] = []

    def send_text(self, phone: str, body: str) -> str:
        if self.fail:
            raise GatewayError("The gateway answered 466")
        self.sent.append((phone, body))
        return "BAE5367237E13A87"


@pytest.fixture
def admin(make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    return bearer("admin@example.com")


@pytest.fixture
def field(pg_client: TestClient, admin, pg) -> str:
    created = create_field(pg_client, admin, name="Konya tarlası")
    with pg.begin() as connection:
        connection.execute(
            text("UPDATE fields SET elevation_m = 1000 WHERE id = :id"), {"id": created["id"]}
        )
    rows = weather(date(2001, 1, 1), date(2025, 12, 31), rain=3.0)
    for row in rows:
        if row["date"] == date(2024, 3, 10):
            row["precipitation_mm"] = 25.0
    store(pg, created["id"], rows)
    return created["id"]


@pytest.fixture
def gateway():
    recorder = Recorder()
    app.dependency_overrides[get_gateway] = lambda: recorder
    yield recorder
    app.dependency_overrides.pop(get_gateway, None)


def generate(client, headers, field_id, **body):
    payload = {"season_year": 2023, "locale": "tr"} | body
    return client.post(
        f"/api/v1/fields/{field_id}/messages/generate", json=payload, headers=headers
    )


# --- Writing the drafts ------------------------------------------------------------------


def test_the_season_gets_a_draft_for_each_event(pg_client: TestClient, admin, field):
    response = generate(pg_client, admin, field)
    assert response.status_code == 201, response.text
    body = response.json()
    by_type = {d["event_type"]: d for d in body["drafts"]}
    assert set(by_type) == {"decision", "heavy_rain", "leaching", "harvest"}
    assert all(d["status"] == "pending" for d in body["drafts"])

    decision = by_type["decision"]
    assert decision["event_date"] == "2023-10-01"
    assert decision["body"].startswith("Ekim kararı, 1 Eki 2023.")
    assert "Kışlık buğday" in decision["body"]
    assert "Zira karar vermez" in decision["body"]
    assert decision["payload"]["above_threshold"] is True

    rain = by_type["heavy_rain"]
    assert rain["event_date"] == "2024-03-10"
    assert "bir günde 25 mm" in rain["body"]
    assert by_type["leaching"]["event_date"] == "2024-03-10"

    harvest = by_type["harvest"]
    assert harvest["event_date"] == "2024-06-27"  # sown 1 Nov 2023, day 240 (2024 is a leap year)
    assert "%100" in harvest["body"]
    assert "bu sezon su yetti" in harvest["body"]


def test_running_it_again_writes_nothing_new(pg_client: TestClient, admin, field):
    first = generate(pg_client, admin, field).json()
    second = generate(pg_client, admin, field).json()
    assert second["created"] == 0
    assert second["skipped"] == first["created"]


def test_the_last_season_ends_with_the_field_card(pg_client: TestClient, admin, field):
    body = generate(pg_client, admin, field, season_year=2025).json()
    by_type = {d["event_type"]: d for d in body["drafts"]}
    assert "card" in by_type and "decision" in by_type
    card = by_type["card"]
    assert card["event_date"] == "2025-12-31"
    for line in ("Zira tarla kartı", "Konya tarlası", "A) ", "B) Esnek nadas", "C) ", "geçici"):
        assert line in card["body"]
    assert "Zira karar vermez" in card["body"]
    # The rotation (wheat, fallow) starts with wheat in 2001, so 2025 is a wheat year again.
    assert by_type["decision"]["payload"]["planned_crop"] == "winter_wheat"


def test_english_drafts(pg_client: TestClient, admin, field):
    body = generate(pg_client, admin, field, locale="en").json()
    decision = next(d for d in body["drafts"] if d["event_type"] == "decision")
    assert decision["body"].startswith("Autumn decision, 1 Oct 2023.")
    assert "winter wheat" in decision["body"]


def test_a_season_outside_the_record_is_refused(pg_client: TestClient, admin, field):
    response = generate(pg_client, admin, field, season_year=2030)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "season_outside_record"


# --- The approval step -------------------------------------------------------------------


def first_draft(client, headers, field_id, event_type="heavy_rain") -> dict:
    drafts = generate(client, headers, field_id).json()["drafts"]
    return next(d for d in drafts if d["event_type"] == event_type)


def test_nothing_is_sent_until_a_draft_is_approved(pg_client: TestClient, admin, field, gateway):
    draft = first_draft(pg_client, admin, field)
    assert gateway.sent == []
    listed = pg_client.get("/api/v1/messages", params={"status": "pending"}, headers=admin).json()
    assert draft["id"] in [d["id"] for d in listed]


def test_approving_needs_a_recipient(pg_client: TestClient, admin, field, gateway):
    draft = first_draft(pg_client, admin, field)
    response = pg_client.post(f"/api/v1/messages/{draft['id']}/approve", json={}, headers=admin)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "no_recipient"
    assert gateway.sent == []


def test_an_approved_draft_goes_to_the_farmer(pg_client: TestClient, admin, field, gateway):
    draft = first_draft(pg_client, admin, field)
    response = pg_client.post(
        f"/api/v1/messages/{draft['id']}/approve", json={"recipient_phone": PHONE}, headers=admin
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "sent" and body["sent_at"]
    assert body["recipient_hint"] == "…4567"
    assert "recipient_phone" not in body
    assert gateway.sent == [("905321234567", draft["body"])]


def test_the_agronomist_can_edit_the_text_first(pg_client: TestClient, admin, field, gateway):
    draft = first_draft(pg_client, admin, field)
    edited = pg_client.patch(
        f"/api/v1/messages/{draft['id']}",
        json={"body": "Şiddetli yağış oldu, tarlaya girmeyin.", "recipient_phone": "05321234567"},
        headers=admin,
    )
    assert edited.status_code == 200 and edited.json()["has_recipient"] is True
    pg_client.post(f"/api/v1/messages/{draft['id']}/approve", json={}, headers=admin)
    assert gateway.sent == [("905321234567", "Şiddetli yağış oldu, tarlaya girmeyin.")]


def test_without_credentials_an_approved_draft_waits(pg_client: TestClient, admin, field):
    app.dependency_overrides[get_gateway] = lambda: None
    try:
        draft = first_draft(pg_client, admin, field)
        waiting = pg_client.post(
            f"/api/v1/messages/{draft['id']}/approve",
            json={"recipient_phone": PHONE},
            headers=admin,
        ).json()
        assert waiting["status"] == "approved" and waiting["error"] == "gateway_not_configured"
        assert (
            pg_client.get("/api/v1/messages/gateway", headers=admin).json()["configured"] is False
        )

        recorder = Recorder()
        app.dependency_overrides[get_gateway] = lambda: recorder
        sent = pg_client.post(f"/api/v1/messages/{draft['id']}/send", headers=admin).json()
        assert sent["status"] == "sent" and sent["error"] is None
        assert len(recorder.sent) == 1
    finally:
        app.dependency_overrides.pop(get_gateway, None)


def test_a_failed_send_is_recorded_and_can_be_retried(pg_client: TestClient, admin, field):
    broken = Recorder(fail=True)
    app.dependency_overrides[get_gateway] = lambda: broken
    try:
        draft = first_draft(pg_client, admin, field)
        failed = pg_client.post(
            f"/api/v1/messages/{draft['id']}/approve",
            json={"recipient_phone": PHONE},
            headers=admin,
        ).json()
        assert failed["status"] == "failed" and "466" in failed["error"]

        working = Recorder()
        app.dependency_overrides[get_gateway] = lambda: working
        retried = pg_client.post(f"/api/v1/messages/{draft['id']}/send", headers=admin).json()
        assert retried["status"] == "sent"
    finally:
        app.dependency_overrides.pop(get_gateway, None)


def test_a_rejected_or_sent_draft_cannot_be_decided_again(
    pg_client: TestClient, admin, field, gateway
):
    draft = first_draft(pg_client, admin, field)
    assert (
        pg_client.post(f"/api/v1/messages/{draft['id']}/reject", headers=admin).json()["status"]
        == "rejected"
    )
    again = pg_client.post(
        f"/api/v1/messages/{draft['id']}/approve", json={"recipient_phone": PHONE}, headers=admin
    )
    assert again.status_code == 422 and again.json()["detail"]["code"] == "not_editable"
    assert gateway.sent == []


def test_only_staff_who_review_may_decide(
    pg_client: TestClient, admin, field, make_user, bearer, gateway
):
    draft = first_draft(pg_client, admin, field)
    make_user("coop@example.com", Role.COOPERATIVE_USER, "Koop")
    coop = bearer("coop@example.com")
    # The cooperative user does not see another organization's field or its drafts.
    assert pg_client.get("/api/v1/messages", headers=coop).json() == []
    assert (
        pg_client.post(f"/api/v1/messages/{draft['id']}/approve", json={}, headers=coop).status_code
        == 403
    )
    assert (
        pg_client.post(
            f"/api/v1/fields/{field}/messages/generate", json={"season_year": 2023}, headers=coop
        ).status_code
        == 403
    )
    assert pg_client.get("/api/v1/messages").status_code == 401


# --- Pieces ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+90 532 123 45 67", "905321234567"),
        ("05321234567", "905321234567"),
        ("00905321234567", "905321234567"),
        ("905321234567", "905321234567"),
    ],
)
def test_phone_numbers_are_normalised(raw, expected):
    assert normalise_phone(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "abc", "1" * 16])
def test_a_bad_phone_number_is_refused(raw):
    with pytest.raises(ValueError):
        normalise_phone(raw)


def test_each_decision_variant_says_the_right_thing():
    config = get_config()
    day = date(2025, 10, 15)

    def say(crop, above):
        event = Event(
            "decision",
            day,
            {
                "storage_mm": 12.0,
                "taw_mm": 144.0,
                "threshold_mm": 60.0,
                "planned_crop": crop,
                "above_threshold": above,
            },
        )
        return render(event, locale="tr", config=config, field_name="x")

    assert "esnek kurala göre tarla nadasa bırakılır" in say("winter_wheat", False)
    assert "ekimini destekliyor" in say("winter_wheat", True)
    assert "tarlayı nadasa bırakın" in say(None, False)
    assert "bir ürünü taşıyabilir" in say(None, True)
    assert all(
        "Zira karar vermez" in say(c, a) for c in ("winter_wheat", None) for a in (True, False)
    )


def test_every_template_exists_in_both_languages():
    templates = get_config().messages.templates
    assert templates and all(set(texts) == {"tr", "en"} for texts in templates.values())


def test_the_gateway_client_sends_one_post_and_hides_its_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"], seen["json"] = str(request.url), request.read()
        return httpx.Response(200, json={"idMessage": "ABC"})

    client = GreenApiClient(
        base_url="https://api.green-api.com",
        instance_id="1101",
        token="SECRET",
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert client.send_text(PHONE, "Merhaba") == "ABC"
    assert seen["url"] == "https://api.green-api.com/waInstance1101/sendMessage/SECRET"
    assert b"905321234567@c.us" in seen["json"]

    refused = GreenApiClient(
        base_url="https://api.green-api.com",
        instance_id="1101",
        token="SECRET",
        http=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(466))),
    )
    with pytest.raises(GatewayError) as error:
        refused.send_text(PHONE, "x")
    assert "SECRET" not in str(error.value)


def test_the_gateway_needs_credentials():
    with pytest.raises(NotConfigured):
        GreenApiClient.from_settings(Settings(green_api_instance_id="", green_api_token=""))
    assert Settings(green_api_instance_id="1", green_api_token="t").whatsapp_configured
