import numpy as np


def extract_pattern_mask(img_rgb: np.ndarray, rgb_range: dict) -> np.ndarray:
    """
    Build a binary mask from an RGB image given per-channel ranges.

    Returns a uint8 array with:
        0   -> pattern pixel (matches the range)
        255 -> background pixel

    Parameters
    ----------
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

    mask = np.full(r.shape, 255, dtype=np.uint8)
    mask[pattern_pixels] = 0

    stats = _mask_stats(mask)
    return mask, stats


def _mask_stats(mask: np.ndarray) -> dict:
    total = mask.size
    pattern_count = int(np.sum(mask == 0))
    return {
        "total_pixels": total,
        "pattern_pixels": pattern_count,
        "pattern_ratio": round(pattern_count / total, 4),
    }