import cv2
import numpy as np
from typing import Optional


def detect_pattern_center_and_outer_ring(
    img_rgb: np.ndarray,
    circle_color_range: dict,
    max_ring_radius_px: int,
    min_radius: int = 20,
    hough_accumulator_threshold: int = 20,
    ring_density_threshold: float = 0.10,
) -> dict:
    """
    Single entry point for circle detection. Returns both the consensus
    center and the outer ring radius.

    Separating these into two Hough passes was unnecessary complexity:
    both pieces of information come from the same set of detected circles.

    Parameters
    ----------
    img_rgb                    : H x W x 3 RGB image
    circle_color_range         : RGB range for the concentric ring color
    max_ring_radius_px         : hard upper bound on ring radius. Set this
                                 per manufacturer to prevent false positives
                                 larger than the actual outer ring.
    min_radius                 : lower bound on ring radius in pixels
    hough_accumulator_threshold: lower = more circles detected (more noise),
                                 higher = fewer circles (may miss real ones).
                                 Tune per manufacturer if needed.
    ring_density_threshold     : minimum fraction of a circle's circumference
                                 that must contain ring-colored pixels for it
                                 to be accepted as a real ring.
                                 0.10 means 10% of the circumference.

    Returns
    -------
    dict:
        center           : (cx, cy) or None
        outer_radius_px  : float or None
        all_radii        : list of accepted ring radii (diagnostic)
        rejected_radii   : list of radii that failed density check (diagnostic)
    """
    ring_mask = _build_ring_mask(img_rgb, circle_color_range)
    blurred = cv2.GaussianBlur(ring_mask, (5, 5), sigmaX=1.5)
    height, width = ring_mask.shape

    raw_circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=hough_accumulator_threshold,
        minRadius=min_radius,
        maxRadius=max_ring_radius_px,
    )

    if raw_circles is None:
        return {
            "center": None,
            "outer_radius_px": None,
            "all_radii": [],
            "rejected_radii": [],
        }

    raw_circles = np.round(raw_circles[0]).astype(int)  # shape (N, 3): cx, cy, r

    # Step 1: get consensus center from all detected circles
    center = _consensus_center(raw_circles)
    cx, cy = center

    # Step 2: validate each detected radius by measuring actual pixel density
    # at that distance from the consensus center.
    # This rejects Hough false positives that have no real pixels on their circumference.
    accepted_radii = []
    rejected_radii = []

    for circle in raw_circles:
        r = int(circle[2])
        density = _measure_ring_density(ring_mask, cx, cy, r, height, width)
        if density >= ring_density_threshold:
            accepted_radii.append(r)
        else:
            rejected_radii.append(r)

    outer_radius_px = float(max(accepted_radii)) if accepted_radii else None

    return {
        "center": center,
        "outer_radius_px": outer_radius_px,
        "all_radii": sorted(accepted_radii),
        "rejected_radii": sorted(rejected_radii),
    }


def _measure_ring_density(
    ring_mask: np.ndarray,
    cx: int, cy: int,
    radius: int,
    height: int, width: int,
    angle_step_deg: float = 1.0,
) -> float:
    """
    Sample 360 points around a circle of given radius centered at (cx, cy).
    Return the fraction of sampled points that contain ring-colored pixels.
    """
    angles = np.deg2rad(np.arange(0, 360, angle_step_deg))
    xs = np.round(cx + radius * np.cos(angles)).astype(int)
    ys = np.round(cy + radius * np.sin(angles)).astype(int)

    valid = (xs >= 0) & (xs < width) & (ys >= 0) & (ys < height)
    xs, ys = xs[valid], ys[valid]

    if len(xs) == 0:
        return 0.0

    return float(np.sum(ring_mask[ys, xs] > 0)) / len(xs)


def _build_ring_mask(img_rgb: np.ndarray, circle_color_range: dict) -> np.ndarray:
    r, g, b = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]
    match = (
        (r >= circle_color_range["r_min"]) & (r <= circle_color_range["r_max"]) &
        (g >= circle_color_range["g_min"]) & (g <= circle_color_range["g_max"]) &
        (b >= circle_color_range["b_min"]) & (b <= circle_color_range["b_max"])
    )
    out = np.zeros(r.shape, dtype=np.uint8)
    out[match] = 255
    return out


def _consensus_center(circles: np.ndarray, tolerance: int = 15) -> tuple:
    centers = circles[:, :2]
    clusters = []

    for cx, cy in centers:
        placed = False
        for cluster in clusters:
            mean_cx = np.mean([p[0] for p in cluster])
            mean_cy = np.mean([p[1] for p in cluster])
            if abs(cx - mean_cx) <= tolerance and abs(cy - mean_cy) <= tolerance:
                cluster.append((cx, cy))
                placed = True
                break
        if not placed:
            clusters.append([(cx, cy)])

    largest = max(clusters, key=len)
    return (
        int(np.mean([p[0] for p in largest])),
        int(np.mean([p[1] for p in largest])),
    )