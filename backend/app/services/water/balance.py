"""The daily root-zone water balance (PDT section 7.5).

Storage is the water above the wilting point, in mm, between 0 and TAW. Every function takes
the values it needs; none reads configuration.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.services.water.crop import stress_coefficient


@dataclass(frozen=True)
class CropDay:
    """The outcome of one day with a crop."""

    storage: float
    actual_et: float
    crop_et: float
    ks: float
    deep_percolation: float


def fallow_day(
    storage: float, precipitation: float, *, taw: float, fallow_efficiency: float
) -> tuple[float, float]:
    """A day without a crop: the soil keeps ``fallow_efficiency`` of the rain, up to TAW.

    Returns the new storage and the water lost as deep percolation.
    """
    wanted = storage + fallow_efficiency * precipitation
    return min(taw, wanted), max(0.0, wanted - taw)


def crop_day(
    storage: float,
    *,
    precipitation: float,
    irrigation: float,
    et0: float,
    kc: float,
    taw: float,
    p: float,
    eff_rain_fraction: float,
) -> CropDay:
    """A day with a crop: S = S₀ + P_eff + I − ET_a − D, with ET_a = Ks · Kc · ET0.

    Ks is read from the storage at the start of the day. Actual evapotranspiration cannot be
    more than the water that is there, and storage never leaves 0 to TAW.
    """
    ks = stress_coefficient(storage, taw, p)
    crop_et = kc * et0
    available = storage + eff_rain_fraction * precipitation + irrigation
    actual = min(ks * crop_et, available)
    remaining = available - actual
    return CropDay(
        storage=min(taw, remaining),
        actual_et=actual,
        crop_et=crop_et,
        ks=ks,
        deep_percolation=max(0.0, remaining - taw),
    )


def simulate_fallow(
    precipitation: Iterable[float | None],
    *,
    taw: float,
    fallow_efficiency: float,
    initial_fraction: float,
) -> list[float]:
    """Storage at the end of each day of a fallow period. A missing rain value counts as no
    rain; the caller reports how many days were missing."""
    storage = initial_fraction * taw
    series: list[float] = []
    for rain in precipitation:
        storage, _ = fallow_day(storage, rain or 0.0, taw=taw, fallow_efficiency=fallow_efficiency)
        series.append(storage)
    return series
