import cv2
import numpy as np


def extract_ring_mask(img_rgb: np.ndarray, circle_color_range: dict) -> np.ndarray:
    """
    Isolate pixels matching the concentric ring color range.

    Returns
    -------
    ring_mask : np.ndarray (H x W, uint8)
        255 = ring-colored pixel
        0   = everything else
    """
    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]

    match = (
        (r >= circle_color_range["r_min"]) & (r <= circle_color_range["r_max"]) &
        (g >= circle_color_range["g_min"]) & (g <= circle_color_range["g_max"]) &
        (b >= circle_color_range["b_min"]) & (b <= circle_color_range["b_max"])
    )

    ring_mask = np.zeros(r.shape, dtype=np.uint8)
    ring_mask[match] = 255

    return ring_mask