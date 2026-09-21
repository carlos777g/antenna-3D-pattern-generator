import type * as THREE from "three";

/**
 * The RF-08 mesh export format.
 *
 * This is an output format for external reuse (CP-05, CP-06), not an input
 * to any service. It names its coordinate frame explicitly because a tool
 * reading the file has no schema document at hand, unlike a consumer of the
 * transported contract.
 */
export interface MeshExport {
  schemaVersion: 1;
  frame: "antennaZUp";
  floorDb: number;
  vertexCount: number;
  positions: number[];
  indices: number[];
  magnitudeDb: number[];
}

export function buildMeshExport(
  geometry: THREE.BufferGeometry,
  magnitudeDb: number[],
  floorDb: number,
): MeshExport {
  const position = geometry.attributes.position;
  const index = geometry.getIndex();

  if (!position || !index) {
    throw new Error("geometry must have both position and index to export");
  }

  return {
    schemaVersion: 1,
    frame: "antennaZUp",
    floorDb,
    vertexCount: position.count,
    positions: Array.from(position.array as Float32Array),
    indices: Array.from(index.array as Uint32Array),
    magnitudeDb: [...magnitudeDb],
  };
}
