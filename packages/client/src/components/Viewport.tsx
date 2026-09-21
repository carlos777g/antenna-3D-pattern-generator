import type { RefObject } from "react";

/**
 * Viewport
 * Single responsibility: render the <canvas> that Three.js draws into,
 * plus any error the render pipeline reports. It owns no Three.js state.
 */
export function Viewport({
  canvasRef,
  error,
}: {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  error: string | null;
}) {
  return (
    <div className="flex-1 relative">
      <canvas
        ref={canvasRef}
        aria-label="Interactive 3D radiation pattern"
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />
      {error && (
        <p role="alert" className="absolute top-4 left-4 bg-[#4a1020] px-3 py-2 text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
