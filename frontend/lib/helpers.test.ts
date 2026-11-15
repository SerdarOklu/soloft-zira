import { describe, expect, it } from 'vitest';

import { formatDate, formatDateTime, formatNumber, MISSING } from './format';
import { MIN_CORNERS, parseLatLon, toGeoJsonPolygon, type LonLat } from './geometry';
import { backendPath } from './proxy';

describe('proxy path (the browser may only reach the fields API)', () => {
  it('maps the fields endpoints to the backend', () => {
    expect(backendPath(['fields'])).toBe('/api/v1/fields');
    expect(backendPath(['fields', '5f0e', 'weather', 'fetch'])).toBe(
      '/api/v1/fields/5f0e/weather/fetch',
    );
  });

  it('refuses every other part of the API', () => {
    expect(backendPath(['auth', 'login'])).toBeNull();
    expect(backendPath(['data-center', 'jobs'])).toBeNull();
    expect(backendPath([])).toBeNull();
  });

  it.each([['..'], ['.'], ['a/b'], ['a%2Fb'], ['a?x=1'], ['a b'], [''], ['%2e%2e']])(
    'refuses the unsafe segment %j',
    (segment) => {
      expect(backendPath(['fields', segment])).toBeNull();
    },
  );
});

describe('field geometry', () => {
  const corners: LonLat[] = [
    [32.5, 37.9],
    [32.51, 37.9],
    [32.51, 37.91],
  ];

  it('closes the ring and keeps [longitude, latitude] order', () => {
    expect(toGeoJsonPolygon(corners)).toEqual({
      type: 'Polygon',
      coordinates: [[...corners, corners[0]]],
    });
  });

  it('needs at least three corners', () => {
    expect(MIN_CORNERS).toBe(3);
    expect(toGeoJsonPolygon(corners.slice(0, 2))).toBeNull();
    expect(toGeoJsonPolygon([])).toBeNull();
  });

  it('does not change the corners it was given', () => {
    const copy = structuredClone(corners);
    toGeoJsonPolygon(corners);
    expect(corners).toEqual(copy);
  });

  it('reads "latitude, longitude" in the ways people type it', () => {
    expect(parseLatLon('37.90, 32.50')).toEqual({ lat: 37.9, lon: 32.5 });
    expect(parseLatLon('37.9 32.5')).toEqual({ lat: 37.9, lon: 32.5 });
    expect(parseLatLon('-33.9; 151.2')).toEqual({ lat: -33.9, lon: 151.2 });
  });

  it.each(['', '37.9', '37.9, 32.5, 10', 'abc, def', '95, 10', '10, 200'])(
    'rejects %j as a position',
    (text) => {
      expect(parseLatLon(text)).toBeNull();
    },
  );
});

describe('formatting', () => {
  it('shows a dash for a missing number or date', () => {
    expect(formatNumber(null, 'tr')).toBe(MISSING);
    expect(formatNumber(undefined, 'en')).toBe(MISSING);
    expect(formatDate(null, 'tr')).toBe(MISSING);
    expect(formatDateTime('', 'tr')).toBe(MISSING);
  });

  it('follows the language for the decimal separator', () => {
    expect(formatNumber(1215.57, 'en', 1)).toBe('1,215.6');
    expect(formatNumber(1215.57, 'tr', 1)).toBe('1.215,6');
  });

  it('keeps a calendar date on its own day in every time zone', () => {
    expect(formatDate('2024-01-31', 'en')).toBe('Jan 31, 2024');
    expect(formatDate('2024-01-31T23:59:00+00:00', 'en')).toBe('Jan 31, 2024');
  });

  it('shows timestamps in the time zone of the farms', () => {
    // 21:30 UTC is already the next morning in Türkiye (UTC+3).
    expect(formatDateTime('2024-01-31T21:30:00+00:00', 'en')).toContain('Feb 1, 2024');
  });
});
