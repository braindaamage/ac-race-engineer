/**
 * Format a token count using compact notation.
 *
 * - 0–999: raw number ("0", "42", "999")
 * - 1,000–999,999: one decimal + "K" ("1.0K", "847.3K")
 * - 1,000,000+: one decimal + "M" ("1.0M", "12.5M")
 */
export function formatTokenCount(n: number): string {
  if (n < 1000) {
    return String(n);
  }
  if (n < 1_000_000) {
    return (n / 1000).toFixed(1) + "K";
  }
  return (n / 1_000_000).toFixed(1) + "M";
}
