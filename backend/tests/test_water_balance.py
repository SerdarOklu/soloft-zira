"""Crop coefficient, soil water capacity and the daily balance against FAO-56 worked examples
(chapters 6 and 8), plus the fallow rule of the Zira specification (PDT 7.5)."""

from __future__ import annotations

import random

import pytest

from app.services.water import balance, crop

# --- Chapter 6: the crop coefficient ----------------------------------------------------

EXAMPLE_28 = {
    "kc_ini": 0.15,
    "kc_mid": 1.19,
    "kc_end": 0.35,
    "l_ini": 25,
    "l_dev": 25,
    "l_mid": 30,
    "l_late": 20,
}


@pytest.mark.parametrize(
    ("day", "expected"),
    [(20, 0.15), (40, 0.77), (70, 1.19), (95, 0.56)],
)
def test_example_28_kc_on_a_day_of_each_stage(day: int, expected: float):
    assert crop.kc_curve(day, **EXAMPLE_28) == pytest.approx(expected, abs=0.005)


def test_kc_is_continuous_between_stages_and_holds_kc_end_after_harvest():
    kc = {day: crop.kc_curve(day, **EXAMPLE_28) for day in range(1, 105)}
    assert kc[25] == pytest.approx(0.15)  # last day of the initial stage
    assert kc[50] == pytest.approx(1.19)  # last day of development
    assert kc[80] == pytest.approx(1.19)  # last day of the mid-season
    assert kc[100] == pytest.approx(0.35)  # last day of the late season
    assert kc[104] == pytest.approx(0.35)
    assert max(abs(kc[d + 1] - kc[d]) for d in range(1, 104)) < 0.05


@pytest.mark.parametrize(
    "arguments",
    [
        {"day": 0},
        {"day": 1, "l_ini": 0},
        {"day": 1, "l_late": -3},
    ],
)
def test_kc_curve_refuses_impossible_input(arguments: dict):
    with pytest.raises(ValueError):
        crop.kc_curve(**(EXAMPLE_28 | arguments))


@pytest.mark.parametrize(
    ("u2", "rh_min", "expected"),
    [
        (1.3, 75, 1.07),  # Example 27, maize in Taipei (humid)
        (4.6, 44, 1.30),  # Example 27, maize in Mocha (arid)
    ],
)
def test_example_27_kc_mid_for_maize(u2: float, rh_min: float, expected: float):
    kc_mid = crop.adjust_kc_mid(
        1.20, u2=u2, rh_min=rh_min, height_m=2.0, reference_u2=2.0, reference_rh_min=45.0
    )
    assert kc_mid == pytest.approx(expected, abs=0.005)


def test_box_15_kc_mid_for_dry_beans():
    kc_mid = crop.adjust_kc_mid(
        1.15, u2=2.2, rh_min=30, height_m=0.4, reference_u2=2.0, reference_rh_min=45.0
    )
    assert kc_mid == pytest.approx(1.19, abs=0.005)


def test_kc_mid_is_unchanged_under_the_reference_climate():
    kc_mid = crop.adjust_kc_mid(
        1.15, u2=2.0, rh_min=45, height_m=1.0, reference_u2=2.0, reference_rh_min=45.0
    )
    assert kc_mid == pytest.approx(1.15)


# --- Chapter 8: soil water capacity and stress -----------------------------------------


@pytest.mark.parametrize(
    ("crop_name", "root_depth", "p", "soil_mm_per_m", "taw", "raw"),
    [
        ("onion on loamy sand", 0.4, 0.30, 90, 36, 11),
        ("tomato on silt", 0.8, 0.40, 170, 136, 54),
        ("maize on silt", 1.2, 0.55, 170, 204, 112),
        ("maize on silty clay", 1.2, 0.55, 120, 144, 79),
    ],
)
def test_example_36_taw_and_raw(crop_name, root_depth, p, soil_mm_per_m, taw, raw):
    computed_taw = crop.total_available_water(soil_mm_per_m, root_depth)
    assert computed_taw == pytest.approx(taw, abs=0.5), crop_name
    assert crop.readily_available_water(computed_taw, p) == pytest.approx(raw, abs=0.6), crop_name


def test_the_depletion_fraction_follows_the_crop_water_use_and_stays_in_bounds():
    kwargs = {"reference_etc": 5.0, "p_min": 0.1, "p_max": 0.8}
    assert crop.adjusted_depletion_fraction(0.55, 5.0, **kwargs) == pytest.approx(0.55)
    assert crop.adjusted_depletion_fraction(0.55, 9.0, **kwargs) == pytest.approx(0.39)
    assert crop.adjusted_depletion_fraction(0.55, 1.0, **kwargs) == pytest.approx(0.71)
    assert crop.adjusted_depletion_fraction(0.55, 20.0, **kwargs) == 0.1
    assert crop.adjusted_depletion_fraction(0.75, 0.0, **kwargs) == 0.8


def test_ks_is_one_until_the_readily_available_water_is_used():
    taw, p = 160.0, 0.4
    assert crop.stress_coefficient(taw, taw, p) == 1.0
    assert crop.stress_coefficient((1 - p) * taw, taw, p) == 1.0
    assert crop.stress_coefficient((1 - p) * taw / 2, taw, p) == pytest.approx(0.5)
    assert crop.stress_coefficient(0.0, taw, p) == 0.0


def test_example_37_ten_days_of_water_stress_on_tomato():
    """Tomato on silt, 55 mm of depletion, no rain or irrigation, ET0 5 mm/day and Kc 1.2."""
    taw, p = 160.0, 0.40
    printed = [  # (Ks, ETc adjusted, depletion at the end of the day) for days 1 to 10
        (1.00, 6.0, 61.0),
        (1.00, 6.0, 67.0),
        (0.97, 5.8, 72.8),
        (0.91, 5.4, 78.3),
        (0.85, 5.1, 83.4),
        (0.80, 4.8, 88.2),
        (0.75, 4.5, 92.6),
        (0.70, 4.2, 96.9),
        (0.66, 3.9, 100.8),
        (0.62, 3.7, 104.5),
    ]
    storage = taw - 55.0  # storage is what is left above the wilting point
    for day, (ks, adjusted, depletion) in enumerate(printed, start=1):
        result = balance.crop_day(
            storage,
            precipitation=0.0,
            irrigation=0.0,
            et0=5.0,
            kc=1.2,
            taw=taw,
            p=p,
            eff_rain_fraction=0.8,
        )
        assert result.ks == pytest.approx(ks, abs=0.006), f"day {day}"
        assert result.actual_et == pytest.approx(adjusted, abs=0.06), f"day {day}"
        assert taw - result.storage == pytest.approx(depletion, abs=0.06), f"day {day}"
        storage = result.storage


# --- The daily balance ------------------------------------------------------------------


def test_rain_fills_the_root_zone_and_the_excess_is_deep_percolation():
    day = balance.crop_day(
        90.0,
        precipitation=50.0,
        irrigation=0.0,
        et0=4.0,
        kc=1.0,
        taw=100.0,
        p=0.5,
        eff_rain_fraction=0.8,
    )
    # 90 + 0.8 * 50 - 4 = 126; the root zone holds 100.
    assert day.storage == pytest.approx(100.0)
    assert day.deep_percolation == pytest.approx(26.0)
    assert day.actual_et == pytest.approx(4.0)
    assert day.ks == 1.0


def test_irrigation_reaches_the_root_zone():
    day = balance.crop_day(
        60.0,
        precipitation=0.0,
        irrigation=30.0,
        et0=5.0,
        kc=1.0,
        taw=100.0,
        p=0.5,
        eff_rain_fraction=0.8,
    )
    assert day.storage == pytest.approx(85.0)  # 60 + 30 - 5, no stress at the start of the day


def test_stress_is_read_from_the_storage_at_the_start_of_the_day():
    """As in FAO-56 Example 37: Ks uses the depletion of the previous day, so water that
    arrives today does not lift today's stress."""
    day = balance.crop_day(
        20.0,
        precipitation=0.0,
        irrigation=30.0,
        et0=5.0,
        kc=1.0,
        taw=100.0,
        p=0.5,
        eff_rain_fraction=0.8,
    )
    assert day.ks == pytest.approx(0.4)  # 20 / ((1 - 0.5) * 100)
    assert day.actual_et == pytest.approx(2.0)
    assert day.storage == pytest.approx(48.0)


def test_a_crop_cannot_evaporate_water_that_is_not_there():
    day = balance.crop_day(
        1.0,
        precipitation=0.0,
        irrigation=0.0,
        et0=8.0,
        kc=1.2,
        taw=100.0,
        p=0.5,
        eff_rain_fraction=0.8,
    )
    assert day.actual_et <= 1.0
    assert day.storage >= 0.0


def test_fallow_keeps_only_the_configured_share_of_the_rain():
    storage, lost = balance.fallow_day(40.0, 20.0, taw=100.0, fallow_efficiency=0.25)
    assert storage == pytest.approx(45.0)
    assert lost == 0.0


def test_fallow_storage_stops_at_taw():
    storage, lost = balance.fallow_day(98.0, 40.0, taw=100.0, fallow_efficiency=0.25)
    assert storage == 100.0
    assert lost == pytest.approx(8.0)


def test_a_fallow_period_starts_from_the_initial_fraction_and_counts_missing_rain_as_none():
    series = balance.simulate_fallow(
        [0.0, 10.0, None, 20.0], taw=200.0, fallow_efficiency=0.25, initial_fraction=0.5
    )
    assert series == pytest.approx([100.0, 102.5, 102.5, 107.5])


def test_storage_stays_between_zero_and_taw_whatever_the_weather():
    rng = random.Random(7)
    taw, p = 120.0, 0.5
    storage = 0.5 * taw
    for _ in range(2000):
        day = balance.crop_day(
            storage,
            precipitation=rng.choice([0.0, 0.0, 0.0, rng.uniform(0, 80)]),
            irrigation=rng.choice([0.0, 0.0, 25.0]),
            et0=rng.uniform(0, 9),
            kc=rng.uniform(0.2, 1.3),
            taw=taw,
            p=p,
            eff_rain_fraction=0.8,
        )
        assert 0.0 <= day.storage <= taw
        assert 0.0 <= day.ks <= 1.0
        assert day.actual_et <= day.crop_et + 1e-9
        storage = day.storage
