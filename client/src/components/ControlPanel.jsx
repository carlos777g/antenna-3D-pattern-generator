/**
 * ControlPanel
 * Responsabilidad única: UI para modificar los parámetros de Three.js.
 *
 * Recibe `params` y `onChange` desde App.
 * No sabe nada de Three.js — solo emite cambios de estado hacia arriba.
 */
export function ControlPanel({ params, onChange }) {
  const set = (key, val) => onChange({ ...params, [key]: val });

  const colorModes = [
    { key: "altura", label: "📏 Altura (Y)" },
    { key: "distancia", label: "🎯 Distancia al origen" },
    { key: "latitud", label: "🌐 Latitud |Y|" },
  ];

  const concepts = [
    "Scene",
    "PerspectiveCamera",
    "WebGLRenderer",
    "SphereGeometry",
    "BufferAttribute → color",
    "MeshPhongMaterial",
    "requestAnimationFrame",
    "AxesHelper",
  ];

  return (
    <div className="w-60 p-5 bg-[#1a1a2e] flex flex-col gap-5 overflow-y-auto font-mono text-[#e0e0ff]">
      {/* Header */}
      <div className="text-[#7b7bff] text-sm font-bold border-b border-[#333] pb-2">
        ⚙️ PARÁMETROS THREE.JS
      </div>

      {/* Radio */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px] text-[#aaa]">
          Radio: <b className="text-white">{params.radius.toFixed(1)}</b>
        </label>
        <input
          type="range"
          min="0.3"
          max="2"
          step="0.1"
          value={params.radius}
          onChange={(e) => set("radius", parseFloat(e.target.value))}
          className="accent-[#7b7bff] w-full"
        />
      </div>

      {/* Segmentos W */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px] text-[#aaa]">
          Segmentos W (longitud):{" "}
          <b className="text-white">{params.widthSeg}</b>
        </label>
        <input
          type="range"
          min="4"
          max="64"
          step="2"
          value={params.widthSeg}
          onChange={(e) => set("widthSeg", parseInt(e.target.value))}
          className="accent-[#7b7bff] w-full"
        />
      </div>

      {/* Segmentos H */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px] text-[#aaa]">
          Segmentos H (latitud):{" "}
          <b className="text-white">{params.heightSeg}</b>
        </label>
        <input
          type="range"
          min="4"
          max="64"
          step="2"
          value={params.heightSeg}
          onChange={(e) => set("heightSeg", parseInt(e.target.value))}
          className="accent-[#7b7bff] w-full"
        />
      </div>

      {/* Modo de color */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px] text-[#aaa]">
          Modo de color (BufferAttribute)
        </label>
        {colorModes.map(({ key, label }) => (
          <div
            key={key}
            onClick={() => set("colorMode", key)}
            className={`px-3 py-1.5 rounded-md cursor-pointer text-xs border transition-colors
              ${
                params.colorMode === key
                  ? "bg-[#7b7bff22] border-[#7b7bff]"
                  : "bg-white/5 border-[#333] hover:bg-white/10"
              }`}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Wireframe */}
      <div
        onClick={() => set("wireframe", !params.wireframe)}
        className={`px-3 py-2 rounded-md cursor-pointer text-xs border transition-colors
          ${
            params.wireframe
              ? "bg-[#7b7bff33] border-[#7b7bff]"
              : "bg-white/5 border-[#333] hover:bg-white/10"
          }`}
      >
        {params.wireframe ? "✅" : "⬜"} Wireframe (ver vértices)
      </div>

      {/* Info técnica */}
      <div className="mt-auto text-[10px] text-[#555] leading-loose">
        <div className="text-[#666] mb-1">📚 CONCEPTOS ACTIVOS</div>
        {concepts.map((c) => (
          <div key={c}>
            • <span className="text-[#888]">{c}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
