import type { ReactNode } from "react";

/**
 * ControlPanel
 * Single responsibility: UI for display parameters.
 * Contains no mathematics - it emits changes upward.
 */
export function ControlPanel({
  floorDb,
  onFloorChange,
  symmetryAssumption,
  rangeDb,
  error,
  children,
}: {
  floorDb: number;
  onFloorChange: (value: number) => void;
  symmetryAssumption: "axial" | "none" | null;
  rangeDb: { min: number; max: number } | null;
  error: string | null;
  children?: ReactNode;
}) {
  return (
    <aside className="w-72 p-5 bg-[#1a1a2e] flex flex-col gap-5 overflow-y-auto text-[#e0e0ff]">
      <h2 className="text-[#7b7bff] text-sm font-bold border-b border-[#333] pb-2">
        Display
      </h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="floor-db" className="text-[11px] text-[#aaa]">
          Dynamic range floor: <b className="text-white">{floorDb} dB</b>
        </label>
        <input
          id="floor-db"
          type="range"
          min={-60}
          max={-10}
          step={1}
          value={floorDb}
          onChange={(event) => onFloorChange(Number(event.target.value))}
        />
        <p className="text-[11px] text-[#777]">
          Magnitudes at or below this level are drawn at the origin.
        </p>
      </div>

      {rangeDb && (
        <p className="text-[11px] text-[#aaa]">
          Pattern range: {rangeDb.min} dB to {rangeDb.max} dB
        </p>
      )}

      {symmetryAssumption === "axial" && (
        <p className="text-[11px] text-[#ffcc66] border border-[#5a4a20] p-2">
          Reconstructed under an axial symmetry assumption. This is a
          simplification, not an equivalent-accuracy result.
        </p>
      )}

      {children}

      {error && (
        <p role="alert" className="text-[11px] text-[#ff8080]">
          {error}
        </p>
      )}
    </aside>
  );
}
