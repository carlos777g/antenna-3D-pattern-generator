import { useRef } from "react";
import { useThreeScene } from "../hooks/useThreeScene";

/**
 * Viewport
 * Responsabilidad única: renderizar el <canvas> donde vive Three.js.
 *
 * Recibe params desde ControlPanel (vía App) y los pasa al hook.
 * No contiene lógica Three.js directa — eso es trabajo del hook.
 */
export function Viewport({ params }) {
  const canvasRef = useRef(null);
  useThreeScene(canvasRef, params);

  return (
    <canvas
      ref={canvasRef}
      className="flex-1 block cursor-grab active:cursor-grabbing"
    />
  );
}