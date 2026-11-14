"""Administrative commands.

    uv run python -m app.cli create-user --email a@b.c --name "Ada" --role admin
    uv run python -m app.cli seed-reference

The password is read from the ZIRA_PASSWORD environment variable or asked for
interactively; it is never taken from the command line, where it would end up in
shell history.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.core.parameters import Config, get_config
from app.core.security import hash_password
from app.models import CropType, DataSource, Role, User

MIN_PASSWORD_LENGTH = 10


def create_user(session: Session, *, email: str, name: str, role: Role, password: str) -> User:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    if not local or not domain or " " in email:
        raise ValueError(f"'{email}' is not an email address")
    if session.scalar(select(User).where(func.lower(User.email) == email)):
        raise ValueError(f"A user with email {email} already exists")
    user = User(email=email, name=name, role=role, password_hash=hash_password(password))
    session.add(user)
    session.flush()
    return user


def _bounds(value: float | tuple[float, float]) -> tuple[float, float]:
    return value if isinstance(value, tuple) else (value, value)


def seed_reference(session: Session, config: Config) -> dict[str, int]:
    """Copy crops and data sources from config/ into their tables. Safe to run again."""
    crops = {row.key: row for row in session.scalars(select(CropType))}
    for key, crop in config.crops.items():
        row = crops.get(key) or CropType(key=key)
        kc_ini = crop.kc_ini
        if isinstance(kc_ini, float):
            row.kc_ini, row.kc_ini_non_frozen = kc_ini, None
        else:
            row.kc_ini, row.kc_ini_non_frozen = kc_ini.frozen_soil, kc_ini.non_frozen_soil
        row.name = crop.name_tr
        row.season_type = crop.season_type
        row.is_legume = crop.is_legume
        row.kc_mid_min, row.kc_mid_max = _bounds(crop.kc_mid)
        row.kc_end_min, row.kc_end_max = _bounds(crop.kc_end)
        row.height_m = crop.height_m
        row.zr_min_m, row.zr_max_m = crop.zr_m
        row.p = crop.p
        if crop.stage_lengths_days:
            row.l_ini, row.l_dev, row.l_mid, row.l_late = crop.stage_lengths_days
        session.add(row)

    sources = {row.key: row for row in session.scalars(select(DataSource))}
    for key, source in config.data_sources.items():
        row = sources.get(key) or DataSource(key=key)
        row.name = source.name
        row.collection_id = source.collection_id
        row.resolution = source.resolution
        session.add(row)

    session.flush()
    return {"crop_types": len(config.crops), "data_sources": len(config.data_sources)}


def _read_password() -> str:
    password = os.environ.get("ZIRA_PASSWORD")
    if password:
        return password
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        raise ValueError("Passwords do not match")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    user = commands.add_parser("create-user", help="create a user account")
    user.add_argument("--email", required=True)
    user.add_argument("--name", required=True)
    user.add_argument(
        "--role",
        required=True,
        choices=[Role.ADMIN.value, Role.AGRONOMIST.value, Role.COOPERATIVE_USER.value],
    )

    commands.add_parser("seed-reference", help="load crops and data sources from config/")

    args = parser.parse_args(argv)
    try:
        with Session(get_engine()) as session, session.begin():
            if args.command == "create-user":
                created = create_user(
                    session,
                    email=args.email,
                    name=args.name,
                    role=Role(args.role),
                    password=_read_password(),
                )
                print(f"Created {created.role.value} {created.email}")
            else:
                counts = seed_reference(session, get_config())
                print(f"Seeded {counts['crop_types']} crops, {counts['data_sources']} data sources")
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
