# CLAUDE.md

Repository-wide instructions for Claude Code. Module-specific
instructions live in each module's own `CLAUDE.md`
(`packages/client/CLAUDE.md`, `packages/server/CLAUDE.md`,
`python/reconstruction-service/CLAUDE.md`) and are additive to this
file — they must not contradict it.

## Project

Browser-based application that reconstructs 3D antenna radiation
patterns from partial 2D data (image datasheet cuts or analytic
expressions). Full architecture, requirements, and rationale are in
[README.md](./README.md) — read it before making structural changes.
This file only covers conventions Claude Code must follow while writing
code in this repository.

## Repository layout

```
packages/client/                 React + Three.js frontend
packages/server/                 Node.js + Express REST API
packages/schema/                 (optional) shared data-contract types
python/reconstruction-service/   FastAPI microservice
docs/                            data-schema.md, theory.md, validation-plan.md
data/sessions/{uuid}.json        runtime session storage, gitignored
```

## Hard constraints

- **Language**: all code, identifiers, comments, and technical
  documentation are in English, with no exceptions. Do not introduce
  Spanish file names, function names, variable names, or comments,
  even in scratch/debug code.
- **Package manager**: pnpm only, for every JavaScript package. Never
  generate `package-lock.json` or `yarn.lock`, and never invoke `npm`
  or `yarn` commands.
- **Containers**: each module owns exactly one `Dockerfile`. Multi-service
  orchestration only happens through the root `docker-compose.yml`.
  Never combine multiple services into a single Dockerfile.
- **Analytic expression evaluation**: user-submitted expressions over
  `theta`/`phi` must never be evaluated with `eval`, `exec`, or
  `new Function` against raw input, in either Node or Python. Use a
  sandboxed expression parser with an explicit function allow-list
  (`sin`, `cos`, `exp`, `pow`, `abs`) and no access to the runtime,
  filesystem, or network. This applies even in prototypes or
  throwaway scripts.
- **Session storage**: one JSON file per session at
  `data/sessions/{uuid}.json`. Never introduce a shared, append-only
  index file — the system is multi-user, and a shared mutable file is
  a race condition. Listing sessions is done by reading the directory.
- **Data contract**: `docs/data-schema.md` is the source of truth for
  the unified JSON shape (camelCase field names, 1-degree angular
  resolution). A schema change is made there first, then propagated to
  `packages/server` and `python/reconstruction-service`.

## Testing

Every module requires an automated test suite before it is considered
complete. Ad-hoc scripts that print output for manual inspection are
useful during development but do not substitute for tests — if a
module has no `tests/` directory with real assertions, it is not done,
regardless of how much manual verification has happened.

## Commands

Not yet defined — this repository is still in the scaffolding phase.
This section will be filled in with real `dev`/`build`/`test` commands
as each module (`packages/client`, `packages/server`,
`python/reconstruction-service`) is actually scaffolded. Do not invent
commands here in the meantime.

## Current phase

Per the [Implementation Roadmap](./README.md#implementation-roadmap) in
the root README, the project is in Phase 1: migrating and correcting
the existing image-processing prototype (`pattern_extractor/`) into
`python/reconstruction-service`. Known issues in that migration are
tracked in that module's own documentation once it exists, not here.
