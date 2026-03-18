import cv2
import numpy as np


def detect_concentric_circles(
    img_rgb: np.ndarray,
    circle_color_range: dict,
    min_radius: int = 20,
    max_radius: int = 500,
) -> dict:
    """
    Detect concentric circles in the image to estimate the radiation
    pattern center and available ring radii.

    Strategy:
        1. Isolate pixels matching the circle color range -> binary mask
        2. Apply Hough Circle Transform on that mask
        3. Cluster detected circles by center proximity to find consensus center
        4. Return center (cx, cy) and sorted list of detected radii

    Parameters
    ----------
    img_rgb          : H x W x 3 RGB image
    circle_color_range: dict with r/g/b min/max for the ring color
    min_radius       : minimum circle radius to search for (pixels)
    max_radius       : maximum circle radius to search for (pixels)

    Returns
    -------
    dict with keys:
        center   : (cx, cy) tuple in pixel coordinates, or None if not found
        radii    : sorted list of detected ring radii in pixels
        debug_circles: raw Hough output for visualization
    """
    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]

    ring_pixels = (
        (r >= circle_color_range["r_min"]) & (r <= circle_color_range["r_max"]) &
        (g >= circle_color_range["g_min"]) & (g <= circle_color_range["g_max"]) &
        (b >= circle_color_range["b_min"]) & (b <= circle_color_range["b_max"])
    )

    ring_mask = np.zeros(r.shape, dtype=np.uint8)
    ring_mask[ring_pixels] = 255

    # Hough needs a single-channel uint8 image
    # We apply a slight blur to reduce noise from PNG compression artifacts
    blurred = cv2.GaussianBlur(ring_mask, (5, 5), sigmaX=1.5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,          # minimum distance between circle centers
        param1=50,           # Canny high threshold (internal edge detection)
        param2=20,           # accumulator threshold: lower = more false positives
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    if circles is None:
        return {"center": None, "radii": [], "debug_circles": None}

    circles = np.round(circles[0]).astype(int)  # shape: (N, 3) -> [cx, cy, r]

    center = _consensus_center(circles)
    radii = sorted([int(c[2]) for c in circles])

    return {
        "center": center,
        "radii": radii,
        "debug_circles": circles,
    }


def _consensus_center(circles: np.ndarray, tolerance: int = 15) -> tuple:
    """
    Given detected circles, find the most agreed-upon center.
    Circles whose centers are within `tolerance` pixels of each other
    are considered the same center. Returns the centroid of the
    largest cluster.
    """
    centers = circles[:, :2]  # (N, 2)
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
    cx = int(np.mean([p[0] for p in largest]))
    cy = int(np.mean([p[1] for p in largest]))
    return (cx, cy)