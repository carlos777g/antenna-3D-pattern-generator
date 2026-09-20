# 3D Radiation Pattern Contract — Design

Date: 2026-09-20
Status: approved, pending implementation plan

## Problem

`docs/data-schema.md` defines the 2D half of the unified contract only:
`views[].pattern` as 360 `{angleDeg, magnitudeDb}` samples. The Python
extraction CLI already emits exactly that shape.

The 3D half does not exist anywhere. The root README hints at
`{x, y, z, magnitudeDb}` per vertex, but that phrase is not a contract:
it specifies no vertex ordering, no triangulation, no index buffer, no
angular grid, no units, no normalization, and no pole or seam rule. Three
consumers are blocked on it:

- `python/reconstruction-service` (phase 2) has no target shape to emit.
- `packages/server` cannot validate what it forwards.
- `packages/client` cannot build a `THREE.BufferGeometry` from it.

Because the renderer is Three.js, the natural temptation is to make the
service emit a Three.js buffer directly. This design rejects that, for
the reasons recorded below.

## Decisions

### D1 — The contract is an angular grid, not a Three.js buffer

The service emits a uniform spherical grid of magnitudes. The client
derives positions, indices, normals and colors from it.

Rejected alternative: the service emits flat `positions[]`, `indices[]`
and `magnitudeDb[]` ready for `BufferGeometry.setAttribute`. It is
superficially the better fit for the renderer, but:

- It bakes the dB-to-radius mapping into persisted session data. That
  mapping is a visualization decision (see D4), so every change to the
  dynamic-range floor would require a server round-trip and would
  invalidate stored sessions.
- Payload grows roughly threefold (three float coordinates per vertex
  instead of one magnitude), plus an index array.
- CP-06 requires the exported JSON to be reconstructible in external
  tools (Python, generic 3D viewers). An angular grid is tool-agnostic;
  a Three.js buffer layout is not.

The Three.js buffer remains a real output format, but as a derived
export (see D6), not as the transported and persisted contract.

### D2 — Angles stay in the physical Z-up frame

`thetaDeg` is the polar angle measured from `+Z`; `phiDeg` is the
azimuth measured from `+X` in the `XY` plane. The contract never
mentions Three.js axes.

Three.js is Y-up, so a conversion is required. It happens in the client,
and it is applied to a container `Object3D` rather than baked into the
vertex data. The geometry therefore stays in antenna coordinates, which
keeps the mesh export (D6) consistent with the contract and keeps the
JSON comparable against MATLAB and HFSS references without
reinterpretation.

This matches the convention already used by `docs/theory.md` and by the
`XY`/`XZ`/`YZ` values of `views[].plane`.

### D3 — Grid layout, poles and seam

```json
"pattern3d": {
  "thetaDeg": { "start": 0, "stop": 180, "stepDeg": 1, "count": 181 },
  "phiDeg":   { "start": 0, "stop": 359, "stepDeg": 1, "count": 360 },
  "magnitudeDb": [ 0.0, -0.1, "... 65160 values ..." ],
  "rangeDb": { "min": -38.4, "max": 0.0 },
  "symmetryAssumption": "axial"
}
```

- **Ordering.** Row-major with theta as the outer index. The value at
  `(i, j)` lives at `magnitudeDb[i * 360 + j]`, where `theta = i` degrees
  and `phi = j` degrees. A single flat array rather than a nested one:
  65 160 numbers (about 450 KB of JSON) that copy straight into a
  `Float32Array` with no flattening step.
- **Resolution.** 1 degree in both angles, consistent with the existing
  ingestion resolution. `count` is carried explicitly so a consumer
  validates length instead of assuming it.
- **Poles.** The `theta = 0` and `theta = 180` rows must hold 360
  identical values. This is a testable condition; without it the client
  produces a torn pole.
- **Seam.** `phi = 359` closes against `phi = 0`. Column 0 is **not**
  duplicated at the end of each row. The client closes the ring in the
  index buffer. Duplicating it is the classic error that leaves a
  visible crack or a shading seam.
- **Magnitude.** Finite dB values normalized so that the maximum is
  0 dB. No `null`, no `NaN`, no `-Infinity`; the service clamps at its
  own extraction floor before emitting.
- **`rangeDb`.** Precomputed minimum and maximum, so the client can
  build a color scale without scanning 65 160 values. `max` is 0 by
  construction under the normalization rule above; it is carried
  explicitly so consumers read it rather than hardcoding the
  assumption.
- **`symmetryAssumption`.** `"axial"` for `revolution`, `"none"` for
  `patent`. It exists because `python/reconstruction-service/CLAUDE.md`
  requires `revolution` results to be labeled with their symmetry
  assumption wherever they are surfaced — the client cannot label what
  the payload does not carry.

The block sits alongside `views` in the same session JSON. It is absent
until reconstruction has run.

### D4 — dB-to-radius mapping belongs to the client

```
r = clamp((magnitudeDb - floorDb) / (0 - floorDb), 0, 1)
```

Default `floorDb` is -40 and is user-adjustable. A floor is necessary
because dB is unbounded below: a null at -60 dB would collapse to the
origin and produce degenerate spikes. Because the contract carries
magnitudes rather than radii (D1), changing the floor rebuilds the
geometry locally with no server round-trip.

The rule inherited from the Python service holds on this side too: dB
values are mapped, never averaged and never multiplied. Any arithmetic
that combines two dB quantities as if they were linear ratios is a bug.

Color is mapped from `magnitudeDb` against `rangeDb`, not from the
radius, so the color scale stays physically readable when the user
moves `floorDb`.

### D5 — Client module boundaries

| Module | Responsibility | Pure |
|---|---|---|
| `GeometryBuilder` | `pattern3d` → `BufferGeometry` | yes |
| `ColorMapper` | `magnitudeDb` + `rangeDb` → color attribute | yes |
| `SceneManager` | renderer, camera and controls lifecycle | no (WebGL) |
| `useThreeScene` | React ↔ `SceneManager` glue | no |
| `Viewport`, `ControlPanel` | UI only, no mathematics | — |

Buffer construction: 181 × 360 = 65 160 vertices and 129 600 triangles.
Indices use an explicit `Uint32Array`. `Uint16` would fit today by 376
positions, so any future resolution change would overflow silently —
the explicit 32-bit choice removes that trap. Spherical-to-Cartesian
conversion uses the physical frame of D2
(`x = r·sinθ·cosφ`, `y = r·sinθ·sinφ`, `z = r·cosθ`), followed by
`computeVertexNormals()` for shading.

Boundary validation runs before construction: `count` agrees with array
length, all values finite, pole rows constant. A failure surfaces as a
typed error in the UI. A malformed grid must never be rendered as if it
were a valid pattern.

### D6 — Two output formats with distinct roles

- `pattern3d` (this contract) is what is transported between services
  and persisted in the session JSON.
- The mesh export of RF-08 serializes the *derived* buffer (positions,
  indices, magnitudes) in antenna coordinates. It is a client-side
  export format for external reuse (CP-05, CP-06), not an input to any
  service.

### D7 — `schemaVersion` is introduced now

`docs/data-schema.md` lists schema versioning as an open item. Adding a
whole new top-level block is the right moment to close it. Sessions
carry `schemaVersion: 1`. A consumer that reads an unknown version
rejects the payload rather than guessing.

## Documentation changes

The root `CLAUDE.md` requires a schema change to be made in
`docs/data-schema.md` first and propagated afterwards, so the order
below is binding.

1. **`docs/data-schema.md`** — source of truth. Adds the `pattern3d`
   block, the Z-up angular convention, the pole and seam rules, and
   `schemaVersion: 1`, closing the versioning open item.
2. **`README.md` (root)** — updates the unified contract example, and
   fixes the roadmap's `packages/api` and `packages/web` names, which do
   not match the actual `packages/server` and `packages/client`
   directories (the same stale name also appears in the contract
   section's propagation note).
3. **`packages/client/README.md`** — module scope, render pipeline, the
   dB-to-radius mapping, the RF-07 and RF-08 exports, and setup. The
   file is currently a Vite placeholder.
4. **`packages/client/CLAUDE.md`** — module conventions: strict
   TypeScript and English, the module boundaries of D5, no mathematics
   in components, the dB arithmetic prohibition, `Uint32` indices,
   geometry in Z-up with the rotation applied on the container, and the
   repository's tests-required rule.
5. **`packages/schema/README.md`** — the package moves from "optional,
   not yet confirmed" to confirmed, carrying both the 2D and 3D
   contract types.
6. **`packages/server/README.md`** — one paragraph stating that the
   server validates and forwards `pattern3d` and computes no geometry.
7. **`python/reconstruction-service/CLAUDE.md`** — one line in the
   existing forward-looking phase 2 section, naming `pattern3d` as the
   mandatory output shape. Without it, the producer of the data has no
   contract to emit against.
8. **`python/reconstruction-service/README.md`** — removes the stale
   "angular range wording" note claiming the root README says "0–360".
   The root README was corrected to "0–359" in commit `977f122`, so the
   note now reports a contradiction that no longer exists.

## Testing

`GeometryBuilder` and `ColorMapper` are pure functions and are unit
tested with Vitest, without WebGL:

- vertex count equals `thetaDeg.count × phiDeg.count`
- pole rows collapse without tearing
- the seam closes: the last column's triangles reference column 0
- radius is monotonic in `magnitudeDb` and clamped at `floorDb`
- every index is within bounds
- malformed grids (length mismatch, non-finite value, non-constant pole
  row) raise the typed boundary error instead of producing geometry

`SceneManager` is deliberately kept thin because it cannot be unit
tested without a GPU.

This satisfies the root `CLAUDE.md` rule that a module without a
`tests/` directory containing real assertions is not done.

## Known deviations to resolve in implementation

The current `packages/client` prototype is JavaScript with Spanish
comments, which violates two hard constraints of the root `CLAUDE.md`
(strict TypeScript in `packages/client`, and English-only identifiers
and comments). Migrating the prototype to TypeScript and translating its
comments is step 1 of the client implementation plan, ahead of any work
on `buildRadiationPattern`.

## Out of scope

- The `patent` reconstruction method remains blocked on the open
  angle/direction convention item in `docs/theory.md`. This contract
  describes the shape its output must take, not the method itself.
- Resolutions other than 1 degree. Any resampling is an explicit step in
  the reconstruction stage, per the existing ingestion rule.
- Multi-source fusion, per the root README's scope section.
