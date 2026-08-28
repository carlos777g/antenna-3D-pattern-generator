# outer_ring_detector.py
"""
Locate the outermost graticule ring, which is the radius the polar sampler
calibrates dB values against.

Approach: a datasheet polar plot draws evenly spaced concentric rings, so the
radial density profile of the ring mask is a periodic comb. Rather than hunting
for the single outermost ring - which fails on these images, where the graticule
is one anti-aliased pixel wide and inner rings are often denser than the outer
one - this module fits the comb: it scores candidate ring spacings by the mean
density at all ring_count multiples and takes the best-scoring spacing.

outer_radius_px = ring_count * period

ring_count comes from the manufacturer config, since it is read directly off the
plot's radial dB labels (e.g. labels -30, -22.5, -15, -7.5, 0 means 4 rings).
"""
import numpy as np

# Ring spacings below this are not physically plausible on these plots and
# invite locking onto anti-aliasing noise near the center.
MIN_RING_PERIOD_PX = 6.0

# Sub-pixel search step: ring spacing is rarely an exact integer once a
# datasheet has been rasterized and rescaled.
PERIOD_STEP_PX = 0.5

# Mean comb density below this means no ring structure was found at all.
MIN_COMB_SCORE = 0.05

# Radial slack when sampling a ring: a 1-px anti-aliased circle drawn at
# radius r leaves lit pixels at r-1 and r+1 too, and exact-integer sampling
# misses most of them.
RADIAL_TOLERANCE_PX = 1

ANGLE_STEP_DEG = 0.5


def measure_ring_density(
    ring_mask: np.ndarray,
    center: tuple,
    radius: float,
    radial_tolerance: int = RADIAL_TOLERANCE_PX,
    angle_step_deg: float = ANGLE_STEP_DEG,
) -> float:
    """
    Sample points around a circle of the given radius and return the fraction
    that land on a ring pixel.

    An angle counts as a hit if any pixel within radial_tolerance of the
    circle is lit, which is what makes thin anti-aliased graticules measurable.
    Points falling outside the image are excluded from the denominator.
    """
    if radius <= 0:
        return 0.0

    cx, cy = center
    height, width = ring_mask.shape

    angles = np.deg2rad(np.arange(0, 360, angle_step_deg))
    cos_a, sin_a = np.cos(angles), np.sin(angles)

    hit = np.zeros(angles.shape, dtype=bool)
    inside_any = np.zeros(angles.shape, dtype=bool)

    for offset in range(-radial_tolerance, radial_tolerance + 1):
        sample_radius = radius + offset
        if sample_radius <= 0:
            continue
        xs = np.round(cx + sample_radius * cos_a).astype(int)
        ys = np.round(cy + sample_radius * sin_a).astype(int)

        inside = (xs >= 0) & (xs < width) & (ys >= 0) & (ys < height)
        inside_any |= inside
        hit[inside] |= ring_mask[ys[inside], xs[inside]] == 255

    if not inside_any.any():
        return 0.0

    return float(np.count_nonzero(hit & inside_any) / np.count_nonzero(inside_any))


def max_fitting_radius(shape: tuple, center: tuple) -> int:
    """
    Largest radius fully contained in the image from this center. Beyond it,
    density measurements are taken over a truncated circle and stop being
    comparable between radii.
    """
    height, width = shape[:2]
    cx, cy = center
    return int(min(cx, cy, width - cx, height - cy))


def detect_ring_period(
    ring_mask: np.ndarray,
    center: tuple,
    ring_count: int,
    max_search_radius: float,
    min_period_px: float = MIN_RING_PERIOD_PX,
    period_step_px: float = PERIOD_STEP_PX,
) -> tuple[float, float] | None:
    """
    Find the ring spacing whose comb of ring_count multiples best matches the
    ring mask.

    Returns (period_px, score) where score is the mean density across the comb,
    or None if no candidate spacing fits inside max_search_radius.
    """
    if ring_count < 1:
        raise ValueError(f"ring_count must be >= 1, got {ring_count}")

    max_period = max_search_radius / ring_count
    if max_period < min_period_px:
        return None

    best_period = None
    best_score = -1.0

    for period in np.arange(min_period_px, max_period + 1e-9, period_step_px):
        score = float(np.mean([
            measure_ring_density(ring_mask, center, period * k)
            for k in range(1, ring_count + 1)
        ]))
        if score > best_score:
            best_score = score
            best_period = float(period)

    if best_period is None:
        return None
    return best_period, best_score


def detect_outer_ring(
    ring_mask: np.ndarray,
    center: tuple,
    ring_count: int,
    max_ring_radius_px: int | None = None,
    min_comb_score: float = MIN_COMB_SCORE,
) -> float | None:
    """
    Find the outermost graticule ring radius.

    Parameters
    ----------
    ring_mask          : H x W uint8, 255 = ring pixel, 0 = background
    center             : (cx, cy) in pixel coordinates
    ring_count         : number of concentric rings between the plot center and
                         the outermost ring, from the manufacturer config
    max_ring_radius_px : optional upper bound on the outer radius. Capped at the
                         largest radius that fits in the image, so an
                         over-generous config value is harmless - unlike an
                         over-tight one, which used to hide the real ring.
    min_comb_score     : minimum mean ring density to accept a fit

    Returns
    -------
    outer_radius_px : float, or None if no ring structure was found
    """
    if center is None:
        return None

    fitting = max_fitting_radius(ring_mask.shape, center)
    max_search_radius = fitting if max_ring_radius_px is None else min(
        float(max_ring_radius_px), float(fitting)
    )
    if max_search_radius <= 0:
        return None

    fit = detect_ring_period(ring_mask, center, ring_count, max_search_radius)
    if fit is None:
        return None

    period, score = fit
    if score < min_comb_score:
        return None

    return round(period * ring_count, 1)
