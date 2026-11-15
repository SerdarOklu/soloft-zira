#!/usr/bin/env python3
"""Zira sensor simulator (phase 7, PDT section 12).

It plays the part of the soil-moisture nodes of one field: for four depths (10, 30, 60 and 100 cm)
it posts volumetric water content readings to ``POST /api/v1/sensors/{node_id}/readings`` with the
same schema a real node would use, so moving to hardware changes no backend code. Every reading is
marked ``is_simulated`` and the screens say "simulated".

The moisture it writes is a made-up scenario, not a measurement: pick how wet the soil is with
``--wetness`` (0 is the wilting point, 1 is field capacity). The raw values are written through the
inverse of the sensor calibration (``--slope``, ``--intercept``), so that once the same calibration
is recorded for the field, the backend reads back the scenario.

Only the standard library is used.

    python simulator/zira_sensor_sim.py --api http://localhost:8000 --key $SENSOR_INGEST_KEY \\
        --field-id <field id> --end 2025-10-01T09:00:00Z --days 3 --wetness 0.5
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

DEPTHS_CM = (10, 30, 60, 100)
# The surface dries and wets faster than the deep soil, so the shallow layers swing more.
SWING = {10: 0.10, 30: 0.06, 60: 0.03, 100: 0.015}
# On average the surface is a little drier than the deep soil.
DEPTH_OFFSET = {10: -0.04, 30: -0.02, 60: 0.0, 100: 0.02}


def build_readings(
    *,
    rng: random.Random,
    wetness: float,
    theta_wp: float,
    theta_fc: float,
    slope: float,
    intercept: float,
    walk: dict[int, float],
) -> list[dict[str, float]]:
    """One reading per depth. ``walk`` holds each depth's drift between steps and is updated."""
    readings = []
    for depth in DEPTHS_CM:
        walk[depth] = max(-SWING[depth], min(SWING[depth], walk[depth] + rng.gauss(0, SWING[depth] / 3)))
        fraction = min(1.0, max(0.0, wetness + DEPTH_OFFSET[depth] + walk[depth]))
        theta = theta_wp + fraction * (theta_fc - theta_wp)
        raw = (theta - intercept) / slope
        readings.append({"depth_cm": depth, "vwc_raw": round(min(1.0, max(0.0, raw)), 4)})
    return readings


def payload(field_id: str, when: datetime, readings: list[dict[str, float]], battery: float) -> dict:
    return {
        "field_id": field_id,
        "measured_at": when.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "is_simulated": True,
        "battery_v": round(battery, 2),
        "readings": readings,
    }


def post(api: str, key: str, node_id: str, body: dict) -> dict:
    request = urllib.request.Request(
        f"{api.rstrip('/')}/api/v1/sensors/{node_id}/readings",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Sensor-Key": key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (the URL is the operator's)
        return json.load(response)


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--api", default=os.environ.get("ZIRA_API", "http://localhost:8000"))
    parser.add_argument("--key", default=os.environ.get("SENSOR_INGEST_KEY", ""))
    parser.add_argument("--field-id", required=True, help="the Zira field's id")
    parser.add_argument("--nodes", type=int, default=3, help="nodes in the field (3 to 4 is typical)")
    parser.add_argument("--node-prefix", default="ZIRA_SIM")
    parser.add_argument("--end", default=None, help="last reading time, ISO 8601 (default: now)")
    parser.add_argument("--days", type=float, default=3.0)
    parser.add_argument("--step-hours", type=float, default=6.0)
    parser.add_argument("--wetness", type=float, default=0.5, help="0 wilting point, 1 field capacity")
    parser.add_argument("--theta-wp", type=float, default=0.15)
    parser.add_argument("--theta-fc", type=float, default=0.31)
    parser.add_argument("--slope", type=float, default=1.0, help="sensor calibration slope to invert")
    parser.add_argument("--intercept", type=float, default=0.0, help="sensor calibration intercept")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true", help="print the readings, post nothing")
    args = parser.parse_args(argv)

    if not args.dry_run and not args.key:
        print("Set --key or SENSOR_INGEST_KEY.", file=sys.stderr)
        return 2
    if not 0.0 <= args.wetness <= 1.0 or args.theta_wp >= args.theta_fc or args.slope <= 0:
        print("Check --wetness (0 to 1), --theta-wp below --theta-fc, and --slope above 0.", file=sys.stderr)
        return 2

    end = parse_time(args.end) if args.end else datetime.now(UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    steps = max(1, int(args.days * 24 / args.step_hours))
    rng = random.Random(args.seed)
    sent = 0
    for index in range(args.nodes):
        node_id = f"{args.node_prefix}_{index + 1:03d}"
        walk = dict.fromkeys(DEPTHS_CM, 0.0)
        for step in range(steps, -1, -1):
            when = end - timedelta(hours=step * args.step_hours)
            readings = build_readings(
                rng=rng, wetness=args.wetness, theta_wp=args.theta_wp, theta_fc=args.theta_fc,
                slope=args.slope, intercept=args.intercept, walk=walk,
            )
            body = payload(args.field_id, when, readings, battery=3.9 - 0.002 * (steps - step))
            if args.dry_run:
                print(node_id, json.dumps(body))
                continue
            try:
                post(args.api, args.key, node_id, body)
            except urllib.error.HTTPError as error:
                print(f"{node_id} {when:%Y-%m-%d %H:%M}: {error.code} {error.read().decode()[:200]}", file=sys.stderr)
                return 1
            sent += 1
    if not args.dry_run:
        print(f"Posted {sent} readings of {args.nodes} nodes, simulated, ending {end:%Y-%m-%d %H:%M} UTC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
