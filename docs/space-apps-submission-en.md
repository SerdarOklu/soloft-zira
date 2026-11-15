# NASA Space Apps 2026: submission form text (English)

Copy each block into the matching field. Every URL must be the full address and open without a login. Items in [brackets] are for you to fill in.

---

## Project Name

Zira: Which Crop Rotation Can This Field's Water Carry?

## Summary (about 170 words)

Zira is a decision-support platform for dryland farmers, agronomists and cooperatives. On sowing-decision day it shows how many millimetres of plant-available water a field's soil holds, with an uncertainty range, and compares three rotations (current, water-triggered flexible, legume-based) over 24 seasons of NASA data. It reads each field's cropped-or-fallow history from Landsat 8/9 and MODIS NDVI, runs a daily FAO-56 water balance on NASA POWER weather, and cross-checks the model with SMAP, GPM IMERG and GRACE-FO. A soil-moisture sensor, simulated in this version, can correct the model. The result becomes a printable Zira Card and a short WhatsApp message that reaches the farmer only after an agronomist approves it. Zira addresses Field Shift by replacing calendar-based planning (such as "wheat, then fallow") with water-based evidence in the Konya Closed Basin, Türkiye, where groundwater falls and over 740 sinkholes are recorded. Zira does not decide; it helps the farmer and agronomist decide with evidence.

## Project Demonstration *

[Public link to the demo.] **Rule from the form: a slide deck of at most 7 slides, or a video of 30 seconds or less.** If your separate video is longer than 30 seconds, it does not meet this rule; then use the 7-slide deck as the demo link and put the longer video under "Project". Upload the deck as a PDF to Google Drive/GitHub with "anyone with the link" access.

## Project (public link) *

https://zira.soloftindustries.com

If the repository is public, you can add it as the second link: [https://github.com/... full URL]. The live site must open without a password or registration for a Global Award; check that a visitor without an account can see something meaningful (a public landing page or demo access). If the site needs a login, put a public page (README, repository or video) here.

## Project Details

**What it does.** Zira answers one question: "How much usable water does this field hold on sowing day, and which rotation does that water carry?" An agronomist draws a field on a map. Zira then (1) fetches 25 years of NASA POWER weather, (2) reads ten seasons of NDVI from inside the field polygon, from Landsat 8/9 at 30 m with MODIS as fallback, and calls each season cropped, fallow or unknown for the agronomist to confirm, (3) runs a daily FAO-56 water balance (Penman–Monteith ET0, crop coefficients, root-zone storage) with a low–mid–high range, and (4) replays three rotations on identical weather, soil and starting water. A season counts as "water was enough" if actual divided by potential evapotranspiration is at least 0.70.

**NASA data.** POWER (weather), Landsat 8/9 and MODIS MOD13Q1/MYD13Q1 (field history), NASADEM (elevation and slope), SMAP, GPM IMERG and GRACE-FO (regional cross-checks, never inputs), GIBS (imagery).

**Impact.** Free data, a field-level comparison, a plain message to the farmer, and cooperative-scale management. Roles are enforced on the server, and no message leaves without agronomist approval.

**Tools.** Python (FastAPI, SQLAlchemy, Celery, rasterio, h5py), PostgreSQL/PostGIS, Redis, Next.js/React/TypeScript, Leaflet, Docker, Green API (WhatsApp). Turkish and English interface.

**Honest limits.** Crop stage lengths and thresholds are provisional until an agronomist approves them; sensor data are simulated; Landsat and MODIS separate cropped from fallow but not crop type. Every figure shows its uncertainty.

## Use of Super Intelligence (SI) *

Select: **code and data**, and **text** if the form has such an option. Select "images and videos" and "audio" only if SI tools were used for them (for example an AI voice-over or AI-made graphics in the video); otherwise do not select them. Do not select "I did not use SI".

Acknowledge it where the form says it must be visible. A ready sentence for the README, the slides and the repository description:

> Zira was built with the help of an SI assistant (Claude, by Anthropic): it helped write the code, the interface text, the message-draft templates and the presentation text. The team reviewed and tested the result. [Add other tools you used.] No SI-generated images or audio are used, and no NASA branding is used or modified.

For metadata: the git history already carries `Co-Authored-By: Claude` lines in the commit messages of the SI-assisted commits. Keep them, and add the sentence above to `README.md`.

## NASA Data * (Link Text → Link URL)

| Link Text | Link URL |
|---|---|
| NASA POWER Project (Daily API) | https://power.larc.nasa.gov/ |
| MODIS/Terra Vegetation Indices 16-Day 250m (MOD13Q1 V061) | https://doi.org/10.5067/MODIS/MOD13Q1.061 |
| MODIS/Aqua Vegetation Indices 16-Day 250m (MYD13Q1 V061) | https://doi.org/10.5067/MODIS/MYD13Q1.061 |
| Landsat 8–9 OLI/TIRS Collection 2 Level-2 (NASA/USGS) | https://doi.org/10.5066/P9OGBGM6 |
| NASADEM Merged DEM Global 1 arc second (SRTM reprocessing) | https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 |
| SMAP Enhanced L3 Daily 9 km Soil Moisture (SPL3SMP_E), NSIDC DAAC | https://nsidc.org/data/spl3smp_e |
| GPM IMERG Final Precipitation, Daily (GES DISC) | https://gpm.nasa.gov/data/imerg |
| GRACE and GRACE-FO JPL Mascon RL06.3, PO.DAAC | https://podaac.jpl.nasa.gov/GRACE-FO |
| NASA GIBS (Global Imagery Browse Services) | https://earthdata.nasa.gov/gibs |
| NASA Earthdata (login and access) | https://www.earthdata.nasa.gov/ |
| NASA Common Metadata Repository (CMR) | https://cmr.earthdata.nasa.gov/search |

## Space Agency Partner & Other Data (Link Text → Link URL)

| Link Text | Link URL |
|---|---|
| FAO Irrigation and Drainage Paper 56, Crop evapotranspiration (Allen et al. 1998) | https://www.fao.org/4/x0490e/x0490e00.htm |
| FAO Irrigation and Drainage Paper 33, Yield response to water (Doorenbos and Kassam 1979) | https://www.fao.org/4/i2800e/i2800e.pdf |
| Microsoft Planetary Computer open STAC catalogue (hosts Landsat, MODIS, NASADEM copies) | https://planetarycomputer.microsoft.com/ |
| Khorrami, Arık and Gündüz (2021), sinkholes and groundwater, GIScience & Remote Sensing | https://doi.org/10.1080/15481603.2021.2000349 |
| NTV/IHA (17 Aug 2026), Konya sinkhole count above 740 | https://www.ntv.com.tr/yerel-haberler/galerikonya-ovasinda-alarm-sayi-740i-asti-1737722 |
| Esri World Imagery (map basemap in the field editor) | https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9 |
| Leaflet (open-source map library) | https://leafletjs.com/ |
| FastAPI | https://fastapi.tiangolo.com/ |
| Next.js | https://nextjs.org/ |
| PostGIS / PostgreSQL | https://postgis.net/ |
| Celery | https://docs.celeryq.dev/ |
| rasterio | https://rasterio.readthedocs.io/ |
| h5py | https://www.h5py.org/ |
| Green API (WhatsApp messaging) | https://green-api.com/en/ |
| Soloft UDS design system (own work, private repository) | [add the link if public; otherwise remove this row] |

## Project Submission Verification

- **Agree to Terms and Conditions:** tick it after reading the Project Submission Guide.
- **Confirm All Work is Original:** tick it only when every external resource (code, text, images, fonts, map tiles) is in the two tables above. Before you tick it, check: the self-hosted fonts (decision 0009) and any logo or image in the demo deck and video; add each to "Other Data". Do not use NASA logos or mission patches anywhere.

---

## Before you submit

1. The video limit is 30 seconds. If yours is longer, the deck is the demo.
2. Every link must open in a private browser window with no login.
3. The repository is private today. A private repository does not meet "publicly accessible"; make it public (resolve decision 0005 and the private UDS dependency) or use another public link.
4. I could not open the data-set pages from here. Check each NASA link above in a browser; fix any that moved (the SMAP, IMERG, GRACE-FO and GIBS pages are the ones I am least sure of).
5. Add the SI sentence to `README.md` and the first slide notes or last slide.
