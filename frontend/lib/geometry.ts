import type { GeoJsonPolygon } from './types';

/** [longitude, latitude], the order GeoJSON uses. */
export type LonLat = [number, number];

export const MIN_CORNERS = 3;

/** A closed GeoJSON Polygon from the corners the user clicked, or null with too few. */
export function toGeoJsonPolygon(corners: LonLat[]): GeoJsonPolygon | null {
  if (corners.length < MIN_CORNERS) return null;
  return { type: 'Polygon', coordinates: [[...corners, corners[0]]] };
}

/** Parses "37.90, 32.50" (latitude, longitude). Null when it is not a valid position. */
export function parseLatLon(text: string): { lat: number; lon: number } | null {
  const parts = text.split(/[,;\s]+/).filter(Boolean);
  if (parts.length !== 2) return null;
  const [lat, lon] = parts.map((part) => Number(part.replace(',', '.')));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  return { lat, lon };
}
