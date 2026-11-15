"""Sensors: ingest from a node or the simulator, calibration, and node status (phase 7)."""

from __future__ import annotations

import hmac
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import SessionDep, require_roles
from app.core.config import get_settings
from app.core.parameters import get_config
from app.models import Field, Role, SensorCalibration, SensorObservation, User
from app.schemas.sensors import (
    CalibrationIn,
    CalibrationOut,
    IngestOut,
    NodeReading,
    NodeStatus,
    ReadingsIn,
    SensorStatusOut,
)
from app.services import sensors as service
from app.services.fields import visible_to

ingest_router = APIRouter(prefix="/sensors", tags=["sensors"])
router = APIRouter(prefix="/fields/{field_id}", tags=["sensors"])

NODE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_FUTURE = timedelta(hours=1)

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]
Calibrator = Annotated[User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST))]


def _refuse(code: str, http_status: int = status.HTTP_422_UNPROCESSABLE_CONTENT):
    return HTTPException(http_status, detail={"code": code})


def _silence_h() -> float:
    return float(get_config().parameters.get("sensors", "sensor_silence_h"))


@ingest_router.post("/{node_id}/readings", response_model=IngestOut)
def ingest(
    node_id: Annotated[str, Path(min_length=1, max_length=64)],
    body: ReadingsIn,
    session: SessionDep,
    x_sensor_key: Annotated[str | None, Header()] = None,
) -> IngestOut:
    """A node (or the simulator) posts one reading per depth. The calling device proves itself
    with the shared key in ``X-Sensor-Key``; with no key set on the server, ingest is off."""
    expected = get_settings().sensor_ingest_key
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "ingest_disabled"})
    if x_sensor_key is None or not hmac.compare_digest(x_sensor_key, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": "bad_sensor_key"})
    if not NODE_ID.match(node_id):
        raise _refuse("invalid_node_id")
    if body.measured_at > datetime.now(UTC) + MAX_FUTURE:
        raise _refuse("reading_in_the_future")
    if session.get(Field, body.field_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "unknown_field"})
    owner = session.scalar(
        select(SensorObservation.field_id).where(SensorObservation.node_id == node_id).limit(1)
    )
    if owner is not None and owner != body.field_id:
        raise _refuse("node_belongs_to_another_field", status.HTTP_409_CONFLICT)

    calibration = service.calibration_of(session, body.field_id)
    rows = [
        {
            "field_id": body.field_id,
            "node_id": node_id,
            "measured_at": body.measured_at,
            "depth_cm": reading.depth_cm,
            "vwc_raw": reading.vwc_raw,
            "vwc_calibrated": service.calibrate(reading.vwc_raw, calibration),
            "battery": body.battery_v,
            "is_simulated": body.is_simulated,
        }
        for reading in body.readings
    ]
    statement = insert(SensorObservation).values(rows)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["node_id", "measured_at", "depth_cm"],
            set_={
                "vwc_raw": statement.excluded.vwc_raw,
                "vwc_calibrated": statement.excluded.vwc_calibrated,
                "battery": statement.excluded.battery,
                "is_simulated": statement.excluded.is_simulated,
            },
        )
    )
    session.commit()
    return IngestOut(stored=len(rows), calibrated=calibration is not None)


def _field(session: SessionDep, user: User, field_id: uuid.UUID) -> Field:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


def _calibration_out(row: SensorCalibration) -> CalibrationOut:
    return CalibrationOut(
        slope=row.slope,
        intercept=row.intercept,
        theta_wp=row.theta_wp,
        theta_fc=row.theta_fc,
        note=row.note,
        calibrated_at=row.calibrated_at,
    )


@router.get("/sensor-calibration", response_model=CalibrationOut | None)
def read_calibration(
    field_id: uuid.UUID, session: SessionDep, user: StaffUser
) -> CalibrationOut | None:
    field = _field(session, user, field_id)
    row = service.calibration_of(session, field.id)
    return _calibration_out(row) if row else None


@router.put("/sensor-calibration", response_model=CalibrationOut)
def write_calibration(
    field_id: uuid.UUID, body: CalibrationIn, session: SessionDep, user: Calibrator
) -> CalibrationOut:
    """Record the gravimetric calibration of the field's sensors (agronomist or admin)."""
    field = _field(session, user, field_id)
    row = service.calibration_of(session, field.id)
    if row is None:
        row = SensorCalibration(field_id=field.id, theta_wp=body.theta_wp, theta_fc=body.theta_fc)
        session.add(row)
    row.slope, row.intercept = body.slope, body.intercept
    row.theta_wp, row.theta_fc, row.note = body.theta_wp, body.theta_fc, body.note
    row.calibrated_by = user.id
    row.calibrated_at = datetime.now(UTC)
    session.commit()
    session.refresh(row)
    return _calibration_out(row)


@router.get("/sensors", response_model=SensorStatusOut)
def sensor_status(field_id: uuid.UUID, session: SessionDep, user: StaffUser) -> SensorStatusOut:
    """The nodes of a field, their newest reading per depth, and whether the field is in sensor
    mode or has fallen back to satellite mode."""
    field = _field(session, user, field_id)
    silence = _silence_h()
    now = datetime.now(UTC)
    calibration = service.calibration_of(session, field.id)

    latest_per_node = (
        select(SensorObservation.node_id, func.max(SensorObservation.measured_at).label("seen"))
        .where(SensorObservation.field_id == field.id)
        .group_by(SensorObservation.node_id)
        .subquery()
    )
    nodes: list[NodeStatus] = []
    for node_id, seen in session.execute(
        select(latest_per_node.c.node_id, latest_per_node.c.seen).order_by(
            latest_per_node.c.node_id
        )
    ):
        rows = session.scalars(
            select(SensorObservation)
            .where(
                SensorObservation.field_id == field.id,
                SensorObservation.node_id == node_id,
                SensorObservation.measured_at == seen,
            )
            .order_by(SensorObservation.depth_cm)
        ).all()
        nodes.append(
            NodeStatus(
                node_id=node_id,
                last_seen=seen,
                status="active" if now - seen <= timedelta(hours=silence) else "silent",
                battery_v=next((r.battery for r in rows if r.battery is not None), None),
                is_simulated=any(r.is_simulated for r in rows),
                readings=[
                    NodeReading(
                        depth_cm=r.depth_cm,
                        vwc_raw=r.vwc_raw,
                        vwc_calibrated=service.calibrate(r.vwc_raw, calibration),
                    )
                    for r in rows
                ],
            )
        )
    state = service.sensor_state(session, field.id, now, silence_h=silence)
    return SensorStatusOut(
        field_id=field.id,
        mode="sensor" if state else "satellite",
        silence_h=silence,
        calibration=_calibration_out(calibration) if calibration else None,
        nodes=nodes,
    )
