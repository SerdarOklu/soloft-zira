"""When a message is worth writing: events read from the daily trace of the current rotation.

Pure functions over the trace of strategy A (the rotation the farmer follows). The numbers in
each event are the model's own, so the draft can say what it rests on.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.services.water.rotation import DayTrace, SeasonResult

LEACHING_QUIET_DAYS = 3  # one warning per episode, not one per day


@dataclass(frozen=True)
class Event:
    type: str
    day: date
    payload: dict[str, Any]


@dataclass(frozen=True)
class Thresholds:
    heavy_rain_mm: float
    leaching_mm: float
    stress_day_marks: tuple[int, ...]


def detect_events(
    trace: Sequence[DayTrace],
    results: Sequence[SeasonResult],
    *,
    window: tuple[date, date],
    crop_for_year: Callable[[int], str | None],
    decision: tuple[int, int],
    taw_mm: float,
    flex_threshold_mm: float,
    thresholds: Thresholds,
    season_lengths: dict[str, int],
    sowing_dates: dict[str, tuple[int, int]],
    sufficient_for: Callable[[SeasonResult], bool],
    with_card: bool,
) -> list[Event]:
    start, end = window
    by_day = {t.day: t for t in trace}
    events: list[Event] = []

    # Decision day of each autumn inside the window.
    for year in range(start.year, end.year + 1):
        day = date(year, *decision)
        if not start <= day <= end or day not in by_day:
            continue
        storage = by_day[day].storage
        events.append(
            Event(
                "decision",
                day,
                {
                    "storage_mm": storage,
                    "taw_mm": taw_mm,
                    "threshold_mm": flex_threshold_mm,
                    "planned_crop": crop_for_year(year),
                    "above_threshold": storage >= flex_threshold_mm,
                },
            )
        )

    last_leaching: date | None = None
    mid_stress: dict[int, int] = {}
    for t in trace:
        if t.stress_in_mid and t.sowing_year is not None:
            mid_stress[t.sowing_year] = mid_stress.get(t.sowing_year, 0) + 1
            if mid_stress[t.sowing_year] in thresholds.stress_day_marks and start <= t.day <= end:
                events.append(
                    Event("stress", t.day, {"crop": t.crop, "days": mid_stress[t.sowing_year]})
                )
        if not start <= t.day <= end:
            continue
        if t.precipitation >= thresholds.heavy_rain_mm:
            events.append(
                Event(
                    "heavy_rain",
                    t.day,
                    {"rain_mm": t.precipitation, "storage_mm": t.storage, "taw_mm": taw_mm},
                )
            )
        if t.deep_percolation >= thresholds.leaching_mm:
            if last_leaching is None or (t.day - last_leaching).days > LEACHING_QUIET_DAYS:
                events.append(Event("leaching", t.day, {"drained_mm": t.deep_percolation}))
            last_leaching = t.day

    for result in results:
        if not result.sown or result.crop is None or result.ratio is None:
            continue
        month, day_of_month = sowing_dates[result.crop]
        harvest = date(result.year, month, day_of_month) + timedelta(
            days=season_lengths[result.crop] - 1
        )
        if start <= harvest <= end:
            events.append(
                Event(
                    "harvest",
                    harvest,
                    {
                        "crop": result.crop,
                        "ratio": result.ratio,
                        "stress_days": result.stress_days,
                        "sufficient": sufficient_for(result),
                    },
                )
            )

    if with_card and trace:
        last = trace[-1]
        if start <= last.day <= end:
            events.append(Event("card", last.day, {"storage_mm": last.storage, "taw_mm": taw_mm}))

    return sorted(events, key=lambda e: (e.day, e.type))
