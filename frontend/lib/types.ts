/** Shapes the backend returns (backend/app/schemas/fields.py). */

export type WaterRegime = 'rainfed' | 'irrigated';

export interface GeoJsonPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface FieldOut {
  id: string;
  code: string;
  name: string;
  region: string | null;
  water_regime: WaterRegime | null;
  soil_texture: string | null;
  area_ha: number | null;
  elevation_m: number | null;
  centroid: { lat: number; lon: number } | null;
  geometry: GeoJsonPolygon | null;
  weather_days: number;
  created_at: string;
}

export type JobStatus = 'queued' | 'running' | 'done' | 'failed';

export interface JobOut {
  id: string;
  field_id: string | null;
  field_code: string | null;
  field_name: string | null;
  source: string;
  status: JobStatus;
  date_from: string | null;
  date_to: string | null;
  rows_written: number | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface YearStat {
  year: number;
  days: number;
  precipitation_mm: number | null;
  temperature_avg: number | null;
  temperature_min: number | null;
  temperature_max: number | null;
}

export interface DailyRow {
  date: string;
  precipitation_mm: number | null;
  temperature_avg: number | null;
  temperature_max: number | null;
  temperature_min: number | null;
  humidity: number | null;
  wind_speed: number | null;
  solar_radiation: number | null;
  surface_pressure: number | null;
  quality_flag: string | null;
}

export interface WeatherSummary {
  days: number;
  first_date: string | null;
  last_date: string | null;
  last_fetched_at: string | null;
  units: Record<string, string>;
  wind_height_m: number | null;
  years: YearStat[];
  recent: DailyRow[];
  latest_job: JobOut | null;
}

export interface JobCounts {
  queued: number;
  running: number;
  done: number;
  failed: number;
}

export type SourceStatus = 'ok' | 'error' | 'never_fetched' | 'not_connected';

export interface SourceOut {
  key: string;
  name: string;
  role: string;
  access: string;
  resolution: string;
  priority: string;
  scale_warning: string;
  collection_id: string | null;
  connected: boolean;
  status: SourceStatus;
  last_success_at: string | null;
  observations: number;
  jobs: JobCounts;
}

export interface Marker {
  id: string;
  code: string;
  name: string;
  lat: number;
  lon: number;
  area_ha: number | null;
  has_weather: boolean;
}

export interface DashboardSummary {
  field_count: number;
  fields_with_weather: number;
  fields_missing_weather: { id: string; code: string; name: string }[];
  jobs: JobCounts;
  last_weather_update: string | null;
  markers: Marker[];
}

export interface SoilOption {
  key: string;
  name_tr: string;
  taw_mm_per_m: [number, number];
}
