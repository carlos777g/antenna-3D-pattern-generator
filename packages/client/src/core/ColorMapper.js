import * as THREE from "three";

/**
 * ColorMapper
 * Responsabilidad única: mapear valores numéricos a colores RGB
 * y aplicarlos como BufferAttribute sobre una geometría existente.
 *
 * El colormap "jet" (azul→cian→verde→amarillo→rojo) es ideal para
 * representar intensidades de campo eléctrico / distancias radiales.
 */
export class ColorMapper {
  /**
   * Recorre todos los vértices de una geometría, calcula t ∈ [0,1]
   * según el modo elegido, y asigna el BufferAttribute "color".
   *
   * @param {THREE.BufferGeometry} geometry  - geometría a colorear
   * @param {string} mode  - "altura" | "distancia" | "latitud"
   * @param {number} scale - valor máximo esperado para normalizar
   */
  static applyToGeometry(geometry, mode, scale = 1) {
    const positions = geometry.attributes.position;
    const count = positions.count;
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const z = positions.getZ(i);

      const t = ColorMapper._normalize(x, y, z, mode, scale);
      const { r, g, b } = ColorMapper.jet(t);

      colors[i * 3]     = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  }

  // ------------------------------------------------------------------
  // Calcula t ∈ [0,1] para un vértice (x,y,z) según el modo
  // ------------------------------------------------------------------
  static _normalize(x, y, z, mode, scale) {
    switch (mode) {
      case "altura":
        // t según componente Y (−scale → 0, +scale → 1)
        return (y + scale) / (2 * scale);

      case "distancia":
        // t según distancia euclidiana al origen
        return Math.sqrt(x * x + y * y + z * z) / scale;

      case "latitud":
        // t según |Y| normalizado (polos = 1, ecuador = 0)
        return Math.abs(y) / scale;

      default:
        return 0.5;
    }
  }

  // ------------------------------------------------------------------
  // Colormap "jet": azul → cian → verde → amarillo → rojo
  // t ∈ [0, 1]
  // ------------------------------------------------------------------
  static jet(t) {
    t = Math.max(0, Math.min(1, t));

    const stops = [
      [0,    [0, 0, 1]],
      [0.25, [0, 1, 1]],
      [0.5,  [0, 1, 0]],
      [0.75, [1, 1, 0]],
      [1,    [1, 0, 0]],
    ];

    for (let i = 0; i < stops.length - 1; i++) {
      const [t0, c0] = stops[i];
      const [t1, c1] = stops[i + 1];
      if (t >= t0 && t <= t1) {
        const f = (t - t0) / (t1 - t0);
        return {
          r: c0[0] + f * (c1[0] - c0[0]),
          g: c0[1] + f * (c1[1] - c0[1]),
          b: c0[2] + f * (c1[2] - c0[2]),
        };
      }
    }
    return { r: 1, g: 0, b: 0 };
  }

  // ------------------------------------------------------------------
  // PRÓXIMOS COLORMAPS (para distintos tipos de visualización)
  // ------------------------------------------------------------------
  // static viridis(t) { ... }
  // static plasma(t)  { ... }
  // static hot(t)     { ... }
}