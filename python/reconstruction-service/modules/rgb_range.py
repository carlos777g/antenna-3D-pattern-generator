# rgb_range.py
import numpy as np

RGB_RANGE_KEYS = ("r_min", "r_max", "g_min", "g_max", "b_min", "b_max")


def apply_rgb_range(img_rgb: np.ndarray, rgb_range: dict) -> np.ndarray:
    """
    Build a binary mask of the pixels whose RGB components all fall inside
    the inclusive per-channel bounds of rgb_range.

    Module-wide mask convention: 255 = matched (feature) pixel,
    0 = background. Every mask produced in this service follows it.

    Parameters
    ----------
    img_rgb   : H x W x 3 numpy array in RGB order
    rgb_range : dict with keys r_min, r_max, g_min, g_max, b_min, b_max

    Returns
    -------
    mask : np.ndarray (H x W, uint8), 255 = matched, 0 = background
    """
    missing = [key for key in RGB_RANGE_KEYS if key not in rgb_range]
    if missing:
        raise KeyError(f"rgb_range is missing required keys: {missing}")

    if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        raise ValueError(
            f"Expected an H x W x 3 RGB array, got shape {img_rgb.shape}"
        )

    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]

    matched = (
        (r >= rgb_range["r_min"]) & (r <= rgb_range["r_max"]) &
        (g >= rgb_range["g_min"]) & (g <= rgb_range["g_max"]) &
        (b >= rgb_range["b_min"]) & (b <= rgb_range["b_max"])
    )

    mask = np.zeros(r.shape, dtype=np.uint8)
    mask[matched] = 255
    return mask
