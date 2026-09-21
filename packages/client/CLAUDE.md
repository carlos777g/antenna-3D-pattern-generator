# CLAUDE.md — packages/client

Additive to the root [CLAUDE.md](../../CLAUDE.md); must not contradict
it. Read [README.md](./README.md) for the render pipeline before
changing anything in `src/core`.

## Language and types

TypeScript with `"strict": true`. No new `.js` or `.jsx` files, and no
`any` used to escape a contract type — the point of `packages/schema` is
that the compiler catches drift from `docs/data-schema.md`.

All comments and identifiers in English, including scratch code.

## Module boundaries

`core/GeometryBuilder.ts`, `core/ColorMapper.ts` and
`core/radiusMapping.ts` are pure: data in, data out, no Three.js
renderer access, no React, no `window`. That is what makes them
testable without a GPU, so keep it that way.

`core/SceneManager.ts` owns WebGL and is deliberately thin, because it
cannot be unit tested. Logic that could live in a pure module does not
belong here.

React components contain no mathematics. A component that computes a
radius, a colour or an angle is a boundary violation.

## Hard rules

- **No dB arithmetic.** dB values are mapped, never averaged, summed or
  multiplied. Combining two dB quantities as if they were linear ratios
  is a bug, not a rounding concern.
- **Index buffers use `Uint32Array` explicitly.** At 1 degree the mesh
  has 65 160 vertices, which fits `Uint16` by 376 positions. Any future
  resolution change would overflow silently.
- **Do not duplicate the seam column.** `phi = 359` closes against
  `phi = 0` through the index buffer.
- **Geometry stays in the Z-up antenna frame.** The Y-up conversion is a
  rotation on the container `Object3D` in `SceneManager`. Never rotate
  the vertex data.
- **Validate before building.** A `pattern3d` that fails
  `validatePattern3d` surfaces a typed error in the UI. A malformed grid
  is never rendered as if it were a valid pattern.
- **Label the symmetry assumption.** When `symmetryAssumption` is
  `"axial"`, the UI says so wherever the pattern is shown. It is a
  simplification, not an equivalent-accuracy result.

## No reconstruction here

Interpolation, symmetry inference and analytic expression evaluation
belong to `python/reconstruction-service`. If a task seems to require
reconstruction mathematics in the client, the contract is wrong — fix
`docs/data-schema.md` instead.

## Testing

Vitest. `GeometryBuilder`, `ColorMapper` and `radiusMapping` have real
assertions covering vertex count, pole collapse, seam closure, radius
monotonicity and index bounds. Ad-hoc visual inspection in the browser
is useful but is not a substitute.
