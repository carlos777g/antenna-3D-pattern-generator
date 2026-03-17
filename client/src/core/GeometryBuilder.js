import * as THREE from "three";
import { ColorMapper } from "./ColorMapper";

/**
 * GeometryBuilder
 * Responsabilidad única: construir geometrías Three.js a partir de parámetros.
 *
 * Por ahora expone buildSphere() como figura de demostración.
 * En el futuro expondrá buildRadiationPattern(points) donde
 * points = array de { theta, phi, r } provenientes del backend.
 *
 * Devuelve siempre un THREE.Mesh listo para pasarle a SceneManager.setMesh()
 */
export class GeometryBuilder {
  /**
   * Esfera parametrizada con colores por vértice.
   * @param {object} params
   * @param {number} params.radius      - radio de la esfera
   * @param {number} params.widthSeg    - segmentos horizontales (longitud)
   * @param {number} params.heightSeg   - segmentos verticales (latitud)
   * @param {string} params.colorMode   - "altura" | "distancia" | "latitud"
   * @param {boolean} params.wireframe  - mostrar aristas
   * @returns {THREE.Mesh}
   */
  static buildSphere(params) {
    const { radius, widthSeg, heightSeg, colorMode, wireframe } = params;

    const geometry = new THREE.SphereGeometry(radius, widthSeg, heightSeg);

    // Aplicar colores por vértice usando ColorMapper
    ColorMapper.applyToGeometry(geometry, colorMode, radius);

    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      wireframe,
      shininess: 80,
    });

    return new THREE.Mesh(geometry, material);
  }

  // ------------------------------------------------------------------
  // PRÓXIMO PASO: buildRadiationPattern
  // Recibirá puntos esféricos del backend y construirá una BufferGeometry
  // ------------------------------------------------------------------
  //
  // static buildRadiationPattern(points) {
    // points: [{ theta, phi, r }, ...]
    // 1. Convertir esféricas → cartesianas
    // 2. Crear BufferGeometry y asignar positions
    // 3. Llamar ColorMapper.applyToGeometry(geometry, "distancia", maxR)
    // 4. Retornar THREE.Mesh
  // }
}