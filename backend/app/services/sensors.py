"""Field soil-moisture sensors: calibration, the state on a day, and node status (PDT 7.9, 12).

A sensor reports volumetric water content (VWC, m3/m3) at several depths. It is trusted only after
a calibration exists for the field (gravimetric, per soil type), and only while it keeps reporting:
after ``sensor_silence_h`` hours without data the field falls back to satellite mode.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SensorCalibration, SensorObservation


@dataclass(frozen=True)
class SensorState:
    """Root-zone water read from the sensors on one day."""

    available_fraction: float  # 0 at the wilting point, 1 at field capacity
    nodes: int
    depths_cm: tuple[int, ...]
    measured_at: datetime  # the newest reading used
    vwc_by_depth: dict[int, float]  # calibrated, mean over nodes


def calibrate(raw: float, calibration: SensorCalibration | None) -> float | None:
    """The calibrated VWC, or None while the field has no calibration."""
    if calibration is None:
        return None
    return calibration.slope * raw + calibration.intercept


def layer_thicknesses(depths_cm: list[int]) -> dict[int, float]:
    """Thickness in cm of the soil each sensor represents: layers split halfway between sensors,
    the first from the surface and the last as far below its sensor as the layer above reaches."""
    ordered = sorted(depths_cm)
    edges = [0.0]
    for upper, lower in zip(ordered, ordered[1:], strict=False):
        edges.append((upper + lower) / 2)
    edges.append(ordered[-1] + (ordered[-1] - edges[-1]))
    return {depth: edges[i + 1] - edges[i] for i, depth in enumerate(ordered)}


def available_fraction(
    vwc_by_depth: dict[int, float], *, theta_wp: float, theta_fc: float
) -> float:
    """Depth-weighted share of the plant-available water the soil holds (PDT 7.9)."""
    thickness = layer_thicknesses(list(vwc_by_depth))
    span = theta_fc - theta_wp
    total = sum(thickness.values())
    weighted = sum(
        thickness[depth] * min(1.0, max(0.0, (vwc - theta_wp) / span))
        for depth, vwc in vwc_by_depth.items()
    )
    return weighted / total


def end_of_day(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=UTC)


def calibration_of(session: Session, field_id) -> SensorCalibration | None:
    return session.scalar(select(SensorCalibration).where(SensorCalibration.field_id == field_id))


def sensor_state(
    session: Session,
    field_id,
    at: datetime,
    *,
    silence_h: float,
    min_depths: int = 2,
) -> SensorState | None:
    """What the sensors say at ``at``, or None: no calibration, no recent data, or too few depths.

    Each node's newest reading per depth in the ``silence_h`` hours before ``at`` counts; the
    nodes are averaged per depth, because a field has three or four of them.
    """
    calibration = calibration_of(session, field_id)
    if calibration is None:
        return None
    rows = session.scalars(
        select(SensorObservation)
        .where(
            SensorObservation.field_id == field_id,
            SensorObservation.measured_at <= at,
            SensorObservation.measured_at > at - timedelta(hours=silence_h),
        )
        .order_by(SensorObservation.measured_at)
    ).all()
    newest: dict[tuple[str, int], SensorObservation] = {}
    for row in rows:  # ascending, so the last one per node and depth wins
        newest[(row.node_id, row.depth_cm)] = row
    if not newest:
        return None
    by_depth: dict[int, list[float]] = defaultdict(list)
    for (_, depth), row in newest.items():
        by_depth[depth].append(calibrate(row.vwc_raw, calibration))  # type: ignore[arg-type]
    if len(by_depth) < min_depths:
        return None
    vwc = {depth: sum(values) / len(values) for depth, values in by_depth.items()}
    return SensorState(
        available_fraction=available_fraction(
            vwc, theta_wp=calibration.theta_wp, theta_fc=calibration.theta_fc
        ),
        nodes=len({node for node, _ in newest}),
        depths_cm=tuple(sorted(vwc)),
        measured_at=max(row.measured_at for row in newest.values()),
        vwc_by_depth=vwc,
    )
