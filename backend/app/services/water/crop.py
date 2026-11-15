"""Crop coefficient and soil water capacity (PDT sections 7.3 and 7.4; FAO-56 chapters 6 and 8)."""

from __future__ import annotations


def kc_curve(
    day: int,
    *,
    kc_ini: float,
    kc_mid: float,
    kc_end: float,
    l_ini: int,
    l_dev: int,
    l_mid: int,
    l_late: int,
) -> float:
    """Kc on day ``day`` of the season (1 is the sowing day), Eq. 66.

    Constant ``kc_ini``, a linear rise to ``kc_mid``, constant ``kc_mid``, then a linear fall to
    ``kc_end``. After the last day the crop is not growing and ``kc_end`` stays.
    """
    if day < 1:
        raise ValueError("The season starts on day 1")
    if min(l_ini, l_dev, l_mid, l_late) <= 0:
        raise ValueError("Every stage length must be positive")
    if day <= l_ini:
        return kc_ini
    if day <= l_ini + l_dev:
        return kc_ini + (day - l_ini) / l_dev * (kc_mid - kc_ini)
    if day <= l_ini + l_dev + l_mid:
        return kc_mid
    if day <= l_ini + l_dev + l_mid + l_late:
        return kc_mid + (day - (l_ini + l_dev + l_mid)) / l_late * (kc_end - kc_mid)
    return kc_end


def adjust_kc_mid(
    kc_mid_table: float,
    *,
    u2: float,
    rh_min: float,
    height_m: float,
    reference_u2: float,
    reference_rh_min: float,
) -> float:
    """Kc mid corrected for the climate of the stage, Eq. 62.

    The FAO tables hold for ``reference_rh_min`` and ``reference_u2`` (45 % and 2 m/s); both
    come from the parameter sheet.
    """
    correction = 0.04 * (u2 - reference_u2) - 0.004 * (rh_min - reference_rh_min)
    return kc_mid_table + correction * (height_m / 3.0) ** 0.3


def total_available_water(taw_mm_per_m: float, root_depth_m: float) -> float:
    """TAW in mm, Eq. 82. ``taw_mm_per_m`` is 1000 (θ_FC − θ_WP)."""
    return taw_mm_per_m * root_depth_m


def readily_available_water(taw: float, p: float) -> float:
    """RAW in mm, Eq. 83."""
    return p * taw


def adjusted_depletion_fraction(
    p_table: float, etc: float, *, reference_etc: float, p_min: float, p_max: float
) -> float:
    """p corrected for the crop's evapotranspiration rate (Table 22 note): p = p_table +
    0.04 (5 − ETc), kept between ``p_min`` and ``p_max``."""
    return max(p_min, min(p_max, p_table + 0.04 * (reference_etc - etc)))


def stress_coefficient(storage: float, taw: float, p: float) -> float:
    """Ks (Eq. 84), from the water in the root zone at the start of the day.

    One while the storage is at least (1 − p) TAW; below that it falls linearly to zero.
    Storage is the water above the wilting point, so depletion is TAW − storage.
    """
    threshold = (1.0 - p) * taw
    if storage >= threshold:
        return 1.0
    return max(0.0, storage / threshold)
