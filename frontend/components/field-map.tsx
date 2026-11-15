'use client';

import 'leaflet/dist/leaflet.css';

import type * as Leaflet from 'leaflet';
import { useEffect, useRef, useState } from 'react';

import type { LonLat } from '@/lib/geometry';
import type { GeoJsonPolygon } from '@/lib/types';

// Basemap tiles come from OpenStreetMap, which asks for this credit on every map.
const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '© OpenStreetMap contributors';
// Where the map opens before the user has chosen a place. Not a field coordinate.
const OPENING_VIEW: [number, number] = [39, 35];
const OPENING_ZOOM = 6;

export interface MapMarker {
  id: string;
  name: string;
  lat: number;
  lon: number;
  filled: boolean;
}

interface Props {
  /** `draw`: click to add corners. `view`: show one polygon or a set of markers. */
  mode: 'draw' | 'view';
  ariaLabel: string;
  /** Draw mode: the corners so far, [longitude, latitude]. */
  corners?: LonLat[];
  onAddCorner?: (lon: number, lat: number) => void;
  /** Draw mode: move the map here when `nonce` changes. */
  flyTo?: { lat: number; lon: number; nonce: number } | null;
  /** View mode. */
  geometry?: GeoJsonPolygon | null;
  markers?: MapMarker[];
  onSelectMarker?: (id: string) => void;
  className?: string;
}

interface Ready {
  lib: typeof Leaflet;
  map: Leaflet.Map;
  layers: Leaflet.LayerGroup;
  /** The product accent, read from the theme at run time. No colour lives in this file. */
  accent: string;
}

export function FieldMap({
  mode,
  ariaLabel,
  corners = [],
  onAddCorner,
  flyTo = null,
  geometry = null,
  markers = [],
  onSelectMarker,
  className,
}: Props) {
  const container = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState<Ready | null>(null);
  const onAdd = useRef(onAddCorner);
  const onSelect = useRef(onSelectMarker);
  useEffect(() => {
    onAdd.current = onAddCorner;
    onSelect.current = onSelectMarker;
  });

  // Leaflet needs the browser, so it is loaded here and not at import time.
  useEffect(() => {
    let cancelled = false;
    let instance: Leaflet.Map | null = null;
    void (async () => {
      const loaded = (await import('leaflet')) as typeof Leaflet & { default?: typeof Leaflet };
      const lib = loaded.default ?? loaded;
      if (cancelled || !container.current) return;
      const map = lib.map(container.current, {
        center: OPENING_VIEW,
        zoom: OPENING_ZOOM,
        doubleClickZoom: mode !== 'draw',
      });
      instance = map;
      lib.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(map);
      const layers = lib.layerGroup().addTo(map);
      if (mode === 'draw') {
        map.on('click', (event: Leaflet.LeafletMouseEvent) =>
          onAdd.current?.(event.latlng.lng, event.latlng.lat),
        );
      }
      const accent =
        getComputedStyle(document.documentElement).getPropertyValue('--uds-primary').trim() ||
        'currentColor';
      setReady({ lib, map, layers, accent });
    })();
    return () => {
      cancelled = true;
      instance?.remove();
      setReady(null);
    };
  }, [mode]);

  // Draw mode: the corners so far.
  useEffect(() => {
    if (!ready || mode !== 'draw') return;
    const { lib, layers, accent } = ready;
    layers.clearLayers();
    const points = corners.map(([lon, lat]) => [lat, lon] as [number, number]);
    if (points.length >= 3) {
      lib.polygon(points, { color: accent, weight: 2, fillOpacity: 0.2 }).addTo(layers);
    } else if (points.length === 2) {
      lib.polyline(points, { color: accent, weight: 2 }).addTo(layers);
    }
    points.forEach((point) =>
      lib.circleMarker(point, { radius: 5, color: accent, weight: 2, fillOpacity: 1 }).addTo(layers),
    );
  }, [ready, mode, corners]);

  // Draw mode: jump to a typed position.
  useEffect(() => {
    if (!ready || !flyTo) return;
    ready.map.flyTo([flyTo.lat, flyTo.lon], 15);
  }, [ready, flyTo]);

  // View mode: one field boundary.
  useEffect(() => {
    if (!ready || mode !== 'view' || !geometry) return;
    const { lib, map, layers, accent } = ready;
    layers.clearLayers();
    const shape = lib
      .geoJSON(geometry as GeoJSON.Polygon, { style: { color: accent, weight: 2, fillOpacity: 0.2 } })
      .addTo(layers);
    map.fitBounds(shape.getBounds(), { padding: [24, 24], maxZoom: 17 });
  }, [ready, mode, geometry]);

  // View mode: field locations.
  useEffect(() => {
    if (!ready || mode !== 'view' || geometry) return;
    const { lib, map, layers, accent } = ready;
    layers.clearLayers();
    markers.forEach((marker) => {
      const dot = lib
        .circleMarker([marker.lat, marker.lon], {
          radius: 7,
          color: accent,
          weight: 2,
          fillOpacity: marker.filled ? 0.9 : 0.2,
        })
        .addTo(layers);
      // A field name is typed by a user: it goes in as text, never as HTML.
      const label = document.createElement('span');
      label.textContent = marker.name;
      dot.bindTooltip(label);
      dot.on('click', () => onSelect.current?.(marker.id));
    });
    if (markers.length > 0) {
      const bounds = lib.latLngBounds(markers.map((marker) => [marker.lat, marker.lon]));
      map.fitBounds(bounds, { padding: [32, 32], maxZoom: markers.length === 1 ? 12 : 10 });
    }
  }, [ready, mode, geometry, markers]);

  return (
    <div
      ref={container}
      role="application"
      aria-label={ariaLabel}
      className={['zira-map', className].filter(Boolean).join(' ')}
    />
  );
}
