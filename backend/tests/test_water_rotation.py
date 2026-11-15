"""The rotation engine on small cases that can be worked out by hand (PDT 7.6 to 7.8).

One crop with Kc 1 in every stage, 10-day stages (40 days), root depth 1 m on soil that holds
100 mm per metre, so TAW is 100 mm. The season starts on 1 March.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services.water.rotation import (
    RunParams,
    SeasonCrop,
    current_plan,
    legume_plan,
    simulate,
    sowing_years,
    summarise,
)

CROP = SeasonCrop(
    key="crop",
    sow_month=3,
    sow_day=1,
    l_ini=10,
    l_dev=10,
    l_mid=10,
    l_late=10,
    kc_ini=1.0,
    kc_mid=1.0,
    kc_end=1.0,
    p_table=0.5,
    root_depth_m=1.0,
)


def params(**changes) -> RunParams:
    base = {
        "taw_per_m": 100.0,
        "eff_rain_fraction": 1.0,
        "fallow_efficiency": 0.25,
        "initial_fraction": 0.5,
        "reference_depth_m": 1.0,
        "min_valid_share": 0.95,
        "sufficiency_ratio": 0.7,
        "critical_stress_days_max": None,
        "flex_threshold_frac": 0.5,
        "decision_month": 2,
        "decision_day": 15,
        "p_ref_etc": 5.0,
        "p_min": 0.1,
        "p_max": 0.8,
    }
    return RunParams(**{**base, **changes})


def record(year: int, *, rain: float | None, et0: float | None):
    first = date(year, 1, 1)
    days = [first + timedelta(days=i) for i in range(365)]
    return days, [rain] * len(days), [et0] * len(days)


def test_current_rotation_repeats_cyclically():
    plan = current_plan(["wheat", None], [2001, 2002, 2003, 2004])
    assert plan == {2001: "wheat", 2002: None, 2003: "wheat", 2004: None}


def test_legume_goes_in_every_nth_fallow_season():
    plan = current_plan(["wheat", None], [2001, 2002, 2003, 2004, 2005, 2006])
    result = legume_plan(plan, every_n_fallow=2, legume="lentil")
    assert result == {
        2001: "wheat",
        2002: None,
        2003: "wheat",
        2004: "lentil",
        2005: "wheat",
        2006: None,
    }


def test_sowing_years_need_the_whole_season_inside_the_record():
    winter = SeasonCrop(
        **{**CROP.__dict__, "sow_month": 11, "l_ini": 30, "l_dev": 140, "l_mid": 40, "l_late": 30}
    )
    years = sowing_years(
        date(2001, 1, 1),
        date(2005, 12, 31),
        crops=[winter],
        decision_month=10,
        decision_day=1,
        limit=25,
    )
    assert years == [2001, 2002, 2003, 2004]
    assert sowing_years(
        date(2001, 1, 1),
        date(2005, 12, 31),
        crops=[winter],
        decision_month=10,
        decision_day=1,
        limit=2,
    ) == [2003, 2004]


def test_a_wet_season_has_enough_water():
    # 10 mm of rain every day keeps the soil full: actual ET equals crop ET (5 mm x 40 days).
    days, rain, et0 = record(2001, rain=10.0, et0=5.0)
    (season,) = simulate(
        days, rain, et0, crops={"crop": CROP}, plan={2001: "crop"}, params=params()
    )
    assert season.crop_et == pytest.approx(200.0)
    assert season.actual_et == pytest.approx(200.0)
    assert season.stress_days == 0
    assert season.is_sufficient(params())


def test_a_dry_season_runs_out_and_is_not_sufficient():
    # No rain: the soil starts at 50 mm and cannot give more than that.
    days, rain, et0 = record(2001, rain=0.0, et0=5.0)
    (season,) = simulate(
        days, rain, et0, crops={"crop": CROP}, plan={2001: "crop"}, params=params()
    )
    assert season.crop_et == pytest.approx(200.0)
    assert 40.0 < season.actual_et <= 50.0 + 1e-9
    assert season.stress_days > 0
    assert not season.is_sufficient(params())
    assert season.deficit == pytest.approx(season.crop_et - season.actual_et)


def test_a_fallow_season_is_not_scored():
    days, rain, et0 = record(2001, rain=5.0, et0=5.0)
    (season,) = simulate(days, rain, et0, crops={"crop": CROP}, plan={2001: None}, params=params())
    assert not season.sown
    assert not season.is_valid(0.95)
    summary = summarise([season], params(), 0.75)
    assert (summary.sown, summary.valid, summary.sufficient, summary.fallow) == (0, 0, 0, 1)
    assert summary.share is None


def test_a_season_with_too_many_missing_days_is_not_valid():
    days, rain, et0 = record(2001, rain=10.0, et0=5.0)
    for index in range(60, 70):  # 10 of the 40 season days have no ET0
        et0[index] = None
    (season,) = simulate(
        days, rain, et0, crops={"crop": CROP}, plan={2001: "crop"}, params=params()
    )
    assert season.complete_days == 30 and season.days == 40
    assert not season.is_valid(0.95)
    assert not season.is_sufficient(params())


def test_flexible_strategy_holds_back_when_the_soil_is_below_the_threshold():
    # No rain: the soil is at 50 mm on the decision day. Threshold 0.6 x 100 = 60 mm.
    days, rain, et0 = record(2001, rain=0.0, et0=5.0)
    (held,) = simulate(
        days,
        rain,
        et0,
        crops={"crop": CROP},
        plan={2001: "crop"},
        flexible=frozenset({2001}),
        params=params(flex_threshold_frac=0.6),
    )
    assert held.planned == "crop" and held.crop is None and not held.sown
    assert held.storage_at_decision == pytest.approx(50.0)
    (sown,) = simulate(
        days,
        rain,
        et0,
        crops={"crop": CROP},
        plan={2001: "crop"},
        flexible=frozenset({2001}),
        params=params(flex_threshold_frac=0.5),
    )
    assert sown.crop == "crop"


def test_strategies_start_from_the_same_storage():
    # Before the first sowing day nothing differs between a sown and a fallow plan.
    days, rain, et0 = record(2001, rain=0.0, et0=5.0)
    (a,) = simulate(days, rain, et0, crops={"crop": CROP}, plan={2001: "crop"}, params=params())
    (b,) = simulate(
        days,
        rain,
        et0,
        crops={"crop": CROP},
        plan={2001: "crop"},
        flexible=frozenset({2001}),
        params=params(),
    )
    assert b.storage_at_decision == pytest.approx(50.0)
    assert a.actual_et == pytest.approx(b.actual_et)


def test_decision_day_must_come_before_sowing():
    days, rain, et0 = record(2001, rain=1.0, et0=1.0)
    with pytest.raises(ValueError):
        simulate(
            days,
            rain,
            et0,
            crops={"crop": CROP},
            plan={2001: "crop"},
            flexible=frozenset({2001}),
            params=params(decision_month=3, decision_day=1),
        )


def test_critical_stress_cap_can_fail_a_season():
    days, rain, et0 = record(2001, rain=0.0, et0=5.0)
    capped = params(critical_stress_days_max=0, sufficiency_ratio=0.1)
    (season,) = simulate(days, rain, et0, crops={"crop": CROP}, plan={2001: "crop"}, params=capped)
    assert season.actual_et / season.crop_et >= 0.1
    assert not season.is_sufficient(capped)
