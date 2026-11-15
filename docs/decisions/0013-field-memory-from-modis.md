# 0013: Field Memory from MODIS, without Earth Engine

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need an agronomist.

## Decision

Phase 5 was planned on Google Earth Engine (Landsat 8 and 9, MODIS). Earth Engine needs a Google
Cloud project, Earth Engine registration and a service account, none of which exist. To still give
the product its history of cropped and fallow seasons, Field Memory reads NASA's **MODIS NDVI**
(MOD13Q1 Terra and MYD13Q1 Aqua, version 061, 250 m, 16-day composites; together about one
sample every eight days) from the cloud-optimised GeoTIFFs of the **public Microsoft Planetary
Computer STAC catalogue**. No account or key is needed; the server reads the files directly.
(NASA's ORNL DAAC MODIS web service, the first choice, did not answer from the server.)

- **Polygon statistics.** For each composite the job takes the pixels inside the field polygon,
  keeps the ones whose pixel reliability is 0 (good) or 1 (marginal), and stores their mean and
  median NDVI, the count, the share left out, and a quality flag (ok, partial, cloudy). A field
  smaller than a pixel still reads the pixel it touches.
- **The call.** A season is named by its harvest year and covers 1 March to 30 September, which
  holds the peak of winter cereals (April to June) and of spring crops (July to August). The field is
  *cropped* if the highest NDVI of the window reaches the threshold, *fallow* if not, and *unknown*
  with fewer than five clear composites. Confidence is the margin from the threshold (full at 0.2
  NDVI) times how many composites were clear (full at 13).
- **A person confirms.** Detections are computed from the stored NDVI and are never final. A
  user or an agronomist confirms or changes each season; the result is stored in `crop_cycles` with
  who confirmed it. Strategy A of the rotation comparison can then use this confirmed history
  (`rotation=history`), as the PDT intends.
- **Data Center.** MODIS now counts as connected and shows its jobs and image counts. Landsat 8
  and 9, GPM IMERG, SMAP, GRACE and ECOSTRESS stay "not connected": they need Earth Engine or
  access that is not set up. SRTM stays unconnected (elevation comes from POWER).

## Provisional and open

1. **The NDVI threshold is 0.40**, a starting value in `config/rotation_demo.yaml`.
   `parameters.yaml` keeps `field_memory.ndvi_cropped_threshold` unset because no source gives a
   value. It must be calibrated with fields of known history in Konya.
2. **Cropped or fallow only.** The method does not know the crop species, nor winter from summer
   crops, so a confirmed history becomes the main winter crop in strategy A. Crop type has to be
   entered by a person.
3. **250 m is coarse.** One pixel is about 6 ha, so a small parcel mixes in its neighbours. Landsat
   at 30 m is the better source and needs Earth Engine.
4. **Cloud, snow and gaps** leave seasons low-confidence or unknown; the screen says how many.
5. **Dependency.** The job reads from a Microsoft-hosted catalogue. If it is unavailable the fetch
   fails with a reason on the job; already stored NDVI keeps working.
