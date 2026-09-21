import { describe, it, expect } from "vitest";
import { GeometryBuilder } from "../src/core/GeometryBuilder";
import { buildMeshExport } from "../src/core/meshExport";
import { isotropic, THETA_COUNT, PHI_COUNT } from "./fixtures/makePattern3d";

describe("buildMeshExport", () => {
  it("carries one position triple per vertex", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);

    expect(exported.vertexCount).toBe(THETA_COUNT * PHI_COUNT);
    expect(exported.positions).toHaveLength(THETA_COUNT * PHI_COUNT * 3);
    expect(exported.magnitudeDb).toHaveLength(THETA_COUNT * PHI_COUNT);
  });

  it("carries the full index buffer", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);

    expect(exported.indices).toHaveLength((THETA_COUNT - 1) * PHI_COUNT * 6);
  });

  it("declares the antenna frame and the floor used to build it", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern, {
      floorDb: -25,
    });

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -25);

    expect(exported.frame).toBe("antennaZUp");
    expect(exported.floorDb).toBe(-25);
    expect(exported.schemaVersion).toBe(1);
  });

  it("round-trips through JSON without losing data", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);
    const reparsed = JSON.parse(JSON.stringify(exported)) as typeof exported;

    expect(reparsed.positions).toHaveLength(exported.positions.length);
    expect(reparsed.indices[17]).toBe(exported.indices[17]);
  });
});
