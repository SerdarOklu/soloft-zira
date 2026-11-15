"""Passwordless sign-in for farmers: a one-time link and a one-time WhatsApp code.

The gateway is replaced by a recorder; nothing is really sent.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.messages import get_gateway
from app.core.config import get_settings
from app.main import app
from app.models import LoginToken, Role, User
from app.services.login import MAX_CODES_PER_HOUR, MAX_WRONG_CODES

pytestmark = pytest.mark.db

PHONE = "0532 123 45 67"
STORED = "905321234567"


class Recorder:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_text(self, phone: str, body: str) -> str:
        self.sent.append((phone, body))
        return "ID"

    def last_code(self) -> str:
        match = re.search(r"\b(\d{6})\b", self.sent[-1][1])
        assert match
        return match.group(1)


@pytest.fixture
def gateway():
    recorder = Recorder()
    app.dependency_overrides[get_gateway] = lambda: recorder
    yield recorder
    app.dependency_overrides.pop(get_gateway, None)


@pytest.fixture
def coop(make_user, bearer):
    make_user("koop@example.com", Role.COOPERATIVE_USER, "Koop")
    return bearer("koop@example.com")


@pytest.fixture
def farmer(pg_client: TestClient, coop) -> dict:
    """A farmer made without a password, with a phone number."""
    made = pg_client.post(
        "/api/v1/users",
        json={"name": "Ali", "email": "ali@example.com", "phone": PHONE, "role": "farmer"},
        headers=coop,
    )
    assert made.status_code == 201, made.text
    return made.json()


def link_for(client, headers, user_id) -> str:
    response = client.post(f"/api/v1/users/{user_id}/login-link", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["token"]


def redeem(client, token):
    return client.post("/api/v1/auth/link/redeem", json={"token": token})


def request_code(client, phone=PHONE):
    return client.post("/api/v1/auth/code/request", json={"phone": phone})


def verify(client, code, phone=PHONE):
    return client.post("/api/v1/auth/code/verify", json={"phone": phone, "code": code})


# --- accounts -------------------------------------------------------------------------------


def test_a_farmer_can_be_made_without_a_password_and_cannot_sign_in_with_one(
    pg_client: TestClient, farmer
):
    assert farmer["phone"] == STORED and farmer["role"] == "farmer"
    tried = pg_client.post(
        "/api/v1/auth/login", json={"email": "ali@example.com", "password": "anything-at-all-1"}
    )
    assert tried.status_code == 401


def test_staff_accounts_still_need_a_password(pg_client: TestClient, make_user, bearer):
    make_user("admin@example.com", Role.ADMIN)
    headers = bearer("admin@example.com")
    made = pg_client.post(
        "/api/v1/users",
        json={"name": "Mühendis", "email": "m@example.com", "role": "agronomist"},
        headers=headers,
    )
    assert made.status_code == 422 and made.json()["detail"]["code"] == "password_required"


def test_a_phone_number_belongs_to_one_account_and_must_be_a_number(
    pg_client: TestClient, coop, farmer
):
    same = pg_client.post(
        "/api/v1/users",
        json={"name": "Veli", "email": "veli@example.com", "phone": "+90 532 123 45 67"},
        headers=coop,
    )
    assert same.status_code == 422 and same.json()["detail"]["code"] == "phone_taken"
    bad = pg_client.post(
        "/api/v1/users",
        json={"name": "Veli", "email": "veli@example.com", "phone": "12"},
        headers=coop,
    )
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "invalid_phone"


# --- link -----------------------------------------------------------------------------------


def test_a_link_signs_a_farmer_in_once(pg_client: TestClient, coop, farmer):
    token = link_for(pg_client, coop, farmer["id"])
    first = redeem(pg_client, token)
    assert first.status_code == 200
    body = first.json()
    assert body["user"]["role"] == "farmer" and body["user"]["email"] == "ali@example.com"
    assert body["expires_in"] == get_settings().farmer_session_days * 86400
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert pg_client.get("/api/v1/farmer/summary", headers=headers).status_code == 200
    # The same link is dead after one use, and the farmer still reaches nothing of the staff.
    assert redeem(pg_client, token).status_code == 401
    assert pg_client.get("/api/v1/users", headers=headers).status_code == 403


def test_only_a_hash_of_the_link_is_stored(pg_client: TestClient, pg, coop, farmer):
    token = link_for(pg_client, coop, farmer["id"])
    with Session(pg) as db:
        stored = db.scalars(select(LoginToken)).all()
    assert (
        len(stored) == 1 and token not in stored[0].secret_hash and len(stored[0].secret_hash) == 64
    )


def test_a_new_link_replaces_the_old_one(pg_client: TestClient, coop, farmer):
    old = link_for(pg_client, coop, farmer["id"])
    new = link_for(pg_client, coop, farmer["id"])
    assert redeem(pg_client, old).status_code == 401
    assert redeem(pg_client, new).status_code == 200


def test_an_expired_link_is_refused(pg_client: TestClient, pg, coop, farmer):
    token = link_for(pg_client, coop, farmer["id"])
    with Session(pg) as db, db.begin():
        for row in db.scalars(select(LoginToken)):
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    assert redeem(pg_client, token).status_code == 401


def test_a_link_for_a_farmer_who_was_closed_is_refused(pg_client: TestClient, coop, farmer):
    token = link_for(pg_client, coop, farmer["id"])
    pg_client.patch(f"/api/v1/users/{farmer['id']}", json={"is_active": False}, headers=coop)
    assert redeem(pg_client, token).status_code == 401
    refused = pg_client.post(f"/api/v1/users/{farmer['id']}/login-link", headers=coop)
    assert refused.status_code == 422


def test_a_made_up_link_is_refused(pg_client: TestClient, farmer):
    assert redeem(pg_client, "x" * 43).status_code == 401


def test_links_are_for_farmers_of_your_own_organization_only(
    pg_client: TestClient, make_user, bearer, farmer
):
    make_user("baska@example.com", Role.COOPERATIVE_USER, "Baska")
    other = bearer("baska@example.com")
    assert (
        pg_client.post(f"/api/v1/users/{farmer['id']}/login-link", headers=other).status_code == 404
    )


def test_a_link_cannot_be_made_for_a_staff_account_or_by_a_farmer(
    pg_client: TestClient, pg, make_user, bearer, coop, farmer
):
    make_user("admin@example.com", Role.ADMIN)
    admin_id = pg_client.get("/api/v1/auth/me", headers=bearer("admin@example.com")).json()["id"]
    assert pg_client.post(f"/api/v1/users/{admin_id}/login-link", headers=coop).status_code == 404
    farmer_headers = {
        "Authorization": "Bearer "
        + redeem(pg_client, link_for(pg_client, coop, farmer["id"])).json()["access_token"]
    }
    assert (
        pg_client.post(
            f"/api/v1/users/{farmer['id']}/login-link", headers=farmer_headers
        ).status_code
        == 403
    )


# --- code -----------------------------------------------------------------------------------


def test_a_code_goes_to_the_farmers_whatsapp_and_signs_them_in_once(
    pg_client: TestClient, farmer, gateway
):
    assert request_code(pg_client).status_code == 202
    assert [phone for phone, _ in gateway.sent] == [STORED]
    assert "Kodu kimseyle paylaşmayın" in gateway.sent[0][1]
    code = gateway.last_code()
    signed = verify(pg_client, code)
    assert signed.status_code == 200 and signed.json()["user"]["role"] == "farmer"
    assert signed.json()["expires_in"] == get_settings().farmer_session_days * 86400
    assert verify(pg_client, code).status_code == 401


def test_a_wrong_code_is_refused_and_too_many_kill_the_code(pg_client: TestClient, farmer, gateway):
    request_code(pg_client)
    code = gateway.last_code()
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(MAX_WRONG_CODES):
        assert verify(pg_client, wrong).status_code == 401
    # Even the right code no longer works: the farmer asks for a new one.
    assert verify(pg_client, code).status_code == 401


def test_an_expired_code_is_refused(pg_client: TestClient, pg, farmer, gateway):
    request_code(pg_client)
    with Session(pg) as db, db.begin():
        for row in db.scalars(select(LoginToken)):
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert verify(pg_client, gateway.last_code()).status_code == 401


def test_a_new_code_replaces_the_old_one(pg_client: TestClient, farmer, gateway):
    request_code(pg_client)
    first = gateway.last_code()
    request_code(pg_client)
    second = gateway.last_code()
    if first != second:
        assert verify(pg_client, first).status_code == 401
    assert verify(pg_client, second).status_code == 200


def test_only_a_hash_of_the_code_is_stored(pg_client: TestClient, pg, farmer, gateway):
    request_code(pg_client)
    code = gateway.last_code()
    with Session(pg) as db:
        row = db.scalars(select(LoginToken)).one()
    assert code not in row.secret_hash and len(row.secret_hash) == 64


def test_codes_are_limited_per_hour(pg_client: TestClient, farmer, gateway):
    for _ in range(MAX_CODES_PER_HOUR + 2):
        assert request_code(pg_client).status_code == 202
    assert len(gateway.sent) == MAX_CODES_PER_HOUR


def test_the_answer_does_not_tell_whether_a_number_has_an_account(
    pg_client: TestClient, farmer, gateway
):
    known = request_code(pg_client)
    unknown = request_code(pg_client, "0555 000 11 22")
    garbage = request_code(pg_client, "abc")
    assert known.status_code == unknown.status_code == garbage.status_code == 202
    assert known.json() == unknown.json() == garbage.json()
    assert len(gateway.sent) == 1
    assert verify(pg_client, "123456", "0555 000 11 22").status_code == 401


def test_a_staff_phone_never_gets_a_code(pg_client: TestClient, pg, make_user, gateway):
    make_user("admin@example.com", Role.ADMIN)
    with Session(pg) as db, db.begin():
        db.scalars(select(User).where(User.email == "admin@example.com")).one().phone = STORED
    assert request_code(pg_client).status_code == 202
    assert gateway.sent == []
    assert verify(pg_client, "123456").status_code == 401


def test_a_closed_farmer_gets_no_code(pg_client: TestClient, coop, farmer, gateway):
    pg_client.patch(f"/api/v1/users/{farmer['id']}", json={"is_active": False}, headers=coop)
    assert request_code(pg_client).status_code == 202
    assert gateway.sent == []


def test_without_a_gateway_the_code_is_unavailable(pg_client: TestClient, farmer):
    app.dependency_overrides[get_gateway] = lambda: None
    try:
        response = request_code(pg_client)
    finally:
        app.dependency_overrides.pop(get_gateway, None)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "code_unavailable"


def test_a_code_must_be_six_digits(pg_client: TestClient, farmer, gateway):
    assert verify(pg_client, "12345").status_code == 422
    assert verify(pg_client, "abcdef").status_code == 422


def test_a_farmer_session_from_a_code_reaches_only_the_farmers_screens(
    pg_client: TestClient, farmer, gateway
):
    request_code(pg_client)
    token = verify(pg_client, gateway.last_code()).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert pg_client.get("/api/v1/farmer/summary", headers=headers).status_code == 200
    assert pg_client.get("/api/v1/data-center/sources", headers=headers).status_code == 403
    assert pg_client.get("/api/v1/users", headers=headers).status_code == 403
    assert pg_client.get(f"/api/v1/fields/{uuid.uuid4()}", headers=headers).status_code == 404
