"""Field Memory: was the field cropped or fallow in each of the last seasons? (PDT 4.1, phase 5)

Pure functions over the MODIS NDVI series of a field. A season is named by its harvest year and
covers the growing window from 1 March to 30 September of that year, which holds the peak of
winter cereals (April to June) and of spring-sown crops (July to August). The field is *cropped*
when the highest NDVI of the window reaches the threshold, *fallow* when it does not, and
*unknown* when too few clear composites exist to say.

What this cannot do: it separates cropped from fallow, not crop species, and it cannot tell a
winter crop from a summer one. A field smaller than a few pixels gives a mixed signal. The
threshold is provisional until an agronomist calibrates it with ground truth (decision 0013).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

WINDOW_START = (3, 1)
WINDOW_END = (9, 30)
# About one composite every eight days (Terra and Aqua together) over the 214-day window.
EXPECTED_OBSERVATIONS = 26
MIN_GOOD_OBSERVATIONS = 5
# Margin above or below the threshold that counts as a clear call, in NDVI.
FULL_CONFIDENCE_MARGIN = 0.2
# Clear composites needed for the coverage part of the confidence to reach its maximum.
FULL_COVERAGE_OBSERVATIONS = EXPECTED_OBSERVATIONS // 2

CROPPED, FALLOW, UNKNOWN = "cropped", "fallow", "unknown"


@dataclass(frozen=True)
class Obs:
    day: date
    ndvi: float | None
    valid_pixels: int


@dataclass(frozen=True)
class SeasonDetection:
    season: str  # "2024-2025"
    harvest_year: int
    state: str
    peak_ndvi: float | None
    peak_date: date | None
    good_observations: int
    total_observations: int
    confidence: float | None


def harvest_years(today: date, history_years: int) -> list[int]:
    """The last ``history_years`` seasons whose window has ended, oldest first."""
    last = today.year if today > date(today.year, *WINDOW_END) else today.year - 1
    return list(range(last - history_years + 1, last + 1))


def season_name(harvest_year: int) -> str:
    return f"{harvest_year - 1}-{harvest_year}"


def detect(
    observations: Sequence[Obs], *, threshold: float, history_years: int, today: date
) -> list[SeasonDetection]:
    seasons = []
    for year in harvest_years(today, history_years):
        start, end = date(year, *WINDOW_START), date(year, *WINDOW_END)
        window = [o for o in observations if start <= o.day <= end]
        good = [o for o in window if o.ndvi is not None and o.valid_pixels >= 1]
        if len(good) < MIN_GOOD_OBSERVATIONS:
            seasons.append(
                SeasonDetection(
                    season_name(year), year, UNKNOWN, None, None, len(good), len(window), None
                )
            )
            continue
        peak = max(good, key=lambda o: o.ndvi or 0.0)
        peak_value = peak.ndvi or 0.0
        state = CROPPED if peak_value >= threshold else FALLOW
        margin = min(1.0, abs(peak_value - threshold) / FULL_CONFIDENCE_MARGIN)
        coverage = min(1.0, len(good) / FULL_COVERAGE_OBSERVATIONS)
        seasons.append(
            SeasonDetection(
                season_name(year),
                year,
                state,
                peak_value,
                peak.day,
                len(good),
                len(window),
                round(margin * coverage, 3),
            )
        )
    return seasons


def confidence_level(confidence: float | None) -> str | None:
    if confidence is None:
        return None
    if confidence >= 0.66:
        return "high"
    return "medium" if confidence >= 0.33 else "low"


def rotation_from_history(states: Sequence[str]) -> list[str | None]:
    """A confirmed history as a rotation for strategy A: cropped seasons become the main
    winter crop, fallow seasons stay fallow. Crop species are not known (PDT 4.1)."""
    return ["winter_wheat" if state == CROPPED else None for state in states]
