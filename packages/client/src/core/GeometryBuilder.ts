import * as THREE from "three";
import { validatePattern3d, type Pattern3d } from "schema";
import { DEFAULT_FLOOR_DB, magnitudeToRadius } from "./radiusMapping";

export interface RadiationPatternOptions {
  /** Dynamic-range floor in dB; defaults to DEFAULT_FLOOR_DB. */
  floorDb?: number;
}

/**
 * GeometryBuilder
 * Single responsibility: build Three.js geometry from a pattern3d grid.
 * Pure: data in, data out, with no renderer, React or window access.
 */
export class GeometryBuilder {
  /**
   * Builds the radiation-pattern surface from a pattern3d grid.
   *
   * The result is in the physical Z-up antenna frame, exactly as the
   * contract defines it. Converting to the renderer's Y-up frame is
   * SceneManager's job, applied to a container object so the vertex data
   * stays comparable against external references.
   *
   * @throws Pattern3dError when the grid violates the contract.
   */
  static buildRadiationPattern(
    pattern: Pattern3d,
    options: RadiationPatternOptions = {},
  ): THREE.BufferGeometry {
    validatePattern3d(pattern);

    const floorDb = options.floorDb ?? DEFAULT_FLOOR_DB;
    const thetaCount = pattern.thetaDeg.count;
    const phiCount = pattern.phiDeg.count;

    const positions = new Float32Array(thetaCount * phiCount * 3);
    const degToRad = Math.PI / 180;

    for (let i = 0; i < thetaCount; i += 1) {
      const theta =
        (pattern.thetaDeg.start + i * pattern.thetaDeg.stepDeg) * degToRad;
      const sinTheta = Math.sin(theta);
      const cosTheta = Math.cos(theta);

      for (let j = 0; j < phiCount; j += 1) {
        const phi =
          (pattern.phiDeg.start + j * pattern.phiDeg.stepDeg) * degToRad;
        const vertex = i * phiCount + j;
        const r = magnitudeToRadius(pattern.magnitudeDb[vertex] ?? 0, floorDb);

        positions[vertex * 3] = r * sinTheta * Math.cos(phi);
        positions[vertex * 3 + 1] = r * sinTheta * Math.sin(phi);
        positions[vertex * 3 + 2] = r * cosTheta;
      }
    }

    // Two triangles per cell. Uint32 is explicit: 65 160 vertices fits Uint16
    // by only 376 positions, so a resolution change would overflow silently.
    const indices = new Uint32Array((thetaCount - 1) * phiCount * 6);
    let cursor = 0;

    for (let i = 0; i < thetaCount - 1; i += 1) {
      for (let j = 0; j < phiCount; j += 1) {
        // The seam closes through the modulo: column 0 is never duplicated.
        const jNext = (j + 1) % phiCount;

        const a = i * phiCount + j;
        const b = i * phiCount + jNext;
        const c = (i + 1) * phiCount + j;
        const d = (i + 1) * phiCount + jNext;

        // Winding (a, c, b) traverses +theta then +phi. For a radial surface
        // d(p)/d(theta) x d(p)/d(phi) = r^2 sin(theta) * p_hat, which points
        // outward, so this is counter-clockwise seen from outside - the
        // front face in Three.js.
        indices[cursor] = a;
        indices[cursor + 1] = c;
        indices[cursor + 2] = b;
        indices[cursor + 3] = b;
        indices[cursor + 4] = c;
        indices[cursor + 5] = d;
        cursor += 6;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setIndex(new THREE.BufferAttribute(indices, 1));
    geometry.computeVertexNormals();

    return geometry;
  }
}
