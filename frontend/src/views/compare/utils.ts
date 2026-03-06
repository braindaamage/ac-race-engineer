/**
 * Format a numeric delta with sign prefix.
 * Returns "N/A" for null/undefined.
 */
export function formatDelta(value: number | null | undefined, precision: number = 2): string {
  if (value == null) return "N/A";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(precision)}`;
}

/**
 * Format lap time in seconds to mm:ss.xxx
 */
export function formatLapTime(seconds: number | null | undefined): string {
  if (seconds == null) return "N/A";
  const mins = Math.floor(seconds / 60);
  const secs = seconds - mins * 60;
  return `${mins}:${secs.toFixed(3).padStart(6, "0")}`;
}

/**
 * Return direction of a delta value.
 */
export function deltaDirection(value: number | null | undefined): "increase" | "decrease" | "unchanged" {
  if (value == null || value === 0) return "unchanged";
  return value > 0 ? "increase" : "decrease";
}

// Metrics where a positive delta means degradation (higher = worse)
const NEGATIVE_IS_GOOD: Set<string> = new Set([
  "lap_time_delta_s",
  "tyre_temp_delta",
  "slip_angle_delta",
  "slip_ratio_delta",
]);

/**
 * Determine if a delta represents an improvement.
 * - lap_time_delta_s: negative = faster = good
 * - peak_lat_g_delta: positive = more grip = good
 * - tyre/slip deltas: negative = generally good (lower temps/angles)
 */
/**
 * Check if a delta value is effectively zero after rounding to display precision.
 */
export function isNearZero(value: number, precision: number = 2): boolean {
  return Math.abs(value) < 0.5 * Math.pow(10, -precision);
}

export function isImprovement(metricKey: string, delta: number): boolean {
  if (NEGATIVE_IS_GOOD.has(metricKey)) {
    return delta < 0;
  }
  // peak_lat_g_delta: positive = more grip = improvement
  return delta > 0;
}
