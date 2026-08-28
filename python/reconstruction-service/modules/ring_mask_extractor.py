# ring_mask_extractor.py
import numpy as np

from modules.rgb_range import apply_rgb_range


def extract_ring_mask(img_rgb: np.ndarray, circle_color_range: dict) -> np.ndarray:
    """
    Isolate pixels matching the concentric ring (graticule) color range.

    Returns
    -------
    ring_mask : np.ndarray (H x W, uint8)
        255 = ring-colored pixel
        0   = everything else
    """
    return apply_rgb_range(img_rgb, circle_color_range)
