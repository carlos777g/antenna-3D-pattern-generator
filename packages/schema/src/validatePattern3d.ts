import type { AngularAxis, Pattern3d } from "./contract";

export type Pattern3dErrorCode =
  | "AXIS_INVALID"
  | "LENGTH_MISMATCH"
  | "NON_FINITE"
  | "POLE_NOT_CONSTANT";

export class Pattern3dError extends Error {
  constructor(
    public readonly code: Pattern3dErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "Pattern3dError";
  }
}

function validateAxis(axis: AngularAxis, name: string): void {
  if (axis.stepDeg <= 0) {
    throw new Pattern3dError(
      "AXIS_INVALID",
      `${name}.stepDeg must be positive, got ${axis.stepDeg}`,
    );
  }

  const expected = Math.round((axis.stop - axis.start) / axis.stepDeg) + 1;
  if (axis.count !== expected) {
    throw new Pattern3dError(
      "AXIS_INVALID",
      `${name}.count is ${axis.count} but start/stop/stepDeg imply ${expected}`,
    );
  }
}

/**
 * Validates a pattern3d block against the rules in docs/data-schema.md.
 * Throws Pattern3dError on the first violation; returns nothing on success.
 *
 * A malformed grid must never reach geometry construction: it renders as a
 * plausible-looking but wrong pattern, which is worse than an error.
 */
export function validatePattern3d(pattern: Pattern3d): void {
  const { thetaDeg, phiDeg, magnitudeDb } = pattern;

  validateAxis(thetaDeg, "thetaDeg");
  validateAxis(phiDeg, "phiDeg");

  const expectedLength = thetaDeg.count * phiDeg.count;
  if (magnitudeDb.length !== expectedLength) {
    throw new Pattern3dError(
      "LENGTH_MISMATCH",
      `magnitudeDb has ${magnitudeDb.length} values, expected ` +
        `${expectedLength} (${thetaDeg.count} x ${phiDeg.count})`,
    );
  }

  for (let i = 0; i < magnitudeDb.length; i += 1) {
    const value = magnitudeDb[i];
    if (value === undefined || !Number.isFinite(value)) {
      throw new Pattern3dError(
        "NON_FINITE",
        `magnitudeDb[${i}] is ${String(value)}; every magnitude must be finite`,
      );
    }
  }

  // Both pole rows collapse to a single point in space, so every value in
  // them must agree. A non-constant pole row tears the mesh open.
  for (const rowIndex of [0, thetaDeg.count - 1]) {
    const offset = rowIndex * phiDeg.count;
    const reference = magnitudeDb[offset];
    for (let j = 1; j < phiDeg.count; j += 1) {
      if (magnitudeDb[offset + j] !== reference) {
        throw new Pattern3dError(
          "POLE_NOT_CONSTANT",
          `pole row theta=${rowIndex * thetaDeg.stepDeg} is not constant: ` +
            `index ${offset + j} is ${String(magnitudeDb[offset + j])}, ` +
            `expected ${String(reference)}`,
        );
      }
    }
  }
}
