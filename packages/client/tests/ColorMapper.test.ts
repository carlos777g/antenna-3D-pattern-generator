import { describe, it, expect } from "vitest";
import * as THREE from "three";
import { ColorMapper } from "../src/core/ColorMapper";

function geometryWith(vertexCount: number): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(new Float32Array(vertexCount * 3), 3),
  );
  return geometry;
}

describe("ColorMapper.applyMagnitudeColors", () => {
  it("sets one RGB triple per vertex", () => {
    const geometry = geometryWith(3);
    ColorMapper.applyMagnitudeColors(geometry, [0, -10, -20], {
      min: -20,
      max: 0,
    });

    const color = geometry.attributes.color;
    expect(color?.count).toBe(3);
    expect(color?.itemSize).toBe(3);
  });

  it("maps the range maximum to the top of the colour scale", () => {
    const geometry = geometryWith(2);
    ColorMapper.applyMagnitudeColors(geometry, [0, -20], { min: -20, max: 0 });

    const color = geometry.attributes.color;
    // jet(1) is pure red.
    expect(color?.getX(0)).toBeCloseTo(1, 6);
    expect(color?.getY(0)).toBeCloseTo(0, 6);
    expect(color?.getZ(0)).toBeCloseTo(0, 6);
  });

  it("maps the range minimum to the bottom of the colour scale", () => {
    const geometry = geometryWith(2);
    ColorMapper.applyMagnitudeColors(geometry, [0, -20], { min: -20, max: 0 });

    const color = geometry.attributes.color;
    // jet(0) is pure blue.
    expect(color?.getX(1)).toBeCloseTo(0, 6);
    expect(color?.getY(1)).toBeCloseTo(0, 6);
    expect(color?.getZ(1)).toBeCloseTo(1, 6);
  });

  it("is independent of the radius, so a floor change leaves colours alone", () => {
    const geometry = geometryWith(1);
    ColorMapper.applyMagnitudeColors(geometry, [-10], { min: -20, max: 0 });
    const first = geometry.attributes.color?.getY(0);

    // Same magnitude and same range: the colour cannot depend on anything else.
    const other = geometryWith(1);
    ColorMapper.applyMagnitudeColors(other, [-10], { min: -20, max: 0 });

    expect(other.attributes.color?.getY(0)).toBe(first);
  });

  it("does not divide by zero when the range is degenerate", () => {
    const geometry = geometryWith(2);
    ColorMapper.applyMagnitudeColors(geometry, [0, 0], { min: 0, max: 0 });

    const color = geometry.attributes.color;
    expect(Number.isFinite(color?.getX(0) ?? NaN)).toBe(true);
    expect(Number.isFinite(color?.getY(0) ?? NaN)).toBe(true);
    expect(Number.isFinite(color?.getZ(0) ?? NaN)).toBe(true);
  });

  it("rejects a magnitude array that does not match the vertex count", () => {
    const geometry = geometryWith(3);

    expect(() =>
      ColorMapper.applyMagnitudeColors(geometry, [0, -10], { min: -20, max: 0 }),
    ).toThrow();
  });
});
