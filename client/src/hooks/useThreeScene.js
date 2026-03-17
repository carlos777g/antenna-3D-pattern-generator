import { useEffect, useRef } from "react";
import { SceneManager } from "../core/SceneManager";
import { GeometryBuilder } from "../core/GeometryBuilder";

/**
 * useThreeScene
 * Puente entre React y Three.js.
 *
 * Responsabilidades:
 *  1. Inicializar SceneManager una sola vez (al montar el componente)
 *  2. Reconstruir la geometría cada vez que cambian los parámetros
 *  3. Limpiar recursos al desmontar (stopLoop, removeEventListeners)
 *
 * @param {React.RefObject} canvasRef - ref al elemento <canvas>
 * @param {object} params             - parámetros de geometría y color
 */
export function useThreeScene(canvasRef, params) {
  const sceneRef = useRef(null);

  // ── Inicialización (solo al montar) ──────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const sm = new SceneManager(canvas);
    sceneRef.current = sm;

    // Construir geometría inicial
    const mesh = GeometryBuilder.buildSphere(params);
    sm.setMesh(mesh);
    sm.startLoop();

    // Redimensionar si cambia el viewport
    const onResize = () =>
      sm.resize(canvas.clientWidth, canvas.clientHeight);
    window.addEventListener("resize", onResize);

    return () => {
      sm.stopLoop();
      window.removeEventListener("resize", onResize);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // [] → solo una vez

  // ── Actualizar geometría cuando cambian params ────────────────────
  useEffect(() => {
    const sm = sceneRef.current;
    if (!sm) return;

    const mesh = GeometryBuilder.buildSphere(params);
    sm.setMesh(mesh);
  }, [params]);

  // Exponer sceneRef por si un componente necesita acceso directo
  return sceneRef;
}