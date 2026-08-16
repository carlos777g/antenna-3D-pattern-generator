# polar_sampler.py
import numpy as np
from typing import Optional


def sample_polar(
    mask: np.ndarray,
    center: tuple,
    db_scale: dict,
    angle_offset_deg: float = 0.0,
    angle_step_deg: float = 1.0,
    ray_search_margin_px: int = 10,
) -> list[dict]:
    """
    For each angle, cast a ray from center outward and find the outermost
    pattern pixel. Map its distance to a dB value using the ring calibration.

    The ring calibration assumes evenly spaced concentric rings between
    the minimum and maximum radius found from the mask bounding geometry.

    Parameters
    ----------
    mask              : binary mask, 0 = pattern pixel, 255 = background
    center            : (cx, cy) in pixel coordinates
    db_scale          : dict with keys: rings, min_db, max_db
    angle_offset_deg  : rotation offset so that 0 deg points to the correct
                        direction in the image (0 = right / East by default)
    angle_step_deg    : angular resolution of the output (default 1 deg)
    ray_search_margin_px: extra pixels beyond the outermost detected radius
                          to search, to avoid clipping the pattern edge

    Returns
    -------
    List of dicts: [{"angle_deg": float, "magnitude_db": float | None}, ...]
    None magnitude means no pattern pixel was found along that ray.
    """
    cx, cy = center
    height, width = mask.shape

    # Estimate the maximum useful radius from the image geometry
    max_possible_radius = int(min(
        cx, cy,
        width - cx,
        height - cy,
    )) + ray_search_margin_px

    # Build the ring-to-dB linear mapping
    # ring 0 = innermost, ring (rings-1) = outermost
    num_rings = db_scale["rings"]
    min_db = db_scale["min_db"]
    max_db = db_scale["max_db"]

    # Estimate ring radii from the mask itself: find the outermost pattern pixel
    # distance from center, then distribute rings evenly up to that distance
    pattern_coords = np.argwhere(mask == 0)  # (row, col) pairs
    if len(pattern_coords) == 0:
        return []

    # Distance of each pattern pixel from center
    rows, cols = pattern_coords[:, 0], pattern_coords[:, 1]
    distances = np.sqrt((cols - cx) ** 2 + (rows - cy) ** 2)
    outer_radius_px = float(np.percentile(distances, 95))  # use 95th percentile to ignore outliers

    ring_radii_px = np.linspace(0, outer_radius_px, num_rings + 1)[1:]  # exclude r=0

    results = []
    angles_deg = np.arange(0, 360, angle_step_deg)

    for angle_deg in angles_deg:
        # Apply offset and convert to radians
        # angle_offset rotates the coordinate system so that the caller's
        # 0 deg maps to the correct image direction
        effective_angle_rad = np.deg2rad(angle_deg + angle_offset_deg)

        # Direction vector for this ray
        dx = np.cos(effective_angle_rad)
        dy = -np.sin(effective_angle_rad)  # y-axis is inverted in image coordinates

        magnitude_db = _sample_ray(
            mask, cx, cy, dx, dy,
            max_possible_radius,
            ring_radii_px,
            min_db, max_db,
        )

        results.append({
            "angle_deg": round(float(angle_deg), 2),
            "magnitude_db": magnitude_db,
        })

    return results


def _sample_ray(
    mask: np.ndarray,
    cx: int, cy: int,
    dx: float, dy: float,
    max_radius: int,
    ring_radii_px: np.ndarray,
    min_db: float,
    max_db: float,
) -> Optional[float]:
    """
    Walk outward along a ray and find the outermost pattern pixel.
    Map that pixel's distance to a dB value by interpolating between ring radii.
    Returns None if no pattern pixel is found along the ray.
    """
    height, width = mask.shape
    outermost_distance = None

    # Walk the ray pixel by pixel using Bresenham-style integer steps
    for step in range(1, max_radius):
        px = int(round(cx + dx * step))
        py = int(round(cy + dy * step))

        if px < 0 or px >= width or py < 0 or py >= height:
            break

        if mask[py, px] == 0:  # pattern pixel
            outermost_distance = float(step)

    if outermost_distance is None:
        return None

    # Map distance to dB via linear interpolation across the ring radii
    # ring_radii_px[-1] maps to min_db (outermost = lowest gain)
    # ring_radii_px[0]  maps to max_db (innermost = highest gain)
    # Note: check your config — min_db/max_db naming is relative to ring position,
    # not necessarily to dB value magnitude (some manufacturers have inverted scales)
    magnitude_db = float(np.interp(
        outermost_distance,
        [ring_radii_px[0], ring_radii_px[-1]],
        [max_db, min_db],
    ))

    return round(magnitude_db, 2)
