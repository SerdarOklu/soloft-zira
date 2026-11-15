# 0014: Sensors, the simulator, the cooperative panel and the farmer view

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need an agronomist.

## Decision

Phase 7 adds the ground side of the product: soil-moisture sensors (with a simulator in place of
hardware), the correction of the Water Vault by a sensor, and the two last roles of PDT 10.3.

### Sensors

- **Ingest.** `POST /api/v1/sensors/{node_id}/readings` takes the reading schema of PDT 12.2: the
  field's id, the time, an `is_simulated` flag, the battery voltage, and one `vwc_raw` per depth.
  A node (or the simulator) proves itself with a shared key in `X-Sensor-Key`, set as
  `SENSOR_INGEST_KEY` on the server; with no key set, ingest is off. A repeat of the same node,
  time and depth overwrites. A node belongs to one field.
- **Calibration before trust.** A reading is stored raw, and calibrated by a line
  (`slope × raw + intercept`) recorded per field with the wilting point and field capacity
  (`sensor_calibrations`, entered by an agronomist or admin, the result of weighing soil samples).
  Without a calibration the sensor is not trusted and the Water Vault stays in satellite mode.
- **Silence.** The Water Vault reads, for the chosen day, each node's newest reading per depth in
  the 48 hours (`sensor_silence_h`) before the end of that day. With none, or fewer than two
  depths, the field is in satellite mode; the sensor status shows silent nodes.
- **Correction (PDT 7.9).** The calibrated readings give the share of plant-available water at each
  depth, `(θ − θWP) / (θFC − θWP)` clipped to 0 to 1, weighted by the layer each sensor stands for
  (layers split halfway between sensors). That share times the crop's TAW is the decision-day
  storage, and replaces the model's. The screen shows both numbers and their difference, which is the
  "satellite versus sensor" view of PDT 4.3.
- **Range (PDT 7.10).** With a sensor the range is a narrower band: the sensor reading plus and minus
  10 % of TAW (`sensor_uncertainty_frac`, a provisional value in `config/rotation_demo.yaml`), and the
  soil capacity is taken as measured, not as a range.

### The simulator

`simulator/zira_sensor_sim.py` (standard library only) posts three nodes of four-depth readings,
marked simulated, for a chosen wetness scenario, through the real ingest endpoint. The tests run it
end to end: after the simulator's data and a calibration, the Water Vault leaves satellite mode and
the decision-day water moves from the model's 231 mm to the scenario's 140 mm of 279 mm (the phase 7
approval criterion). Hardware changes no backend code.

### Cooperative panel and farmer view

- **Cooperative user.** Creates farmer accounts in their own organization (a temporary password the
  cooperative passes on), closes or opens them, and links each field to a farmer. An admin can do the
  same anywhere. The panel is the Settings screen, now "Users and cooperative".
- **Farmer.** Sees one screen, "My field": the usable water on the latest decision day (sensor or
  satellite), its range, and the messages that were **sent** to them. A farmer never sees a draft, a
  field that is not theirs, another user, or the staff screens; the API refuses them, not only the menu.
  After sign-in a farmer lands on their screen.

## Provisional and open

1. **Sensor band** of 10 % of TAW is a placeholder. It should come from the calibration error on a
   real soil.
2. **The sensors read 0 to about 120 cm** (four depths); the crop's root zone is 1.8 m for wheat, so
   the share of available water is scaled to the crop's TAW. Deeper water is assumed to follow it.
3. **No hardware, no real calibration.** The only data so far is simulated; a node's calibration is
   one line per field, not per soil layer or per node. Drift detection against neighbouring nodes and
   threshold alerts (PDT 12.3, step 3) are not built.
4. **Shared ingest key.** One key for all nodes is enough for a demo; a deployment with real hardware
   should give each node its own key.
5. **The farmer's phone number and WhatsApp linking** stay with the message flow of decision 0012;
   the farmer view shows only messages that reached the sent state.
