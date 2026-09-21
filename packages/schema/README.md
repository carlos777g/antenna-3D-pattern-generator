# Schema (shared data contract)

TypeScript types and a runtime validator for the unified data contract
defined in [docs/data-schema.md](../../docs/data-schema.md), imported by
both `packages/client` and `packages/server` so the two cannot drift
from the contract silently.

The contract document is the source of truth. This package follows it;
it never defines schema on its own.

## Contents

- `src/contract.ts` — types for the session document, `views[].pattern`
  and `pattern3d`.
- `src/validatePattern3d.ts` — runtime validation of a `pattern3d`
  block: axis consistency, finite magnitudes, constant pole rows.

## Usage

```ts
import { validatePattern3d, type Pattern3d } from "schema";
```
