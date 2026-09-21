import { describe, it, expect } from "vitest";
import { validatePattern3d, Pattern3dError, type Pattern3d } from "../src/index";

const THETA_COUNT = 181;
const PHI_COUNT = 360;

/** An isotropic pattern: every direction at 0 dB. Always valid. */
function makeValidPattern(): Pattern3d {
  return {
    thetaDeg: { start: 0, stop: 180, stepDeg: 1, count: THETA_COUNT },
    phiDeg: { start: 0, stop: 359, stepDeg: 1, count: PHI_COUNT },
    magnitudeDb: new Array(THETA_COUNT * PHI_COUNT).fill(0),
    rangeDb: { min: 0, max: 0 },
    symmetryAssumption: "axial",
  };
}

describe("validatePattern3d", () => {
  it("accepts a well-formed pattern", () => {
    expect(() => validatePattern3d(makeValidPattern())).not.toThrow();
  });

  it("rejects a magnitude array whose length disagrees with the axis counts", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb = pattern.magnitudeDb.slice(0, -1);

    expect(() => validatePattern3d(pattern)).toThrow(Pattern3dError);
    try {
      validatePattern3d(pattern);
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("LENGTH_MISMATCH");
    }
  });

  it("rejects a non-finite magnitude", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[5000] = Number.NEGATIVE_INFINITY;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("NON_FINITE");
    }
  });

  it("rejects a non-constant theta=0 pole row", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[7] = -3;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("POLE_NOT_CONSTANT");
    }
  });

  it("rejects a non-constant theta=180 pole row", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[(THETA_COUNT - 1) * PHI_COUNT + 12] = -3;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("POLE_NOT_CONSTANT");
    }
  });

  it("rejects an axis whose count disagrees with start, stop and step", () => {
    const pattern = makeValidPattern();
    pattern.thetaDeg = { start: 0, stop: 180, stepDeg: 1, count: 180 };

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("AXIS_INVALID");
    }
  });
});
