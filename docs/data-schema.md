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

## Open items (not yet defined)

- Exact trigger rule for populating `computed.directivityDb` and
  `computed.efficiency` (which `metadata.antennaType` values are
  supported, and what reference value must be present).
- Versioning strategy for this schema if it needs to change after the
  API is in use (e.g., a `schemaVersion` field).

## Shape

See the root [README.md](../README.md#unified-data-contract) for the
current JSON example. This file is where schema decisions are recorded
as they are made; the README holds the illustrative example.
