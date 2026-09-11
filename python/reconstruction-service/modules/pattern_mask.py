# pattern_mask.py
import cv2
import numpy as np

from modules.rgb_range import apply_rgb_range


def extract_pattern_mask(img_rgb: np.ndarray, rgb_range: dict) -> tuple[np.ndarray, dict]:
    """
    Apply rgb_range filter to isolate the plotted pattern trace.

    A morphological closing (dilation then erosion) is applied to fill small
    gaps in the detected trace, which occur when the color range is precise
    enough to avoid noise but tight enough that anti-aliasing creates
    discontinuities.

    Returns
    ----------------
    mask : np.ndarray (H x W, uint8)
        255 = pattern pixel (matched rgb_range)
        0   = background pixel
    stats : dict
        total_pixels, pattern_pixels, pattern_ratio (after closing)
    ----------------

    Parameters
    ----------------
    img_rgb  : H x W x 3 numpy array in RGB order
    rgb_range: dict with keys r_min, r_max, g_min, g_max, b_min, b_max
    """
    mask = apply_rgb_range(img_rgb, rgb_range)

    # Morphological closing: fills small gaps (internal holes) in the trace
    # without expanding the outer boundary significantly. Kernel size 3x3
    # targets gaps 1-2 pixels wide, typical of anti-aliasing in rasterized
    # plots when the color range is restrictive.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    total = mask.size
    pattern_count = int(np.count_nonzero(mask == 255))
    stats = {
        "total_pixels": total,
        "pattern_pixels": pattern_count,
        "pattern_ratio": round(pattern_count / total, 4),
    }

    return mask, stats
