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

export interface CropOption {
  key: string;
  name_tr: string;
  season_type: string | null;
  root_depth_m: number;
  season_ready: boolean;
}

export interface WaterVaultDay {
  date: string;
  precipitation_mm: number | null;
  et0_mm: number | null;
  storage_mm: number;
}

export interface WaterVault {
  field_id: string;
  crop: CropOption & { season_blocker: string | null };
  date: string;
  date_is_default: boolean;
  decision: {
    storage_mm: number;
    low_mm: number;
    high_mm: number;
    taw_mm: number;
    taw_low_mm: number;
    taw_high_mm: number;
    fill_fraction: number;
  };
  window: { start: string; end: string; days: number; missing_days: number };
  parameters: {
    fallow_efficiency: number;
    initial_storage_frac: number;
    spinup_days: number;
    uncertainty_delta: number;
  };
  needs_signoff: string[];
  assumptions: string[];
  soil_calibrated: boolean;
  et0_days: number;
  et0_blocker: string | null;
  daily: WaterVaultDay[];
}

export interface RotationSeason {
  year: number;
  planned: string | null;
  crop: string | null;
  valid: boolean;
  sufficient: boolean;
  ratio: number | null;
  deficit_mm: number;
  stress_days: number;
  storage_at_decision_mm: number | null;
}

export interface RotationMetrics {
  sown: number;
  valid: number;
  sufficient: number;
  fallow: number;
  share: number | null;
  share_low: number | null;
  share_high: number | null;
  sufficient_low: number;
  sufficient_high: number;
  stress_days_mean: number | null;
  deficit_mean_mm: number | null;
  irrigation_need_mean_mm: number | null;
}

export interface RotationDifference {
  share_points: number | null;
  stress_days_mean: number | null;
  deficit_mean_mm: number | null;
  irrigation_need_mean_mm: number | null;
  sufficient: number;
}

export interface RotationStrategy {
  key: 'A' | 'B' | 'C';
  crops: string[];
  metrics: RotationMetrics;
  difference: RotationDifference | null;
  seasons: RotationSeason[];
}

export interface RotationComparison {
  field_id: string;
  model_version: string;
  provisional: boolean;
  provisional_sources: string[];
  rotation: (string | null)[];
  first_day: string;
  last_day: string;
  seasons: number;
  reference: {
    crop: string;
    root_depth_m: number;
    taw_mm: number;
    taw_low_mm: number;
    taw_high_mm: number;
  };
  flex_threshold_mm: number;
  sufficiency_ratio: number;
  irrigation_efficiency: number;
  needs_signoff: string[];
  assumptions: string[];
  strategies: RotationStrategy[];
}

export type DraftStatus = 'pending' | 'approved' | 'sent' | 'rejected' | 'failed';

export interface MessageDraft {
  id: string;
  field_id: string;
  field_name: string;
  event_type: string;
  event_date: string;
  locale: string;
  body: string;
  payload: Record<string, unknown>;
  status: DraftStatus;
  recipient_hint: string | null;
  has_recipient: boolean;
  error: string | null;
  created_at: string;
  decided_at: string | null;
  sent_at: string | null;
}

export interface GatewayStatus {
  configured: boolean;
  provider: string;
}

export type CycleState = 'cropped' | 'fallow' | 'unknown';

export interface FieldMemorySeason {
  season: string;
  harvest_year: number;
  detected_state: CycleState;
  peak_ndvi: number | null;
  peak_date: string | null;
  good_observations: number;
  total_observations: number;
  confidence: number | null;
  confidence_level: 'high' | 'medium' | 'low' | null;
  confirmed_state: CycleState | null;
  confirmed_by: 'user' | 'agronomist' | null;
  confirmed_at: string | null;
}

export interface FieldMemory {
  field_id: string;
  history_years: number;
  threshold: number;
  provisional: boolean;
  coverage: { observations: number; good: number; first_date: string | null; last_date: string | null };
  seasons: FieldMemorySeason[];
  series: { date: string; ndvi: number | null; valid_pixels: number; flag: string | null }[];
  latest_job: JobOut | null;
  confirmed_count: number;
}
