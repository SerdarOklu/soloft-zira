"""Reference evapotranspiration, FAO-56 Penman-Monteith (PDT section 7.1 and 7.2).

Equation numbers are those of FAO Irrigation and Drainage Paper 56, chapters 3 and 4.
Units: temperature in °C, pressure in kPa, wind in m/s, radiation in MJ m⁻² day⁻¹,
elevation in m, ET0 in mm day⁻¹.
"""

from __future__ import annotations

import math
from datetime import date

# Solar constant, MJ m⁻² min⁻¹ (Eq. 21).
SOLAR_CONSTANT = 0.0820
# Stefan-Boltzmann constant, MJ K⁻⁴ m⁻² day⁻¹ (Eq. 39).
STEFAN_BOLTZMANN = 4.903e-9
# Albedo of the hypothetical grass reference crop (Eq. 38).
ALBEDO = 0.23
# Soil heat flux over a day is taken as zero (Eq. 42).
SOIL_HEAT_FLUX = 0.0


def saturation_vapour_pressure(temperature: float) -> float:
    """e°(T), Eq. 11."""
    return 0.6108 * math.exp(17.27 * temperature / (temperature + 237.3))


def slope_vapour_pressure_curve(temperature: float) -> float:
    """Δ, Eq. 13."""
    return 4098.0 * saturation_vapour_pressure(temperature) / (temperature + 237.3) ** 2


def atmospheric_pressure(elevation_m: float) -> float:
    """P from the elevation, Eq. 7. Used when no measured pressure is available."""
    return 101.3 * ((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26


def psychrometric_constant(pressure_kpa: float) -> float:
    """γ, Eq. 8."""
    return 0.000665 * pressure_kpa


def mean_saturation_vapour_pressure(t_max: float, t_min: float) -> float:
    """e_s, Eq. 12."""
    return (saturation_vapour_pressure(t_max) + saturation_vapour_pressure(t_min)) / 2.0


def actual_vapour_pressure_from_mean_humidity(rh_mean: float, t_max: float, t_min: float) -> float:
    """e_a from the mean relative humidity, Eq. 19. POWER supplies RH2M, a daily mean."""
    return rh_mean / 100.0 * mean_saturation_vapour_pressure(t_max, t_min)


def actual_vapour_pressure_from_extremes(
    rh_max: float, rh_min: float, t_max: float, t_min: float
) -> float:
    """e_a from the daily maximum and minimum humidity, Eq. 17."""
    return (
        saturation_vapour_pressure(t_min) * rh_max / 100.0
        + saturation_vapour_pressure(t_max) * rh_min / 100.0
    ) / 2.0


def minimum_relative_humidity(ea: float, t_max: float) -> float:
    """RH_min estimated from e_a and the maximum temperature (PDT 7.1)."""
    return 100.0 * ea / saturation_vapour_pressure(t_max)


def wind_at_2m(speed: float, height_m: float) -> float:
    """Wind speed at 2 m from a measurement at ``height_m``, Eq. 47."""
    return speed * 4.87 / math.log(67.8 * height_m - 5.42)


def day_of_year(day: date) -> int:
    return day.timetuple().tm_yday


def extraterrestrial_radiation(latitude_deg: float, doy: int) -> float:
    """R_a, Eq. 21, with the inverse relative distance (Eq. 23), the solar declination
    (Eq. 24) and the sunset hour angle (Eq. 25)."""
    phi = math.radians(latitude_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    declination = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    # Clamped for the polar day and night, where the sun never sets or rises.
    sunset = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(declination))))
    return (
        (24.0 * 60.0 / math.pi)
        * SOLAR_CONSTANT
        * dr
        * (
            sunset * math.sin(phi) * math.sin(declination)
            + math.cos(phi) * math.cos(declination) * math.sin(sunset)
        )
    )


def clear_sky_radiation(ra: float, elevation_m: float) -> float:
    """R_so, Eq. 37."""
    return (0.75 + 2e-5 * elevation_m) * ra


def net_longwave_radiation(t_max: float, t_min: float, ea: float, rs: float, rso: float) -> float:
    """R_nl, Eq. 39. The ratio Rs/Rso is limited to 1."""
    if rso <= 0:
        raise ValueError("Clear-sky radiation must be positive")
    ratio = min(rs / rso, 1.0)
    emission = STEFAN_BOLTZMANN * ((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4) / 2.0
    return emission * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * ratio - 0.35)


def reference_et0(
    *,
    doy: int,
    latitude_deg: float,
    elevation_m: float,
    t_max: float,
    t_min: float,
    t_mean: float,
    ea: float,
    u2: float,
    rs: float,
    pressure_kpa: float,
) -> float:
    """Daily ET0 by the FAO-56 Penman-Monteith equation (Eq. 6), never below zero."""
    ra = extraterrestrial_radiation(latitude_deg, doy)
    rso = clear_sky_radiation(ra, elevation_m)
    rn = (1.0 - ALBEDO) * rs - net_longwave_radiation(t_max, t_min, ea, rs, rso)
    es = mean_saturation_vapour_pressure(t_max, t_min)
    delta = slope_vapour_pressure_curve(t_mean)
    gamma = psychrometric_constant(pressure_kpa)
    radiation = 0.408 * delta * (rn - SOIL_HEAT_FLUX)
    aerodynamic = gamma * 900.0 / (t_mean + 273.0) * u2 * (es - ea)
    return max(0.0, (radiation + aerodynamic) / (delta + gamma * (1.0 + 0.34 * u2)))
