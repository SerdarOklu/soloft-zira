"""Shared field queries: who may see a field, and the NASA data a field already has."""

from __future__ import annotations

from sqlalchemy import ColumnElement, ScalarSelect, func, select, true

from app.models import Field, Role, User, WeatherObservation
from app.services.power import SOURCE as POWER_SOURCE


def visible_to(user: User) -> ColumnElement[bool]:
    """Admins and agronomists see every field. A cooperative user sees the fields of their
    own organization, or only the ones they created when they belong to none."""
    if user.role in (Role.ADMIN, Role.AGRONOMIST):
        return true()
    if user.organization_id is not None:
        return Field.organization_id == user.organization_id
    return Field.created_by == user.id


def weather_days() -> ScalarSelect[int]:
    """Days of NASA POWER data stored for the field in the enclosing query."""
    return (
        select(func.count())
        .select_from(WeatherObservation)
        .where(
            WeatherObservation.field_id == Field.id,
            WeatherObservation.source == POWER_SOURCE,
        )
        .correlate(Field)
        .scalar_subquery()
    )
