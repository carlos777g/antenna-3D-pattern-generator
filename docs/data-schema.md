# Unified Data Contract

Source of truth for the JSON shape shared across `packages/server` and
`python/reconstruction-service`. Any change here must be reflected in
both, and in `packages/schema` if that package exists.

## Fixed parameters

- Angular resolution: **1 degree**, fixed at ingestion. `pattern` arrays
  cover 0-359 degrees in 1-degree steps.
- Field naming: camelCase in the contract (`angleDeg`, `magnitudeDb`,
  `sourceType`, etc.), regardless of the naming convention used
  internally by either service (e.g., Python internals may stay
  snake_case; the FastAPI response layer is responsible for the
  camelCase mapping at the boundary).

## Schema versioning

Every session document carries `"schemaVersion": 1`. A consumer that
reads a version it does not recognize rejects the payload rather than
guessing at the shape.

## 3D pattern block (`pattern3d`)

Present once reconstruction has run; absent before that. It sits
alongside `views` in the same session document.

```json
"pattern3d": {
  "thetaDeg": { "start": 0, "stop": 180, "stepDeg": 1, "count": 181 },
  "phiDeg":   { "start": 0, "stop": 359, "stepDeg": 1, "count": 360 },
  "magnitudeDb": [0.0, -0.1, "... 65160 values ..."],
  "rangeDb": { "min": -38.4, "max": 0.0 },
  "symmetryAssumption": "axial"
}
```

- **Angular frame.** `thetaDeg` is the polar angle from `+Z`; `phiDeg`
  is the azimuth from `+X` in the `XY` plane. This is the physical
  antenna frame, matching `docs/theory.md` and the `XY`/`XZ`/`YZ`
  values of `views[].plane`. The contract never refers to renderer
  axes; a Y-up renderer converts on its own side.
- **Ordering.** Row-major with theta as the outer index: the value at
  `(i, j)` is `magnitudeDb[i * phiDeg.count + j]`, where `theta = i`
  and `phi = j` degrees. One flat array, not a nested one, so it copies
  straight into a typed array.
- **Poles.** The `theta = 0` and `theta = 180` rows must each hold 360
  identical values. A consumer that receives a non-constant pole row
  rejects the payload.
- **Seam.** `phi = 359` closes against `phi = 0`. Column 0 is **not**
  duplicated at the end of a row; the consumer closes the ring in its
  index buffer. Duplicating it produces a visible crack or shading seam.
- **Magnitude.** Finite dB normalized so the maximum is `0`. No `null`,
  `NaN` or `-Infinity`; the service clamps at its extraction floor
  before emitting.
- **`rangeDb`.** Precomputed minimum and maximum so a consumer can build
  a colour scale without scanning 65 160 values. `max` is `0` by
  construction, and is carried explicitly so consumers read it instead
  of hardcoding the assumption.
- **`symmetryAssumption`.** `"axial"` for `revolution`, `"none"` for
  `patent`. It exists so a consumer can label a `revolution` result with
  its simplifying assumption, as required by
  `python/reconstruction-service/CLAUDE.md`.

The contract deliberately carries no `x`/`y`/`z`, no index buffer, no
colours and no radii. Those are derived by the renderer, because the
dB-to-radius mapping is a visualization decision and baking it into
persisted data would freeze the dynamic-range floor.

## Open items (not yet defined)

- Exact trigger rule for populating `computed.directivityDb` and
  `computed.efficiency` (which `metadata.antennaType` values are
  supported, and what reference value must be present).

## Shape

See the root [README.md](../README.md#unified-data-contract) for the
current JSON example. This file is where schema decisions are recorded
as they are made; the README holds the illustrative example.
