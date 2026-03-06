import { describe, it, expect } from "vitest";
import {
  formatDelta,
  formatLapTime,
  deltaDirection,
  isImprovement,
} from "../../../src/views/compare/utils";

describe("formatDelta", () => {
  it("returns positive sign for positive values", () => {
    expect(formatDelta(1.5, 2)).toBe("+1.50");
  });

  it("returns no sign prefix for negative values (minus from number)", () => {
    expect(formatDelta(-0.45, 2)).toBe("-0.45");
  });

  it("returns +0.00 for zero", () => {
    expect(formatDelta(0, 2)).toBe("+0.00");
  });

  it("returns N/A for null", () => {
    expect(formatDelta(null)).toBe("N/A");
  });

  it("returns N/A for undefined", () => {
    expect(formatDelta(undefined)).toBe("N/A");
  });

  it("respects precision parameter", () => {
    expect(formatDelta(1.23456, 3)).toBe("+1.235");
    expect(formatDelta(-0.1, 1)).toBe("-0.1");
  });

  it("defaults to 2 decimal places", () => {
    expect(formatDelta(3.1)).toBe("+3.10");
  });
});

describe("formatLapTime", () => {
  it("formats seconds to mm:ss.xxx", () => {
    expect(formatLapTime(82.456)).toBe("1:22.456");
  });

  it("handles sub-minute times", () => {
    expect(formatLapTime(45.123)).toBe("0:45.123");
  });

  it("pads seconds to 6 chars (ss.xxx)", () => {
    expect(formatLapTime(60.5)).toBe("1:00.500");
  });

  it("returns N/A for null", () => {
    expect(formatLapTime(null)).toBe("N/A");
  });

  it("returns N/A for undefined", () => {
    expect(formatLapTime(undefined)).toBe("N/A");
  });
});

describe("deltaDirection", () => {
  it("returns increase for positive", () => {
    expect(deltaDirection(1.5)).toBe("increase");
  });

  it("returns decrease for negative", () => {
    expect(deltaDirection(-0.3)).toBe("decrease");
  });

  it("returns unchanged for zero", () => {
    expect(deltaDirection(0)).toBe("unchanged");
  });

  it("returns unchanged for null", () => {
    expect(deltaDirection(null)).toBe("unchanged");
  });

  it("returns unchanged for undefined", () => {
    expect(deltaDirection(undefined)).toBe("unchanged");
  });
});

describe("isImprovement", () => {
  it("negative lap_time_delta_s is improvement (faster)", () => {
    expect(isImprovement("lap_time_delta_s", -0.5)).toBe(true);
  });

  it("positive lap_time_delta_s is not improvement (slower)", () => {
    expect(isImprovement("lap_time_delta_s", 0.5)).toBe(false);
  });

  it("positive peak_lat_g_delta is improvement (more grip)", () => {
    expect(isImprovement("peak_lat_g_delta", 0.05)).toBe(true);
  });

  it("negative peak_lat_g_delta is not improvement (less grip)", () => {
    expect(isImprovement("peak_lat_g_delta", -0.05)).toBe(false);
  });

  it("negative tyre_temp_delta is improvement", () => {
    expect(isImprovement("tyre_temp_delta", -1.2)).toBe(true);
  });

  it("positive tyre_temp_delta is not improvement", () => {
    expect(isImprovement("tyre_temp_delta", 1.2)).toBe(false);
  });

  it("negative slip_angle_delta is improvement", () => {
    expect(isImprovement("slip_angle_delta", -0.2)).toBe(true);
  });

  it("negative slip_ratio_delta is improvement", () => {
    expect(isImprovement("slip_ratio_delta", -0.01)).toBe(true);
  });
});
