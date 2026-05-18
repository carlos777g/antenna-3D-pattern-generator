import numpy as np


def extract_pattern_mask(img_rgb: np.ndarray, rgb_range: dict) -> np.ndarray:
    """
    Apply rgb_range filter to isolate pattern pixels.

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
    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]

    pattern_pixels = (
        (r >= rgb_range["r_min"]) & (r <= rgb_range["r_max"]) &
        (g >= rgb_range["g_min"]) & (g <= rgb_range["g_max"]) &
        (b >= rgb_range["b_min"]) & (b <= rgb_range["b_max"])
    )

    mask = np.zeros(r.shape, dtype=np.uint8)
    mask[pattern_pixels] = 255

    total = mask.size
    pattern_count = int(np.sum(mask == 255))
    stats = {
        "total_pixels": total,
        "pattern_pixels": pattern_count,
        "pattern_ratio": round(pattern_count / total, 4),
    }

    return mask, stats