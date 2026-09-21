/**
 * Types for the unified data contract.
 * `docs/data-schema.md` is the source of truth; this file follows it and
 * never defines schema on its own.
 */

export type SourceType = "image" | "analytic";
export type Plane = "XY" | "XZ" | "YZ";
export type ReconstructionMethod = "revolution" | "patent";

/** "axial" for the revolution method, "none" for the patent method. */
export type SymmetryAssumption = "axial" | "none";

/** An inclusive angular axis sampled at a fixed step, in degrees. */
export interface AngularAxis {
  start: number;
  stop: number;
  stepDeg: number;
  count: number;
}

export interface PatternSample {
  angleDeg: number;
  magnitudeDb: number;
}

export interface PatternView {
  plane: Plane;
  pattern: PatternSample[];
}

/**
 * The reconstructed 3D pattern: a uniform spherical grid of magnitudes in
 * the physical Z-up frame. `magnitudeDb` is row-major with theta as the
 * outer index, so the value at (i, j) is magnitudeDb[i * phiDeg.count + j].
 */
export interface Pattern3d {
  thetaDeg: AngularAxis;
  phiDeg: AngularAxis;
  magnitudeDb: number[];
  rangeDb: { min: number; max: number };
  symmetryAssumption: SymmetryAssumption;
}

export interface SessionDocument {
  schemaVersion: 1;
  sourceType: SourceType;
  plane: Plane;
  metadata: {
    provider: string | null;
    antennaType: string | null;
    polarization: string | null;
  };
  reconstructionMethod: ReconstructionMethod | null;
  views: PatternView[];
  /** Absent until reconstruction has run. */
  pattern3d?: Pattern3d;
  computed: {
    directivityDb: number | null;
    efficiency: number | null;
  };
}
