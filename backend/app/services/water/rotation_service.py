"""The rotation comparison for one field (PDT 4.4, 7.6 to 7.10): joins the engine to the data.

Strategy A is the rotation the user gives (Field Memory, phase 5, does not exist yet, so it is
user-supplied and the answer says so). B and C are derived from A under the same conditions.
Each strategy runs three times (low, middle, high) for the uncertainty range (PDT 7.10).
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.parameters import Config
from app.models import Field, SoilProfile, WeatherObservation
from app.schemas.rotation import (
    DifferenceOut,
    MetricsOut,
    ReferenceOut,
    RotationOut,
    SeasonOut,
    StrategyOut,
)
from app.services.power import SOURCE as POWER_SOURCE
from app.services.water.crop import total_available_water
from app.services.water.rotation import (
    RunParams,
    SeasonCrop,
    SeasonResult,
    Summary,
    current_plan,
    legume_plan,
    simulate,
    sowing_years,
    summarise,
)
from app.services.water.vault import VaultError, _et0_for

DEFAULT_ROTATION = ["winter_wheat", None]
PROVISIONAL_SOURCE = "rotation_demo"


def parse_rotation(text: str | None) -> list[str | None]:
    """``winter_wheat,fallow`` to ``["winter_wheat", None]``."""
    if not text:
        return list(DEFAULT_ROTATION)
    parts = [part.strip() for part in text.split(",") if part.strip()]
    return [None if part == "fallow" else part for part in parts] or list(DEFAULT_ROTATION)


def _season_crop(key: str, config: Config) -> SeasonCrop:
    demo = config.rotation_demo.crops.get(key)
    crop = config.crops.get(key)
    if crop is None:
        raise VaultError("unknown_crop", crop=key)
    if demo is None:
        raise VaultError("season_values_missing", crop=key)
    month, day = (int(part) for part in demo.sowing_date.split("-"))
    ini, dev, mid, late = demo.stage_lengths_days
    kc_ini = crop.kc_ini
    if not isinstance(kc_ini, float):
        kc_ini = getattr(kc_ini, demo.kc_ini_variant or "non_frozen_soil")

    def middle(value: float | tuple[float, float]) -> float:
        return value if isinstance(value, float) else (value[0] + value[1]) / 2

    return SeasonCrop(
        key=key,
        sow_month=month,
        sow_day=day,
        l_ini=ini,
        l_dev=dev,
        l_mid=mid,
        l_late=late,
        kc_ini=float(kc_ini),
        kc_mid=middle(crop.kc_mid),
        kc_end=middle(crop.kc_end),
        p_table=crop.p,
        root_depth_m=crop.zr_m[1],  # version 1 uses the maximum root depth (PDT 7.4)
    )


def _metrics(runs: list[Summary]) -> MetricsOut:
    """Middle run for the figures, all three for the range."""
    middle = runs[1]
    shares = [run.share for run in runs if run.share is not None]
    sufficient = [run.sufficient for run in runs]
    return MetricsOut(
        sown=middle.sown,
        valid=middle.valid,
        sufficient=middle.sufficient,
        fallow=middle.fallow,
        share=middle.share,
        share_low=min(shares) if shares else None,
        share_high=max(shares) if shares else None,
        sufficient_low=min(sufficient),
        sufficient_high=max(sufficient),
        stress_days_mean=middle.stress_days_mean,
        deficit_mean_mm=middle.deficit_mean_mm,
        irrigation_need_mean_mm=middle.irrigation_need_mean_mm,
    )


def _season_out(result: SeasonResult, params: RunParams) -> SeasonOut:
    return SeasonOut(
        year=result.year,
        planned=result.planned,
        crop=result.crop,
        valid=result.is_valid(params.min_valid_share),
        sufficient=result.is_sufficient(params),
        ratio=result.ratio,
        deficit_mm=result.deficit,
        stress_days=result.stress_days,
        storage_at_decision_mm=result.storage_at_decision,
    )


def _difference(candidate: MetricsOut, baseline: MetricsOut) -> DifferenceOut:
    def delta(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else a - b

    share = delta(candidate.share, baseline.share)
    return DifferenceOut(
        share_points=None if share is None else share * 100,
        stress_days_mean=delta(candidate.stress_days_mean, baseline.stress_days_mean),
        deficit_mean_mm=delta(candidate.deficit_mean_mm, baseline.deficit_mean_mm),
        irrigation_need_mean_mm=delta(
            candidate.irrigation_need_mean_mm, baseline.irrigation_need_mean_mm
        ),
        sufficient=candidate.sufficient - baseline.sufficient,
    )


def rotation_comparison(
    session: Session,
    field: Field,
    rotation: list[str | None],
    config: Config,
    inputs_out: dict | None = None,
) -> RotationOut:
    """``inputs_out``, when given, receives what the runs used so a caller can replay one run
    (the message events read the daily trace of strategy A)."""
    if not any(rotation):
        raise VaultError("rotation_without_crop")
    location = session.execute(
        select(func.ST_Y(Field.centroid)).where(Field.id == field.id)
    ).scalar_one_or_none()
    if location is None:
        raise VaultError("no_location")
    if field.elevation_m is None:
        raise VaultError("no_elevation")

    scope = (WeatherObservation.field_id == field.id, WeatherObservation.source == POWER_SOURCE)
    rows = list(
        session.scalars(select(WeatherObservation).where(*scope).order_by(WeatherObservation.date))
    )
    if not rows:
        raise VaultError("no_weather_data")

    profile = session.scalar(
        select(SoilProfile)
        .where(SoilProfile.field_id == field.id)
        .order_by(SoilProfile.created_at.desc())
        .limit(1)
    )
    soil = config.soils.get(profile.texture) if profile and profile.texture else None
    if profile is None or soil is None or profile.taw_mm_per_m is None:
        raise VaultError("no_soil")

    demo = config.rotation_demo
    parameters = config.parameters
    legume_key = demo.strategy_c_legume
    used_keys = {key for key in rotation if key} | {legume_key}
    crops = {key: _season_crop(key, config) for key in used_keys}

    decision = parameters.get("core", "decision_date")["winter"]
    decision_month, decision_day = (int(part) for part in decision.split("-"))

    # The record is a dense daily series from the first to the last stored day.
    first_day, last_day = rows[0].date, rows[-1].date
    by_date = {row.date: row for row in rows}
    days = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    rain = [by_date[d].precipitation_mm if d in by_date else None for d in days]
    et0 = [
        _et0_for(by_date[d], latitude=float(location), elevation_m=field.elevation_m)
        if d in by_date
        else None
        for d in days
    ]

    years = sowing_years(
        first_day,
        last_day,
        crops=list(crops.values()),
        decision_month=decision_month,
        decision_day=decision_day,
        limit=int(parameters.get("core", "n_seasons")),
    )
    if not years:
        raise VaultError("not_enough_history", first_date=first_day.isoformat())

    plan_a = current_plan(rotation, years)
    plan_c = legume_plan(
        plan_a,
        every_n_fallow=int(parameters.get("core", "legume_every_n_fallow")),
        legume=legume_key,
    )
    flexible = frozenset(year for year, crop in plan_a.items() if crop is not None)

    main_crop = next(key for key in rotation if key)
    reference_depth = crops[main_crop].root_depth_m
    delta = float(parameters.get("core", "uncertainty_rain_delta"))
    base_eff = float(parameters.get("core", "eff_rain_fraction"))
    base_fallow = float(parameters.get("core", "fallow_efficiency"))
    efficiency = demo.irrigation_efficiency.value

    soil_low, soil_high = soil.taw_mm_per_m
    soil_mid = float(profile.taw_mm_per_m)
    if profile.is_calibrated:
        soil_low = soil_high = soil_mid
    variants = [(soil_low, -delta), (soil_mid, 0.0), (soil_high, delta)]

    def params_for(taw_per_m: float, shift: float) -> RunParams:
        clamp = lambda x: min(1.0, max(0.0, x))  # noqa: E731
        cap = parameters.get("core", "critical_stress_days_max")
        return RunParams(
            taw_per_m=taw_per_m,
            eff_rain_fraction=clamp(base_eff + shift),
            fallow_efficiency=clamp(base_fallow + shift),
            initial_fraction=float(parameters.get("core", "initial_storage_frac")),
            reference_depth_m=reference_depth,
            min_valid_share=float(parameters.get("core", "min_valid_day_share")),
            sufficiency_ratio=float(parameters.get("core", "sufficiency_ratio")),
            critical_stress_days_max=None if cap is None else int(cap),
            flex_threshold_frac=float(parameters.get("core", "flex_sow_threshold_frac")),
            decision_month=decision_month,
            decision_day=decision_day,
            p_ref_etc=float(parameters.get("corrections", "p_ref_etc")),
            p_min=float(parameters.get("corrections", "p_min")),
            p_max=float(parameters.get("corrections", "p_max")),
        )

    plans = {
        "A": (plan_a, frozenset()),
        "B": (plan_a, flexible),
        "C": (plan_c, frozenset()),
    }
    if inputs_out is not None:
        inputs_out.update(
            days=days,
            rain=rain,
            et0=et0,
            crops=crops,
            plan_a=plan_a,
            years=years,
            middle_params=params_for(soil_mid, 0.0),
            reference_taw=total_available_water(soil_mid, reference_depth),
            decision_month=decision_month,
            decision_day=decision_day,
            flex_threshold_mm=float(parameters.get("core", "flex_sow_threshold_frac"))
            * total_available_water(soil_mid, reference_depth),
        )
    strategies: list[StrategyOut] = []
    baseline: MetricsOut | None = None
    for key, (plan, flex) in plans.items():
        runs, middle_params, middle_results = [], None, []
        for index, (taw_per_m, shift) in enumerate(variants):
            params = params_for(taw_per_m, shift)
            results = simulate(
                days, rain, et0, crops=crops, plan=plan, flexible=flex, params=params
            )
            runs.append(summarise(results, params, efficiency))
            if index == 1:
                middle_params, middle_results = params, results
        metrics = _metrics(runs)
        if key == "A":
            baseline = metrics
        sown_crops = sorted({r.crop for r in middle_results if r.crop})
        strategies.append(
            StrategyOut(
                key=key,
                crops=sown_crops,
                metrics=metrics,
                difference=None
                if key == "A" or baseline is None
                else _difference(metrics, baseline),
                seasons=[_season_out(r, middle_params) for r in middle_results],
            )
        )

    reference_taw = total_available_water(soil_mid, reference_depth)
    threshold = float(parameters.get("core", "flex_sow_threshold_frac"))
    used = [
        "eff_rain_fraction",
        "fallow_efficiency",
        "sufficiency_ratio",
        "initial_storage_frac",
        "spinup_seasons",
        "min_valid_day_share",
        "flex_sow_threshold_frac",
        "legume_every_n_fallow",
        "legume_crop",
        "decision_date",
        "uncertainty_rain_delta",
    ]
    return RotationOut(
        field_id=field.id,
        model_version=parameters.model_version,
        provisional=True,
        provisional_sources=["stage_lengths", "sowing_dates", "irrigation_efficiency", "legume"],
        rotation=rotation,
        first_day=first_day,
        last_day=last_day,
        seasons=len(years),
        reference=ReferenceOut(
            crop=main_crop,
            root_depth_m=reference_depth,
            taw_mm=reference_taw,
            taw_low_mm=total_available_water(soil_low, reference_depth),
            taw_high_mm=total_available_water(soil_high, reference_depth),
        ),
        flex_threshold_mm=threshold * reference_taw,
        sufficiency_ratio=float(parameters.get("core", "sufficiency_ratio")),
        irrigation_efficiency=efficiency,
        needs_signoff=[n for n in used if parameters.core[n].status == "needs_signoff"],
        assumptions=[
            "rotation_user_supplied",
            "fallow_between_seasons",
            "no_sensor",
            "regional_weather",
            "kc_mid_table_value",
            "range_from_soil_and_rain",
        ],
        strategies=strategies,
    )
