/**
 * Format a lap time in seconds to M:SS.mmm format.
 */
export function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const whole = Math.floor(secs);
  const ms = Math.round((secs - whole) * 1000);
  return `${mins}:${String(whole).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
}

/**
 * Format speed in km/h with one decimal place.
 */
export function formatSpeed(kmh: number): string {
  return `${kmh.toFixed(1)} km/h`;
}

/**
 * Format a time delta in seconds with sign and 3 decimal places.
 * Positive = slower, negative = faster.
 */
export function formatDelta(seconds: number): string {
  const sign = seconds > 0 ? "+" : "";
  return `${sign}${seconds.toFixed(3)}`;
}

/**
 * Format temperature in degrees Celsius.
 */
export function formatTemperature(celsius: number): string {
  return `${celsius.toFixed(0)}\u00B0C`;
}

/**
 * Format a percentage value with one decimal place.
 */
export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}
