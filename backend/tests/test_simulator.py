"""The sensor simulator, end to end: its readings go through the real ingest endpoint and correct
the Water Vault (the phase 7 approval criterion)."""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import REPO_ROOT, get_settings
from app.models import Role
from tests.test_fields_api import create_field
from tests.test_water_vault_api import FIRST_DAY, LAST_DAY, store, weather

pytestmark = pytest.mark.db

SPEC = importlib.util.spec_from_file_location(
    "zira_sensor_sim", Path(REPO_ROOT) / "simulator" / "zira_sensor_sim.py"
)
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)

KEY = "sim-key"


def test_readings_are_inverse_calibrated_and_repeatable():
    def make(seed):
        return sim.build_readings(
            rng=random.Random(seed),
            wetness=0.5,
            theta_wp=0.15,
            theta_fc=0.31,
            slope=0.5,
            intercept=0.1,
            walk=dict.fromkeys(sim.DEPTHS_CM, 0.0),
        )

    first = make(3)
    assert first == make(3) and first != make(4)
    assert [r["depth_cm"] for r in first] == [10, 30, 60, 100]
    # raw = (theta - intercept) / slope, so the calibrated value lands back between the bounds.
    for reading in first:
        theta = 0.5 * reading["vwc_raw"] + 0.1
        assert 0.15 <= theta <= 0.31


def test_the_simulator_refuses_nonsense_settings(capsys):
    assert sim.main(["--field-id", "x", "--wetness", "1.5", "--dry-run"]) == 2
    assert sim.main(["--field-id", "x"]) == 2  # no key and not a dry run


def test_simulated_readings_correct_the_water_vault(
    pg_client: TestClient, make_user, bearer, pg, capsys
):
    make_user("agro@example.com", Role.AGRONOMIST)
    headers = bearer("agro@example.com")
    field = create_field(pg_client, headers)["id"]
    store(pg, field, weather(FIRST_DAY, LAST_DAY))
    settings = get_settings()
    settings.sensor_ingest_key = KEY
    try:
        before = pg_client.get(
            f"/api/v1/fields/{field}/water-vault", params={"crop": "winter_wheat"}, headers=headers
        ).json()
        assert before["mode"] == "satellite" and before["decision"]["storage_mm"] == pytest.approx(
            230.75
        )

        pg_client.put(
            f"/api/v1/fields/{field}/sensor-calibration",
            json={"slope": 1.0, "intercept": 0.0, "theta_wp": 0.15, "theta_fc": 0.31},
            headers=headers,
        )
        assert (
            sim.main(
                [
                    "--field-id",
                    field,
                    "--end",
                    "2025-10-01T09:00:00Z",
                    "--days",
                    "2",
                    "--wetness",
                    "0.5",
                    "--dry-run",
                ]
            )
            == 0
        )
        lines = [
            line for line in capsys.readouterr().out.splitlines() if line.startswith("ZIRA_SIM_")
        ]
        assert len(lines) == 3 * 9  # three nodes, nine readings each (every six hours for two days)
        for line in lines:
            node, body = line.split(" ", 1)
            response = pg_client.post(
                f"/api/v1/sensors/{node}/readings",
                json=json.loads(body),
                headers={"X-Sensor-Key": KEY},
            )
            assert response.status_code == 200 and response.json()["calibrated"] is True

        after = pg_client.get(
            f"/api/v1/fields/{field}/water-vault", params={"crop": "winter_wheat"}, headers=headers
        ).json()
    finally:
        settings.sensor_ingest_key = ""
    assert after["mode"] == "sensor"
    # The scenario is half-full soil: about 140 mm of 279, far from the model's 231 mm.
    assert 110 < after["decision"]["storage_mm"] < 170
    assert after["sensor"]["difference_mm"] < -50
    assert after["sensor"]["nodes"] == 3
    status = pg_client.get(f"/api/v1/fields/{field}/sensors", headers=headers).json()
    assert all(node["is_simulated"] for node in status["nodes"])
