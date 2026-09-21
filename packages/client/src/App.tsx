import { useEffect, useRef, useState } from "react";
import type { Pattern3d } from "schema";
import { DEFAULT_FLOOR_DB } from "./core/radiusMapping";
import { loadPattern3d } from "./core/patternService";
import { GeometryBuilder } from "./core/GeometryBuilder";
import { buildMeshExport } from "./core/meshExport";
import { useThreeScene } from "./hooks/useThreeScene";
import { Viewport } from "./components/Viewport";
import { ControlPanel } from "./components/ControlPanel";
import { ExportButtons } from "./components/ExportButtons";

function download(filename: string, href: string): void {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  anchor.click();
}

/**
 * App
 * Single responsibility: state orchestration.
 * Owns the loaded pattern and the display floor, and never imports Three.js.
 */
export default function App() {
  const [pattern, setPattern] = useState<Pattern3d | null>(null);
  const [floorDb, setFloorDb] = useState(DEFAULT_FLOOR_DB);
  const [loadError, setLoadError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { error: renderError, sceneRef } = useThreeScene(
    canvasRef,
    pattern,
    floorDb,
  );

  useEffect(() => {
    loadPattern3d()
      .then(setPattern)
      .catch((caught: unknown) => setLoadError(String(caught)));
  }, []);

  const handleSnapshot = () => {
    const manager = sceneRef.current;
    if (!manager) return;
    download("radiation-pattern.png", manager.captureSnapshot());
  };

  const handleMeshJson = () => {
    if (!pattern) return;
    const geometry = GeometryBuilder.buildRadiationPattern(pattern, { floorDb });
    const payload = buildMeshExport(geometry, pattern.magnitudeDb, floorDb);
    geometry.dispose();
    download(
      "radiation-pattern-mesh.json",
      URL.createObjectURL(
        new Blob([JSON.stringify(payload)], { type: "application/json" }),
      ),
    );
  };

  return (
    <div className="flex h-screen bg-[#0f0f1a] text-[#e0e0ff] font-mono">
      <Viewport canvasRef={canvasRef} error={renderError} />
      <ControlPanel
        floorDb={floorDb}
        onFloorChange={setFloorDb}
        symmetryAssumption={pattern?.symmetryAssumption ?? null}
        rangeDb={pattern?.rangeDb ?? null}
        error={loadError}
      >
        <ExportButtons
          onSnapshot={handleSnapshot}
          onMeshJson={handleMeshJson}
          disabled={!pattern}
        />
      </ControlPanel>
    </div>
  );
}
