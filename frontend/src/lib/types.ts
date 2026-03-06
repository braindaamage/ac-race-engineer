export interface SessionRecord {
  session_id: string;
  car: string;
  track: string;
  session_date: string;
  lap_count: number;
  best_lap_time: number | null;
  state: string;
  session_type: string | null;
  csv_path: string | null;
  meta_path: string | null;
}

export interface SessionListResponse {
  sessions: SessionRecord[];
}

export interface ProcessResponse {
  job_id: string;
  session_id: string;
}

export interface SyncResult {
  discovered: number;
  already_known: number;
  incomplete: number;
}

export type UISessionState = "new" | "processing" | "ready" | "engineered" | "failed";

export interface ProcessingJobInfo {
  jobId: string;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Analysis types
// ---------------------------------------------------------------------------

export interface LapSummary {
  lap_number: number;
  classification: "flying" | "outlap" | "inlap" | "invalid" | "incomplete";
  is_invalid: boolean;
  lap_time_s: number;
  tyre_temps_avg: Record<string, number>;
  peak_lat_g: number;
  peak_lon_g: number;
  full_throttle_pct: number;
  braking_pct: number;
  max_speed: number;
  sector_times_s: number[] | null;
}

export interface LapListResponse {
  session_id: string;
  lap_count: number;
  laps: LapSummary[];
}

export interface LapTelemetryResponse {
  session_id: string;
  lap_number: number;
  sample_count: number;
  channels: {
    normalized_position: number[];
    throttle: number[];
    brake: number[];
    steering: number[];
    speed_kmh: number[];
    gear: number[];
  };
}

export interface WheelTempZones {
  core: number;
  inner: number;
  mid: number;
  outer: number;
}

export interface TimingMetrics {
  lap_time_s: number;
  sector_times_s: number[] | null;
}

export interface SpeedMetrics {
  max_speed: number;
  min_speed: number;
  avg_speed: number;
}

export interface DriverInputMetrics {
  full_throttle_pct: number;
  partial_throttle_pct: number;
  off_throttle_pct: number;
  braking_pct: number;
  avg_steering_angle: number;
  gear_distribution: Record<number, number>;
}

export interface TyreMetrics {
  temps_avg: Record<string, WheelTempZones>;
  temps_peak: Record<string, WheelTempZones>;
  pressure_avg: Record<string, number>;
  temp_spread: Record<string, number>;
  front_rear_balance: number;
  wear_rate: Record<string, number> | null;
}

export interface GripMetrics {
  slip_angle_avg: Record<string, number>;
  slip_angle_peak: Record<string, number>;
  slip_ratio_avg: Record<string, number>;
  slip_ratio_peak: Record<string, number>;
  peak_lat_g: number;
  peak_lon_g: number;
}

export interface SuspensionMetrics {
  travel_avg: Record<string, number>;
  travel_peak: Record<string, number>;
  travel_range: Record<string, number>;
}

export interface FuelMetrics {
  fuel_start: number;
  fuel_end: number;
  consumption: number;
}

export interface LapMetrics {
  timing: TimingMetrics;
  tyres: TyreMetrics;
  grip: GripMetrics;
  driver_inputs: DriverInputMetrics;
  speed: SpeedMetrics;
  fuel: FuelMetrics | null;
  suspension: SuspensionMetrics;
}

export interface CornerPerformance {
  entry_speed_kmh: number;
  apex_speed_kmh: number;
  exit_speed_kmh: number;
  duration_s: number;
}

export interface CornerGrip {
  peak_lat_g: number;
  avg_lat_g: number;
  understeer_ratio: number | null;
}

export interface CornerTechnique {
  brake_point_norm: number | null;
  throttle_on_norm: number | null;
  trail_braking_intensity: number;
}

export interface CornerMetrics {
  corner_number: number;
  performance: CornerPerformance;
  grip: CornerGrip;
  technique: CornerTechnique;
}

export interface LapDetailResponse {
  session_id: string;
  lap_number: number;
  classification: string;
  is_invalid: boolean;
  metrics: LapMetrics;
  corners: CornerMetrics[];
}
