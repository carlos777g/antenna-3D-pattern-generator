# Theoretical Foundation

This document is the source of truth for the mathematics behind the two
reconstruction methods (`revolution`, `patent`). Any implementation in
`python/reconstruction-service` must match this document; if an
implementation detail is not covered here, it is undefined and must be
resolved here first, not invented ad hoc in code.

## Critical implementation requirement, read this first

**Both reconstruction methods operate on linear gain, normalized to a
maximum of 1 — never on dB values directly.** Our unified data contract
stores `magnitudeDb` (typically negative, relative to peak). Every
formula below that multiplies or divides gain values requires converting
to linear gain first:

```
g_linear = 10 ** (magnitude_db / 10)
```

(power-ratio convention). After computing a result in linear space,
convert back for storage:

```
magnitude_db = 10 * log10(g_linear)
```

with an explicit epsilon floor on `g_linear` before the `log10` call
(e.g. `max(g_linear, 1e-6)`) to avoid `-inf` from numerical noise. This
conversion happens at the boundary of the reconstruction module — inputs
arrive as dB (per the unified contract), get converted to linear
internally, and results get converted back to dB before being written to
the output mesh. Do not carry dB values into the interpolation math at
any point.

## 1. Revolution method (single view, axial symmetry)

Assumption: the pattern is symmetric about the antenna's boresight axis.
A single 2D cut `gv(theta)` (elevation, -90 to 90 degrees) is swept
around the full azimuth:

```
G(theta, phi) = gv(theta)      for all phi in [0, 360)
```

This is a strong simplifying assumption — it ignores any real azimuthal
variation in the pattern. It is only a reasonable approximation for
antennas that are close to rotationally symmetric. This must be stated
as a documented limitation wherever `revolution` results are presented,
not silently treated as equivalent in accuracy to the `patent` method.

Cartesian mapping (see coordinate convention in Section 2.1):

```
r = g_linear(theta)
x = r * cos(theta) * cos(phi)
y = r * cos(theta) * sin(phi)
z = r * sin(theta)
```

## 2. Patent method (US7535425B2): two-view hybrid rotation + interpolation

### 2.1 Coordinate system and view roles (interpretation decision)

The patent uses a spherical system with origin at the antenna:
`theta` = elevation relative to the horizontal (X-Y) plane, range
[-90, 90] degrees, 0 at the equator; `phi` = azimuth, range
[0, 360) degrees. The antenna's default boresight points along +X. The
antenna is physically mounted along the Z axis.

The method requires assigning each of the two input views to one of two
distinct roles — they are NOT interchangeable inputs to the same
formula:

- **Vertical pattern `gv(theta')`**: a full 360-degree elevation cut
  (front lobe + back lobe), lying in the plane containing the Z axis
  (the prime meridian, phi=0/phi=180).
- **Horizontal pattern `gh(phi')`**: a full 360-degree azimuth cut,
  lying in the equatorial (X-Y) plane.

**Decision (must be confirmed before implementation):** in our unified
contract, a `patent` reconstruction uses exactly two views. We map
`plane: "XY"` to the horizontal role (`gh`) and `plane: "XZ"` or
`plane: "YZ"` to the vertical role (`gv`). If both submitted views are
vertical-type planes (e.g. XZ and YZ, no XY present), this mapping does
not apply and reconstruction must be rejected with a validation error —
the patent method requires one view in each role, not two views of the
same role.

**Open item, not yet resolved:** the patent's front/back mapping (Eq. 2
below) assumes a known relationship between the manufacturer's raw
angle convention (0-360 degrees, some starting direction, clockwise or
counterclockwise) and `theta`/`phi` as defined here. Our unified
contract's `angleDeg` does not currently encode direction or which
angle corresponds to boresight. This must be resolved (either a fixed
convention documented here, or an added metadata field) before the
patent method can be implemented correctly — do not assume a default
silently.

### 2.2 Front/back lobe mapping (patent Eq. 2)

The vertical pattern is tabulated over a full loop of its own raw angle
`theta'` (0 to 360 degrees). To use it as `gv(theta)` for `theta` in
[-90, 90] on both the front (phi=0) and back (phi=180) meridians:

```
theta' = theta                  for 0 <= theta <= 90,  phi = 0    (front, upper)
theta' = 180 - theta            for 0 <= theta <= 90,  phi = 180  (back,  upper)
theta' = 180 - theta            for -90 <= theta < 0,  phi = 180  (back,  lower)
theta' = 360 + theta            for -90 <= theta < 0,  phi = 0    (front, lower)
```

If the tabulated array has no exact entry at the required `theta'`,
interpolate between neighboring tabulated angles (our 1-degree
resolution makes this mostly exact; only relevant if resampling to a
different resolution).

### 2.3 Rotation estimate from the front lobe (Eq. 5 / Eq. 6)

For a chosen elevation `thetaP`, rotate the front-lobe vertical gain
around the full azimuth, using the horizontal pattern shape (normalized
to its own boresight value) as a multiplicative weight:

```
G_R(thetaP, phi) = [ gh(phi) / gh(0) ] * gv(thetaP)
```

If `gh(0)` is near zero (boresight near a null), normalize by the
horizontal pattern's maximum value instead:

```
G_R(thetaP, phi) = [ gh(phi) / gh_max ] * gv(thetaP)
```

This is the classic "rotation method" from prior art on its own. Its
known defect (documented in the patent, Section "Description of the
Related Art"): it only uses the front-lobe vertical gain — the back
lobe of the vertical pattern is discarded entirely, which can miss real
back-lobe structure by a large margin (the patent cites over 12 dB
error in one example).

### 2.4 Correction term from the back lobe (Eq. 7 / Eq. 8)

Compare what the front-lobe rotation predicts at the back meridian
(`phi=180`) against the actual measured back-lobe vertical gain, and
turn the mismatch into a correction:

```
delta(thetaP, 180) = gv(180 - thetaP) - [ gh(180) / gh(0) ] * gv(thetaP)
```

Generalize this correction to all `phi` using a transition weight
function `W(phi)` (Section 2.6) that is 0 at `phi=0` and 1 at `phi=180`:

```
delta(thetaP, phi) = W(phi) * { gv(180 - thetaP) - [ gh(180) / gh(0) ] * gv(thetaP) }
```

### 2.5 Final hybrid estimate (Eq. 9 / Eq. 10 / Eq. 11)

```
G_new(thetaP, phi) = G_R(thetaP, phi) + delta(thetaP, phi)
```

Equivalently (interpolation form, shows the horizontal pattern shaping
the interpolation weights themselves — this is the patent's core novel
result, not present in either prior-art method on its own):

```
G_new(thetaP, phi) = [ gh(phi)/gh(0) - W(phi)*gh(180) ] * gv(thetaP)
                    + W(phi) * gv(180 - thetaP)
```

For negative `thetaP` (southern hemisphere / lower elevations), the
same structure applies with the front-lobe index taken as
`gv(360 + thetaP)` instead of `gv(thetaP)`, per the mapping in Section
2.2. Implement this as a sign branch on `thetaP`, mirroring the two
formulas — do not derive a separate formula from scratch.

### 2.6 Transition weight function `W(phi)`

Requirement: `W(0) = 0`, `W(180) = 1`, monotonic in between, periodic
(symmetric back down to `W(360) = 0`).

**Linear (Eq. 12):**

```
W_linear(phi) = phi / 180                for 0 <= phi <= 180
W_linear(phi) = (360 - phi) / 180        for 180 < phi <= 360
```

**Cubic smoothstep (Eq. 13) — recommended default.** The patent
explicitly notes this produces smoother transitions with far fewer
"heart-shaped" artifacts than the linear version, because it has zero
slope at both `phi=0` and `phi=180`:

```
W_cubic(phi) = 3 * W_linear(phi)^2 - 2 * W_linear(phi)^3
```

**Decision:** use `W_cubic` as the default transition function. Only
fall back to `W_linear` if a specific validation case shows it performs
worse for a given antenna pattern — do not implement only the linear
version for simplicity.

### 2.7 Fast single-point form (Eq. 14)

For computing gain at one arbitrary `(theta, phi)` direction (not
building the full mesh — e.g. for a line-of-sight gain lookup, not part
of our RF-05 mesh generation but worth keeping as a documented
building block), the patent gives a closed form combining Sections 2.3
and 2.5 without materializing the full grid. Not required for v1 scope
(RF-05 asks for full mesh generation); documented here in case a future
feature needs single-direction gain without the mesh.

## 3. Grid construction and mesh assembly

1. Build a `theta x phi` grid at the unified contract's 1-degree
   resolution (or whichever resolution the reconstruction step targets;
   the input `pattern` arrays are 1-degree, the output mesh resolution
   is a separate parameter that may differ, e.g. the patent's own
   examples use 1 degree in theta and 6 degrees in phi for performance).
2. For each `thetaP` row, compute `G_new(thetaP, phi)` for all `phi`
   using Sections 2.3-2.6, in linear gain.
3. Convert each `G_new` value back to dB (Section "Critical
   implementation requirement").
4. Convert each `(theta, phi, magnitudeDb)` triple to Cartesian
   `(x, y, z)` using the same mapping as the revolution method (Section
   1), with `r` in linear gain.
5. Connect adjacent grid points into triangular or quad faces to form
   the exportable mesh (RF-08 / the `{x, y, z, magnitudeDb}` array).

## 4. Scope boundaries for this implementation

- Only exactly two, mutually orthogonal views are supported for the
  `patent` method in this system (matches RF-04's "2 views" wording).
  The patent's own text mentions extensions to non-orthogonal slices and
  to more than two slices (applied sequentially per angular sector) —
  these are explicitly OUT OF SCOPE. Do not implement them without a
  separate design discussion.
- The reconstructed surface is not claimed to be physically unique or
  exact — the patent's own background section states this explicitly:
  given only two cross sections, infinitely many 3D surfaces are
  consistent with them, and this method produces "a reasonable
  estimate," not "the correct" one. This directly affects how CP-07
  validation thresholds should be interpreted: expect structural/
  qualitative agreement with reference data (main-lobe direction, gross
  shape, order-of-magnitude of side-lobe levels), not point-for-point
  exact match.
- Mismatches at the boundary conditions (front/back vertical gain not
  matching the horizontal pattern's value at the same meridian) are
  expected in real manufacturer data and are tolerated by design — do
  not "fix" or force-normalize the input patterns to make them agree
  before running the algorithm; that would defeat the purpose of a
  method designed specifically to be robust to this inconsistency.

## 5. Interpretation decisions log

Every ambiguity resolved while implementing this method goes here, with
a one-line justification. Do not resolve an ambiguity silently in code
without adding an entry.

| Decision | Resolution | Status |
|---|---|---|
| dB vs. linear gain in the algorithm's math | Convert to linear at the module boundary; never operate on dB directly | Resolved |
| Which `plane` maps to `gv` vs `gh` | XY -> horizontal (`gh`); XZ or YZ -> vertical (`gv`) | Resolved, pending confirmation |
| Raw angle convention (direction, boresight zero) vs. `theta`/`phi` | Not yet defined in the unified contract | **Open — blocks implementation** |
| Transition function | Cubic smoothstep (`W_cubic`) by default | Resolved |
| More than 2 views / non-orthogonal views | Out of scope for this implementation | Resolved |
