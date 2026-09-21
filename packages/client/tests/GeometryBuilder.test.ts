import { describe, it, expect } from "vitest";
import { Pattern3dError } from "schema";
import { GeometryBuilder } from "../src/core/GeometryBuilder";
import {
  makePattern3d,
  isotropic,
  THETA_COUNT,
  PHI_COUNT,
} from "./fixtures/makePattern3d";

describe("GeometryBuilder.buildRadiationPattern", () => {
  it("emits one vertex per grid point, with no duplicated seam column", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.attributes.position?.count).toBe(THETA_COUNT * PHI_COUNT);
  });

  it("emits two triangles per grid cell", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.getIndex()?.count).toBe((THETA_COUNT - 1) * PHI_COUNT * 2 * 3);
  });

  it("uses a 32-bit index buffer", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.getIndex()?.array).toBeInstanceOf(Uint32Array);
  });

  it("keeps every index inside the vertex range", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const index = geometry.getIndex();
    const vertexCount = geometry.attributes.position?.count ?? 0;

    let max = -1;
    let min = Number.POSITIVE_INFINITY;
    for (let i = 0; i < (index?.count ?? 0); i += 1) {
      const value = index?.getX(i) ?? -1;
      if (value > max) max = value;
      if (value < min) min = value;
    }

    expect(min).toBe(0);
    expect(max).toBe(vertexCount - 1);
  });

  it("closes the seam: the last phi column references column 0", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const index = geometry.getIndex();

    // The first cell of the last column is (i=0, j=359). Its triangles must
    // reference vertex (i=0, j=0) = index 0 and (i=1, j=0) = index PHI_COUNT.
    const firstCellOfLastColumn = (PHI_COUNT - 1) * 6;
    const triangleIndices = new Set<number>();
    for (let k = 0; k < 6; k += 1) {
      triangleIndices.add(index?.getX(firstCellOfLastColumn + k) ?? -1);
    }

    expect(triangleIndices.has(0)).toBe(true);
    expect(triangleIndices.has(PHI_COUNT)).toBe(true);
  });

  it("collapses the theta=0 pole to a single point", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;

    for (let j = 1; j < PHI_COUNT; j += 1) {
      expect(position?.getX(j)).toBeCloseTo(position?.getX(0) ?? NaN, 10);
      expect(position?.getY(j)).toBeCloseTo(position?.getY(0) ?? NaN, 10);
      expect(position?.getZ(j)).toBeCloseTo(position?.getZ(0) ?? NaN, 10);
    }
  });

  it("places an isotropic pattern on a unit sphere in the Z-up frame", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;

    // theta=0 is +Z, theta=90/phi=0 is +X, theta=90/phi=90 is +Y.
    expect(position?.getZ(0)).toBeCloseTo(1, 10);
    expect(position?.getX(90 * PHI_COUNT)).toBeCloseTo(1, 10);
    expect(position?.getY(90 * PHI_COUNT + 90)).toBeCloseTo(1, 10);
  });

  it("winds triangles so that normals point outward", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;
    const normal = geometry.attributes.normal;

    // On a sphere the outward normal is parallel to the position vector.
    for (const i of [45 * PHI_COUNT + 10, 90 * PHI_COUNT + 200, 135 * PHI_COUNT]) {
      const dot =
        (position?.getX(i) ?? 0) * (normal?.getX(i) ?? 0) +
        (position?.getY(i) ?? 0) * (normal?.getY(i) ?? 0) +
        (position?.getZ(i) ?? 0) * (normal?.getZ(i) ?? 0);
      expect(dot).toBeGreaterThan(0);
    }
  });

  it("shrinks the radius as the magnitude drops", () => {
    // A pattern that falls off with theta: 0 dB at the pole, -40 dB at theta=180.
    const pattern = makePattern3d((thetaDeg) => -40 * (thetaDeg / 180));
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);
    const position = geometry.attributes.position;

    const radiusAt = (i: number) =>
      Math.hypot(
        position?.getX(i) ?? 0,
        position?.getY(i) ?? 0,
        position?.getZ(i) ?? 0,
      );

    expect(radiusAt(0)).toBeCloseTo(1, 10);
    expect(radiusAt(90 * PHI_COUNT)).toBeCloseTo(0.5, 6);
    expect(radiusAt((THETA_COUNT - 1) * PHI_COUNT)).toBeCloseTo(0, 10);
  });

  it("honours a caller-supplied floor", () => {
    const pattern = makePattern3d(() => -10);

    const withDefaultFloor = GeometryBuilder.buildRadiationPattern(pattern);
    const withTightFloor = GeometryBuilder.buildRadiationPattern(pattern, {
      floorDb: -20,
    });

    // -10 dB is 75% of the way up a -40 dB range, but only 50% of a -20 dB range.
    expect(withDefaultFloor.attributes.position?.getZ(0)).toBeCloseTo(0.75, 10);
    expect(withTightFloor.attributes.position?.getZ(0)).toBeCloseTo(0.5, 10);
  });

  it("rejects a malformed pattern instead of building geometry", () => {
    const pattern = isotropic();
    pattern.magnitudeDb[7] = -3; // breaks the constant theta=0 pole row

    expect(() => GeometryBuilder.buildRadiationPattern(pattern)).toThrow(
      Pattern3dError,
    );
  });
});
