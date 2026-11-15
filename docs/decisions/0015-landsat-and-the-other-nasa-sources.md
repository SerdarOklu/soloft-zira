# 0015: Landsat and SRTM go live; what stays out and why

**Status:** Accepted for the demo, 15 November 2026. Items marked **Open** need a decision or access.

## Decision

- **Landsat 8 and 9 are connected**, without Earth Engine, the same way MODIS is (decision 0013): the
  NASA/USGS Collection 2 Level-2 surface-reflectance scenes are read from the cloud-optimised
  GeoTIFFs of the public Microsoft Planetary Computer STAC catalogue. For each scene (cloud cover
  under 70 %) the job reads the red, near-infrared and quality bands inside the field polygon, keeps
  the pixels the quality band marks clear (no fill, cloud, cirrus, shadow or snow), converts to
  surface reflectance (`DN * 0.0000275 - 0.2`) and stores the mean and median NDVI. At 30 m a field
  of a few hectares holds dozens of pixels, where MODIS holds a handful.
- **Field Memory uses Landsat when it can.** It calls the history from Landsat if at least six of the
  ten seasons can be called from it (four clear scenes in the March to September window), otherwise
  from MODIS; the screen says which, and a person can choose either. One click on "Fetch" queues
  MODIS and both Landsat platforms, one job each. The NDVI threshold is the same provisional 0.40
  (decision 0013); a 30 m pixel is purer than a 250 m one, so its best threshold is probably higher,
  which only a calibration with fields of known history can settle.
- **SRTM is connected** through NASADEM, NASA's reprocessing of the SRTM data (30 m), read from the
  same open catalogue. For the pixels inside the polygon the job stores the mean, lowest and highest
  elevation and the mean slope (`regional_observations`, migration 0004). A missing field elevation
  is filled from it; an elevation that POWER already gave is kept, so no stored result changes.
- **Landsat 9** has scenes only from 2022; for earlier years it returns nothing, which is not an error.

## What is still not connected

| Source | State | Why |
| --- | --- | --- |
| GPM IMERG | Not a separate source | NASA POWER's precipitation already uses IMERG. The Planetary Computer copy (`gpm-imerg-hhr`) ends in May 2021 and the recent files need an Earthdata login, so no verified route exists for a second, recent series. |
| SMAP | Not connected | The science files need an Earthdata login. GIBS offers browse imagery that can be decoded through published colour maps (the browser prototype does this), but the colour-map and date-coverage details could not be verified from the server in the time available, and the result would be a trend check, not a measurement. |
| GRACE / GRACE-FO | Not connected | Same reason as SMAP. |
| ECOSTRESS | Not connected | Needs an Earthdata login (LP DAAC); the current model does not use it. |

**Open.** Connecting SMAP and GRACE needs one of: (a) a free NASA Earthdata account, whose
credentials would go in the server environment, to read the science files; or (b) a verified GIBS
decoding path, labelled as a browse-image trend check. The Data Center keeps showing them as
"not connected", never as healthy.
