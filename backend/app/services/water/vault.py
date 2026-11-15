"""The Water Vault for one field, crop and date (PDT sections 4.3, 7.4, 7.5, 7.9 and 7.10).

What it computes: the water the root zone holds on the chosen day, in mm, with a low to high
range. What it assumes, in plain terms: the field was fallow during the warm-up before that
day, because the crop history comes with Field Memory (phase 5). The crop season itself
(ETc, actual ET, stress) needs the stage lengths the agronomist has not set, so it is not run.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.parameters import Config, Crop
from app.models import Field, SoilProfile, WeatherObservation
from app.schemas.water import (
    CropInfo,
    CropOption,
    DayRow,
    Decision,
    Parameters,
    WaterVaultOut,
    Window,
)
from app.services.power import SOURCE as POWER_SOURCE
from app.services.water import et0
from app.services.water.balance import simulate_fallow
from app.services.water.crop import total_available_water

DAYS_PER_SEASON = 365
STAGE_LENGTHS_NOT_SET = "stage_lengths_not_set"


class VaultError(Exception):
    """A reason the Water Vault cannot answer. ``code`` is shown to the user in their language."""

    def __init__(self, code: str, **details: Any) -> None:
        super().__init__(code)
        self.code = code
        self.details = details


def crop_info(key: str, crop: Crop) -> CropInfo:
    ready = crop.stage_lengths_days is not None
    return CropInfo(
        key=key,
        name_tr=crop.name_tr,
        season_type=crop.season_type,
        root_depth_m=crop.zr_m[1],  # version 1 uses the maximum root depth (PDT 7.4)
        season_ready=ready,
        season_blocker=None if ready else STAGE_LENGTHS_NOT_SET,
    )


def crop_options(config: Config) -> list[CropOption]:
    options = []
    for key, crop in config.crops.items():
        info = crop_info(key, crop)
        options.append(
            CropOption(
                key=key,
                name_tr=info.name_tr,
                season_type=info.season_type,
                root_depth_m=info.root_depth_m,
                season_ready=info.season_ready,
            )
        )
    return options


def latest_decision_date(config: Config, crop: Crop, last_data_day: date) -> date:
    """The most recent decision day of the crop's season type that the data already covers."""
    if crop.season_type not in ("winter", "summer"):
        raise VaultError("season_type_not_set")
    month, day = (
        int(part)
        for part in config.parameters.get("core", "decision_date")[crop.season_type].split("-")
    )
    candidate = date(last_data_day.year, month, day)
    return candidate if candidate <= last_data_day else date(last_data_day.year - 1, month, day)


def _et0_for(row: WeatherObservation, *, latitude: float, elevation_m: float) -> float | None:
    needed = (
        row.temperature_max,
        row.temperature_min,
        row.temperature_avg,
        row.humidity,
        row.wind_speed,
        row.solar_radiation,
        row.surface_pressure,
        row.wind_height_m,
    )
    if any(value is None for value in needed):
        return None
    return et0.reference_et0(
        doy=et0.day_of_year(row.date),
        latitude_deg=latitude,
        elevation_m=elevation_m,
        t_max=row.temperature_max,
        t_min=row.temperature_min,
        t_mean=row.temperature_avg,
        ea=et0.actual_vapour_pressure_from_mean_humidity(
            row.humidity, row.temperature_max, row.temperature_min
        ),
        u2=et0.wind_at_2m(row.wind_speed, row.wind_height_m),
        rs=row.solar_radiation,
        pressure_kpa=row.surface_pressure,
    )


def water_vault(
    session: Session,
    field: Field,
    crop_key: str,
    on: date | None,
    config: Config,
) -> WaterVaultOut:
    crop = config.crops.get(crop_key)
    if crop is None:
        raise VaultError("unknown_crop", crop=crop_key)

    location = session.execute(
        select(func.ST_Y(Field.centroid), func.ST_X(Field.centroid)).where(Field.id == field.id)
    ).one()
    if location[0] is None:
        raise VaultError("no_location")
    latitude = float(location[0])

    scope = (WeatherObservation.field_id == field.id, WeatherObservation.source == POWER_SOURCE)
    first_day, last_day = session.execute(
        select(func.min(WeatherObservation.date), func.max(WeatherObservation.date)).where(*scope)
    ).one()
    if first_day is None:
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

    parameters = config.parameters
    spinup_days = int(parameters.get("core", "spinup_seasons")) * DAYS_PER_SEASON
    fallow_efficiency = float(parameters.get("core", "fallow_efficiency"))
    initial_fraction = float(parameters.get("core", "initial_storage_frac"))
    delta = float(parameters.get("core", "uncertainty_rain_delta"))
    min_share = float(parameters.get("core", "min_valid_day_share"))

    date_is_default = on is None
    day = latest_decision_date(config, crop, last_day) if on is None else on
    if day > last_day:
        raise VaultError("date_after_data", last_date=last_day.isoformat())
    start = day - timedelta(days=spinup_days - 1)
    if start < first_day:
        raise VaultError(
            "not_enough_history",
            first_date=first_day.isoformat(),
            earliest_date=(first_day + timedelta(days=spinup_days - 1)).isoformat(),
        )

    rows = {
        row.date: row
        for row in session.scalars(
            select(WeatherObservation).where(*scope, WeatherObservation.date.between(start, day))
        )
    }
    days = [start + timedelta(days=offset) for offset in range(spinup_days)]
    rain = [rows[d].precipitation_mm if d in rows else None for d in days]
    missing = sum(1 for value in rain if value is None)
    if (spinup_days - missing) / spinup_days < min_share:
        raise VaultError(
            "too_many_gaps", missing_days=missing, days=spinup_days, required_share=min_share
        )

    # Soil capacity. A calibrated field has one measured value; otherwise the FAO-56 range of
    # its texture gives the low and high runs (PDT 7.10).
    root_depth = crop.zr_m[1]
    mid_taw = total_available_water(profile.taw_mm_per_m, root_depth)
    if profile.is_calibrated:
        low_taw = high_taw = mid_taw
    else:
        low_taw = total_available_water(soil.taw_mm_per_m[0], root_depth)
        high_taw = total_available_water(soil.taw_mm_per_m[1], root_depth)

    def run(taw: float, efficiency: float) -> list[float]:
        return simulate_fallow(
            rain,
            taw=taw,
            fallow_efficiency=min(1.0, max(0.0, efficiency)),
            initial_fraction=initial_fraction,
        )

    middle = run(mid_taw, fallow_efficiency)
    low = run(low_taw, fallow_efficiency - delta)
    high = run(high_taw, fallow_efficiency + delta)

    et0_blocker = None
    if field.elevation_m is None:
        et0_blocker = "no_elevation"

    daily: list[DayRow] = []
    et0_days = 0
    for index, d in enumerate(days):
        value = None
        if et0_blocker is None and d in rows:
            value = _et0_for(rows[d], latitude=latitude, elevation_m=field.elevation_m)
        if value is not None:
            et0_days += 1
        daily.append(
            DayRow(date=d, precipitation_mm=rain[index], et0_mm=value, storage_mm=middle[index])
        )

    used = ["fallow_efficiency", "initial_storage_frac", "spinup_seasons", "uncertainty_rain_delta"]
    used += ["min_valid_day_share"]
    if date_is_default:
        used.append("decision_date")
    needs_signoff = [name for name in used if parameters.core[name].status == "needs_signoff"]

    return WaterVaultOut(
        field_id=field.id,
        crop=crop_info(crop_key, crop),
        date=day,
        date_is_default=date_is_default,
        decision=Decision(
            storage_mm=middle[-1],
            low_mm=low[-1],
            high_mm=high[-1],
            taw_mm=mid_taw,
            taw_low_mm=low_taw,
            taw_high_mm=high_taw,
            fill_fraction=middle[-1] / mid_taw if mid_taw else 0.0,
        ),
        window=Window(start=start, end=day, days=spinup_days, missing_days=missing),
        parameters=Parameters(
            fallow_efficiency=fallow_efficiency,
            initial_storage_frac=initial_fraction,
            spinup_days=spinup_days,
            uncertainty_delta=delta,
        ),
        needs_signoff=needs_signoff,
        assumptions=[
            "fallow_before_the_day",
            "regional_weather",
            "no_sensor",
            "range_from_soil_and_fallow_efficiency",
        ],
        soil_calibrated=bool(profile.is_calibrated),
        et0_days=et0_days,
        et0_blocker=et0_blocker,
        daily=daily,
    )
