# Reconstruction Service

CLI tool that extracts 2D polar radiation patterns from antenna datasheet
images and writes them in the unified JSON contract defined in
[`docs/data-schema.md`](../../docs/data-schema.md).

This is Phase 1 of the module. It is a command-line extractor and nothing
more — there is deliberately **no FastAPI app, no Dockerfile, no 3D mesh
reconstruction, and no analytic-expression path** here yet. Those arrive in a
later phase; do not go looking for them.

See the root [README.md](../../README.md) for overall architecture and the root
[CLAUDE.md](../../CLAUDE.md) for repository-wide conventions. The pipeline's
internal design is in [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

---

## Setup

```bash
cd python/reconstruction-service
pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` is the runtime set (`opencv-python`, `numpy`).
`requirements-dev.txt` pulls that in and adds `pytest`.

## Running

Process the whole calibrated queue (the five datasheets in `datasheets/`):

```bash
python main.py            # normal run
python main.py --debug    # debug logging + intermediate overlay images
```

Process a single image:

```bash
python main.py \
  --image datasheets/taoglas-1.png \
  --manufacturer taoglas \
  --plane XZ \
  --debug
```

`--plane` is one of `XY`, `XZ`, `YZ`. It cannot be inferred from pixels, so it
must be declared — either on the command line or in `PROCESSING_QUEUE` in
`pipeline.py`.

`--output-dir` overrides where results land (default `output/`).

**Relative paths resolve against this service directory, not your working
directory.** `python /path/to/main.py` works from anywhere.

## Tests

```bash
python -m pytest -q                                     # full suite
python -m pytest tests/test_polar_sampler.py -q         # one file
python -m pytest tests/test_polar_sampler.py::test_pattern_pixel_constant_is_255 -q
```

Unit tests build synthetic images with numpy, so they do not depend on the
datasheet PNGs. `tests/test_pipeline_integration.py` runs the real ones.

---

## The pipeline

`main.py` is an argparse shell; `pipeline.py` is the orchestrator. Six steps:

| Step | Module | What it does |
|------|--------|--------------|
| 1  | `modules/image_loader.py`        | Load the PNG, convert BGR → RGB |
| 2  | `modules/pattern_mask.py`        | Threshold `rgb_range` to isolate the plotted trace |
| 3a | `modules/ring_mask_extractor.py` | Threshold `circle_color_range` to isolate the graticule |
| 3b | `modules/center_detector.py`     | Hough circles + consensus clustering → `(cx, cy)` |
| 3c | `modules/outer_ring_detector.py` | Fit the ring comb → `outer_radius_px` |
| 4  | `modules/polar_sampler.py`       | Cast one ray per degree, map distance → dB |
| 5  | `modules/visualizer.py`          | Annotated overlay for calibration review |
| 6  | `modules/result_writer.py`       | Contract JSON + snake_case debug JSON |

Steps 2 and 3a share their thresholding through `modules/rgb_range.py`, which
is also where the mask convention lives: **255 = feature, 0 = background.**

## Output

```
output/
    json/{stem}.json                        the unified contract
    images/{stem}.png                       annotated mask (trace + center + ring)
    debug/extraction/{stem}.json            center, radius, coverage, warnings
    debug/ring_mask/{stem}.png              --debug only
    debug/center_overlay/{stem}.png         --debug only
    debug/outer_ring_overlay/{stem}.png     --debug only
```

`output/json/{stem}.json` is the deliverable:

```json
{
  "sourceType": "image",
  "plane": "XZ",
  "metadata": { "provider": "taoglas", "antennaType": null, "polarization": null },
  "reconstructionMethod": null,
  "views": [
    { "plane": "XZ", "pattern": [ { "angleDeg": 0.0, "magnitudeDb": -16.4 } ] }
  ],
  "computed": { "directivityDb": null, "efficiency": null }
}
```

`pattern` always has exactly 360 entries, `angleDeg` running `0..359` at 1°
resolution. `magnitudeDb` is `null` where no trace pixel was found on that ray.

`reconstructionMethod` and `computed` are `null` on purpose: extraction does not
choose a reconstruction method or compute directivity — the API layer does.

Pixel-space values (`center_px`, `outer_radius_px`, `coverage_ratio`) are
calibration artifacts with no place in the contract, so they go to
`output/debug/extraction/{stem}.json` instead, and stay snake_case.

---

## Adding or calibrating a manufacturer

Everything manufacturer-specific lives in `config/manufacturer_config.py`.
Adding a vendor touches **only that file**.

**1. Read the dB scale off the plot.** `center_db` is the value at the plot
origin, `outer_db` the value at the outermost graticule ring. On every datasheet
here the center is the lowest value, so `center_db < outer_db` — this is
enforced by `validate_manufacturer_config`.

**2. Count the rings.** `ring_count` is the number of concentric rings between
the center and the outer ring, read off the same radial labels. For example
labels `-30 / -22.5 / -15 / -7.5 / 0` means `ring_count: 4`. The detector fits
the ring *spacing* and derives `outer_radius_px = ring_count × spacing`, so this
number has to be right.

**3. Sample the colours.** `rgb_range` bounds the trace colour;
`circle_color_range` bounds the graticule colour. Bound **every** channel that
distinguishes the trace — leaving one unbounded is how the rf-elements config
accidentally matched a near-white anti-aliasing colour scattered across the
whole figure.

**4. Run with `--debug` and read the overlays.**

- `debug/center_overlay/` — is the red crosshair on the plot origin?
- `debug/outer_ring_overlay/` — is the blue circle on the outermost graticule
  ring? If not, `ring_count` or `circle_color_range` is wrong.
- `images/` — does the white mask look like the trace alone, with no graticule,
  legend, or axis labels bleeding in?

**5. Check the numbers, then check the picture.** `coverage_ratio` in
`debug/extraction/{stem}.json` is the fraction of the 360 rays that found the
trace.

> **Coverage is not correctness.** A leaky `rgb_range` produces *high* coverage
> and a *wrong* pattern, because each ray takes its outermost hit and a stray
> pixel out near the plot edge wins. rf-elements read 100% coverage while its
> output was a starburst of radial spikes. Always re-plot the emitted `pattern`
> in polar coordinates and compare it against the source image before calling a
> manufacturer calibrated.

Note too that a strongly directive pattern legitimately collapses to the plot
center over most angles, so a low coverage there is not automatically a defect.

A quick re-plot:

```python
import json, numpy as np, matplotlib.pyplot as plt

pattern = json.load(open("output/json/taoglas-1.json"))["views"][0]["pattern"]
points = [(np.deg2rad(p["angleDeg"]), p["magnitudeDb"])
          for p in pattern if p["magnitudeDb"] is not None]
ax = plt.subplot(projection="polar")
ax.plot(*zip(*points))
plt.show()
```

---

## Current calibration status

Measured with `python main.py --debug`:

| Manufacturer | `outer_radius_px` | Coverage | Status |
|---|---|---|---|
| `taoglas`        | 104.0 | 100.0% | calibrated |
| `rf_elements`    | 162.0 | 100.0% | calibrated |
| `quectel`        | 145.0 |  95.3% | calibrated |
| `alpha_wireless` | 129.5 |  84.7% | known limitation, `xfail` |
| `molex`          |  36.0 |  12.5% | known limitation, `xfail` |

## Known limitations

**`molex` — outer ring not found.** Its graticule draws radial spoke lines every
10° in the same grey as the concentric rings, so the ring mask is roughly
uniformly dense at *every* radius. The comb fit scores a candidate spacing by
mean density over its `ring_count` multiples, and against a radially uniform
mask that score barely varies, so the fit collapses onto the smallest allowed
period (`MIN_RING_PERIOD_PX`): it reports `outer_radius_px = 36` where the real
outer ring sits near 135 px. Fixing this needs the detector to separate rings
from spokes — scoring the angular *uniformity* of hits at a radius rather than
their count.

**`alpha_wireless` — trace and graticule share a colour.** The plot is greyscale
and its graticule is drawn as black dashed lines, the same colour family as the
trace, so no `rgb_range` can separate them. The window is kept tight, giving
~85% honest coverage; widening it raises the number while the extra rays land on
the graticule. Separating them needs a geometric filter, not a colour one.

Both are marked `xfail(strict=True)` in `tests/test_pipeline_integration.py`, so
a fix will show up as an `XPASS` rather than going unnoticed.

**Unused helper.** `utils/file_utils.resolve_output_path` is currently called by
nothing; `pipeline.py` resolves its own output paths.

**`docs/MODULES_DETAIL.md` is still empty** — the per-module signature and
tuning-knob reference has not been written yet.

## 3D reconstruction algorithms

Not built yet (roadmap phase 2: `revolution` and `patent` methods,
analytic-expression path). Full mathematical specification is in
[`docs/theory.md`](../../docs/theory.md) — read it before starting that
work. The `patent` method is currently blocked on an open item in that
document's interpretation decisions log (the angle/direction convention
between this module's extracted `angleDeg` and the patent's coordinate
assumptions); `revolution` and the analytic path are not blocked.
