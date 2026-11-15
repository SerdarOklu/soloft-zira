"""Demo sign-in by role, and the demo seed (jury demo)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.cli import create_user
from app.core.config import get_settings
from app.core.parameters import get_config
from app.models import Field, Role, SensorCalibration, User
from app.services.demo import DEMO_FIELD_CODE, seed_demo

pytestmark = pytest.mark.db


@pytest.fixture
def demo_on(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEMO_ROLE_LOGIN", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _seed(pg: Engine):
    with Session(pg) as db:
        return seed_demo(db, get_config())


def test_off_by_default_even_when_seeded(pg: Engine, pg_client: TestClient):
    _seed(pg)
    assert pg_client.get("/api/v1/auth/demo/roles").json() == {"enabled": False, "roles": []}
    refused = pg_client.post("/api/v1/auth/demo/login", json={"role": "admin"})
    assert refused.status_code == 404


def test_enabled_but_not_seeded_lists_nothing(pg: Engine, pg_client: TestClient, demo_on):
    assert pg_client.get("/api/v1/auth/demo/roles").json()["enabled"] is False
    refused = pg_client.post("/api/v1/auth/demo/login", json={"role": "admin"})
    assert refused.status_code == 404


def test_each_role_signs_in_without_a_password(pg: Engine, pg_client: TestClient, demo_on):
    _seed(pg)
    roles = pg_client.get("/api/v1/auth/demo/roles").json()
    assert roles["enabled"] is True
    assert [r["role"] for r in roles["roles"]] == [
        "admin",
        "agronomist",
        "cooperative_user",
        "farmer",
    ]
    for role in ("admin", "agronomist", "cooperative_user", "farmer"):
        response = pg_client.post("/api/v1/auth/demo/login", json={"role": role})
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == role
        token = response.json()["access_token"]
        me = pg_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.json()["email"].endswith("@demo.zira")


def test_demo_accounts_have_no_usable_password(pg: Engine, pg_client: TestClient, demo_on):
    _seed(pg)
    for guess in ("demo", "password", "a-long-enough-password"):
        response = pg_client.post(
            "/api/v1/auth/login", json={"email": "demo-admin@demo.zira", "password": guess}
        )
        assert response.status_code == 401


def test_a_real_user_cannot_be_entered_this_way(
    pg: Engine, pg_client: TestClient, demo_on, make_user
):
    make_user("real.admin@example.com", Role.ADMIN)
    # No demo accounts are seeded, and a real admin is never picked by role.
    refused = pg_client.post("/api/v1/auth/demo/login", json={"role": "admin"})
    assert refused.status_code == 404


def test_a_deactivated_demo_account_is_not_offered(pg: Engine, pg_client: TestClient, demo_on):
    _seed(pg)
    with Session(pg) as db, db.begin():
        user = db.scalar(select(User).where(User.email == "demo-farmer@demo.zira"))
        user.is_active = False
    roles = [r["role"] for r in pg_client.get("/api/v1/auth/demo/roles").json()["roles"]]
    assert "farmer" not in roles
    refused = pg_client.post("/api/v1/auth/demo/login", json={"role": "farmer"})
    assert refused.status_code == 404


def test_seed_creates_the_field_linked_to_the_farmer_and_is_repeatable(pg: Engine):
    first = _seed(pg)
    assert len(first.created_users) == 4 and first.field_created and first.calibration_set
    again = _seed(pg)
    assert again.created_users == [] and not again.field_created and not again.calibration_set

    with Session(pg) as db:
        fields = list(db.scalars(select(Field).where(Field.code == DEMO_FIELD_CODE)))
        assert len(fields) == 1
        demo_field = fields[0]
        farmer = db.scalar(select(User).where(User.role == Role.FARMER))
        assert demo_field.farmer_user_id == farmer.id
        assert demo_field.area_ha and 3 < demo_field.area_ha < 15
        assert db.scalar(
            select(SensorCalibration).where(SensorCalibration.field_id == demo_field.id)
        )


def test_the_demo_farmer_sees_only_their_field(pg: Engine, pg_client: TestClient, demo_on):
    _seed(pg)
    with Session(pg) as db, db.begin():
        agronomist = db.scalar(select(User).where(User.role == Role.AGRONOMIST))
        other = create_user(
            db, email="other@example.com", name="Other", role=Role.FARMER, password="x" * 12
        )
        db.add(
            Field(
                code="ZR-OTHER",
                name="Another farmer",
                created_by=agronomist.id,
                farmer_user_id=other.id,
            )
        )
    token = pg_client.post("/api/v1/auth/demo/login", json={"role": "farmer"}).json()[
        "access_token"
    ]
    fields = pg_client.get("/api/v1/fields", headers={"Authorization": f"Bearer {token}"}).json()
    assert [f["code"] for f in fields] == [DEMO_FIELD_CODE]


def test_seed_writes_drafts_from_the_model_without_a_recipient(pg: Engine):
    from datetime import date

    from sqlalchemy import text

    from app.models import MessageDraft
    from tests.test_water_vault_api import store, weather

    _seed(pg)
    with Session(pg) as db:
        demo_field = db.scalar(select(Field).where(Field.code == DEMO_FIELD_CODE))
        field_id = str(demo_field.id)
    with pg.begin() as connection:
        connection.execute(
            text("UPDATE fields SET elevation_m = 1000 WHERE id = :id"), {"id": field_id}
        )
    rows = weather(date(2001, 1, 1), date(2025, 12, 31), rain=3.0)
    for row in rows:
        if row["date"] == date(2024, 3, 10):
            row["precipitation_mm"] = 25.0
    store(pg, field_id, rows)

    with Session(pg) as db:
        report = seed_demo(db, get_config(), draft_season=2023)
    assert report.drafts_created >= 2
    with Session(pg) as db:
        drafts = list(db.scalars(select(MessageDraft)))
        assert all(d.status == "pending" and d.recipient_phone is None for d in drafts)
        assert all(d.body.strip() for d in drafts)
        decisions = [d for d in drafts if d.event_type == "decision"]
        assert decisions and all("Zira karar vermez" in d.body for d in decisions)
    with Session(pg) as db:
        again = seed_demo(db, get_config(), draft_season=2023)
    assert again.drafts_created == 0
