import { useState } from "react";
import { Viewport } from "./components/Viewport";
import { ControlPanel } from "./components/ControlPanel";
// import { DataInput } from "./components/DataInput"; // próximo paso

/**
 * App
 * Responsabilidad: orquestador de estado.
 *
 * - Dueño del estado `params` (parámetros de geometría y color)
 * - Pasa params → Viewport (para Three.js)
 * - Pasa params + onChange → ControlPanel (para la UI)
 *
 * Regla: App no importa nada de Three.js directamente.
 */

const INITIAL_PARAMS = {
  radius:    1,
  widthSeg:  32,
  heightSeg: 32,
  wireframe: false,
  colorMode: "altura",
};
export default function App() {
  const [params, setParams] = useState(INITIAL_PARAMS);

  return (
    <div className="flex h-screen bg-[#0f0f1a] text-[#e0e0ff] font-mono">
      {/* Canvas Three.js — recibe params, no sabe de UI */}
      <Viewport params={params} />

      {/* Panel de control — emite cambios hacia arriba via onChange */}
      <ControlPanel params={params} onChange={setParams} />

      {/* DataInput irá aquí cuando implementemos la entrada de datos */}
      {/* <DataInput onDataReady={(points) => { ... }} /> */}
    </div>
  );
}