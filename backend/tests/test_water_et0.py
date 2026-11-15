"""ET0 against the worked examples of FAO Irrigation and Drainage Paper 56.

The expected numbers are those printed in the paper (chapters 3 and 4); the tolerance is the
rounding of the printed value. Example 18 is the full daily Penman-Monteith calculation.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.services.water import et0

# --- Chapter 3: the quantities that go into ET0 ---------------------------------------


def test_example_2_pressure_and_psychrometric_constant_at_1800_m():
    pressure = et0.atmospheric_pressure(1800)
    assert pressure == pytest.approx(81.8, abs=0.05)
    assert et0.psychrometric_constant(81.8) == pytest.approx(0.054, abs=0.0005)


def test_example_3_mean_saturation_vapour_pressure():
    assert et0.saturation_vapour_pressure(24.5) == pytest.approx(3.075, abs=0.001)
    assert et0.saturation_vapour_pressure(15.0) == pytest.approx(1.705, abs=0.001)
    assert et0.mean_saturation_vapour_pressure(24.5, 15.0) == pytest.approx(2.39, abs=0.005)


def test_example_5_actual_vapour_pressure_from_humidity():
    assert et0.saturation_vapour_pressure(18.0) == pytest.approx(2.064, abs=0.001)
    assert et0.saturation_vapour_pressure(25.0) == pytest.approx(3.168, abs=0.001)
    # Eq. 17, from the daily maximum and minimum humidity.
    assert et0.actual_vapour_pressure_from_extremes(82, 54, 25.0, 18.0) == pytest.approx(
        1.70, abs=0.005
    )
    # Eq. 19, from the mean humidity, which is what POWER supplies: (82 + 54) / 2 = 68 %.
    assert et0.actual_vapour_pressure_from_mean_humidity(68, 25.0, 18.0) == pytest.approx(
        1.78, abs=0.01
    )


def test_example_8_extraterrestrial_radiation_at_20_degrees_south():
    ra = et0.extraterrestrial_radiation(-20.0, doy=246)  # 3 September
    assert ra == pytest.approx(32.2, abs=0.1)


def test_example_10_extraterrestrial_radiation_at_rio_de_janeiro():
    ra = et0.extraterrestrial_radiation(-22.9, doy=135)  # 15 May
    assert ra == pytest.approx(25.1, abs=0.1)


def test_example_11_net_longwave_radiation():
    rnl = et0.net_longwave_radiation(t_max=25.1, t_min=19.1, ea=2.1, rs=14.5, rso=18.8)
    assert rnl == pytest.approx(3.5, abs=0.05)


def test_example_14_wind_speed_at_2_m():
    assert et0.wind_at_2m(3.2, height_m=10) == pytest.approx(2.4, abs=0.05)
    # The equation is an approximation: at 2 m it returns 1.0002, not exactly 1.
    assert et0.wind_at_2m(1.0, height_m=2) == pytest.approx(1.0, abs=1e-3)


def test_day_of_year():
    assert et0.day_of_year(date(2023, 7, 6)) == 187
    assert et0.day_of_year(date(2023, 9, 3)) == 246


# --- Chapter 4: Example 18, Uccle (Brussels), 6 July ----------------------------------

UCCLE = {
    "latitude_deg": 50.80,
    "elevation_m": 100.0,
    "t_max": 21.5,
    "t_min": 12.3,
    "rh_max": 84.0,
    "rh_min": 63.0,
    "wind_10m": 10.0 / 3.6,  # 10 km/h
    "rs": 22.07,  # from the 9.25 sunshine hours, as printed in the paper
    "doy": 187,
}


def test_example_18_intermediate_values():
    t_mean = (UCCLE["t_max"] + UCCLE["t_min"]) / 2
    pressure = et0.atmospheric_pressure(UCCLE["elevation_m"])
    ea = et0.actual_vapour_pressure_from_extremes(
        UCCLE["rh_max"], UCCLE["rh_min"], UCCLE["t_max"], UCCLE["t_min"]
    )
    ra = et0.extraterrestrial_radiation(UCCLE["latitude_deg"], UCCLE["doy"])
    rso = et0.clear_sky_radiation(ra, UCCLE["elevation_m"])
    rnl = et0.net_longwave_radiation(UCCLE["t_max"], UCCLE["t_min"], ea, UCCLE["rs"], rso)

    assert et0.wind_at_2m(UCCLE["wind_10m"], 10) == pytest.approx(2.078, abs=0.002)
    assert pressure == pytest.approx(100.1, abs=0.05)
    assert t_mean == pytest.approx(16.9)
    assert et0.psychrometric_constant(pressure) == pytest.approx(0.0666, abs=0.0002)
    assert et0.slope_vapour_pressure_curve(t_mean) == pytest.approx(0.122, abs=0.001)
    assert et0.mean_saturation_vapour_pressure(UCCLE["t_max"], UCCLE["t_min"]) == pytest.approx(
        1.998, abs=0.003
    )
    assert ea == pytest.approx(1.409, abs=0.002)
    assert ra == pytest.approx(41.09, abs=0.1)
    assert rso == pytest.approx(30.90, abs=0.1)
    assert rnl == pytest.approx(3.71, abs=0.05)
    assert (1 - et0.ALBEDO) * UCCLE["rs"] - rnl == pytest.approx(13.28, abs=0.05)


def test_example_18_reference_evapotranspiration_is_3_9_mm_per_day():
    result = et0.reference_et0(
        doy=UCCLE["doy"],
        latitude_deg=UCCLE["latitude_deg"],
        elevation_m=UCCLE["elevation_m"],
        t_max=UCCLE["t_max"],
        t_min=UCCLE["t_min"],
        t_mean=(UCCLE["t_max"] + UCCLE["t_min"]) / 2,
        ea=et0.actual_vapour_pressure_from_extremes(
            UCCLE["rh_max"], UCCLE["rh_min"], UCCLE["t_max"], UCCLE["t_min"]
        ),
        u2=et0.wind_at_2m(UCCLE["wind_10m"], 10),
        rs=UCCLE["rs"],
        pressure_kpa=et0.atmospheric_pressure(UCCLE["elevation_m"]),
    )
    assert result == pytest.approx(3.88, abs=0.03)


# --- Properties the paper's numbers do not cover ---------------------------------------


def _et0(**overrides: float) -> float:
    inputs = {
        "doy": 200,
        "latitude_deg": 37.9,
        "elevation_m": 1000.0,
        "t_max": 32.0,
        "t_min": 16.0,
        "t_mean": 24.0,
        "ea": 1.0,
        "u2": 2.0,
        "rs": 27.0,
        "pressure_kpa": 89.0,
    }
    return et0.reference_et0(**(inputs | overrides))


def test_a_dry_windy_sunny_day_evaporates_more_than_a_humid_calm_dull_one():
    dry = _et0(ea=0.8, u2=4.0, rs=29.0)
    humid = _et0(ea=2.5, u2=0.5, rs=10.0)
    assert dry > humid > 0


def test_et0_never_goes_below_zero():
    # Air that holds more vapour than saturation (e_a above e_s) pulls the aerodynamic term
    # below zero; on a dark winter day the equation then gives a negative number, and ET0 is 0.
    raw = _et0(doy=355, t_max=1.0, t_min=-1.0, t_mean=0.0, ea=1.6, rs=1.0, u2=3.0)
    assert raw == 0.0


def test_et0_rises_with_solar_radiation():
    assert _et0(rs=24.0) < _et0(rs=27.0)


def test_the_polar_night_does_not_break_the_radiation_formula():
    assert et0.extraterrestrial_radiation(80.0, doy=355) == pytest.approx(0.0, abs=1e-6)
    assert et0.extraterrestrial_radiation(80.0, doy=172) > 40.0


def test_clear_sky_radiation_must_be_positive():
    with pytest.raises(ValueError):
        et0.net_longwave_radiation(20.0, 10.0, 1.0, 10.0, 0.0)
