# 0016: SMAP, GPM IMERG and GRACE through NASA Earthdata

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need an agronomist.

## Decision

With a NASA Earthdata user token on the server (`EARTHDATA_TOKEN`, from the product owner's own
free Earthdata account, with the NSIDC, GES DISC and PO.DAAC applications authorized), three more
sources are connected. They are regional **cross-checks of the model, never inputs to it**, and the
screens say so.

| Source | Product | What is read | Scale |
| --- | --- | --- | --- |
| SMAP | SPL3SMP_E (NSIDC) | Morning and evening surface soil moisture (top 5 cm, m3/m3) of the 9 km EASE-Grid 2.0 cell that holds the field | 9 km, daily; gaps between swaths |
| GPM IMERG | GPM_3IMERGDF (Final), then GPM_3IMERGDL (Late) (GES DISC) | Daily rainfall (mm) of the 0.1 degree cell | about 10 km |
| GRACE / GRACE-FO | JPL mascon CRI grid RL06.3 (PO.DAAC) | Monthly liquid water equivalent thickness anomaly (cm), 2002 to the latest month, and its trend since 2003 | 0.5 degree grid, about 300 km |

- **How a file is read.** The catalogue (CMR) finds the file; the archive answers the token with a
  short-lived signed address; the server reads only the field's pixel from the HDF5 file by HTTP range
  requests (a few kilobytes of a file of many megabytes). The token is sent to NASA hosts only, never
  to the signed storage address, and is masked in any stored error message.
- **Window.** SMAP and IMERG are read for the last 60 days of the field's stored weather record, so
  they line up with the Water Vault and the POWER rainfall. GRACE is read for its whole record.
- **IMERG Final ends in September 2025.** After that the Late run (near real time, less accurate) is
  used. The Planetary Computer copy of IMERG stops in 2021, so Earthdata is the only route.
- **Cross-checks shown.** SMAP: mean morning and evening moisture and a chart. IMERG against POWER:
  the totals over the window and the daily correlation. GRACE: the trend in cm per year.
- **Data Center.** These three show as connected only while the server holds the token; without it
  they say "not connected", never healthy.
- **Stored in** `regional_observations`, alongside the SRTM terrain values.

## Not done, and open

1. **ECOSTRESS is not connected.** Granules exist over the demo field (70 m tiles of evapotranspiration
   and a water stress index), but they are one COG per variable per overpass at irregular times, and
   the model does not use evapotranspiration measured from space. Reading them is a separate piece
   of work.
2. **The token expires** (about 60 days). When it does, the three sources fall back to "not
   connected" with the archive's refusal on the job. Renew it in the Earthdata profile and the server
   `.env`.
3. **Surface versus root zone.** SMAP sees the top 5 cm; the Water Vault models a root zone of up to
   1.8 m. The two are compared as trends (do both dry out and wet up together), not as numbers.
4. **GRACE is far coarser than a field** and says nothing about one parcel's groundwater.
5. **The score of agreement** (correlation, trend) is shown, but no threshold turns it into a warning:
   what counts as a worrying disagreement is the agronomist's call.
