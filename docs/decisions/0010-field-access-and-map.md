# 0010: Who sees which field, and the field map

**Status:** Accepted, 15 November 2026

## Decision

- **Visibility.** An admin and an agronomist see every field. A cooperative user sees the
  fields of their own organization, or only the ones they created when they belong to none.
  A field outside that scope answers 404, not 403, so its existence is not revealed. Only an
  admin deletes a field.
- **Geometry.** A field is a single closed polygon (no holes), sent as GeoJSON. PostGIS
  checks that it is valid, then derives the centroid and the area; neither is typed in. NASA
  data is always fetched for the stored centroid, so no coordinate lives in code.
- **Soil.** The soil texture is a key of `config/soils.yaml`. The profile stores the middle of
  the FAO-56 range as the starting value, marked as not calibrated, until a sensor
  calibrates it.
- **Map.** Leaflet with OpenStreetMap tiles. The drawing tool is ours: click to add corners,
  undo, clear. In dark mode the tiles are inverted by CSS. The accent is read from the
  theme at run time, so no colour literal enters the code.
- **Browser access to the API.** The browser reaches the backend only through
  `/api/backend/*`, which adds the token from the httpOnly cookie. Only `fields/...` is
  forwarded, every path segment must be a plain identifier, and a POST must be JSON.

## Why

The PDT describes roles but not field ownership. Scoping by organization is the smallest rule
that keeps one cooperative's fields from another's and still lets staff see all of them. It
may change when the cooperative system arrives (phase 7).

## Consequences

- Each map view requests tiles from `tile.openstreetmap.org`: a third-party request, as with
  the fonts (0009). OpenStreetMap's usage policy allows light use; a tile service of our own
  is needed before heavy use.
- The basemap is a street map, not imagery. Satellite imagery would help to draw field
  boundaries, but a source with a suitable licence is not chosen yet.
- A polygon with a hole, or a field made of several parts, is not supported yet.
