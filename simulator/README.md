# Sensor simulator

Arrives in Phase 7. It will post soil-moisture readings for four depths (10, 30, 60 and
100 cm) to `POST /api/v1/sensors/{node_id}/readings`, using the same schema as a real
node, so that moving to hardware changes no backend code.

The reading schema and the sensor rules are in [../docs/PDT.md](../docs/PDT.md), section 12.
