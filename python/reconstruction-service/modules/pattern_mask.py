# pattern_mask.py
import numpy as np

from modules.rgb_range import apply_rgb_range


def extract_pattern_mask(img_rgb: np.ndarray, rgb_range: dict) -> tuple[np.ndarray, dict]:
    """
    Apply rgb_range filter to isolate the plotted pattern trace.

    Returns
    ----------------
    mask : np.ndarray (H x W, uint8)
        255 = pattern pixel (matched rgb_range)
        0   = background pixel
    stats : dict
        total_pixels, pattern_pixels, pattern_ratio
    ----------------

    Parameters
    ----------------
    img_rgb  : H x W x 3 numpy array in RGB order
    rgb_range: dict with keys r_min, r_max, g_min, g_max, b_min, b_max
    """
    mask = apply_rgb_range(img_rgb, rgb_range)

    total = mask.size
    pattern_count = int(np.count_nonzero(mask == 255))
    stats = {
        "total_pixels": total,
        "pattern_pixels": pattern_count,
        "pattern_ratio": round(pattern_count / total, 4),
    }

    return mask, stats
