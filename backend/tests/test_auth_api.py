from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.cli import create_user
from app.main import app
from app.models import Role, User

PASSWORD = "a-long-enough-password"


@pytest.fixture
def agronomist(session: Session) -> User:
    user = create_user(
        session, email="Ayse@Example.com", name="Ayşe", role=Role.AGRONOMIST, password=PASSWORD
    )
    session.commit()
    return user


def _login(client: TestClient, email: str = "ayse@example.com", password: str = PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_returns_token_and_user(client: TestClient, agronomist: User):
    response = _login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"] == {
        "id": str(agronomist.id),
        "email": "ayse@example.com",
        "name": "Ayşe",
        "role": "agronomist",
        "organization_id": None,
    }
    assert "password" not in str(body)


def test_login_is_case_insensitive_on_email(client: TestClient, agronomist: User):
    assert _login(client, email="AYSE@example.com").status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [("ayse@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)],
)
def test_login_fails_the_same_way_for_wrong_password_and_unknown_email(
    client: TestClient, agronomist: User, email: str, password: str
):
    response = _login(client, email=email, password=password)
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_malformed_email_is_a_401_not_a_validation_error(client: TestClient, agronomist: User):
    assert _login(client, email="not-an-email").status_code == 401


def test_internal_domains_can_sign_in(client: TestClient, session: Session):
    create_user(session, email="admin@zira.local", name="A", role=Role.ADMIN, password=PASSWORD)
    session.commit()
    assert _login(client, email="admin@zira.local").status_code == 200


def test_inactive_user_cannot_sign_in(client: TestClient, agronomist: User, session: Session):
    agronomist.is_active = False
    session.commit()
    assert _login(client).status_code == 401


def test_me_requires_a_token(client: TestClient):
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401


def test_me_returns_the_signed_in_user(client: TestClient, agronomist: User):
    token = _login(client).json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "ayse@example.com"


def test_token_of_a_deactivated_user_stops_working(
    client: TestClient, agronomist: User, session: Session
):
    token = _login(client).json()["access_token"]
    agronomist.is_active = False
    session.commit()
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_role_check_is_enforced_by_the_api(client: TestClient, agronomist: User):
    @app.get("/_test/admin-only")
    def admin_only(
        user: Annotated[User, Depends(require_roles(Role.ADMIN))],
    ) -> dict[str, str]:
        return {"ok": user.email}

    try:
        token = _login(client).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/_test/admin-only", headers=headers).status_code == 403
        assert client.get("/_test/admin-only").status_code == 401
    finally:
        app.router.routes[:] = [
            route
            for route in app.router.routes
            if getattr(route, "path", "") != "/_test/admin-only"
        ]
