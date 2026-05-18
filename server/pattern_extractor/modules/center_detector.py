import cv2
import numpy as np
from typing import Optional


def detect_center(ring_mask: np.ndarray) -> Optional[tuple]:
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
        minRadius=20,
        maxRadius=0,   # 0 = no upper limit, handled by ring_mask content
    )

    if circles is None:
        return None

    circles = np.round(circles[0]).astype(int)
    center = _consensus_center(circles)
    return center


def _consensus_center(circles: np.ndarray, tolerance: int = 15) -> tuple:
    """
    Cluster circle centers within tolerance pixels and return the centroid
    of the largest cluster.
    """
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