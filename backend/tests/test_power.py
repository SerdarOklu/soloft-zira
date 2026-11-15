"""NASA POWER client: request built from config, answer parsed, failures reported.

No network: the HTTP transport is replaced.
"""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from app.core.parameters import get_config
from app.services import power
from app.services.power import PowerError, fetch_daily, parse_payload

NAMES = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M", "PS", "ALLSKY_SFC_SW_DWN"]


def _payload(days: dict[str, dict[str, float]]) -> dict:
    """A POWER answer shaped like the real one (checked against API v2.10.3)."""
    parameter = {name: {day: values[name] for day, values in days.items()} for name in NAMES}
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [32.5, 37.9, 1215.57]},
        "properties": {"parameter": parameter},
        "header": {"api": {"version": "v2.10.3"}, "fill_value": -999.0, "time_standard": "UTC"},
        "messages": [],
    }


GOOD_DAY = {
    "PRECTOTCORR": 0.95,
    "T2M": 4.83,
    "T2M_MAX": 10.55,
    "T2M_MIN": -0.86,
    "RH2M": 87.07,
    "WS10M": 2.56,
    "PS": 88.21,
    "ALLSKY_SFC_SW_DWN": 5.4,
}


def test_parse_maps_columns_and_keeps_the_wind_height():
    result = parse_payload(
        _payload({"20240101": GOOD_DAY}), NAMES, missing=-999.0, wind_height=10.0
    )
    assert result.elevation_m == pytest.approx(1215.57)
    assert result.api_version == "v2.10.3"
    assert result.rows == [
        {
            "date": date(2024, 1, 1),
            "wind_height_m": 10.0,
            "precipitation_mm": 0.95,
            "temperature_avg": 4.83,
            "temperature_max": 10.55,
            "temperature_min": -0.86,
            "humidity": 87.07,
            "wind_speed": 2.56,
            "surface_pressure": 88.21,
            "solar_radiation": 5.4,
            "quality_flag": None,
        }
    ]


def test_parse_turns_the_fill_value_into_missing_and_flags_the_day():
    gap = {**GOOD_DAY, "PRECTOTCORR": -999.0}
    rows = parse_payload(
        _payload({"20240101": GOOD_DAY, "20240102": gap}), NAMES, missing=-999.0, wind_height=10.0
    ).rows
    assert rows[0]["quality_flag"] is None
    assert rows[1]["precipitation_mm"] is None
    assert rows[1]["quality_flag"] == "partial"
    assert rows[1]["temperature_avg"] == 4.83  # the other values are kept


@pytest.mark.parametrize("answer", [{"messages": ["Invalid location"]}, {}, []])
def test_parse_rejects_an_answer_without_data(answer):
    with pytest.raises(PowerError, match="without data"):
        parse_payload(answer, NAMES, missing=-999.0, wind_height=10.0)


def test_parse_rejects_an_answer_that_lacks_a_requested_parameter():
    payload = _payload({"20240101": GOOD_DAY})
    del payload["properties"]["parameter"]["PS"]
    with pytest.raises(PowerError, match="lacks parameters: PS"):
        parse_payload(payload, NAMES, missing=-999.0, wind_height=10.0)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_the_request_comes_from_the_parameter_sheet_and_asks_for_utc():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_payload({"20240101": GOOD_DAY}))

    fetch_daily(
        get_config(),
        latitude=37.9,
        longitude=32.5,
        start=date(2024, 1, 1),
        end=date(2024, 1, 1),
        client=_client(handler),
    )
    (request,) = seen
    query = dict(request.url.params)
    assert str(request.url).startswith("https://power.larc.nasa.gov/api/temporal/daily/point")
    assert query["parameters"] == ",".join(NAMES)
    assert query["community"] == "AG"
    assert query["latitude"] == "37.9"
    assert query["longitude"] == "32.5"
    assert query["start"] == "20240101"
    assert query["end"] == "20240101"
    # POWER answers in local solar time unless asked for UTC.
    assert query["time-standard"] == "UTC"


def test_a_server_error_is_retried(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(power.time, "sleep", lambda _seconds: None)
    answers = iter(
        [httpx.Response(503), httpx.Response(200, json=_payload({"20240101": GOOD_DAY}))]
    )
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return next(answers)

    result = fetch_daily(
        get_config(),
        latitude=37.9,
        longitude=32.5,
        start=date(2024, 1, 1),
        end=date(2024, 1, 1),
        client=_client(handler),
    )
    assert len(calls) == 2
    assert len(result.rows) == 1


def test_giving_up_after_repeated_failures(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(power.time, "sleep", lambda _seconds: None)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(PowerError, match="not reachable after 3 attempts"):
        fetch_daily(
            get_config(),
            latitude=37.9,
            longitude=32.5,
            start=date(2024, 1, 1),
            end=date(2024, 1, 1),
            client=_client(handler),
        )
    assert len(calls) == power.MAX_ATTEMPTS


def test_a_rejected_request_is_not_retried_and_shows_the_reason():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(422, json={"messages": ["start must be before end"]})

    with pytest.raises(PowerError, match="HTTP 422.*start must be before end"):
        fetch_daily(
            get_config(),
            latitude=37.9,
            longitude=32.5,
            start=date(2024, 1, 2),
            end=date(2024, 1, 1),
            client=_client(handler),
        )
    assert len(calls) == 1


def test_a_wind_height_that_disagrees_with_the_parameter_sheet_is_refused():
    config = get_config().model_copy(deep=True)
    config.parameters.corrections["wind_measurement_height_m"].value = 2  # but WS10M is requested
    with pytest.raises(PowerError, match="WS10M is measured at 10 m"):
        fetch_daily(
            config,
            latitude=37.9,
            longitude=32.5,
            start=date(2024, 1, 1),
            end=date(2024, 1, 1),
            client=_client(lambda _request: httpx.Response(200, json={})),
        )


def test_the_default_period_is_the_twenty_five_years_of_the_sheet():
    start, end = power.default_range(get_config())
    assert (start, end) == (date(2001, 1, 1), date(2025, 12, 31))
