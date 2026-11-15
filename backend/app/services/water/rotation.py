"""The rotation comparison: one field, one weather series, three strategies (PDT 4.4, 7.6 to 7.8).

Pure functions. Every strategy is simulated day by day over the same record, from the same
starting storage, with the same soil and weather. Only the plan of crops changes, and that
difference is never equalised (PDT 15). Nothing here reads configuration or the database.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.services.water.balance import crop_day, fallow_day
from app.services.water.crop import adjusted_depletion_fraction, kc_curve

FALLOW = None  # a slot with no crop


@dataclass(frozen=True)
class SeasonCrop:
    key: str
    sow_month: int
    sow_day: int
    l_ini: int
    l_dev: int
    l_mid: int
    l_late: int
    kc_ini: float
    kc_mid: float
    kc_end: float
    p_table: float
    root_depth_m: float

    @property
    def length(self) -> int:
        return self.l_ini + self.l_dev + self.l_mid + self.l_late

    def sowing(self, year: int) -> date:
        return date(year, self.sow_month, self.sow_day)


@dataclass(frozen=True)
class RunParams:
    taw_per_m: float
    eff_rain_fraction: float
    fallow_efficiency: float
    initial_fraction: float
    reference_depth_m: float
    min_valid_share: float
    sufficiency_ratio: float
    critical_stress_days_max: int | None
    flex_threshold_frac: float
    decision_month: int
    decision_day: int
    p_ref_etc: float
    p_min: float
    p_max: float


@dataclass
class SeasonResult:
    year: int  # the year of sowing
    planned: str | None
    crop: str | None = None  # what was sown; None when fallow or when strategy B held back
    days: int = 0
    complete_days: int = 0
    crop_et: float = 0.0
    actual_et: float = 0.0
    stress_days: int = 0
    storage_at_decision: float | None = None

    @property
    def sown(self) -> bool:
        return self.crop is not None

    def is_valid(self, min_share: float) -> bool:
        return self.sown and self.days > 0 and self.complete_days / self.days >= min_share

    @property
    def deficit(self) -> float:
        return self.crop_et - self.actual_et

    @property
    def ratio(self) -> float | None:
        return self.actual_et / self.crop_et if self.crop_et > 0 else None

    def is_sufficient(self, params: RunParams) -> bool:
        if not self.is_valid(params.min_valid_share):
            return False
        ratio = self.ratio
        if ratio is None or ratio < params.sufficiency_ratio:
            return False
        cap = params.critical_stress_days_max
        return cap is None or self.stress_days <= cap


def current_plan(rotation: Sequence[str | None], years: Sequence[int]) -> dict[int, str | None]:
    """Strategy A: the sequence repeated cyclically over the sowing years (PDT 7.8)."""
    if not rotation:
        raise ValueError("The current rotation is empty")
    return {year: rotation[index % len(rotation)] for index, year in enumerate(years)}


def legume_plan(
    plan: dict[int, str | None], *, every_n_fallow: int, legume: str
) -> dict[int, str | None]:
    """Strategy C: as A, but every ``every_n_fallow``-th fallow season is sown with the legume."""
    if every_n_fallow < 1:
        raise ValueError("every_n_fallow must be at least 1")
    result = dict(plan)
    fallow_seen = 0
    for year in sorted(plan):
        if plan[year] is FALLOW:
            fallow_seen += 1
            if fallow_seen % every_n_fallow == 0:
                result[year] = legume
    return result


def simulate(
    days: Sequence[date],
    rain: Sequence[float | None],
    et0: Sequence[float | None],
    *,
    crops: dict[str, SeasonCrop],
    plan: dict[int, str | None],
    flexible: frozenset[int] = frozenset(),
    params: RunParams,
) -> list[SeasonResult]:
    """Run one strategy over the record and return one result per sowing year of ``plan``.

    ``flexible`` lists the sowing years in which the planned crop is sown only if the storage
    on the decision day is at least ``flex_threshold_frac`` of the crop's TAW (strategy B).
    A missing rain value counts as no rain; a day without ET0 has no crop water use. Both are
    counted as incomplete days, and a season with too many of them is not valid (PDT 7.6).
    """
    reference_taw = params.taw_per_m * params.reference_depth_m
    storage = params.initial_fraction * reference_taw
    results = {year: SeasonResult(year=year, planned=crop) for year, crop in plan.items()}
    sown: dict[int, str | None] = {
        year: (FALLOW if year in flexible else crop) for year, crop in plan.items()
    }
    for year in flexible:
        sowing = crops[plan[year]].sowing(year) if plan[year] else None
        if sowing and date(year, params.decision_month, params.decision_day) >= sowing:
            raise ValueError("The decision day must come before the sowing day")

    for day, rainfall, reference_et in zip(days, rain, et0, strict=True):
        precipitation = rainfall or 0.0
        active: tuple[int, SeasonCrop, int] | None = None
        for year in (day.year - 1, day.year):
            key = sown.get(year)
            if key is None:
                continue
            crop = crops[key]
            season_day = (day - crop.sowing(year)).days + 1
            if 1 <= season_day <= crop.length:
                active = (year, crop, season_day)
                break

        if active is None:
            storage, _ = fallow_day(
                storage,
                precipitation,
                taw=reference_taw,
                fallow_efficiency=params.fallow_efficiency,
            )
        else:
            year, crop, season_day = active
            crop_taw = params.taw_per_m * crop.root_depth_m
            if season_day == 1:
                storage = min(storage, crop_taw)
            kc = kc_curve(
                season_day,
                kc_ini=crop.kc_ini,
                kc_mid=crop.kc_mid,
                kc_end=crop.kc_end,
                l_ini=crop.l_ini,
                l_dev=crop.l_dev,
                l_mid=crop.l_mid,
                l_late=crop.l_late,
            )
            reference = reference_et or 0.0
            p = adjusted_depletion_fraction(
                crop.p_table,
                kc * reference,
                reference_etc=params.p_ref_etc,
                p_min=params.p_min,
                p_max=params.p_max,
            )
            outcome = crop_day(
                storage,
                precipitation=precipitation,
                irrigation=0.0,
                et0=reference,
                kc=kc,
                taw=crop_taw,
                p=p,
                eff_rain_fraction=params.eff_rain_fraction,
            )
            storage = outcome.storage
            result = results[year]
            result.crop = crop.key
            result.days += 1
            result.complete_days += int(rainfall is not None and reference_et is not None)
            result.crop_et += outcome.crop_et
            result.actual_et += outcome.actual_et
            mid_start = crop.l_ini + crop.l_dev
            if mid_start < season_day <= mid_start + crop.l_mid and outcome.ks < 1.0:
                result.stress_days += 1

        # Strategy B decides at the end of the decision day (PDT 7.8).
        if (
            day.month == params.decision_month
            and day.day == params.decision_day
            and day.year in flexible
        ):
            planned = plan[day.year]
            if planned is not None:
                crop_taw = params.taw_per_m * crops[planned].root_depth_m
                results[day.year].storage_at_decision = storage
                if min(storage, crop_taw) >= params.flex_threshold_frac * crop_taw:
                    sown[day.year] = planned
                    results[day.year].crop = None  # set when the first season day is run
    return [results[year] for year in sorted(results)]


def sowing_years(
    first_day: date,
    last_day: date,
    *,
    crops: Sequence[SeasonCrop],
    decision_month: int,
    decision_day: int,
    limit: int,
) -> list[int]:
    """The years in which a season can be sown and finished inside the record.

    A slot needs its decision day and its sowing day after the first day of data, and the end
    of the longest crop season on or before the last day.
    """
    longest = max(crop.length for crop in crops)
    years = []
    for year in range(first_day.year, last_day.year + 1):
        if date(year, decision_month, decision_day) < first_day:
            continue
        if any(crop.sowing(year) < first_day for crop in crops):
            continue
        end = max(crop.sowing(year) for crop in crops) + timedelta(days=longest - 1)
        if end <= last_day:
            years.append(year)
    return years[-limit:]


@dataclass
class Summary:
    sown: int = 0
    valid: int = 0
    sufficient: int = 0
    fallow: int = 0
    share: float | None = None
    stress_days_mean: float | None = None
    deficit_mean_mm: float | None = None
    irrigation_need_mean_mm: float | None = None
    deficit_total_mm: float = 0.0
    seasons: list[SeasonResult] = field(default_factory=list)


def summarise(
    results: Sequence[SeasonResult], params: RunParams, irrigation_efficiency: float
) -> Summary:
    summary = Summary(seasons=list(results))
    valid = [r for r in results if r.is_valid(params.min_valid_share)]
    summary.sown = sum(1 for r in results if r.sown)
    summary.valid = len(valid)
    summary.fallow = len(results) - summary.sown
    summary.sufficient = sum(1 for r in results if r.is_sufficient(params))
    if valid:
        summary.share = summary.sufficient / len(valid)
        summary.stress_days_mean = sum(r.stress_days for r in valid) / len(valid)
        summary.deficit_mean_mm = sum(r.deficit for r in valid) / len(valid)
        summary.irrigation_need_mean_mm = summary.deficit_mean_mm / irrigation_efficiency
        summary.deficit_total_mm = sum(r.deficit for r in valid)
    return summary
