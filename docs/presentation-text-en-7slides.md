# Zira: presentation text (7 slides, English)

Based on the state of the platform on 15 November 2026. Seven slides; the last one is impact, sources and team (the video is submitted separately). The formula sheet, references and fuller notes are in the Turkish 14-slide file [sunum-metni-tr.md](sunum-metni-tr.md); use it for Q&A.

To fill in: team name, repository link, names of the AI tools used, the video file.
Timing: about 7 minutes of talk; the video is separate.

---

## SLIDE 1 / 7 · COVER

**NASA SPACE APPS CHALLENGE 2026 · FIELD SHIFT: ADAPTING FARMS WITH NASA DATA**

# Zira
**Which rotation can this field's water carry?**

On sowing-decision day, Zira shows the plant-available water in a field's soil in millimetres and compares three rotations over 24 seasons of NASA data.

[Team name] · Live platform: zira.soloftindustries.com

**Speaker notes**
Zira is a decision-support platform for dryland farms. It is built for agronomists and cooperatives; the farmer receives the result as a short WhatsApp message. Zira does not decide; it supports the decision of the agronomist and the farmer. The platform is live: you can sign in, draw a field, pull NASA data, read the field's history from satellite, and compare rotations.

---

## SLIDE 2 / 7 · THE PROBLEM

# Farming is planned by the calendar, not by the water

| | |
|---|---|
| **740+** | Recorded sinkholes in the Konya Closed Basin |
| **3.4 cm / year** | Groundwater storage lost (GRACE-based study) |
| **245 – 534 mm** | Seasonal rainfall at the demo site, from the driest to the wettest of 25 seasons |

Rainfall is less predictable and water is scarcer. A calendar rotation is sown the same way in a 245 mm season and in a 534 mm season. Farmers have no simple tool to weigh one rotation against another for their own field.

*Sources: Konya Technical University Sinkhole Research Center (NTV/IHA, 17 August 2026) · Khorrami, Arık and Gündüz 2021 · NASA POWER*

**Speaker notes**
Our first target is the semi-arid Konya Closed Basin and dryland farming. Researchers link the fall in groundwater to heavy pumping, and the spread of sinkholes to that. Yet the common rotation is fixed: wheat one year, fallow the next. When we read NASA GRACE and GRACE-FO ourselves for the wider region (about 300 km), total water storage falls by 0.46 cm a year over 2002–2022; the 3.4 cm figure is the study's estimate for groundwater inside the basin. The two numbers measure different things and must not be swapped. The 245–534 mm range belongs to the demo site and comes from its 25-season NASA POWER record.

---

## SLIDE 3 / 7 · THE SOLUTION

# One question, three modules, three users

> "On sowing-decision day, how many millimetres of plant-available water does the soil hold, and how do three rotations behave with that water?"

| 1 · Field Memory | 2 · Water Vault | 3 · Zira Card |
|---|---|---|
| Which of the last ten seasons was cropped, which fallow? Read from satellite, confirmed by an agronomist. | Plant-available water on decision day (mm), with a range; corrected by a sensor when there is one. | Rotations A, B and C: in how many of 24 seasons the water was enough, why, and on what evidence. |

**Agronomist** confirms and approves · **Cooperative** manages farmers and fields · **Farmer** receives a short WhatsApp message.
**No message reaches a farmer without agronomist approval.**

**Speaker notes**
The three modules form a chain: Field Memory sets rotation A, the Water Vault gives today's water, the Zira Card compares. Roles are enforced on the server: a farmer cannot see another farmer's field or the agronomist screens because the API refuses, not because the menu hides them. One engine runs for every field; whatever differs between fields lives in the Field Profile, not in code.

---

## SLIDE 4 / 7 · NASA DATA

# Each source has one job, at its own scale

| Source | Job | Scale |
|---|---|---|
| **NASA POWER** | Daily weather, 2001–2025 (9,131 days per field) | ~50 km |
| **Landsat 8/9** | NDVI from inside the field polygon: cropped or fallow over 10 seasons; preferred when it covers enough seasons | 30 m |
| **MODIS MOD13Q1 / MYD13Q1** | The same NDVI, as a fallback for cloudy Landsat periods (~450 images) | 250 m, 16-day |
| **SMAP · GPM IMERG · GRACE** | Not inputs but regional cross-checks of the model: soil moisture, rainfall, basin water-storage trend | 9 km · ~10 km · ~300 km |
| **SRTM (NASADEM)** | Field elevation and slope | 30 m |

The Data Center shows which source is really connected; a source that is not connected is never shown as healthy.

**Speaker notes**
Scale rules: POWER is a regional reanalysis, not a field measurement. SMAP is a 9 km average. GRACE is never the groundwater under a single parcel. The two rainfall sources are never added together: one is the input, the other a cross-check. We read Landsat 8/9 (Collection 2 Level-2) and MODIS (MOD13Q1/MYD13Q1 version 061) from the Microsoft Planetary Computer's open STAC catalogue, with no account needed, instead of Earth Engine. At 30 m, Landsat gives dozens of pixels in a field of a few hectares; a MODIS pixel is about 6 ha, which is why Landsat is preferred. SMAP, GPM and GRACE are read with a NASA Earthdata token; it expires in about 60 days, and when it does the Data Center shows them as "not connected". ECOSTRESS is not connected. SMAP sees only the top 5 cm while the Water Vault models the root zone, so the two are compared as trends. Attribution: weather data come from the NASA LaRC POWER Project, funded by the NASA Earth Science/Applied Science Program. NASA GIBS is part of NASA ESDIS.

---

## SLIDE 5 / 7 · HOW IT WORKS

# From satellite to field: history, water, rotation

**Field Memory:** from Landsat 30 m (MODIS when Landsat covers too few seasons), if a season's (1 March – 30 September) peak NDVI is ≥ 0.40 it is *cropped*, otherwise *fallow*; with too few clean images it is *unknown*. NDVI = (NIR − Red) / (NIR + Red)

**Water Vault (daily FAO-56):**
- ET₀ = [0.408 Δ (Rₙ − G) + γ · 900/(T + 273) · u₂ (eₛ − eₐ)] / [Δ + γ (1 + 0.34 u₂)]
- ETc = Kc × ET₀ · TAW = 1000 (θFC − θWP) Zr
- S(t) = min(TAW, max(0, S(t−1) + Peff + I − ETa − R − D)) · ETa = Ks × Kc × ET₀

**Three rotations, same weather, same soil, same starting water:** A repeats the confirmed history · B sows only if S ≥ 0.50 × TAW on 1 October · C sows a legume in every second fallow season. A season counts as **"water was enough"** if Σ ETa ÷ Σ ETc ≥ 0.70.

**Speaker notes**
This is not a model we invented: it is the FAO-56 standard. ET₀, Kc, TAW/RAW and the stress calculation were tested against FAO-56's printed examples (Example 18: Uccle, ET₀ = 3.88 mm/day). Every result is computed three times (soil capacity low/mid/high, rainfall share ±0.10) and shown as a range; a single number gives a false impression of certainty. The thresholds (0.70, 0.50, 1 October, NDVI 0.40), crop stage lengths (FAO-56 Table 11) and irrigation efficiency live in a separate configuration file with their source, carry a "provisional" label on the card, and are moved to local values with agronomist approval. Season count: the 2001–2025 record yields 24 complete seasons. See the formula sheet for symbols and full formulas.

---

## SLIDE 6 / 7 · RESULTS AND SENSORS

# What we find, and what changes when we measure the ground

**Platform demo field (1 October 2025, winter wheat, loam, capacity 279 mm):** plant-available water 202 mm (range 154–249). Seasons with enough water: A 6 of 12, B 6 of 7, C 11 of 18.

**Kulu validation study (2016–2026):** cropped and fallow seasons separate cleanly; the water model agrees with NASA SMAP and MERRA-2 soil moisture at r = 0.61 (on the platform, SMAP, GPM and GRACE appear as the same kind of regional cross-check); water was enough in 6 of 13 sowings for A, 5 of 10 for B and 3 of 21 for C.

**Sensor mode:** four depths from 10 to 100 cm, a field-specific calibration, the decision-day store replaces the model's, and the range narrows. In the example scenario the model says 231 mm while the sensor says **140 mm**; the gap is shown side by side. After 48 hours of silence the field falls back to satellite mode automatically.

**From event to phone:** sowing-decision day, ≥ 20 mm rain, leaching, stress days, harvest summary → draft → **agronomist approval** → WhatsApp. A farmer sees only sent messages and their own field.

**Speaker notes**
The platform's numbers and the Kulu study's numbers differ because location, soil and rules differ; we do not mix them. Kulu was chosen to test the science in depth because a single 250 m MODIS pixel there shows a clear cropped-fallow signal; it is not a surveyed field. The system criticises itself: the weakest spring greening was in 2022 while the water model assigns the lowest yield to 2024, and low-confidence seasons are flagged on screen. The sensor readings come from a simulator that uses the schema real hardware will send and are labelled "simulated" on screen; moving to hardware changes no backend code. The sensor band (±10 % of TAW) and the thresholds are starting values to be settled with real calibration. Message example: "There are 95 mm of available water in the soil (capacity 279 mm); this is below the 140 mm threshold… Talk to your agronomist before sowing. Zira does not decide." [Verify the Green API pairing before the talk; if it does not work, say "sending is ready, pairing pending".]

---

## SLIDE 7 / 7 · IMPACT, SOURCES AND TEAM

# Zira does not decide; it helps the farmer decide with evidence.

**Impact**
- A field-level rotation comparison from free NASA data.
- A plain message that reaches the farmer only after agronomist approval.
- Management at cooperative scale.

| Honest limits today | Next step |
|---|---|
| Crop stage lengths and thresholds are provisional, awaiting agronomist approval | Real fields from a cooperative; local calibration of the NDVI threshold for Landsat |
| Sensor data come from a simulator; no real calibration yet | Reference soil-moisture probes and real sensor hardware |
| Landsat and MODIS tell cropped from fallow, not the crop type | Crop type entered by the agronomist, then a crop classifier validated on local fields |

**NASA data used:** POWER · MODIS (MOD13Q1, MYD13Q1) · Landsat 8/9 · SRTM/NASADEM · SMAP · GPM IMERG · GRACE-FO · GIBS
*Weather data were obtained from the NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science/Applied Science Program. Imagery was provided through NASA GIBS, part of NASA ESDIS. Full reference list: [docs/kaynakca.md](kaynakca.md).*

**Use of artificial intelligence:** [name the tools]. Used for: code, interface text, message-draft text and these slides. Everything was reviewed by the team. No AI-generated imagery.

**Links:** Live platform: zira.soloftindustries.com · Repository: [link, if public] · Demo video: [link]

**Team:** [team name] · [members] · [mentors and institutions] · Thank you.

**Speaker notes**
Closing: "Zira does not decide; it strengthens the hand of whoever does, with the light of NASA data. Thank you." Validation runs in four stages: one coordinate, then three rotations on one real field, then two more fields in the same basin, then another climate with local calibration; thresholds are never copied to a new region. Do not delete the limits column: it is the jury's first question. The demo video is submitted separately; the end-to-end walk-through (draw a field, NASA data, Field Memory, Water Vault with the sensor simulator, Zira Card, agronomist approval, the farmer's WhatsApp) belongs there, not on this slide.

---

## Checklist before the talk
1. Add Kulu to the platform as a field for the demo video; the test field (Konya, 32.505 / 37.905) has NDVI of 0.15–0.26 all year, so every season comes out "fallow".
2. The 202 mm on slide 6 (demo field) and 231 → 140 mm (sensor scenario) come from different conditions; make the slide match what the demo video shows.
3. Green API QR pairing (the server reported "notAuthorized").
4. The repository is private: to write "open source", resolve decision 0005 and the private UDS dependency, otherwise delete that line.
5. The Earthdata token (SMAP, GPM, GRACE) expires in about 60 days; before the talk check that the Data Center shows those three as connected.
6. "24 seasons" is the platform's figure and "25 seasons" the length of the record; say which one you mean.
