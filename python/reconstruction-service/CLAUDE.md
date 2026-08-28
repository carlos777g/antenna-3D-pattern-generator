# CLAUDE.md — python/reconstruction-service

Conventions for writing code in this module. Additive to the root
[CLAUDE.md](../../CLAUDE.md), which still applies in full and takes precedence.
Human-facing usage, setup, and the calibration workflow live in
[README.md](./README.md); this file is conventions only.

## Analytic expression evaluation (RNF-09)

Stated first because it is the constraint most easily violated by a "quick
prototype". The analytic path is not written yet. When it is: user-submitted
expressions over `theta`/`phi` must **never** reach `eval`, `exec`,
`compile`, or any equivalent. Use a sandboxed parser with an explicit function
allow-list (`sin`, `cos`, `exp`, `pow`, `abs`) and no access to the runtime,
filesystem, or network. This holds in throwaway scripts and notebooks too.

## Mask polarity

Every binary mask in this module is **`255` = feature, `0` = background**, with
no exceptions. A silent inversion of this convention is what broke the polar
sampler before, and it produced plausible-looking output rather than a crash.

All colour thresholding goes through `modules/rgb_range.apply_rgb_range`. Do not
re-implement per-channel min/max comparisons in a new module — that duplication
is precisely how the two halves of the codebase drifted apart.

`algorithms-tests/legacy_extractor.py` uses the *old*, inverted convention
deliberately. It is superseded reference code, is not imported by the pipeline,
and must not be used as a model for new code.

## Naming and the data contract

Internals are snake_case. `modules/result_writer.py` is the **only** camelCase
boundary in the service, mapping onto the contract in
[`docs/data-schema.md`](../../docs/data-schema.md), which is the source of truth
for the shape.

The extraction debug JSON stays snake_case on purpose: it is an internal
artifact, not part of the contract, and keeping it that way is what makes the
camelCase rule mean something where it matters. Do not add pixel-space fields
(`center_px`, `outer_radius_px`, coverage) to the contract payload.

A schema change is made in `docs/data-schema.md` first, then propagated here.

## Configuration

Every manufacturer-specific number lives in `config/manufacturer_config.py` and
nowhere else. Adding a manufacturer must touch only that file. Never hardcode a
threshold, colour range, or radius inside a module.

Algorithmic constants that are *not* manufacturer-specific belong at module
level with a name and a comment explaining the measurement behind the value —
`MIN_RING_PERIOD_PX`, `RADIAL_STEP_PX`, `MIN_ACCEPTABLE_COVERAGE`,
`MIN_COMB_SCORE`. A bare number inline in a function body is a bug waiting to be
untunable.

New config keys must be added to `REQUIRED_KEYS` and checked in
`validate_manufacturer_config`, so a typo fails loudly at load time rather than
falling through to a default branch deep in the pipeline.

## Module shape

One module = one pipeline step, exposing pure functions: given arrays and
parameters, return arrays and values. No global state, no reading config, no
writing to disk.

Disk access belongs to `pipeline.py` (which orchestrates) and to
`result_writer.py` (which is handed an explicit output directory).
`visualizer.build_annotated_image` returns an array; the caller writes it.

`main.py` stays a thin argparse shell. Anything a test might want to call goes
in `pipeline.py`, so importing it never runs the queue.

## Paths

Resolve from `Path(__file__)`, never from the working directory. `pipeline.py`
defines `SERVICE_ROOT` for this; use it. Relative paths passed in by a caller
are resolved against `SERVICE_ROOT`, so the CLI behaves identically from any
directory.

## Testing

Every new module needs a test in `tests/`. Per the root CLAUDE.md, a module
without real assertions is not done, no matter how much manual verification has
happened.

Unit tests use the synthetic fixtures in `tests/conftest.py` — numpy-built
images with a known center and known ring radii — so they stay fast and
deterministic. Tests that need the real PNGs go in
`tests/test_pipeline_integration.py`.

A manufacturer that cannot yet be extracted correctly is marked
`xfail(strict=True)` with a comment stating exactly what is unresolved, not
quietly dropped from the queue. A later fix then surfaces as an `XPASS`.

## Calibration honesty

A coverage number is not a correctness proof. Each ray takes its *outermost*
hit, so a colour range that leaks — into the graticule, the legend, the axis
labels, an anti-aliasing colour — raises coverage while making the output wrong.

Before describing a manufacturer as calibrated, re-plot the emitted `pattern` in
polar coordinates and compare it against the source image. The README documents
the procedure. Do not report a coverage figure as evidence of a working
extraction on its own.
