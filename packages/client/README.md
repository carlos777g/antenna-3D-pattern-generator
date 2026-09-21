# Client (React + Three.js)

Browser frontend: input forms, interactive 3D visualization of a
reconstructed radiation pattern, and export.

See the root [README.md](../../README.md) for architecture and
[docs/data-schema.md](../../docs/data-schema.md) for the data contract.

## What this module does

It consumes the `pattern3d` block of a session document — a 1-degree
spherical grid of dB magnitudes — and derives everything it renders.
It performs no reconstruction: no interpolation, no symmetry inference,
no analytic evaluation. Those belong to
`python/reconstruction-service`.

## Render pipeline

```
pattern3d ──► validatePattern3d ──► GeometryBuilder ──► BufferGeometry
                  (schema)         + ColorMapper           │
                                                           ▼
                                              SceneManager (Three.js)
```

| Module | Responsibility | Pure |
|---|---|---|
| `core/GeometryBuilder.ts` | `pattern3d` → `BufferGeometry` | yes |
| `core/ColorMapper.ts` | magnitudes + `rangeDb` → colour attribute | yes |
| `core/radiusMapping.ts` | dB → normalized radius | yes |
| `core/SceneManager.ts` | renderer, camera, controls lifecycle | no |
| `hooks/useThreeScene.ts` | React ↔ `SceneManager` glue | no |
| `components/*` | UI only, no mathematics | — |

## dB-to-radius mapping

```
r = clamp((magnitudeDb - floorDb) / (0 - floorDb), 0, 1)
```

`floorDb` defaults to -40 dB and is user-adjustable. A floor is
required because dB is unbounded below: a null at -60 dB would collapse
to the origin and produce degenerate spikes. Because the contract
carries magnitudes rather than radii, changing the floor rebuilds the
geometry locally with no server round-trip.

Colour is mapped from `magnitudeDb` against `rangeDb`, not from the
radius, so the colour scale stays physically readable when the floor
moves.

## Coordinate frame

Geometry is built in the physical antenna frame (Z-up), exactly as the
contract defines it. Three.js is Y-up, so the conversion is applied as a
-90 degree rotation about X on a container `Object3D`, never baked into
vertex data. This keeps the mesh export consistent with the contract and
comparable against MATLAB and HFSS references.

## Exports

- **PNG snapshot** (RF-07): the current canvas view.
- **Mesh JSON** (RF-08): the derived buffer — positions, indices and
  magnitudes in antenna coordinates — for external reuse (CP-05,
  CP-06). This is an output format only; no service consumes it.

## Development

```bash
pnpm install          # from the repository root
pnpm --filter client dev
pnpm --filter client test
pnpm --filter client build
```
