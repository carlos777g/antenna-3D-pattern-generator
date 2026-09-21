import { describe, it, expect } from "vitest";
import { magnitudeToRadius, DEFAULT_FLOOR_DB } from "../src/core/radiusMapping";

describe("magnitudeToRadius", () => {
  it("maps the 0 dB maximum to the unit radius", () => {
    expect(magnitudeToRadius(0, -40)).toBe(1);
  });

  it("maps the floor to zero", () => {
    expect(magnitudeToRadius(-40, -40)).toBe(0);
  });

  it("clamps anything below the floor to zero", () => {
    expect(magnitudeToRadius(-60, -40)).toBe(0);
  });

  it("clamps anything above the maximum to one", () => {
    expect(magnitudeToRadius(3, -40)).toBe(1);
  });

  it("is monotonically increasing in magnitude", () => {
    expect(magnitudeToRadius(-10, -40)).toBeGreaterThan(
      magnitudeToRadius(-20, -40),
    );
  });

  it("maps the midpoint of the range to a half radius", () => {
    expect(magnitudeToRadius(-20, -40)).toBeCloseTo(0.5, 10);
  });

  it("defaults the floor to -40 dB", () => {
    expect(DEFAULT_FLOOR_DB).toBe(-40);
  });
});
