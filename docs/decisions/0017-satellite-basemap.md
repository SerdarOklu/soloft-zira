# 0017: A satellite basemap, with Google as an option

**Status:** Accepted for the demo, 15 November 2026.

## Decision

Every map (drawing a field, a field's page, the overview) now opens on **satellite imagery** with
place names on top, because a farmer or an agronomist recognises a field from above and can draw its
boundary on what is really there. A layer switcher offers the imagery, a plain street map
(OpenStreetMap) and a switch for the place names. A field's map zooms one level closer than before.

- **Default imagery: Esri World Imagery** (Maxar and other providers), with Esri's place-name layer.
  It needs no key and works today. Each map carries the credit Esri asks for. Its native detail ends
  around zoom 18; the map stretches a little beyond that.
- **Google satellite is an option, not the default.** Google's tiles may be used only through its own
  APIs, never by copying tile addresses. The map reads `/api/map-config`; if the server has a
  `GOOGLE_MAPS_API_KEY`, it opens a session with the **Map Tiles API** and adds a "Google Satellite"
  choice to the switcher. Without a key nothing changes. Earth Engine is not a basemap and is not used.
- **Getting a key.** In Google Cloud: create a project, enable billing and the *Map Tiles API*, create
  an API key, and restrict it by HTTP referrer to `https://zira.soloftindustries.com/*` and to the Map
  Tiles API only. The key reaches the browser by design, so the restriction is what protects it. Put
  it in the server `.env` as `GOOGLE_MAPS_API_KEY` and restart the frontend; no rebuild is needed.

## Open

1. **Google's attribution.** The map shows "Imagery © Google". Google's terms also ask for the
   per-viewport copyright text from its viewport endpoint, which is not fetched yet. Do that before a
   public launch with the Google layer on.
2. **Google is billed per tile** after a free monthly amount; a busy map costs money. Esri's imagery
   is free for this use but is subject to Esri's terms (attribution, no bulk download).
3. **The imagery is not dated for the field.** It can be years old and may not match the season; it
   is a drawing aid, not evidence of what grew.
