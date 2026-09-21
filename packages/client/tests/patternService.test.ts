import { describe, it, expect, vi, afterEach } from "vitest";
import { loadPattern3d } from "../src/core/patternService";
import { isotropic } from "./fixtures/makePattern3d";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("loadPattern3d", () => {
  it("returns a validated pattern", async () => {
    const pattern = isotropic();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(pattern))),
    );

    await expect(loadPattern3d("/fixtures/x.json")).resolves.toMatchObject({
      symmetryAssumption: "axial",
    });
  });

  it("rejects a malformed pattern rather than returning it", async () => {
    const pattern = isotropic();
    pattern.magnitudeDb[7] = -3;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(pattern))),
    );

    await expect(loadPattern3d("/fixtures/x.json")).rejects.toThrow();
  });

  it("reports a failed request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 404 })),
    );

    await expect(loadPattern3d("/fixtures/x.json")).rejects.toThrow(/404/);
  });
});
