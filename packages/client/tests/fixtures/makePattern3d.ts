import type { Pattern3d } from "schema";

export const THETA_COUNT = 181;
export const PHI_COUNT = 360;

/**
 * Builds a valid pattern3d from a magnitude function over (theta, phi) in
 * degrees. Pole rows are forced constant by evaluating them at phi = 0, so
 * a caller cannot accidentally produce an invalid fixture.
 *
 * This is a test helper, not a reconstruction: the client never computes
 * pattern data in production code.
 */
export function makePattern3d(
  magnitudeAt: (thetaDeg: number, phiDeg: number) => number,
): Pattern3d {
  const magnitudeDb: number[] = new Array(THETA_COUNT * PHI_COUNT);
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;

  for (let i = 0; i < THETA_COUNT; i += 1) {
    const isPole = i === 0 || i === THETA_COUNT - 1;
    for (let j = 0; j < PHI_COUNT; j += 1) {
      const value = magnitudeAt(i, isPole ? 0 : j);
      magnitudeDb[i * PHI_COUNT + j] = value;
      if (value < min) min = value;
      if (value > max) max = value;
    }
  }

  return {
    thetaDeg: { start: 0, stop: 180, stepDeg: 1, count: THETA_COUNT },
    phiDeg: { start: 0, stop: 359, stepDeg: 1, count: PHI_COUNT },
    magnitudeDb,
    rangeDb: { min, max },
    symmetryAssumption: "axial",
  };
}

/** Isotropic: every direction at the 0 dB maximum, so the mesh is a unit sphere. */
export const isotropic = (): Pattern3d => makePattern3d(() => 0);
