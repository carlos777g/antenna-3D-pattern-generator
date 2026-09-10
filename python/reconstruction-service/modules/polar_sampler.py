# polar_sampler.py
import numpy as np
from typing import Optional

# Pixel value that marks a pattern pixel. See modules/rgb_range.py:
# every mask in this service uses 255 = feature, 0 = background.
PATTERN_PIXEL = 255

# Ray walking is sub-pixel and slightly tolerant off-axis, because the plotted
# trace is one anti-aliased pixel wide: a ray stepping 1 px at a time along a
# diagonal skips past a thin curve entirely. Measured on the calibrated
# datasheets, integer stepping with no tolerance found the trace on only 54-72%
# of rays for three of five manufacturers; these settings raise that to
# 81-100%. The cost is up to 1 px of radial slack, well inside the dB
# resolution of a rasterized datasheet plot.
RADIAL_STEP_PX = 0.5
NEIGHBOURHOOD_PX = 1


def sample_polar(
    mask: np.ndarray,
    center: tuple,
    outer_radius_px: float,
    db_scale: dict,
    angle_offset_deg: float = 0.0,
    angle_step_deg: float = 1.0,
    ray_search_margin_px: int = 10,
) -> list[dict]:
    """
    For each angle, cast a ray from center outward and find the outermost
    pattern pixel. Map its distance to a dB value using the radial calibration.

    Calibration is interpolated in radius between anchors read off the
    datasheet plot. `db_scale` is either:
    - simple: {"center_db": ..., "outer_db": ...} - a single linear span from
      the plot center to the outermost graticule ring detected by
      modules/outer_ring_detector.py.
    - piecewise: {"anchors": [(ring, db), ...], "ring_divisions": N} - for
      datasheets whose printed dB labels are not evenly spaced per ring. See
      _resolve_db_anchors.

    Parameters
    ----------
    mask              : binary mask, 255 = pattern pixel, 0 = background
    center            : (cx, cy) in pixel coordinates
    outer_radius_px   : radius in pixels of the outermost graticule ring,
                        as detected by modules/outer_ring_detector.py -
                        never recomputed from the pattern mask here
    db_scale          : radial dB calibration, see above
    angle_offset_deg  : rotation offset so that 0 deg points to the correct
                        direction in the image (0 = right / East by default)
    angle_step_deg    : angular resolution of the output (default 1 deg)
    ray_search_margin_px: extra pixels beyond the outermost ring radius to
                          search, to avoid clipping a trace that overshoots it

    Returns
    -------
    List of dicts: [{"angle_deg": float, "magnitude_db": float | None}, ...]
    None magnitude means no pattern pixel was found along that ray.
    """
    if center is None:
        raise ValueError("center is required; caller must handle a failed detection")
    if outer_radius_px is None or outer_radius_px <= 0:
        raise ValueError(f"outer_radius_px must be positive, got {outer_radius_px}")

    radii_anchors, db_anchors = _resolve_db_anchors(db_scale, outer_radius_px)

    cx, cy = center
    height, width = mask.shape

    # Search a little past the calibration ring, but never past the image edge
    # in the direction of travel; _sample_ray stops at the border anyway.
    max_search_radius = int(round(outer_radius_px)) + ray_search_margin_px
    diagonal = int(np.ceil(np.hypot(height, width)))
    max_search_radius = min(max_search_radius, diagonal)

    results = []
    for angle_deg in np.arange(0, 360, angle_step_deg):
        # angle_offset rotates the coordinate system so that the caller's
        # 0 deg maps to the correct image direction
        effective_angle_rad = np.deg2rad(angle_deg + angle_offset_deg)

        dx = np.cos(effective_angle_rad)
        dy = -np.sin(effective_angle_rad)  # y-axis is inverted in image coordinates

        magnitude_db = _sample_ray(
            mask, cx, cy, dx, dy,
            max_search_radius,
            radii_anchors, db_anchors,
        )

        results.append({
            "angle_deg": round(float(angle_deg), 2),
            "magnitude_db": magnitude_db,
        })

    return results


def _hits_pattern(mask: np.ndarray, px: int, py: int, neighbourhood_px: int) -> bool:
    """
    True if (px, py) or any pixel within neighbourhood_px on the axes is a
    pattern pixel. Only the 4-neighbourhood is checked: a diagonal-only match
    is more likely to be a neighbouring stroke than this ray's trace.
    """
    height, width = mask.shape
    for offset_x, offset_y in _neighbourhood_offsets(neighbourhood_px):
        x, y = px + offset_x, py + offset_y
        if 0 <= x < width and 0 <= y < height and mask[y, x] == PATTERN_PIXEL:
            return True
    return False


def _neighbourhood_offsets(neighbourhood_px: int) -> list[tuple[int, int]]:
    offsets = [(0, 0)]
    for distance in range(1, neighbourhood_px + 1):
        offsets.extend([
            (distance, 0), (-distance, 0), (0, distance), (0, -distance),
        ])
    return offsets


def _resolve_db_anchors(db_scale: dict, outer_radius_px: float) -> tuple:
    """
    Build the (radius_px, magnitude_db) calibration points used for
    np.interp, sorted by ascending radius.

    Two config shapes are supported:
    - simple: {"center_db": ..., "outer_db": ...} - one span from the plot
      center (radius 0) to the outer ring (outer_radius_px).
    - piecewise: {"anchors": [(ring, db), ...], "ring_divisions": N} - for a
      datasheet whose graticule rings are evenly spaced in pixels but whose
      printed dB labels are not evenly spaced per ring. `ring` counts rings
      inward from the outer ring (ring 0 = outer_radius_px); `ring_divisions`
      is the total number of equal pixel divisions from the outer ring to the
      plot center (which need not itself be a labeled anchor). The radius for
      a given ring is outer_radius_px * (ring_divisions - ring) / ring_divisions.
    """
    if "anchors" in db_scale:
        ring_divisions = db_scale["ring_divisions"]
        points = sorted(
            (outer_radius_px * (ring_divisions - ring) / ring_divisions, db)
            for ring, db in db_scale["anchors"]
        )
        radii = np.array([r for r, _ in points], dtype=float)
        dbs = np.array([d for _, d in points], dtype=float)
        return radii, dbs

    return (
        np.array([0.0, float(outer_radius_px)]),
        np.array([db_scale["center_db"], db_scale["outer_db"]]),
    )


def _sample_ray(
    mask: np.ndarray,
    cx: int, cy: int,
    dx: float, dy: float,
    max_search_radius: int,
    radii_anchors: np.ndarray,
    db_anchors: np.ndarray,
    radial_step_px: float = RADIAL_STEP_PX,
    neighbourhood_px: int = NEIGHBOURHOOD_PX,
) -> Optional[float]:
    """
    Walk outward along a ray and find the outermost pattern pixel.
    Map that pixel's distance to a dB value by radial interpolation between
    the calibration anchors. Returns None if no pattern pixel is found along
    the ray.
    """
    height, width = mask.shape
    outermost_distance = None

    steps = int(round(max_search_radius / radial_step_px))
    for step_index in range(1, steps + 1):
        distance = step_index * radial_step_px
        px = int(round(cx + dx * distance))
        py = int(round(cy + dy * distance))

        if px < 0 or px >= width or py < 0 or py >= height:
            break

        if _hits_pattern(mask, px, py, neighbourhood_px):
            outermost_distance = distance

    if outermost_distance is None:
        return None

    # np.interp clamps outside the anchor range, so a trace overshooting the
    # outermost or innermost anchor saturates at that anchor's dB instead of
    # extrapolating past the scale.
    magnitude_db = float(np.interp(outermost_distance, radii_anchors, db_anchors))

    return round(magnitude_db, 2)


def fill_angular_gaps(samples: list[dict], max_gap_deg: float = 5.0) -> list[dict]:
    """
    Interpolate short runs of missing magnitudes.

    Anti-aliasing and thin plot strokes leave isolated angles where no pattern
    pixel lands on the integer ray. A run of consecutive None values is filled
    by linear interpolation between its two valid neighbours when the run spans
    at most max_gap_deg; longer runs are left as None, since those indicate a
    genuine extraction failure rather than a sampling artifact.

    Wraps around 359 -> 0, because the pattern is angularly periodic.
    Returns a new list; the input is not modified.
    """
    filled = [dict(sample) for sample in samples]
    count = len(filled)
    if count == 0:
        return filled

    valid_indices = [i for i, s in enumerate(filled) if s["magnitude_db"] is not None]
    if not valid_indices or len(valid_indices) == count:
        return filled

    step_deg = 360.0 / count

    for position, start_valid in enumerate(valid_indices):
        end_valid = valid_indices[(position + 1) % len(valid_indices)]

        # Number of missing samples between these two valid neighbours
        gap_length = (end_valid - start_valid - 1) % count
        if gap_length == 0 or gap_length * step_deg > max_gap_deg:
            continue

        start_db = filled[start_valid]["magnitude_db"]
        end_db = filled[end_valid]["magnitude_db"]

        for offset in range(1, gap_length + 1):
            index = (start_valid + offset) % count
            weight = offset / (gap_length + 1)
            filled[index]["magnitude_db"] = round(
                start_db + (end_db - start_db) * weight, 2
            )

    return filled


def db_scale_bounds(db_scale: dict) -> tuple[float, float]:
    """
    (min_db, max_db) spanned by a db_scale config, regardless of whether it is
    the simple center/outer shape or the piecewise anchors shape. Used to
    sanity-check that extracted magnitudes stay within the declared scale.
    """
    if "anchors" in db_scale:
        dbs = [db for _, db in db_scale["anchors"]]
        return min(dbs), max(dbs)
    return db_scale["center_db"], db_scale["outer_db"]


def coverage_ratio(samples: list[dict]) -> float:
    """
    Fraction of samples that carry a magnitude, in [0.0, 1.0].
    A low value means the pattern trace was not detected across most angles,
    which usually means this manufacturer's rgb_range needs retuning.
    """
    if not samples:
        return 0.0
    valid = sum(1 for s in samples if s["magnitude_db"] is not None)
    return round(valid / len(samples), 4)
