import * as THREE from "three";

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

/**
 * ColorMapper
 * Single responsibility: map magnitudes in dB to RGB colours and apply them
 * as a BufferAttribute on an existing geometry.
 *
 * The "jet" colormap (blue -> cyan -> green -> yellow -> red) suits
 * field-intensity magnitudes.
 */
export class ColorMapper {
  /**
   * Colours a geometry by magnitude in dB, scaled against the contract's
   * rangeDb.
   *
   * Colour deliberately follows the magnitude rather than the radius: the
   * radius depends on the user's dynamic-range floor, and a colour scale
   * that moved with it would stop being physically readable.
   *
   * Note this maps each dB value independently; it never combines two.
   */
  static applyMagnitudeColors(
    geometry: THREE.BufferGeometry,
    magnitudeDb: number[],
    rangeDb: { min: number; max: number },
  ): void {
    const position = geometry.attributes.position;
    if (!position) {
      throw new Error("geometry has no position attribute to colour");
    }
    if (magnitudeDb.length !== position.count) {
      throw new Error(
        `magnitudeDb has ${magnitudeDb.length} values but the geometry has ` +
          `${position.count} vertices`,
      );
    }

    const span = rangeDb.max - rangeDb.min;
    const colors = new Float32Array(position.count * 3);

    for (let i = 0; i < position.count; i += 1) {
      // A degenerate range (a perfectly isotropic pattern) has no gradient to
      // show, so every vertex sits at the top of the scale.
      const t =
        span === 0 ? 1 : ((magnitudeDb[i] ?? rangeDb.min) - rangeDb.min) / span;
      const { r, g, b } = ColorMapper.jet(t);

      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  }

  /** The "jet" colormap: blue -> cyan -> green -> yellow -> red, t in [0, 1]. */
  static jet(t: number): Rgb {
    const clamped = Math.max(0, Math.min(1, t));

    const stops: [number, [number, number, number]][] = [
      [0, [0, 0, 1]],
      [0.25, [0, 1, 1]],
      [0.5, [0, 1, 0]],
      [0.75, [1, 1, 0]],
      [1, [1, 0, 0]],
    ];

    for (let i = 0; i < stops.length - 1; i += 1) {
      const current = stops[i];
      const next = stops[i + 1];
      if (!current || !next) continue;

      const [t0, c0] = current;
      const [t1, c1] = next;
      if (clamped >= t0 && clamped <= t1) {
        const f = (clamped - t0) / (t1 - t0);
        return {
          r: c0[0] + f * (c1[0] - c0[0]),
          g: c0[1] + f * (c1[1] - c0[1]),
          b: c0[2] + f * (c1[2] - c0[2]),
        };
      }
    }

    return { r: 1, g: 0, b: 0 };
  }
}
