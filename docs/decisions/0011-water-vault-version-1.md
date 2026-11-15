# 0011: What the Water Vault does in phase 4

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need an agronomist.

## Decision

The Water Vault gives the usable water in the root zone, in mm, on a chosen day, with a low to
high range. The equations are the FAO-56 ones of PDT section 7. Each was checked against the
worked examples printed in the paper (see below).

- **Reference evapotranspiration.** Penman-Monteith from POWER: `T2M` as the mean, `RH2M` as the
  mean humidity (Eq. 19), `WS10M` converted to 2 m (Eq. 47), measured pressure `PS`, `ALLSKY_SFC_SW_DWN`
  as `Rs`, latitude from the field's centroid and elevation from the field profile. A day with a
  missing input has no ET0; it is not filled in.
- **The number on the day.** The soil starts at `initial_storage_frac` of TAW at the beginning of
  a warm-up of `spinup_seasons` × 365 days, and gains `fallow_efficiency` of each day's rain up to
  TAW (PDT 7.5, fallow rule). TAW is `taw_mm_per_m` × the crop's maximum root depth (PDT 7.4).
- **Range (PDT 7.10).** Three runs: the low, middle and high water range of the soil texture, with
  the fallow efficiency shifted by `uncertainty_rain_delta` in the same direction. A field with a
  calibrated soil uses its one measured capacity.
- **Without a date,** the most recent decision day of the crop's season type is used
  (`decision_date` in the parameter sheet). A date the user chooses works for any crop.
- **Refusals.** The answer says why it cannot be given: no weather data, a date after the data, no
  warm-up before the date, too many missing days (below `min_valid_day_share`), an unknown crop,
  or a crop whose season type is not set. The screen turns each into a sentence.

## What is not done, and why

- **The crop season (ETc, actual ET, stress).** The code exists and is tested
  (`app/services/water/crop.py`, `balance.py`), but it is not run: the stage lengths in
  `config/crops.yaml` are unset on purpose, for the agronomist to set for the Konya calendar, and the
  rule is that an analysis does not run with a parameter that has no value. The screen says so.
  FAO-56 Table 11 gives starting values for winter wheat (30, 140, 40, 30); they were not used
  because the sheet does not list them as set.
- **Crop history.** Before the chosen day the field is assumed to be fallow, because Field Memory
  (phase 5) does not exist yet. A crop in the previous season would have used water, so the
  number can be too high. The screen states this assumption.
- **Sensors.** The model state is not corrected by a sensor (phase 7), so the range is shown wide.

## Open (needs an agronomist)

1. **Where the uncertainty is applied.** PDT 7.10 shifts `eff_rain_fraction`. In a fallow period that
   parameter plays no part: the soil keeps `fallow_efficiency` of the rain instead. This version
   shifts `fallow_efficiency` by the same `uncertainty_rain_delta`. Confirm, or name the quantity.
2. **Fallow with no evaporation loss.** PDT 7.5 gives fallow storage only a gain, with the loss
   folded into `fallow_efficiency`. Over a year without a crop this can fill the soil more than
   it would be in a field with weeds. Calibrate `fallow_efficiency` with local trials.
3. **The parameters marked `needs_signoff`** (`decision_date`, `fallow_efficiency`,
   `initial_storage_frac`, `spinup_seasons`, `uncertainty_rain_delta`, `min_valid_day_share`). The
   screen lists the ones a result depends on.

## Checked against FAO-56

`backend/tests/test_water_et0.py` and `test_water_balance.py` hold the printed numbers: Examples 2,
3, 5, 8, 10, 11 and 14 (chapter 3), Example 18 (Uccle, 6 July: ET0 3.88 mm/day, every intermediate
value), Example 27 and Box 15 (Kc mid), Example 28 (Kc curve), Example 36 (TAW and RAW) and
Example 37 (ten days of water stress: Ks, actual ET and depletion on each day).
