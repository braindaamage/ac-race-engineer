import { describe, it, expect } from "vitest";
import { formatTokenCount } from "../../src/lib/format";

describe("formatTokenCount", () => {
  it("returns raw number for values under 1000", () => {
    expect(formatTokenCount(0)).toBe("0");
    expect(formatTokenCount(42)).toBe("42");
    expect(formatTokenCount(999)).toBe("999");
  });

  it("uses K suffix for values 1000–999999", () => {
    expect(formatTokenCount(1000)).toBe("1.0K");
    expect(formatTokenCount(1500)).toBe("1.5K");
    expect(formatTokenCount(1440)).toBe("1.4K");
    expect(formatTokenCount(847300)).toBe("847.3K");
    expect(formatTokenCount(999999)).toBe("1000.0K");
  });

  it("uses M suffix for values 1000000+", () => {
    expect(formatTokenCount(1000000)).toBe("1.0M");
    expect(formatTokenCount(1400000)).toBe("1.4M");
    expect(formatTokenCount(12500000)).toBe("12.5M");
  });

  it("preserves trailing zeros", () => {
    expect(formatTokenCount(1000)).toBe("1.0K");
    expect(formatTokenCount(2000)).toBe("2.0K");
    expect(formatTokenCount(1000000)).toBe("1.0M");
    expect(formatTokenCount(5000000)).toBe("5.0M");
  });

  it("rounds correctly at boundaries", () => {
    // 1460 / 1000 = 1.46 → toFixed(1) rounds to "1.5"
    expect(formatTokenCount(1460)).toBe("1.5K");
    // 1440 / 1000 = 1.44 → toFixed(1) rounds to "1.4"
    expect(formatTokenCount(1440)).toBe("1.4K");
    // 999999 / 1000 = 999.999 → toFixed(1) rounds to "1000.0"
    expect(formatTokenCount(999999)).toBe("1000.0K");
  });
});
