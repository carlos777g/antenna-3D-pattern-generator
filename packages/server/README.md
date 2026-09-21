# Server (Node.js + Express)

Not yet scaffolded. This package will contain the REST API: input
validation, session persistence, and orchestration of calls to the
Python reconstruction service.

See the root [README.md](../../README.md) for architecture and the
root [CLAUDE.md](../../CLAUDE.md) for repository-wide conventions.

## Relationship to the 3D contract

The server validates and forwards the `pattern3d` block; it computes no
geometry and no reconstruction. Validation uses the shared validator in
`packages/schema`, so the server and the client reject the same
malformed payloads for the same reasons.
