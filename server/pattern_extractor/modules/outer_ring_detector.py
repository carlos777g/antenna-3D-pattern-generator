import numpy as np


def detect_outer_ring(
    ring_mask: np.ndarray,
    center: tuple,
    max_ring_radius_px: int,
    min_radius: int = 10,
    density_threshold: float = 0.10,
) -> float | None:
    """
    Find the outermost concentric ring radius by scanning from
    max_ring_radius_px inward and measuring pixel density at each radius.

    Parameters
    ----------
    ring_mask          : H x W uint8, 255 = ring pixel, 0 = background
    center             : (cx, cy) in pixel coordinates
    max_ring_radius_px : upper bound for search, from manufacturer config
    min_radius         : lower bound for search in pixels
    density_threshold  : minimum fraction of circumference that must contain
                         ring pixels to accept a radius as a real ring

    Returns
    -------
    outer_radius_px : float, or None if no valid ring found
    """
    cx, cy = center
    height, width = ring_mask.shape

    best_radius = None
    best_density = 0.0

    for r in range(max_ring_radius_px, min_radius, -1):
        density = _measure_ring_density(ring_mask, cx, cy, r, height, width)
        if density >= density_threshold:
            if density > best_density:
                best_density = density
                best_radius = r
            elif best_radius is not None and density < density_threshold * 0.5:
                break

    return float(best_radius) if best_radius is not None else None


def _measure_ring_density(
    ring_mask: np.ndarray,
    cx: int, cy: int,
    radius: int,
    height: int, width: int,
    angle_step_deg: float = 1.0,
) -> float:
    """
    Sample 360 points around a circle of given radius centered at (cx, cy).
    Return the fraction of sampled points that are ring pixels (255).
    """
    angles = np.deg2rad(np.arange(0, 360, angle_step_deg))
    xs = np.round(cx + radius * np.cos(angles)).astype(int)
    ys = np.round(cy + radius * np.sin(angles)).astype(int)

    valid = (xs >= 0) & (xs < width) & (ys >= 0) & (ys < height)
    xs, ys = xs[valid], ys[valid]

    if len(xs) == 0:
        return 0.0

    return float(np.sum(ring_mask[ys, xs] == 255)) / len(xs)