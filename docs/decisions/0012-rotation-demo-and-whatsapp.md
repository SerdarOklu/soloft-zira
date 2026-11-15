# 0012: Rotation comparison with provisional values, and WhatsApp drafts

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need an agronomist.

## Rotation comparison (strategies A, B, C)

The engine runs the three strategies day by day over the same stored NASA POWER record, from
the same starting storage, with the same soil. Only the plan of crops changes (PDT 4.4, 7.6 to
7.8). It reuses the FAO-56 pieces of decision 0011 (Kc curve, Ks, daily balance).

- **Provisional season values.** `crops.yaml` keeps the stage lengths unset for the agronomist,
  and the sheet has no sowing dates or irrigation efficiency. To let the comparison run for the
  demo, `config/rotation_demo.yaml` carries starting values, each with its source: FAO-56
  Table 11 rows for winter wheat (30, 140, 40, 30 days; Mediterranean, November) and lentil
  (25, 35, 70, 40; arid region, Oct/Nov), sowing on 1 November, irrigation efficiency 0.75.
  Every answer says `provisional: true` and the screen and the WhatsApp card say so. When the
  agronomist sets the real values, they go to `crops.yaml` / `parameters.yaml` and the entry
  here is deleted. Konya is colder than the Mediterranean row, so these lengths are likely off.
- **Strategy C uses lentil, not chickpea.** `core.legume_crop` is chickpea, but Table 11 has no
  chickpea row, so there is no length to start from. The demo file overrides it with lentil.
- **Strategy A is user-supplied.** Field Memory (phase 5) does not exist, so the current
  rotation is chosen on screen (default wheat, fallow) and the answer says so.
- **24 seasons, not 25.** The record 2001 to 2025 holds 24 complete seasons sown 2001 to 2024
  (a winter season ends the following summer). The months of 2001 before the first sowing are
  the warm-up.
- **Shared soil depth.** Between seasons the soil is fallow with the root depth of the rotation's
  main crop (1.8 m for wheat). A shallower crop (lentil, 0.8 m) starts with the storage capped at
  its own TAW, which drops the water below its roots. This is slightly pessimistic for C.
- **Kc mid is the table value**, not corrected for the local climate (Eq. 62 needs the stage's
  wind and humidity). A day without ET0 has no crop water use and counts as an incomplete day.
- **Not stored.** The comparison is computed on request (a few seconds). The
  `rotation_scenarios` table of the PDT stays unused for now.

### Open (needs an agronomist)

1. All provisional values above, and the lentil choice for C.
2. **Strategy B** follows A's crop years: it sows the planned crop only if the storage on the
   decision day is at least `flex_sow_threshold_frac` of TAW, otherwise leaves it fallow. It
   never sows in a year A leaves fallow. The PDT text allows either reading.
3. The threshold of 0.5 × TAW (about 140 mm for loam under wheat) and the decision day
   (1 October in `parameters.yaml`) differ from the 60 mm and 15 October of the draft examples.
4. The `needs_signoff` parameters, listed on the screen.

## WhatsApp drafts

Zira writes a message draft when something happens to a field's water, an agronomist approves
it, and only then does it go to the farmer. Nothing is sent without approval.

- **Events** (read from the daily run of strategy A): the autumn decision day (four wordings:
  crop or fallow year, above or below the threshold), a day with rain at or above
  `heavy_rain_mm` (20), water leaving the root zone at or above `leaching_mm` (5), the 5th and
  15th stress day in the sensitive stage, the season summary on the harvest day, and the field
  card for the latest day. The thresholds and every sentence are in
  `config/message_templates.yaml`, in Turkish and English, and need agronomist review.
- **Approval.** Draft states: pending, approved, sent, rejected, failed. Only an admin or
  agronomist can edit, approve or reject. Approving needs a recipient number. The draft keeps
  the numbers it was written from.
- **Gateway: Green API** (free developer plan), chosen by the product owner. The backend, running
  on the server, sends one HTTPS call per approved message. Credentials come from
  `GREEN_API_INSTANCE_ID` and `GREEN_API_TOKEN` in the server `.env`; without them approved
  drafts wait and nothing is sent. The token is never logged or returned.
- **Phone numbers** are stored on the draft and only the last four digits leave the API.
- **Risks.** Green API drives a WhatsApp Web session of a real phone, which WhatsApp does not
  officially support: the number can be blocked, so use a dedicated number and low volume. Message
  text and the recipient pass through Green API's servers. The free plan has limits on
  chats and messages. The official WhatsApp Cloud API avoids the ban risk but needs a Meta
  business account and approved templates.
