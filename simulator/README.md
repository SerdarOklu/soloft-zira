# Sensor simulator

`zira_sensor_sim.py` plays the soil-moisture nodes of one field. For four depths (10, 30, 60 and
100 cm) it posts readings to `POST /api/v1/sensors/{node_id}/readings`, using the same schema as a
real node, so that moving to hardware changes no backend code. Every reading is marked
`is_simulated` and the screens say "simulated". It uses only the Python standard library.

The moisture is a made-up scenario, not a measurement. Choose how wet the soil is with
`--wetness` (0 is the wilting point, 1 is field capacity).

```bash
# 1. The server needs SENSOR_INGEST_KEY set (see .env.example); the simulator sends it as X-Sensor-Key.
# 2. An agronomist records the field's sensor calibration (Water Vault screen, "Sensors"), or:
#    PUT /api/v1/fields/{id}/sensor-calibration  {"slope":1,"intercept":0,"theta_wp":0.15,"theta_fc":0.31}
# 3. Post three nodes of readings that end on the decision day:
python simulator/zira_sensor_sim.py --api https://zira.soloftindustries.com \
    --key "$SENSOR_INGEST_KEY" --field-id <field id> \
    --end 2025-10-01T09:00:00Z --days 3 --wetness 0.5

# See what would be sent without posting:
python simulator/zira_sensor_sim.py --field-id <field id> --dry-run
```

Until a field has a calibration, readings are stored but not trusted: the Water Vault stays in
satellite mode. After `sensor_silence_h` hours (48) without a reading, a field falls back to
satellite mode again. The schema and the rules are in [../docs/PDT.md](../docs/PDT.md), section 12,
and the decisions in [../docs/decisions/0014-sensors-and-cooperative.md](../docs/decisions/0014-sensors-and-cooperative.md).
