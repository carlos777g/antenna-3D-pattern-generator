# test_rgb_range.py
import numpy as np
import pytest

from modules.rgb_range import apply_rgb_range

RANGE = {"r_min": 10, "r_max": 20, "g_min": 0, "g_max": 255, "b_min": 0, "b_max": 255}


def single_pixel(rgb):
    return np.array([[list(rgb)]], dtype=np.uint8)


def test_in_range_pixel_is_255():
    mask = apply_rgb_range(single_pixel((15, 99, 200)), RANGE)
    assert mask[0, 0] == 255


def test_out_of_range_pixel_is_0():
    mask = apply_rgb_range(single_pixel((21, 99, 200)), RANGE)
    assert mask[0, 0] == 0


def test_bounds_are_inclusive():
    assert apply_rgb_range(single_pixel((10, 0, 0)), RANGE)[0, 0] == 255
    assert apply_rgb_range(single_pixel((20, 0, 0)), RANGE)[0, 0] == 255


def test_all_channels_must_match():
    narrow = {**RANGE, "g_min": 100, "g_max": 110}
    # r matches, g does not
    assert apply_rgb_range(single_pixel((15, 50, 0)), narrow)[0, 0] == 0
    assert apply_rgb_range(single_pixel((15, 105, 0)), narrow)[0, 0] == 255


def test_mask_is_uint8_and_two_valued():
    img = np.random.default_rng(0).integers(0, 256, (12, 9, 3), dtype=np.uint8)
    mask = apply_rgb_range(img, RANGE)
    assert mask.dtype == np.uint8
    assert mask.shape == (12, 9)
    assert set(np.unique(mask)).issubset({0, 255})


def test_missing_range_key_raises_keyerror():
    with pytest.raises(KeyError, match="missing required keys"):
        apply_rgb_range(single_pixel((0, 0, 0)), {"r_min": 0})


def test_non_rgb_array_raises_valueerror():
    with pytest.raises(ValueError, match="H x W x 3"):
        apply_rgb_range(np.zeros((4, 4), dtype=np.uint8), RANGE)
