import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cli import create_user, seed_reference
from app.core.config import get_settings
from app.core.parameters import load_config
from app.core.security import verify_password
from app.models import CropType, DataSource, Role, User


def test_create_user_stores_a_hash_and_normalises_email(session: Session):
    user = create_user(
        session,
        email="  Admin@Example.com ",
        name="Admin",
        role=Role.ADMIN,
        password="a-long-password",
    )
    assert user.email == "admin@example.com"
    assert user.password_hash != "a-long-password"
    assert verify_password("a-long-password", user.password_hash)
    assert user.is_active


def test_create_user_rejects_a_non_email(session: Session):
    with pytest.raises(ValueError, match="not an email"):
        create_user(session, email="admin", name="A", role=Role.ADMIN, password="long-enough-pw")


def test_create_user_rejects_short_password_and_duplicates(session: Session):
    with pytest.raises(ValueError, match="at least"):
        create_user(session, email="a@example.com", name="A", role=Role.ADMIN, password="short")
    create_user(
        session, email="a@example.com", name="A", role=Role.ADMIN, password="long-enough-pw"
    )
    with pytest.raises(ValueError, match="already exists"):
        create_user(
            session, email="A@example.com", name="B", role=Role.ADMIN, password="long-enough-pw"
        )
    assert session.scalar(select(func.count()).select_from(User)) == 1


def test_seed_reference_is_repeatable(session: Session):
    config = load_config(get_settings().config_dir)
    assert seed_reference(session, config) == {"crop_types": 8, "data_sources": 9}
    seed_reference(session, config)
    assert session.scalar(select(func.count()).select_from(CropType)) == 8
    assert session.scalar(select(func.count()).select_from(DataSource)) == 9

    wheat = session.scalar(select(CropType).where(CropType.key == "winter_wheat"))
    assert (wheat.kc_ini, wheat.kc_ini_non_frozen) == (0.4, 0.7)
    assert (wheat.kc_end_min, wheat.kc_end_max) == (0.25, 0.4)
    assert (wheat.zr_min_m, wheat.zr_max_m) == (1.5, 1.8)
    assert wheat.l_ini is None  # stage lengths are not set until the agronomist sets them

    barley = session.scalar(select(CropType).where(CropType.key == "barley"))
    assert barley.kc_mid_min == barley.kc_mid_max == 1.15
    assert barley.season_type is None

    landsat = session.scalar(select(DataSource).where(DataSource.key == "landsat8"))
    assert landsat.collection_id == "LANDSAT/LC08/C02/T1_L2"
