# Client 3D Pattern Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the `pattern3d` contract in documentation and make `packages/client` render it as an interactive Three.js radiation pattern with PNG and mesh-JSON export.

**Architecture:** The reconstruction service emits a 1-degree spherical grid of dB magnitudes (`pattern3d`). `packages/schema` owns the TypeScript types and a runtime validator shared by client and server. The client derives all geometry locally: pure functions map dB to radius and to color, build a `BufferGeometry` with a wrapped seam, and hand it to a thin `SceneManager` that applies the Z-up-to-Y-up rotation on a container `Object3D`. Nothing in the client performs reconstruction mathematics.

**Tech Stack:** TypeScript (strict), React 19, Three.js 0.183, Vite 8, Tailwind 4, Vitest, pnpm workspaces.

**Spec:** [`docs/superpowers/specs/2026-09-20-3d-pattern-contract-design.md`](../specs/2026-09-20-3d-pattern-contract-design.md)

## Global Constraints

- All code, identifiers, comments and technical documentation are in **English**, with no exceptions — including scratch and debug code.
- `packages/client` and `packages/server` are **TypeScript with `"strict": true`**. No new `.js` or `.jsx` files in either package.
- **pnpm only.** Never run `npm` or `yarn`; never create `package-lock.json` or `yarn.lock`.
- A schema change is made in **`docs/data-schema.md` first**, then propagated to `packages/server` and `python/reconstruction-service`.
- **dB values are mapped, never averaged and never multiplied.** Any arithmetic combining two dB quantities as linear ratios is a bug.
- Angular resolution is fixed at **1 degree**. `thetaDeg` spans 0-180 (181 samples), `phiDeg` spans 0-359 (360 samples).
- Contract angles are in the **physical Z-up frame**: `thetaDeg` from `+Z`, `phiDeg` from `+X` in the `XY` plane. The Three.js Y-up conversion happens on a container object, never baked into vertex data.
- Magnitudes are finite dB normalized so the maximum is `0`. No `null`, `NaN` or `-Infinity`.
- A module without a `tests/` directory containing real assertions is **not done**.
- `revolution` results must be labeled with their symmetry assumption wherever they are surfaced.

---

### Task 1: Land the `pattern3d` contract in documentation

No code. The root `CLAUDE.md` requires the schema to change in `docs/data-schema.md` before anything else reads it, so this task gates every task that follows.

**Files:**
- Modify: `docs/data-schema.md`
- Modify: `README.md` (Unified Data Contract section)
- Modify: `packages/client/README.md` (currently the Vite placeholder)
- Modify: `packages/client/CLAUDE.md` (currently empty)
- Modify: `packages/schema/README.md`
- Modify: `packages/server/README.md`
- Modify: `python/reconstruction-service/CLAUDE.md`
- Modify: `python/reconstruction-service/README.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the normative field names every later task uses — `pattern3d`, `thetaDeg`, `phiDeg`, `stepDeg`, `count`, `magnitudeDb`, `rangeDb`, `symmetryAssumption`, `schemaVersion`.

- [ ] **Step 1: Add the contract block to `docs/data-schema.md`**

Replace the "Open items (not yet defined)" section's versioning bullet and add a new section after "Fixed parameters":

````markdown
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
````

- [ ] **Step 2: Remove the now-closed versioning open item**

In `docs/data-schema.md`, delete this bullet from "Open items (not yet defined)":

```markdown
- Versioning strategy for this schema if it needs to change after the
  API is in use (e.g., a `schemaVersion` field).
```

Leave the `computed.directivityDb` bullet in place — it is still open.

- [ ] **Step 3: Update the root README contract example**

In `README.md`, in the Unified Data Contract JSON block, add `"schemaVersion": 1` as the first field and the `pattern3d` block between `views` and `computed`. Then add these bullets to the Notes list below it:

```markdown
- `pattern3d` holds the reconstructed 3D grid and is absent until
  reconstruction has run. Its full rules (angular frame, row-major
  ordering, pole and seam constraints) are in `docs/data-schema.md`.
- `schemaVersion` is `1`. A consumer that reads an unknown version
  rejects the payload rather than guessing at the shape.
```

- [ ] **Step 4: Write `packages/client/README.md`**

Replace the whole file:

````markdown
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
````

- [ ] **Step 5: Write `packages/client/CLAUDE.md`**

Replace the whole file:

````markdown
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
````

- [ ] **Step 6: Confirm `packages/schema`**

Replace `packages/schema/README.md`:

```markdown
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
```

- [ ] **Step 7: Note the server's role**

Append to `packages/server/README.md`:

```markdown
## Relationship to the 3D contract

The server validates and forwards the `pattern3d` block; it computes no
geometry and no reconstruction. Validation uses the shared validator in
`packages/schema`, so the server and the client reject the same
malformed payloads for the same reasons.
```

- [ ] **Step 8: Give the Python service its output target**

In `python/reconstruction-service/CLAUDE.md`, in the "3D reconstruction algorithms (not yet implemented)" section, add to the "Hard constraints once that work starts" list:

```markdown
- **Emit the `pattern3d` block defined in `docs/data-schema.md`** — a
  1-degree spherical grid (181 x 360), row-major with theta as the outer
  index, in the physical Z-up frame, with constant pole rows, no
  duplicated seam column, finite dB normalized to a 0 dB maximum, plus
  `rangeDb` and `symmetryAssumption`. That document is the contract; do
  not invent a mesh shape here.
```

- [ ] **Step 9: Delete the stale angular-range note**

In `python/reconstruction-service/README.md`, remove the "Angular range wording" paragraph. The root README was corrected to "0-359" in commit `977f122`, so the contradiction it reports no longer exists.

- [ ] **Step 10: Verify consistency**

Run:

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
grep -rn "packages/api\|packages/web" README.md CLAUDE.md docs/*.md packages/*/README.md packages/*/CLAUDE.md
grep -rn "0-360\|0–360" README.md docs/data-schema.md python/reconstruction-service/README.md
grep -c "pattern3d" docs/data-schema.md README.md packages/client/README.md packages/client/CLAUDE.md
```

Expected: the first two greps print nothing; the third prints a non-zero count for each of the four files.

- [ ] **Step 11: Commit**

```bash
git add docs/data-schema.md README.md packages/client/README.md packages/client/CLAUDE.md packages/schema/README.md packages/server/README.md python/reconstruction-service/CLAUDE.md python/reconstruction-service/README.md
git commit -m "docs(schema): define the pattern3d 3D contract and propagate it"
```

---

### Task 2: pnpm workspace, strict TypeScript and Vitest

The repository root has **no `pnpm-workspace.yaml`**, despite the README describing one, and `packages/client` carries its own `pnpm-lock.yaml`. So `packages/client` cannot import `packages/schema` today. This task fixes that and converts the existing JavaScript prototype, which currently violates two hard constraints (JavaScript instead of TypeScript, Spanish comments).

**Files:**
- Create: `pnpm-workspace.yaml`
- Create: `packages/client/tsconfig.json`
- Create: `packages/client/tsconfig.node.json`
- Create: `packages/client/vitest.config.ts`
- Create: `packages/client/src/vite-env.d.ts`
- Rename: `packages/client/vite.config.js` → `packages/client/vite.config.ts`
- Rename: `packages/client/src/main.jsx` → `main.tsx`, `App.jsx` → `App.tsx`
- Rename: `packages/client/src/components/Viewport.jsx` → `Viewport.tsx`, `ControlPanel.jsx` → `ControlPanel.tsx`
- Rename: `packages/client/src/core/{SceneManager,ColorMapper,GeometryBuilder}.js` → `.ts`
- Rename: `packages/client/src/hooks/useThreeScene.js` → `useThreeScene.ts`
- Delete: `packages/client/src/core/figureService.js`, `packages/client/src/core/figures.json`, `packages/client/pnpm-lock.yaml`
- Modify: `packages/client/package.json`, `packages/client/eslint.config.js`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a workspace where `packages/client` resolves `schema` by name; `pnpm --filter client test` runs Vitest; every `src` file is `.ts`/`.tsx` with English comments.

`figureService.js` and `figures.json` are deleted rather than converted: nothing imports them, and they `fetch("./figures.json")` a file that is not in `public/`. The real data path is the REST API, which Task 7 stubs with a fixture.

- [ ] **Step 1: Create the workspace file**

`pnpm-workspace.yaml` at the repository root:

```yaml
packages:
  - "packages/*"
```

- [ ] **Step 2: Remove the stray package lockfile**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
rm packages/client/pnpm-lock.yaml
```

The workspace lockfile belongs at the root. Do not run `npm` or `yarn` at any point.

- [ ] **Step 3: Add TypeScript and Vitest dependencies**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
pnpm --filter client add -D typescript typescript-eslint vitest @vitest/coverage-v8
```

- [ ] **Step 4: Create `packages/client/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`noUncheckedIndexedAccess` matters here: the geometry code indexes flat arrays constantly, and it forces those reads to be checked rather than assumed.

- [ ] **Step 5: Create `packages/client/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["vite.config.ts", "vitest.config.ts"]
}
```

- [ ] **Step 6: Create `packages/client/src/vite-env.d.ts`**

```ts
/// <reference types="vite/client" />
```

- [ ] **Step 7: Rename `vite.config.js` to `vite.config.ts`**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator/packages/client
git mv vite.config.js vite.config.ts
```

The existing contents compile as-is; no edit is needed.

- [ ] **Step 8: Create `packages/client/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  test: {
    // The pure core modules need no DOM; SceneManager is not unit tested
    // because it requires a GPU.
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});
```

- [ ] **Step 9: Rename the source files**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator/packages/client/src
git mv main.jsx main.tsx
git mv App.jsx App.tsx
git mv components/Viewport.jsx components/Viewport.tsx
git mv components/ControlPanel.jsx components/ControlPanel.tsx
git mv core/SceneManager.js core/SceneManager.ts
git mv core/ColorMapper.js core/ColorMapper.ts
git mv core/GeometryBuilder.js core/GeometryBuilder.ts
git mv hooks/useThreeScene.js hooks/useThreeScene.ts
git rm core/figureService.js core/figures.json
```

- [ ] **Step 10: Translate comments and add types**

Every renamed file keeps its current behaviour; only comments (Spanish to English) and type annotations change. Three concrete examples of the required shape — apply the same treatment to the remaining files.

`src/components/Viewport.tsx`:

```tsx
import { useRef } from "react";
import { useThreeScene } from "../hooks/useThreeScene";
import type { SphereParams } from "../core/GeometryBuilder";

/**
 * Viewport
 * Single responsibility: render the <canvas> that Three.js draws into.
 * Contains no Three.js logic - that belongs to the hook.
 */
export function Viewport({ params }: { params: SphereParams }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useThreeScene(canvasRef, params);

  return (
    <canvas
      ref={canvasRef}
      className="flex-1 block cursor-grab active:cursor-grabbing"
    />
  );
}
```

`src/core/GeometryBuilder.ts` (the demo sphere stays until Task 5 replaces it):

```ts
import * as THREE from "three";
import { ColorMapper } from "./ColorMapper";

export type ColorMode = "height" | "distance" | "latitude";

export interface SphereParams {
  radius: number;
  widthSeg: number;
  heightSeg: number;
  colorMode: ColorMode;
  wireframe: boolean;
}

/**
 * GeometryBuilder
 * Single responsibility: build Three.js geometry from parameters.
 * buildSphere is a development placeholder; Task 5 adds
 * buildRadiationPattern, which is the real entry point.
 */
export class GeometryBuilder {
  static buildSphere(params: SphereParams): THREE.Mesh {
    const { radius, widthSeg, heightSeg, colorMode, wireframe } = params;

    const geometry = new THREE.SphereGeometry(radius, widthSeg, heightSeg);
    ColorMapper.applyToGeometry(geometry, colorMode, radius);

    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      wireframe,
      shininess: 80,
    });

    return new THREE.Mesh(geometry, material);
  }
}
```

The `colorMode` values change from `"altura" | "distancia" | "latitud"` to `"height" | "distance" | "latitude"` — the language rule covers string literals that act as identifiers. Update the matching `case` labels in `ColorMapper._normalize`, the `colorModes` array and its labels in `ControlPanel.tsx`, and `INITIAL_PARAMS.colorMode` in `App.tsx`.

`src/core/SceneManager.ts` needs explicit field declarations for `strict` to accept it — TypeScript does not infer class fields from constructor assignment. Add these above the constructor, and annotate the constructor as `constructor(canvas: HTMLCanvasElement)`:

```ts
  private canvas: HTMLCanvasElement;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  private mesh: THREE.Mesh | null;
  private animId: number | null;
  private _orbit!: { active: boolean; x: number; y: number; rotX: number };
```

`renderer` is public because Task 7's PNG export reads it. `_orbit` is disposed of in Task 6, so it keeps the definite-assignment assertion rather than earning a refactor now.

`src/App.tsx` header comment:

```tsx
/**
 * App
 * Single responsibility: state orchestration.
 *
 * - Owns the `params` state (geometry and colour parameters)
 * - Passes params to Viewport (for Three.js)
 * - Passes params + onChange to ControlPanel (for the UI)
 *
 * Rule: App never imports Three.js directly.
 */
```

Also translate the visible Spanish UI strings in `ControlPanel.tsx` (`PARÁMETROS THREE.JS`, `Radio`, and the colour-mode labels) to English.

- [ ] **Step 11: Update `package.json` scripts**

Add to `packages/client/package.json`:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "test": "vitest run",
  "test:watch": "vitest",
  "typecheck": "tsc --noEmit",
  "preview": "vite preview"
}
```

- [ ] **Step 12: Update `eslint.config.js` for TypeScript**

```js
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 'latest',
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
    },
  },
])
```

- [ ] **Step 13: Verify the toolchain**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
pnpm install
pnpm --filter client typecheck
pnpm --filter client lint
pnpm --filter client build
```

Expected: all four succeed. `typecheck` passing is the real gate — it proves the migration is complete rather than partially annotated.

Then confirm no Spanish survives in source:

```bash
grep -rniE "responsabilidad|única|párametros|parámetros|figura|próximo|escena|radio:|altura|distancia|latitud" packages/client/src
```

Expected: no output.

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "refactor(client): migrate the prototype to strict TypeScript and set up the pnpm workspace"
```

---

### Task 3: Contract types and validator in `packages/schema`

**Files:**
- Create: `packages/schema/package.json`
- Create: `packages/schema/tsconfig.json`
- Create: `packages/schema/src/contract.ts`
- Create: `packages/schema/src/validatePattern3d.ts`
- Create: `packages/schema/src/index.ts`
- Test: `packages/schema/tests/validatePattern3d.test.ts`

**Interfaces:**
- Consumes: the field names fixed by Task 1.
- Produces:
  - `type Pattern3d`, `type AngularAxis`, `type SymmetryAssumption`, `type SessionDocument`
  - `class Pattern3dError extends Error` with a `code: Pattern3dErrorCode` property
  - `type Pattern3dErrorCode = "AXIS_INVALID" | "LENGTH_MISMATCH" | "NON_FINITE" | "POLE_NOT_CONSTANT"`
  - `function validatePattern3d(pattern: Pattern3d): void` — throws `Pattern3dError`, returns nothing on success

The validator lives here rather than in the client so the server rejects the same payloads for the same reasons.

- [ ] **Step 1: Create the package manifest**

`packages/schema/package.json`:

```json
{
  "name": "schema",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": { ".": "./src/index.ts" },
  "scripts": {
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.9.0",
    "vitest": "^3.2.0"
  }
}
```

Source is exported directly rather than built: both consumers are bundled by Vite, so a build step would add a stale-artifact failure mode for no gain.

- [ ] **Step 2: Create `packages/schema/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src", "tests"]
}
```

- [ ] **Step 3: Write the failing test**

`packages/schema/tests/validatePattern3d.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { validatePattern3d, Pattern3dError, type Pattern3d } from "../src/index";

const THETA_COUNT = 181;
const PHI_COUNT = 360;

/** An isotropic pattern: every direction at 0 dB. Always valid. */
function makeValidPattern(): Pattern3d {
  return {
    thetaDeg: { start: 0, stop: 180, stepDeg: 1, count: THETA_COUNT },
    phiDeg: { start: 0, stop: 359, stepDeg: 1, count: PHI_COUNT },
    magnitudeDb: new Array(THETA_COUNT * PHI_COUNT).fill(0),
    rangeDb: { min: 0, max: 0 },
    symmetryAssumption: "axial",
  };
}

describe("validatePattern3d", () => {
  it("accepts a well-formed pattern", () => {
    expect(() => validatePattern3d(makeValidPattern())).not.toThrow();
  });

  it("rejects a magnitude array whose length disagrees with the axis counts", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb = pattern.magnitudeDb.slice(0, -1);

    expect(() => validatePattern3d(pattern)).toThrow(Pattern3dError);
    try {
      validatePattern3d(pattern);
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("LENGTH_MISMATCH");
    }
  });

  it("rejects a non-finite magnitude", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[5000] = Number.NEGATIVE_INFINITY;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("NON_FINITE");
    }
  });

  it("rejects a non-constant theta=0 pole row", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[7] = -3;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("POLE_NOT_CONSTANT");
    }
  });

  it("rejects a non-constant theta=180 pole row", () => {
    const pattern = makeValidPattern();
    pattern.magnitudeDb[(THETA_COUNT - 1) * PHI_COUNT + 12] = -3;

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("POLE_NOT_CONSTANT");
    }
  });

  it("rejects an axis whose count disagrees with start, stop and step", () => {
    const pattern = makeValidPattern();
    pattern.thetaDeg = { start: 0, stop: 180, stepDeg: 1, count: 180 };

    try {
      validatePattern3d(pattern);
      throw new Error("expected validatePattern3d to throw");
    } catch (error) {
      expect((error as Pattern3dError).code).toBe("AXIS_INVALID");
    }
  });
});
```

- [ ] **Step 4: Run the test to verify it fails**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
pnpm --filter schema test
```

Expected: FAIL — cannot resolve `../src/index`.

- [ ] **Step 5: Write `packages/schema/src/contract.ts`**

```ts
/**
 * Types for the unified data contract.
 * `docs/data-schema.md` is the source of truth; this file follows it and
 * never defines schema on its own.
 */

export type SourceType = "image" | "analytic";
export type Plane = "XY" | "XZ" | "YZ";
export type ReconstructionMethod = "revolution" | "patent";

/** "axial" for the revolution method, "none" for the patent method. */
export type SymmetryAssumption = "axial" | "none";

/** An inclusive angular axis sampled at a fixed step, in degrees. */
export interface AngularAxis {
  start: number;
  stop: number;
  stepDeg: number;
  count: number;
}

export interface PatternSample {
  angleDeg: number;
  magnitudeDb: number;
}

export interface PatternView {
  plane: Plane;
  pattern: PatternSample[];
}

/**
 * The reconstructed 3D pattern: a uniform spherical grid of magnitudes in
 * the physical Z-up frame. `magnitudeDb` is row-major with theta as the
 * outer index, so the value at (i, j) is magnitudeDb[i * phiDeg.count + j].
 */
export interface Pattern3d {
  thetaDeg: AngularAxis;
  phiDeg: AngularAxis;
  magnitudeDb: number[];
  rangeDb: { min: number; max: number };
  symmetryAssumption: SymmetryAssumption;
}

export interface SessionDocument {
  schemaVersion: 1;
  sourceType: SourceType;
  plane: Plane;
  metadata: {
    provider: string | null;
    antennaType: string | null;
    polarization: string | null;
  };
  reconstructionMethod: ReconstructionMethod | null;
  views: PatternView[];
  /** Absent until reconstruction has run. */
  pattern3d?: Pattern3d;
  computed: {
    directivityDb: number | null;
    efficiency: number | null;
  };
}
```

- [ ] **Step 6: Write `packages/schema/src/validatePattern3d.ts`**

```ts
import type { AngularAxis, Pattern3d } from "./contract";

export type Pattern3dErrorCode =
  | "AXIS_INVALID"
  | "LENGTH_MISMATCH"
  | "NON_FINITE"
  | "POLE_NOT_CONSTANT";

export class Pattern3dError extends Error {
  constructor(
    public readonly code: Pattern3dErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "Pattern3dError";
  }
}

function validateAxis(axis: AngularAxis, name: string): void {
  if (axis.stepDeg <= 0) {
    throw new Pattern3dError(
      "AXIS_INVALID",
      `${name}.stepDeg must be positive, got ${axis.stepDeg}`,
    );
  }

  const expected = Math.round((axis.stop - axis.start) / axis.stepDeg) + 1;
  if (axis.count !== expected) {
    throw new Pattern3dError(
      "AXIS_INVALID",
      `${name}.count is ${axis.count} but start/stop/stepDeg imply ${expected}`,
    );
  }
}

/**
 * Validates a pattern3d block against the rules in docs/data-schema.md.
 * Throws Pattern3dError on the first violation; returns nothing on success.
 *
 * A malformed grid must never reach geometry construction: it renders as a
 * plausible-looking but wrong pattern, which is worse than an error.
 */
export function validatePattern3d(pattern: Pattern3d): void {
  const { thetaDeg, phiDeg, magnitudeDb } = pattern;

  validateAxis(thetaDeg, "thetaDeg");
  validateAxis(phiDeg, "phiDeg");

  const expectedLength = thetaDeg.count * phiDeg.count;
  if (magnitudeDb.length !== expectedLength) {
    throw new Pattern3dError(
      "LENGTH_MISMATCH",
      `magnitudeDb has ${magnitudeDb.length} values, expected ` +
        `${expectedLength} (${thetaDeg.count} x ${phiDeg.count})`,
    );
  }

  for (let i = 0; i < magnitudeDb.length; i += 1) {
    const value = magnitudeDb[i];
    if (value === undefined || !Number.isFinite(value)) {
      throw new Pattern3dError(
        "NON_FINITE",
        `magnitudeDb[${i}] is ${String(value)}; every magnitude must be finite`,
      );
    }
  }

  // Both pole rows collapse to a single point in space, so every value in
  // them must agree. A non-constant pole row tears the mesh open.
  for (const rowIndex of [0, thetaDeg.count - 1]) {
    const offset = rowIndex * phiDeg.count;
    const reference = magnitudeDb[offset];
    for (let j = 1; j < phiDeg.count; j += 1) {
      if (magnitudeDb[offset + j] !== reference) {
        throw new Pattern3dError(
          "POLE_NOT_CONSTANT",
          `pole row theta=${rowIndex * thetaDeg.stepDeg} is not constant: ` +
            `index ${offset + j} is ${String(magnitudeDb[offset + j])}, ` +
            `expected ${String(reference)}`,
        );
      }
    }
  }
}
```

- [ ] **Step 7: Write `packages/schema/src/index.ts`**

```ts
export * from "./contract";
export * from "./validatePattern3d";
```

- [ ] **Step 8: Run the tests to verify they pass**

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator
pnpm install
pnpm --filter schema test
pnpm --filter schema typecheck
```

Expected: 6 tests PASS, typecheck clean.

- [ ] **Step 9: Add the dependency from the client**

```bash
pnpm --filter client add schema@workspace:*
```

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(schema): add contract types and pattern3d validation"
```

---

### Task 4: dB-to-radius mapping and geometry construction

**Files:**
- Create: `packages/client/src/core/radiusMapping.ts`
- Modify: `packages/client/src/core/GeometryBuilder.ts`
- Create: `packages/client/tests/radiusMapping.test.ts`
- Create: `packages/client/tests/fixtures/makePattern3d.ts`
- Create: `packages/client/tests/GeometryBuilder.test.ts`

**Interfaces:**
- Consumes: `Pattern3d`, `validatePattern3d`, `Pattern3dError` from `schema` (Task 3).
- Produces:
  - `const DEFAULT_FLOOR_DB = -40`
  - `function magnitudeToRadius(magnitudeDb: number, floorDb: number): number`
  - `interface RadiationPatternOptions { floorDb?: number }`
  - `GeometryBuilder.buildRadiationPattern(pattern: Pattern3d, options?: RadiationPatternOptions): THREE.BufferGeometry` — returns geometry with `position`, `normal` and `index` set, in the Z-up antenna frame, with no colour attribute (Task 5 adds that)
  - `makePattern3d(magnitudeAt: (thetaDeg: number, phiDeg: number) => number): Pattern3d` test helper

`buildRadiationPattern` returns a `BufferGeometry`, not a `Mesh`: material choice belongs to `SceneManager`, and geometry alone is what the tests can assert on.

- [ ] **Step 1: Write the failing radius test**

`packages/client/tests/radiusMapping.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { magnitudeToRadius, DEFAULT_FLOOR_DB } from "../src/core/radiusMapping";

describe("magnitudeToRadius", () => {
  it("maps the 0 dB maximum to the unit radius", () => {
    expect(magnitudeToRadius(0, -40)).toBe(1);
  });

  it("maps the floor to zero", () => {
    expect(magnitudeToRadius(-40, -40)).toBe(0);
  });

  it("clamps anything below the floor to zero", () => {
    expect(magnitudeToRadius(-60, -40)).toBe(0);
  });

  it("clamps anything above the maximum to one", () => {
    expect(magnitudeToRadius(3, -40)).toBe(1);
  });

  it("is monotonically increasing in magnitude", () => {
    expect(magnitudeToRadius(-10, -40)).toBeGreaterThan(
      magnitudeToRadius(-20, -40),
    );
  });

  it("maps the midpoint of the range to a half radius", () => {
    expect(magnitudeToRadius(-20, -40)).toBeCloseTo(0.5, 10);
  });

  it("defaults the floor to -40 dB", () => {
    expect(DEFAULT_FLOOR_DB).toBe(-40);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pnpm --filter client test radiusMapping
```

Expected: FAIL — cannot resolve `../src/core/radiusMapping`.

- [ ] **Step 3: Write `packages/client/src/core/radiusMapping.ts`**

```ts
/**
 * Default dynamic-range floor, in dB.
 *
 * A floor is required because dB is unbounded below: a null at -60 dB would
 * collapse to the origin and produce degenerate spikes. -40 dB keeps the
 * main lobe and the first sidelobes legible for typical datasheet patterns.
 */
export const DEFAULT_FLOOR_DB = -40;

/**
 * Maps a magnitude in dB to a normalized radius in [0, 1].
 *
 * The contract normalizes magnitudes so the maximum is 0 dB, so the mapping
 * runs from `floorDb` to 0. This is a visualization decision, not a physical
 * one, which is why it lives in the client and not in the contract.
 *
 * Note this maps a dB value; it never combines two dB values arithmetically.
 */
export function magnitudeToRadius(
  magnitudeDb: number,
  floorDb: number,
): number {
  const span = 0 - floorDb;
  const t = (magnitudeDb - floorDb) / span;
  return Math.min(1, Math.max(0, t));
}
```

- [ ] **Step 4: Run it to verify it passes**

```bash
pnpm --filter client test radiusMapping
```

Expected: 7 tests PASS.

- [ ] **Step 5: Write the test fixture helper**

`packages/client/tests/fixtures/makePattern3d.ts`:

```ts
import type { Pattern3d } from "schema";

export const THETA_COUNT = 181;
export const PHI_COUNT = 360;

/**
 * Builds a valid pattern3d from a magnitude function over (theta, phi) in
 * degrees. Pole rows are forced constant by evaluating them at phi = 0, so
 * a caller cannot accidentally produce an invalid fixture.
 *
 * This is a test helper, not a reconstruction: the client never computes
 * pattern data in production code.
 */
export function makePattern3d(
  magnitudeAt: (thetaDeg: number, phiDeg: number) => number,
): Pattern3d {
  const magnitudeDb: number[] = new Array(THETA_COUNT * PHI_COUNT);
  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;

  for (let i = 0; i < THETA_COUNT; i += 1) {
    const isPole = i === 0 || i === THETA_COUNT - 1;
    for (let j = 0; j < PHI_COUNT; j += 1) {
      const value = magnitudeAt(i, isPole ? 0 : j);
      magnitudeDb[i * PHI_COUNT + j] = value;
      if (value < min) min = value;
      if (value > max) max = value;
    }
  }

  return {
    thetaDeg: { start: 0, stop: 180, stepDeg: 1, count: THETA_COUNT },
    phiDeg: { start: 0, stop: 359, stepDeg: 1, count: PHI_COUNT },
    magnitudeDb,
    rangeDb: { min, max },
    symmetryAssumption: "axial",
  };
}

/** Isotropic: every direction at the 0 dB maximum, so the mesh is a unit sphere. */
export const isotropic = (): Pattern3d => makePattern3d(() => 0);
```

- [ ] **Step 6: Write the failing geometry test**

`packages/client/tests/GeometryBuilder.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { Pattern3dError } from "schema";
import { GeometryBuilder } from "../src/core/GeometryBuilder";
import {
  makePattern3d,
  isotropic,
  THETA_COUNT,
  PHI_COUNT,
} from "./fixtures/makePattern3d";

describe("GeometryBuilder.buildRadiationPattern", () => {
  it("emits one vertex per grid point, with no duplicated seam column", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.attributes.position?.count).toBe(THETA_COUNT * PHI_COUNT);
  });

  it("emits two triangles per grid cell", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.getIndex()?.count).toBe((THETA_COUNT - 1) * PHI_COUNT * 2 * 3);
  });

  it("uses a 32-bit index buffer", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());

    expect(geometry.getIndex()?.array).toBeInstanceOf(Uint32Array);
  });

  it("keeps every index inside the vertex range", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const index = geometry.getIndex();
    const vertexCount = geometry.attributes.position?.count ?? 0;

    let max = -1;
    let min = Number.POSITIVE_INFINITY;
    for (let i = 0; i < (index?.count ?? 0); i += 1) {
      const value = index?.getX(i) ?? -1;
      if (value > max) max = value;
      if (value < min) min = value;
    }

    expect(min).toBe(0);
    expect(max).toBe(vertexCount - 1);
  });

  it("closes the seam: the last phi column references column 0", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const index = geometry.getIndex();

    // The first cell of the last column is (i=0, j=359). Its triangles must
    // reference vertex (i=0, j=0) = index 0 and (i=1, j=0) = index PHI_COUNT.
    const firstCellOfLastColumn = (PHI_COUNT - 1) * 6;
    const triangleIndices = new Set<number>();
    for (let k = 0; k < 6; k += 1) {
      triangleIndices.add(index?.getX(firstCellOfLastColumn + k) ?? -1);
    }

    expect(triangleIndices.has(0)).toBe(true);
    expect(triangleIndices.has(PHI_COUNT)).toBe(true);
  });

  it("collapses the theta=0 pole to a single point", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;

    for (let j = 1; j < PHI_COUNT; j += 1) {
      expect(position?.getX(j)).toBeCloseTo(position?.getX(0) ?? NaN, 10);
      expect(position?.getY(j)).toBeCloseTo(position?.getY(0) ?? NaN, 10);
      expect(position?.getZ(j)).toBeCloseTo(position?.getZ(0) ?? NaN, 10);
    }
  });

  it("places an isotropic pattern on a unit sphere in the Z-up frame", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;

    // theta=0 is +Z, theta=90/phi=0 is +X, theta=90/phi=90 is +Y.
    expect(position?.getZ(0)).toBeCloseTo(1, 10);
    expect(position?.getX(90 * PHI_COUNT)).toBeCloseTo(1, 10);
    expect(position?.getY(90 * PHI_COUNT + 90)).toBeCloseTo(1, 10);
  });

  it("winds triangles so that normals point outward", () => {
    const geometry = GeometryBuilder.buildRadiationPattern(isotropic());
    const position = geometry.attributes.position;
    const normal = geometry.attributes.normal;

    // On a sphere the outward normal is parallel to the position vector.
    for (const i of [45 * PHI_COUNT + 10, 90 * PHI_COUNT + 200, 135 * PHI_COUNT]) {
      const dot =
        (position?.getX(i) ?? 0) * (normal?.getX(i) ?? 0) +
        (position?.getY(i) ?? 0) * (normal?.getY(i) ?? 0) +
        (position?.getZ(i) ?? 0) * (normal?.getZ(i) ?? 0);
      expect(dot).toBeGreaterThan(0);
    }
  });

  it("shrinks the radius as the magnitude drops", () => {
    // A pattern that falls off with theta: 0 dB at the pole, -40 dB at theta=180.
    const pattern = makePattern3d((thetaDeg) => -40 * (thetaDeg / 180));
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);
    const position = geometry.attributes.position;

    const radiusAt = (i: number) =>
      Math.hypot(
        position?.getX(i) ?? 0,
        position?.getY(i) ?? 0,
        position?.getZ(i) ?? 0,
      );

    expect(radiusAt(0)).toBeCloseTo(1, 10);
    expect(radiusAt(90 * PHI_COUNT)).toBeCloseTo(0.5, 6);
    expect(radiusAt((THETA_COUNT - 1) * PHI_COUNT)).toBeCloseTo(0, 10);
  });

  it("honours a caller-supplied floor", () => {
    const pattern = makePattern3d(() => -10);

    const withDefaultFloor = GeometryBuilder.buildRadiationPattern(pattern);
    const withTightFloor = GeometryBuilder.buildRadiationPattern(pattern, {
      floorDb: -20,
    });

    // -10 dB is 75% of the way up a -40 dB range, but only 50% of a -20 dB range.
    expect(withDefaultFloor.attributes.position?.getZ(0)).toBeCloseTo(0.75, 10);
    expect(withTightFloor.attributes.position?.getZ(0)).toBeCloseTo(0.5, 10);
  });

  it("rejects a malformed pattern instead of building geometry", () => {
    const pattern = isotropic();
    pattern.magnitudeDb[7] = -3; // breaks the constant theta=0 pole row

    expect(() => GeometryBuilder.buildRadiationPattern(pattern)).toThrow(
      Pattern3dError,
    );
  });
});
```

- [ ] **Step 7: Run it to verify it fails**

```bash
pnpm --filter client test GeometryBuilder
```

Expected: FAIL — `buildRadiationPattern is not a function`.

- [ ] **Step 8: Implement `buildRadiationPattern`**

Add to `packages/client/src/core/GeometryBuilder.ts` (keeping the existing `buildSphere` and its imports):

```ts
import { validatePattern3d, type Pattern3d } from "schema";
import { DEFAULT_FLOOR_DB, magnitudeToRadius } from "./radiusMapping";

export interface RadiationPatternOptions {
  /** Dynamic-range floor in dB; defaults to DEFAULT_FLOOR_DB. */
  floorDb?: number;
}
```

and this static method to the `GeometryBuilder` class:

```ts
  /**
   * Builds the radiation-pattern surface from a pattern3d grid.
   *
   * The result is in the physical Z-up antenna frame, exactly as the
   * contract defines it. Converting to the renderer's Y-up frame is
   * SceneManager's job, applied to a container object so the vertex data
   * stays comparable against external references.
   *
   * @throws Pattern3dError when the grid violates the contract.
   */
  static buildRadiationPattern(
    pattern: Pattern3d,
    options: RadiationPatternOptions = {},
  ): THREE.BufferGeometry {
    validatePattern3d(pattern);

    const floorDb = options.floorDb ?? DEFAULT_FLOOR_DB;
    const thetaCount = pattern.thetaDeg.count;
    const phiCount = pattern.phiDeg.count;

    const positions = new Float32Array(thetaCount * phiCount * 3);
    const degToRad = Math.PI / 180;

    for (let i = 0; i < thetaCount; i += 1) {
      const theta =
        (pattern.thetaDeg.start + i * pattern.thetaDeg.stepDeg) * degToRad;
      const sinTheta = Math.sin(theta);
      const cosTheta = Math.cos(theta);

      for (let j = 0; j < phiCount; j += 1) {
        const phi =
          (pattern.phiDeg.start + j * pattern.phiDeg.stepDeg) * degToRad;
        const vertex = i * phiCount + j;
        const r = magnitudeToRadius(pattern.magnitudeDb[vertex] ?? 0, floorDb);

        positions[vertex * 3] = r * sinTheta * Math.cos(phi);
        positions[vertex * 3 + 1] = r * sinTheta * Math.sin(phi);
        positions[vertex * 3 + 2] = r * cosTheta;
      }
    }

    // Two triangles per cell. Uint32 is explicit: 65 160 vertices fits Uint16
    // by only 376 positions, so a resolution change would overflow silently.
    const indices = new Uint32Array((thetaCount - 1) * phiCount * 6);
    let cursor = 0;

    for (let i = 0; i < thetaCount - 1; i += 1) {
      for (let j = 0; j < phiCount; j += 1) {
        // The seam closes through the modulo: column 0 is never duplicated.
        const jNext = (j + 1) % phiCount;

        const a = i * phiCount + j;
        const b = i * phiCount + jNext;
        const c = (i + 1) * phiCount + j;
        const d = (i + 1) * phiCount + jNext;

        // Winding (a, c, b) traverses +theta then +phi. For a radial surface
        // d(p)/d(theta) x d(p)/d(phi) = r^2 sin(theta) * p_hat, which points
        // outward, so this is counter-clockwise seen from outside - the
        // front face in Three.js.
        indices[cursor] = a;
        indices[cursor + 1] = c;
        indices[cursor + 2] = b;
        indices[cursor + 3] = b;
        indices[cursor + 4] = c;
        indices[cursor + 5] = d;
        cursor += 6;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setIndex(new THREE.BufferAttribute(indices, 1));
    geometry.computeVertexNormals();

    return geometry;
  }
```

- [ ] **Step 9: Run the tests to verify they pass**

```bash
pnpm --filter client test
pnpm --filter client typecheck
```

Expected: all `radiusMapping` and `GeometryBuilder` tests PASS, typecheck clean.

If the outward-normal test fails, the winding is inverted — swap `c` and `b` in the first triangle and `c` and `d` in the second, then rerun. Do not "fix" it by disabling backface culling.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(client): build radiation-pattern geometry from the pattern3d grid"
```

---

### Task 5: dB-driven vertex colouring

**Files:**
- Modify: `packages/client/src/core/ColorMapper.ts`
- Create: `packages/client/tests/ColorMapper.test.ts`

**Interfaces:**
- Consumes: `Pattern3d` from `schema`; `THREE.BufferGeometry` from Task 4.
- Produces: `ColorMapper.applyMagnitudeColors(geometry: THREE.BufferGeometry, magnitudeDb: number[], rangeDb: { min: number; max: number }): void` — sets the `color` attribute in place.

Colour comes from `magnitudeDb` against `rangeDb`, not from the radius, so the colour scale stays physically meaningful when the user moves `floorDb`. The existing `applyToGeometry` and `jet` stay for the demo sphere.

- [ ] **Step 1: Write the failing test**

`packages/client/tests/ColorMapper.test.ts`:

```ts
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pnpm --filter client test ColorMapper
```

Expected: FAIL — `applyMagnitudeColors is not a function`.

- [ ] **Step 3: Implement it**

Add to the `ColorMapper` class in `packages/client/src/core/ColorMapper.ts`:

```ts
  /**
   * Colours a geometry by magnitude in dB, scaled against the contract's
   * rangeDb.
   *
   * Colour deliberately follows the magnitude rather than the radius: the
   * radius depends on the user's dynamic-range floor, and a colour scale
   * that moved with it would stop being physically readable.
   *
   * Note this maps each dB value independently; it never combines two.
   */
  static applyMagnitudeColors(
    geometry: THREE.BufferGeometry,
    magnitudeDb: number[],
    rangeDb: { min: number; max: number },
  ): void {
    const position = geometry.attributes.position;
    if (!position) {
      throw new Error("geometry has no position attribute to colour");
    }
    if (magnitudeDb.length !== position.count) {
      throw new Error(
        `magnitudeDb has ${magnitudeDb.length} values but the geometry has ` +
          `${position.count} vertices`,
      );
    }

    const span = rangeDb.max - rangeDb.min;
    const colors = new Float32Array(position.count * 3);

    for (let i = 0; i < position.count; i += 1) {
      // A degenerate range (a perfectly isotropic pattern) has no gradient to
      // show, so every vertex sits at the top of the scale.
      const t = span === 0 ? 1 : ((magnitudeDb[i] ?? rangeDb.min) - rangeDb.min) / span;
      const { r, g, b } = ColorMapper.jet(t);

      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  }
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pnpm --filter client test
pnpm --filter client typecheck
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(client): colour the pattern mesh by magnitude in dB"
```

---

### Task 6: Scene frame, orbit controls and React wiring

Replaces the hand-rolled orbit handler (which only tracks one axis and force-rotates the mesh every frame) with `OrbitControls`, and introduces the container object that carries the Z-up-to-Y-up conversion.

**Files:**
- Modify: `packages/client/src/core/SceneManager.ts`
- Modify: `packages/client/src/hooks/useThreeScene.ts`
- Modify: `packages/client/src/App.tsx`
- Modify: `packages/client/src/components/ControlPanel.tsx`
- Modify: `packages/client/src/components/Viewport.tsx`
- Create: `packages/client/src/core/patternService.ts`
- Create: `packages/client/public/fixtures/dipole-pattern3d.json`
- Create: `packages/client/tests/patternService.test.ts`

**Interfaces:**
- Consumes: `GeometryBuilder.buildRadiationPattern` (Task 4), `ColorMapper.applyMagnitudeColors` (Task 5), `validatePattern3d`/`Pattern3dError` (Task 3).
- Produces:
  - `SceneManager.setPatternGeometry(geometry: THREE.BufferGeometry): void`
  - `SceneManager.dispose(): void`
  - `SceneManager.renderer: THREE.WebGLRenderer` (read by Task 7's PNG export)
  - `useThreeScene(canvasRef: React.RefObject<HTMLCanvasElement | null>, pattern: Pattern3d | null, floorDb: number): { error: string | null; sceneRef: React.RefObject<SceneManager | null> }`
  - `loadPattern3d(url?: string): Promise<Pattern3d>`

- [ ] **Step 1: Rewrite the scene frame in `SceneManager.ts`**

Replace the constructor's mesh and orbit setup, and the orbit methods, with:

```ts
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
```

In the constructor, replace `this.mesh = null;` and `this._initOrbit();` with:

```ts
    // The renderer is Y-up; the contract is the physical antenna frame, which
    // is Z-up. Rotating -90 degrees about X maps (x, y, z) to (x, z, -y), so
    // antenna +Z appears as renderer +Y. Applying it here, on a container,
    // keeps the vertex data in antenna coordinates for export and comparison.
    this.frame = new THREE.Group();
    this.frame.rotation.x = -Math.PI / 2;
    this.scene.add(this.frame);

    this.patternMesh = null;

    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    // Keyboard support is required by RNF-05 (multiple input devices).
    this.controls.listenToKeyEvents(window);
```

Add the field declarations at the top of the class:

```ts
  private frame: THREE.Group;
  private patternMesh: THREE.Mesh | null;
  private controls: OrbitControls;
```

Delete `_initOrbit` and `_updateOrbit` entirely, along with the now-unused `mesh` and `_orbit` field declarations added in Task 2. There is no automatic rotation: it fights user interaction and is a motion-sensitivity problem under RNF-05.

- [ ] **Step 2: Replace `setMesh` with `setPatternGeometry` and add `dispose`**

```ts
  /**
   * Installs a pattern geometry, replacing and disposing any previous one.
   * The geometry is expected in the Z-up antenna frame; the container
   * handles the renderer's Y-up convention.
   */
  setPatternGeometry(geometry: THREE.BufferGeometry): void {
    if (this.patternMesh) {
      this.frame.remove(this.patternMesh);
      this.patternMesh.geometry.dispose();
      (this.patternMesh.material as THREE.Material).dispose();
    }

    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      shininess: 40,
    });

    this.patternMesh = new THREE.Mesh(geometry, material);
    this.frame.add(this.patternMesh);
  }

  dispose(): void {
    this.stopLoop();
    this.controls.dispose();
    if (this.patternMesh) {
      this.patternMesh.geometry.dispose();
      (this.patternMesh.material as THREE.Material).dispose();
    }
    this.renderer.dispose();
  }
```

`DoubleSide` is deliberate: a pattern with a deep null can fold through itself, and a one-sided material shows a hole there.

- [ ] **Step 3: Update the animation loop and the renderer options**

In `startLoop`, replace `this._updateOrbit();` with `this.controls.update();`.

In the `WebGLRenderer` constructor call, add `preserveDrawingBuffer: true`:

```ts
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      // Required so the PNG export can read the canvas outside the frame in
      // which it was drawn.
      preserveDrawingBuffer: true,
    });
```

- [ ] **Step 4: Write the failing pattern-service test**

`packages/client/tests/patternService.test.ts`:

```ts
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
```

- [ ] **Step 5: Run it to verify it fails**

```bash
pnpm --filter client test patternService
```

Expected: FAIL — cannot resolve `../src/core/patternService`.

- [ ] **Step 6: Write `packages/client/src/core/patternService.ts`**

```ts
import { validatePattern3d, type Pattern3d } from "schema";

/**
 * Development fixture. The real source is the REST API in packages/server,
 * which does not exist yet (roadmap phase 3); this keeps the client
 * independently runnable until it does.
 */
const FIXTURE_URL = "/fixtures/dipole-pattern3d.json";

/**
 * Loads a pattern3d block and validates it before any consumer sees it.
 * A malformed grid must fail here rather than render as a plausible but
 * wrong pattern.
 */
export async function loadPattern3d(
  url: string = FIXTURE_URL,
): Promise<Pattern3d> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load pattern from ${url}: ${response.status}`);
  }

  const pattern = (await response.json()) as Pattern3d;
  validatePattern3d(pattern);
  return pattern;
}
```

- [ ] **Step 7: Generate the development fixture**

The fixture is a half-wave dipole pattern, `G(theta) = sin^2(theta)` in linear gain, converted to dB and clamped at -40. It is a stand-in for reconstruction output, not a reconstruction — the client never computes pattern data in production code.

```bash
cd /home/car/proyectos/antenna-3D-pattern-generator/packages/client
mkdir -p public/fixtures
node --input-type=module -e '
import { writeFileSync } from "node:fs";

const THETA_COUNT = 181;
const PHI_COUNT = 360;
const FLOOR_DB = -40;

const magnitudeDb = [];
let min = Infinity;
let max = -Infinity;

for (let i = 0; i < THETA_COUNT; i += 1) {
  const theta = (i * Math.PI) / 180;
  const linear = Math.sin(theta) ** 2;
  const db = Math.max(FLOOR_DB, 10 * Math.log10(Math.max(linear, 1e-12)));
  const rounded = Number(db.toFixed(2));
  for (let j = 0; j < PHI_COUNT; j += 1) magnitudeDb.push(rounded);
  if (rounded < min) min = rounded;
  if (rounded > max) max = rounded;
}

writeFileSync(
  "public/fixtures/dipole-pattern3d.json",
  JSON.stringify({
    thetaDeg: { start: 0, stop: 180, stepDeg: 1, count: THETA_COUNT },
    phiDeg: { start: 0, stop: 359, stepDeg: 1, count: PHI_COUNT },
    magnitudeDb,
    rangeDb: { min, max },
    symmetryAssumption: "axial",
  }),
);
'
```

- [ ] **Step 8: Rewrite `useThreeScene.ts`**

```ts
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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const manager = new SceneManager(canvas);
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

  return { error, sceneRef };
}
```

- [ ] **Step 9: Rewrite `App.tsx`**

`App` owns the canvas ref and calls the hook, rather than `Viewport` doing it. That is what lets Task 7 read `sceneRef` for the PNG snapshot without moving the call later.

```tsx
import { useEffect, useRef, useState } from "react";
import type { Pattern3d } from "schema";
import { DEFAULT_FLOOR_DB } from "./core/radiusMapping";
import { loadPattern3d } from "./core/patternService";
import { useThreeScene } from "./hooks/useThreeScene";
import { Viewport } from "./components/Viewport";
import { ControlPanel } from "./components/ControlPanel";

/**
 * App
 * Single responsibility: state orchestration.
 * Owns the loaded pattern and the display floor, and never imports Three.js.
 */
export default function App() {
  const [pattern, setPattern] = useState<Pattern3d | null>(null);
  const [floorDb, setFloorDb] = useState(DEFAULT_FLOOR_DB);
  const [loadError, setLoadError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { error: renderError } = useThreeScene(canvasRef, pattern, floorDb);

  useEffect(() => {
    loadPattern3d()
      .then(setPattern)
      .catch((caught: unknown) => setLoadError(String(caught)));
  }, []);

  return (
    <div className="flex h-screen bg-[#0f0f1a] text-[#e0e0ff] font-mono">
      <Viewport canvasRef={canvasRef} error={renderError} />
      <ControlPanel
        floorDb={floorDb}
        onFloorChange={setFloorDb}
        symmetryAssumption={pattern?.symmetryAssumption ?? null}
        rangeDb={pattern?.rangeDb ?? null}
        error={loadError}
      />
    </div>
  );
}
```

- [ ] **Step 10: Rewrite `Viewport.tsx`**

```tsx
import type { RefObject } from "react";

/**
 * Viewport
 * Single responsibility: render the <canvas> that Three.js draws into,
 * plus any error the render pipeline reports. It owns no Three.js state.
 */
export function Viewport({
  canvasRef,
  error,
}: {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  error: string | null;
}) {
  return (
    <div className="flex-1 relative">
      <canvas
        ref={canvasRef}
        aria-label="Interactive 3D radiation pattern"
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />
      {error && (
        <p role="alert" className="absolute top-4 left-4 bg-[#4a1020] px-3 py-2 text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 11: Rewrite `ControlPanel.tsx`**

Replace the whole component. The sphere parameters are gone; what remains is the display floor, the read-only range, the symmetry label and the error slot.

```tsx
/**
 * ControlPanel
 * Single responsibility: UI for display parameters.
 * Contains no mathematics - it emits changes upward.
 */
export function ControlPanel({
  floorDb,
  onFloorChange,
  symmetryAssumption,
  rangeDb,
  error,
}: {
  floorDb: number;
  onFloorChange: (value: number) => void;
  symmetryAssumption: "axial" | "none" | null;
  rangeDb: { min: number; max: number } | null;
  error: string | null;
}) {
  return (
    <aside className="w-72 p-5 bg-[#1a1a2e] flex flex-col gap-5 overflow-y-auto text-[#e0e0ff]">
      <h2 className="text-[#7b7bff] text-sm font-bold border-b border-[#333] pb-2">
        Display
      </h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="floor-db" className="text-[11px] text-[#aaa]">
          Dynamic range floor: <b className="text-white">{floorDb} dB</b>
        </label>
        <input
          id="floor-db"
          type="range"
          min={-60}
          max={-10}
          step={1}
          value={floorDb}
          onChange={(event) => onFloorChange(Number(event.target.value))}
        />
        <p className="text-[11px] text-[#777]">
          Magnitudes at or below this level are drawn at the origin.
        </p>
      </div>

      {rangeDb && (
        <p className="text-[11px] text-[#aaa]">
          Pattern range: {rangeDb.min} dB to {rangeDb.max} dB
        </p>
      )}

      {symmetryAssumption === "axial" && (
        <p className="text-[11px] text-[#ffcc66] border border-[#5a4a20] p-2">
          Reconstructed under an axial symmetry assumption. This is a
          simplification, not an equivalent-accuracy result.
        </p>
      )}

      {error && (
        <p role="alert" className="text-[11px] text-[#ff8080]">
          {error}
        </p>
      )}
    </aside>
  );
}
```

The symmetry notice is not optional polish: the root constraints require a `revolution` result to be labeled with its assumption wherever it is surfaced.

- [ ] **Step 12: Remove the demo sphere**

`buildSphere`, `SphereParams`, `ColorMode` and `ColorMapper.applyToGeometry` / `_normalize` are now unreferenced. Delete them from `GeometryBuilder.ts` and `ColorMapper.ts`. Keep `ColorMapper.jet`, which `applyMagnitudeColors` uses.

- [ ] **Step 13: Verify**

```bash
pnpm --filter client test
pnpm --filter client typecheck
pnpm --filter client lint
pnpm --filter client build
pnpm --filter client dev
```

Expected: tests and checks pass; the dev server shows a dipole torus-like pattern that orbits with the mouse, zooms with the wheel, responds to arrow keys, and rebuilds when the floor slider moves.

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "feat(client): render pattern3d with orbit controls and a display floor"
```

---

### Task 7: PNG snapshot and mesh JSON export

Implements RF-07 and RF-08, and with them CP-05 and CP-06.

**Files:**
- Create: `packages/client/src/core/meshExport.ts`
- Create: `packages/client/src/components/ExportButtons.tsx`
- Modify: `packages/client/src/core/SceneManager.ts`
- Modify: `packages/client/src/App.tsx`, `packages/client/src/components/ControlPanel.tsx`
- Create: `packages/client/tests/meshExport.test.ts`

**Interfaces:**
- Consumes: `SceneManager` (Task 6), `GeometryBuilder.buildRadiationPattern` (Task 4).
- Produces:
  - `interface MeshExport { schemaVersion: 1; frame: "antennaZUp"; floorDb: number; vertexCount: number; positions: number[]; indices: number[]; magnitudeDb: number[] }`
  - `function buildMeshExport(geometry: THREE.BufferGeometry, magnitudeDb: number[], floorDb: number): MeshExport`
  - `SceneManager.captureSnapshot(): string` — a PNG data URL

`frame: "antennaZUp"` is named explicitly in the export even though the transported contract omits it: an external tool reading the exported file has no accompanying schema document to consult, which is exactly the CP-06 scenario.

- [ ] **Step 1: Write the failing test**

`packages/client/tests/meshExport.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { GeometryBuilder } from "../src/core/GeometryBuilder";
import { buildMeshExport } from "../src/core/meshExport";
import { isotropic, THETA_COUNT, PHI_COUNT } from "./fixtures/makePattern3d";

describe("buildMeshExport", () => {
  it("carries one position triple per vertex", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);

    expect(exported.vertexCount).toBe(THETA_COUNT * PHI_COUNT);
    expect(exported.positions).toHaveLength(THETA_COUNT * PHI_COUNT * 3);
    expect(exported.magnitudeDb).toHaveLength(THETA_COUNT * PHI_COUNT);
  });

  it("carries the full index buffer", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);

    expect(exported.indices).toHaveLength((THETA_COUNT - 1) * PHI_COUNT * 6);
  });

  it("declares the antenna frame and the floor used to build it", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern, {
      floorDb: -25,
    });

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -25);

    expect(exported.frame).toBe("antennaZUp");
    expect(exported.floorDb).toBe(-25);
    expect(exported.schemaVersion).toBe(1);
  });

  it("round-trips through JSON without losing data", () => {
    const pattern = isotropic();
    const geometry = GeometryBuilder.buildRadiationPattern(pattern);

    const exported = buildMeshExport(geometry, pattern.magnitudeDb, -40);
    const reparsed = JSON.parse(JSON.stringify(exported)) as typeof exported;

    expect(reparsed.positions).toHaveLength(exported.positions.length);
    expect(reparsed.indices[17]).toBe(exported.indices[17]);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pnpm --filter client test meshExport
```

Expected: FAIL — cannot resolve `../src/core/meshExport`.

- [ ] **Step 3: Write `packages/client/src/core/meshExport.ts`**

```ts
import type * as THREE from "three";

/**
 * The RF-08 mesh export format.
 *
 * This is an output format for external reuse (CP-05, CP-06), not an input
 * to any service. It names its coordinate frame explicitly because a tool
 * reading the file has no schema document at hand, unlike a consumer of the
 * transported contract.
 */
export interface MeshExport {
  schemaVersion: 1;
  frame: "antennaZUp";
  floorDb: number;
  vertexCount: number;
  positions: number[];
  indices: number[];
  magnitudeDb: number[];
}

export function buildMeshExport(
  geometry: THREE.BufferGeometry,
  magnitudeDb: number[],
  floorDb: number,
): MeshExport {
  const position = geometry.attributes.position;
  const index = geometry.getIndex();

  if (!position || !index) {
    throw new Error("geometry must have both position and index to export");
  }

  return {
    schemaVersion: 1,
    frame: "antennaZUp",
    floorDb,
    vertexCount: position.count,
    positions: Array.from(position.array as Float32Array),
    indices: Array.from(index.array as Uint32Array),
    magnitudeDb: [...magnitudeDb],
  };
}
```

- [ ] **Step 4: Run it to verify it passes**

```bash
pnpm --filter client test meshExport
```

Expected: 4 tests PASS.

- [ ] **Step 5: Add the snapshot method to `SceneManager.ts`**

```ts
  /**
   * Captures the current view as a PNG data URL.
   *
   * The renderer is created with preserveDrawingBuffer so the buffer is
   * still readable outside the frame that drew it; without it this returns
   * a blank image.
   */
  captureSnapshot(): string {
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL("image/png");
  }
```

- [ ] **Step 6: Create `packages/client/src/components/ExportButtons.tsx`**

```tsx
/**
 * ExportButtons
 * Single responsibility: trigger downloads. Contains no mathematics and no
 * Three.js access - it receives ready-made payloads from App.
 */
export function ExportButtons({
  onSnapshot,
  onMeshJson,
  disabled,
}: {
  onSnapshot: () => void;
  onMeshJson: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={onSnapshot}
        disabled={disabled}
        className="bg-[#2a2a44] px-3 py-2 text-xs disabled:opacity-40"
      >
        Export PNG snapshot
      </button>
      <button
        type="button"
        onClick={onMeshJson}
        disabled={disabled}
        className="bg-[#2a2a44] px-3 py-2 text-xs disabled:opacity-40"
      >
        Export mesh JSON
      </button>
    </div>
  );
}
```

- [ ] **Step 7: Wire the exports in `App.tsx`**

Add the download helper and the two handlers, and pass them through `ControlPanel`:

```tsx
function download(filename: string, href: string): void {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  anchor.click();
}
```

Task 6 already has `App` calling `useThreeScene`, so widen that call to keep the scene ref:

```tsx
  const { error: renderError, sceneRef } = useThreeScene(canvasRef, pattern, floorDb);
```

Then add the two handlers:

```tsx
  const handleSnapshot = () => {
    const manager = sceneRef.current;
    if (!manager) return;
    download("radiation-pattern.png", manager.captureSnapshot());
  };

  const handleMeshJson = () => {
    if (!pattern) return;
    const geometry = GeometryBuilder.buildRadiationPattern(pattern, { floorDb });
    const payload = buildMeshExport(geometry, pattern.magnitudeDb, floorDb);
    geometry.dispose();
    download(
      "radiation-pattern-mesh.json",
      URL.createObjectURL(
        new Blob([JSON.stringify(payload)], { type: "application/json" }),
      ),
    );
  };
```

Then render `<ExportButtons onSnapshot={handleSnapshot} onMeshJson={handleMeshJson} disabled={!pattern} />` inside `ControlPanel` by passing it as a child, adding `children?: React.ReactNode` to `ControlPanel`'s props and rendering `{children}` before the error slot.

- [ ] **Step 8: Add the imports the handlers need**

At the top of `App.tsx`:

```tsx
import { GeometryBuilder } from "./core/GeometryBuilder";
import { buildMeshExport } from "./core/meshExport";
import { ExportButtons } from "./components/ExportButtons";
```

`handleMeshJson` rebuilds the geometry rather than reading it back out of `SceneManager`: the builder is pure and cheap, and reaching into the scene graph for data would put rendering state on the export path.

- [ ] **Step 9: Verify**

```bash
pnpm --filter client test
pnpm --filter client typecheck
pnpm --filter client lint
pnpm --filter client build
pnpm --filter client dev
```

Expected: checks pass. In the browser, both buttons download files; the PNG shows the current view rather than a blank image, and the JSON opens with `frame: "antennaZUp"` and a `positions` array of 195 480 numbers.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(client): export a PNG snapshot and the derived mesh JSON"
```

---

## Verification against the spec

| Spec item | Task |
|---|---|
| D1 angular grid contract | 1, 3 |
| D2 Z-up frame, rotation on container | 1, 4, 6 |
| D3 grid layout, poles, seam | 1, 3, 4 |
| D4 dB-to-radius in the client | 1, 4, 6 |
| D5 module boundaries, `Uint32`, boundary validation | 1, 4, 5, 6 |
| D6 two output formats | 1, 7 |
| D7 `schemaVersion` | 1, 3 |
| Testing section | 3, 4, 5, 6, 7 |
| Known deviations (TypeScript, English) | 2 |

## Deferred

- The REST contract with `packages/server` — the server is roadmap phase 3, so Task 6 uses a development fixture and `patternService.ts` is the single file that changes when the API exists.
- Analytic-expression and image input forms (RF-01, RF-02): they need the server's upload endpoint.
- The `patent` method's `symmetryAssumption: "none"` path is typed and handled but untested against real data, since that method is blocked on an open item in `docs/theory.md`.
