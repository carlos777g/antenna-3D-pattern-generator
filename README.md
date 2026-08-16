# 3D Antenna Radiation Pattern Reconstruction

Interactive, browser-based web application that reconstructs 3D antenna radiation
patterns from partial 2D data (E/H-plane cuts from datasheet images) or analytic
expressions over spherical angles (`theta`, `phi`). No installation or licenses
required to run the client.

## Table of Contents

- [Motivation](#motivation)
- [Scope](#scope)
- [System Architecture](#system-architecture)
- [Tech Stack Rationale](#tech-stack-rationale)
- [Repository Structure](#repository-structure)
- [Unified Data Contract](#unified-data-contract)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)
- [Security Considerations](#security-considerations)
- [Concurrency and Storage Model](#concurrency-and-storage-model)
- [Test Plan Overview](#test-plan-overview)
- [Implementation Roadmap](#implementation-roadmap)
- [Documentation Map](#documentation-map)

## Motivation

Antenna manufacturers typically publish only 2D radiation pattern cuts (E-plane,
H-plane) in PDF datasheets, or partial analytic descriptions, rather than full
3D numerical models. This project reconstructs an approximate 3D radiation
pattern from that partial information using two selectable methods:

- **Revolution solid** (`revolution`): axial symmetry assumption from a single
  2D cut.
- **Two-view interpolation** (`patent`), based on the method described in
  patent US7535425B2: combines two orthogonal 2D cuts to reduce the symmetry
  assumption.

The reconstructed mesh is rendered interactively in the browser (WebGL) and can
be validated against external reference data (MATLAB, HFSS) using quantitative
geometric metrics (MSE, main-lobe angular deviation).

## Scope

**In scope:** single-source reconstruction (one image set OR one analytic
expression per run), interactive 3D visualization, PNG snapshot export, mesh
JSON export, internal validation against reference meshes.

**Out of scope (for this iteration):** multi-source fusion (combining an image
AND an analytic expression in the same reconstruction), real-time collaborative
editing, user accounts/authentication beyond basic multi-tenant data isolation.

**Note on "single source per run":** a run uses exactly one source *type*
(`image` or `analytic`), not necessarily a single file. The `revolution` method
consumes one view; the `patent` method consumes two views (e.g., XY and XZ
planes) of the same source type in a single run.

## System Architecture

```
Browser (React + Three.js)
        |
        v
Node.js REST API (Express)  --- validates input, orchestrates flow, persists JSON
        |
        v  (internal HTTP)
Python microservice (FastAPI)  --- image processing, analytic evaluation,
                                    interpolation, mesh generation, metrics
```

### Request flow

1. Client submits input (PNG image(s) or analytic expression) plus metadata
   (`provider`, `antennaType`, `polarization`, `plane`, `reconstructionMethod`).
2. Node API validates structure, file type/size, and metadata consistency.
3. Node API persists the normalized input as an independent session JSON file.
4. Node API calls the Python service (internal HTTP) with the session data.
5. Python service performs image feature extraction (image source) or
   sandboxed expression evaluation (analytic source), producing angular
   pattern pairs (`angleDeg`, `magnitudeDb`).
6. Python service applies the selected reconstruction method to generate a
   uniform spherical mesh (`{x, y, z, magnitudeDb}` per vertex).
7. Python service computes optional metrics (`directivityDb`, `efficiency`)
   when metadata supports it, and returns the full result to Node.
8. Node API persists the result and returns it to the client.
9. Client renders the mesh via Three.js (WebGL), supporting rotation, zoom,
   and perspective changes.
10. Client can export the current view as PNG or the mesh as JSON.
11. For validation runs, a separate comparison pipeline computes MSE and
    angular deviation against a reference mesh (see
    [Test Plan Overview](#test-plan-overview)).

### Division of responsibilities

| Concern | Owner |
|---|---|
| Input schema validation, file type/size checks | Node API |
| Session persistence, REST contract with the client | Node API |
| PNG parsing / polar pattern extraction | Python service |
| Analytic expression parsing and evaluation | Python service |
| Interpolation, mesh generation | Python service |
| Directivity / efficiency computation | Python service |
| Comparison metrics (MSE, angular deviation) | Python service |
| 3D rendering, camera controls | React client (Three.js) |
| PNG snapshot / mesh JSON export | React client |

## Tech Stack Rationale

| Layer | Choice | Rationale |
|---|---|---|
| 3D rendering | Three.js (WebGL) | GPU-accelerated rendering that stays interactive on medium-sized spherical meshes without a dedicated GPU. Provides low-level control over `BufferGeometry` and custom shaders for magnitude-to-color mapping, which a general-purpose charting library does not expose as directly. |
| UI framework | React | Component-based architecture that integrates cleanly with a Three.js render loop (via refs/hooks) and keeps input/visualization/export modules decoupled (RNF-06). |
| API layer | Node.js + Express | Thin orchestration layer: input validation, session persistence, REST contract with the client. Deliberately does not own numerical computation. |
| Numerical/image processing | Python (FastAPI) + NumPy/SciPy/OpenCV | Mathematical expressiveness and mature scientific libraries for image feature extraction, interpolation, and mesh generation. Exposed as an internal HTTP microservice rather than embedded in Node to keep the numerical stack isolated and independently testable. |
| Storage | Independent JSON files on disk | Matches current scope (no query requirements beyond retrieval by session id). Schema is designed to be migrated to a NoSQL store (e.g., MongoDB) without changes, if/when query needs grow. |
| Package manager | pnpm (workspaces) | Single package manager across `client` and `server`; no npm/yarn lockfiles are used in this repository. |
| Containerization | Docker per module + root `docker-compose.yml` | Isolates each module's runtime dependencies (Node version, Python version, native image-processing libraries) and avoids cross-platform environment drift. A single `Dockerfile` builds one image only; `docker-compose.yml` is what orchestrates `client`, `server`, and `reconstruction-service` together. |

### Discarded alternatives

- **Matplotlib / Plotly** for the 3D view: both are viable for static or
  moderately interactive 3D plots, but neither gives direct control over mesh
  geometry and shading needed for magnitude-driven coloring at interactive
  frame rates; Three.js is used as a rendering engine, not a charting library.
- **C++ / Rust** for the backend: no requirement for massive concurrency or a
  high-throughput multi-tenant service exists at this scope; the added
  build/deployment complexity is not justified by the marginal performance
  gain over NumPy/SciPy-backed Python for this workload.

## Repository Structure

Monorepo managed with **pnpm workspaces** for the JavaScript packages, plus an
independent Python service with its own environment. Each runnable module
(`client`, `server`, `reconstruction-service`) has its own `Dockerfile`; a
root `docker-compose.yml` orchestrates all three together. This isolates each
module's runtime and avoids cross-platform dependency issues, at the cost of
requiring Docker (or the module's native toolchain) for local development.

```
/
├── README.md                    # this file — project-level overview
├── CLAUDE.md                    # repo-wide conventions for Claude Code
├── pnpm-workspace.yaml          # packages: ["packages/*"]
├── package.json
├── docker-compose.yml           # orchestrates client, server, python service
├── packages/
│   ├── client/                  # React + Three.js frontend
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── CLAUDE.md
│   ├── server/                  # Node.js + Express REST API
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── CLAUDE.md
│   └── schema/                  # (optional) shared data-contract types,
│                                 # imported by both client and server
├── python/
│   └── reconstruction-service/  # FastAPI microservice
│       ├── Dockerfile
│       ├── README.md
│       └── CLAUDE.md
├── docs/
│   ├── data-schema.md           # unified JSON contract, versioned
│   ├── theory.md                 # theoretical foundation of reconstruction
│   │                              # methods, including interpretation notes
│   │                              # for patent US7535425B2 (no reference
│   │                              # implementation exists for that method)
│   └── validation-plan.md        # CP-01..CP-07 detail, reference datasets
└── data/                         # gitignored runtime storage
    └── sessions/{uuid}.json      # one file per session, no shared index file
```

A single `Dockerfile` builds a single image; it cannot run multiple services.
Multi-container orchestration is the responsibility of `docker-compose.yml`,
not any individual module's `Dockerfile`.

`packages/schema` is a recommended addition, not yet mandatory: without a
shared package, `client` and `server` can silently drift from the JSON
contract in `docs/data-schema.md` with nothing catching it at build time.

## Unified Data Contract

All accepted input (image-based or analytic) is normalized into this shape
before persistence. Field names are in English to match the project-wide
language convention for code and technical documentation.

```json
{
  "sourceType": "image | analytic",
  "plane": "XY | XZ | YZ",
  "metadata": {
    "provider": "string | null",
    "antennaType": "string | null",
    "polarization": "string | null"
  },
  "reconstructionMethod": "revolution | patent",
  "views": [
    {
      "plane": "XY | XZ | YZ",
      "pattern": [
        { "angleDeg": 0, "magnitudeDb": -3.2 }
      ]
    }
  ],
  "computed": {
    "directivityDb": null,
    "efficiency": null
  }
}
```

Notes:

- `views` holds one entry for `revolution` and two for `patent`.
- `pattern` covers 0-360 degrees at a fixed **1 degree** angular resolution,
  set at ingestion time. Any resampling to a different resolution happens
  explicitly in the reconstruction step, not silently at ingestion.
- `computed.directivityDb` and `computed.efficiency` are populated only when
  `metadata.antennaType` is in a supported list AND a reference gain value is
  present; the exact trigger rule is defined in `docs/data-schema.md`, not
  left implicit.
- This document is the source of truth for the schema; any change here must
  be reflected in both `packages/api` and `python/reconstruction-service`.

## Functional Requirements

| ID | Description | Priority |
|---|---|---|
| RF-01 | Load a pattern from a PNG image (datasheet) | High |
| RF-02 | Enter a pattern via an analytic expression over (theta, phi) | High |
| RF-03 | Select metadata: antenna type, provider (if image), plane | High |
| RF-04 | Select reconstruction method: revolution solid or patent US7535425B2 | High |
| RF-05 | Reconstruct 3D: generate a spherical mesh with per-point magnitude | High |
| RF-06 | Interactive 3D visualization: rotation, zoom, perspective change (WebGL) | High |
| RF-07 | Export a static PNG snapshot of the 3D pattern | Medium |
| RF-08 | Export mesh data as JSON (coordinates + magnitude) | Medium |

## Non-Functional Requirements

| ID | Description | Priority |
|---|---|---|
| RNF-01 | Usability: intuitive interface, no prior training in computational graphics required | High |
| RNF-02 | Performance: 3D reconstruction completes in <= 10 seconds | High |
| RNF-03 | Performance: fluid interaction via GPU acceleration | High |
| RNF-04 | Compatibility: Chrome, Firefox, Edge (WebGL) | High |
| RNF-05 | Accessibility: WCAG/POUR compliance (semantic HTML, multiple input devices, assistive tech) | High |
| RNF-06 | Modularity: decoupled input, processing, reconstruction, and visualization components | Medium |
| RNF-07 | Persistence: session data storage for internal validation, safe under concurrent multi-user access | Medium |
| RNF-08 | Portability: runs in-browser without per-platform installation or configuration | Medium |
| RNF-09 | Security: analytic expression evaluation must be sandboxed; no arbitrary code execution path is exposed to user input | High |

RNF-09 was not explicit in the original requirement set and is added here
because RF-02 (user-submitted analytic expressions) is a direct code
execution risk if implemented naively; see
[Security Considerations](#security-considerations).

## Security Considerations

User-submitted analytic expressions (RF-02) must never be evaluated with
`eval()`, `new Function()`, or Python's `eval`/`exec` against the raw string.
The evaluation path must go through a restricted expression parser with an
explicit allow-list of functions (`sin`, `cos`, `exp`, `pow`, `abs`) and
operators, and no access to the surrounding runtime, filesystem, or network.
This is a hard constraint on `python/reconstruction-service`, not an
implementation detail to be decided ad hoc.

Uploaded PNG files must be validated for actual file type (not just
extension), bounded in size (per the 350x350 px input constraint), and
processed without executing any embedded content.

## Concurrency and Storage Model

The application is multi-user. Session data is stored as **independent JSON
files, one per session, named by a generated UUID** (`data/sessions/{uuid}.json`).
There is deliberately no shared, mutable index file (e.g., a single
`sessions.json` that every request appends to): concurrent writes to a shared
file are a race condition that plain file I/O in Node does not protect
against. Any "list sessions" capability is implemented by reading the
directory listing, not by maintaining a shared index.

This keeps the current file-based approach viable under concurrent access
without introducing a database. If query patterns grow beyond
retrieval-by-id and directory listing (e.g., filtering by antenna type across
sessions), that is the trigger to migrate to the planned NoSQL store — not
before.

## Test Plan Overview

Reference data (MATLAB, HFSS) is used only as an external geometric
reference, not to replicate the reconstruction method itself.

| ID | Description | Input | Expected Result |
|---|---|---|---|
| CP-01 | Analytic expression validation | User-defined function | Accepted, or a controlled syntax error |
| CP-02 | Input image validation | 2D pattern PNG | Accepted and processable; extracted (angle, magnitude) pairs, or a controlled error if no clear polar pattern is detected |
| CP-03 | Internal JSON generation | Valid image or expression | JSON with required fields: angular array, metadata, hierarchical structure |
| CP-04 | 3D mesh reconstruction | JSON with angular pattern | Continuous 3D mesh, free of unjustified discontinuities, gaps, or deformation |
| CP-05 | Mesh export | Reconstructed mesh | Exported JSON with spatial coordinates + magnitude, reusable externally |
| CP-06 | External reconstruction from JSON | Exported JSON | Correct visualization in external tools (Python, 3D viewers) |
| CP-07 | Comparison against reference pattern | System mesh + reference mesh | Quantitative metrics: MSE, main-lobe angular deviation |

Full test data sources and pass/fail thresholds are defined in
`docs/validation-plan.md`, not in this file.

## Implementation Roadmap

Development proceeds module by module. Each module gets its own README.md
and CLAUDE.md once work on it begins.

1. **Python image processing module** (`python/reconstruction-service`,
   image path): PNG ingestion, polar pattern extraction, output as the
   unified `views[].pattern` shape.
2. **3D reconstruction algorithms** (`python/reconstruction-service`,
   reconstruction path): `revolution` and `patent` methods, uniform
   spherical mesh generation, analytic expression sandboxed evaluation.
3. **Node API** (`packages/api`): input validation, session persistence,
   orchestration of calls to the Python service, REST contract for the
   client.
4. **Frontend** (`packages/web`): input forms, Three.js visualization,
   PNG/JSON export.
5. **Validation module**: comparison pipeline (MSE, angular deviation)
   against reference datasets.

## Documentation Map

- **Root `README.md`** (this file): project-level architecture, data
  contract, and cross-module decisions. Changes here require review, since
  every module depends on it.
- **Root `CLAUDE.md`**: repo-wide conventions for Claude Code (coding
  standards, workspace commands, how modules are expected to interact).
- **Per-module `README.md`**: scope, setup, and usage specific to that
  module (e.g., `python/reconstruction-service/README.md` documents the
  image-processing pipeline in isolation).
- **Per-module `CLAUDE.md`**: module-specific conventions Claude Code should
  follow when working inside that package; these are additive to, and must
  not contradict, the root `CLAUDE.md`.
