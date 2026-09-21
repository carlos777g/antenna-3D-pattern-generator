import { useEffect, useRef, useState, type RefObject } from "react";
import { Pattern3dError, type Pattern3d } from "schema";
import { SceneManager } from "../core/SceneManager";
import { GeometryBuilder } from "../core/GeometryBuilder";
import { ColorMapper } from "../core/ColorMapper";

/**
 * useThreeScene
 * Bridge between React and Three.js.
 *
 * 1. Creates the SceneManager once, on mount
 * 2. Rebuilds the geometry whenever the pattern or the floor changes
 * 3. Releases GPU resources on unmount
 */
export function useThreeScene(
  canvasRef: RefObject<HTMLCanvasElement | null>,
  pattern: Pattern3d | null,
  floorDb: number,
): { error: string | null; sceneRef: RefObject<SceneManager | null> } {
  const sceneRef = useRef<SceneManager | null>(null);
  const [error, setError] = useState<string | null>(null);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Three.js throws when the browser cannot hand out a WebGL context, which
    // happens whenever GPU acceleration is unavailable or disabled. Letting
    // that escape the effect takes the whole React tree down and leaves a
    // blank page, so it is reported the same way a malformed pattern is.
    let manager: SceneManager;
    try {
      manager = new SceneManager(canvas);
    } catch (caught) {
      setError(
        "WebGL is unavailable in this browser, so the 3D pattern cannot be " +
          "drawn. Enable hardware acceleration (chrome://settings/system) " +
          `and check chrome://gpu for details. Underlying error: ${String(caught)}`,
      );
      return;
    }

    sceneRef.current = manager;
    manager.startLoop();

    const onResize = () =>
      manager.resize(canvas.clientWidth, canvas.clientHeight);
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      manager.dispose();
      sceneRef.current = null;
    };
  }, [canvasRef]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Building the geometry is an imperative GPU side effect, and the error is
  // its outcome, so there is no render-time place to derive it from. The
  // set-state-in-effect rule targets state that could be computed during
  // render; this state cannot.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const manager = sceneRef.current;
    if (!manager || !pattern) return;

    try {
      const geometry = GeometryBuilder.buildRadiationPattern(pattern, {
        floorDb,
      });
      ColorMapper.applyMagnitudeColors(
        geometry,
        pattern.magnitudeDb,
        pattern.rangeDb,
      );
      manager.setPatternGeometry(geometry);
      setError(null);
    } catch (caught) {
      // A malformed grid is reported, never rendered.
      setError(
        caught instanceof Pattern3dError
          ? `Invalid pattern (${caught.code}): ${caught.message}`
          : String(caught),
      );
    }
  }, [pattern, floorDb]);
  /* eslint-enable react-hooks/set-state-in-effect */

  return { error, sceneRef };
}
