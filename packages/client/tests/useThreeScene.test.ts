/**
 * @vitest-environment jsdom
 *
 * jsdom provides no WebGL implementation, so `new THREE.WebGLRenderer(...)`
 * throws here exactly as it does in a browser whose GPU acceleration is
 * disabled ("Error creating WebGL context"). That makes this the natural
 * place to pin down what the hook must do when the renderer cannot start:
 * report it, never take the application down with it.
 */
import { describe, it, expect, afterEach } from "vitest";
import { renderHook, cleanup } from "@testing-library/react";
import { useThreeScene } from "../src/hooks/useThreeScene";

afterEach(() => {
  cleanup();
});

function canvasRef() {
  return { current: document.createElement("canvas") };
}

describe("useThreeScene when WebGL is unavailable", () => {
  it("does not throw out of the hook", () => {
    expect(() =>
      renderHook(() => useThreeScene(canvasRef(), null, -40)),
    ).not.toThrow();
  });

  it("reports the failure as an error message naming WebGL", () => {
    const { result } = renderHook(() => useThreeScene(canvasRef(), null, -40));

    expect(result.current.error).toMatch(/WebGL/i);
  });

  it("leaves no scene manager behind when startup failed", () => {
    const { result } = renderHook(() => useThreeScene(canvasRef(), null, -40));

    expect(result.current.sceneRef.current).toBeNull();
  });
});
