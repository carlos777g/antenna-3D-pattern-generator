import cv2
import numpy as np
from typing import Optional


def detect_center(ring_mask: np.ndarray, center_method: str = "largest_cluster", hough_min_radius: int = 20, hough_max_radius: int = 110,) -> Optional[tuple]:
    """
    Detect the radiation pattern center by running Hough Circle Transform
    on the ring mask and computing the consensus center across all detected
    circles.

    Parameters
    ----------
    ring_mask : np.ndarray (H x W, uint8)
        Output of ring_mask_extractor. 255 = ring pixel, 0 = background.

    Returns
    -------
    center : tuple (cx, cy) in pixel coordinates, or None if not found.
    """
    blurred = cv2.GaussianBlur(ring_mask, (5, 5), sigmaX=1.5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=20,
        param1=50,
        param2=20,
        minRadius=hough_min_radius, # 70 gives better results for quectel
        maxRadius=hough_max_radius,   # 0 = no upper limit, handled by ring_mask content, 90 gives better results for quectel
    )

    if circles is None:
        return None

    circles = np.round(circles[0]).astype(int)
    center = _consensus_center(circles, method=center_method)
    return center


def _consensus_center(circles: np.ndarray, tolerance: int = 15, method: str = "largest_cluster") -> tuple:
    """
    Cluster circle centers within tolerance pixels and return the centroid
    of the largest cluster.
    """
    if method == "median":
        median_cx = float(np.median(circles[:, 0]))
        median_cy = float(np.median(circles[:, 1]))
        refined = [
            (cx, cy) for cx, cy, _ in circles
            if abs(cx - median_cx) <= tolerance and abs(cy - median_cy) <= tolerance
        ]
        if not refined:
            return (int(median_cx), int(median_cy))
        return (
            int(np.mean([p[0] for p in refined])),
            int(np.mean([p[1] for p in refined])),
        )

    # default: largest_cluster
    clusters = []
    for cx, cy, _ in circles:
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