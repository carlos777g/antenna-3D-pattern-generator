# test_pattern_mask.py
import numpy as np

from modules.pattern_mask import extract_pattern_mask
from modules.ring_mask_extractor import extract_ring_mask

from conftest import PATTERN_RGB, RING_RGB

TAOGLAS_PATTERN_RANGE = {
    "r_min": 25, "r_max": 35, "g_min": 0, "g_max": 255, "b_min": 0, "b_max": 255,
}
TAOGLAS_RING_RANGE = {
    "r_min": 0, "r_max": 80, "g_min": 0, "g_max": 80, "b_min": 0, "b_max": 80,
}


def test_pattern_pixels_are_255_background_is_0(synthetic_datasheet):
    mask, _ = extract_pattern_mask(synthetic_datasheet, TAOGLAS_PATTERN_RANGE)
    assert set(np.unique(mask)).issubset({0, 255})
    # The synthetic trace colour must be picked up as pattern.
    trace = np.all(synthetic_datasheet == PATTERN_RGB, axis=2)
    assert np.all(mask[trace] == 255)
    # White background must not be.
    assert mask[0, 0] == 0


def test_stats_are_consistent(synthetic_datasheet):
    mask, stats = extract_pattern_mask(synthetic_datasheet, TAOGLAS_PATTERN_RANGE)
    assert stats["total_pixels"] == mask.size
    assert stats["pattern_pixels"] == int(np.count_nonzero(mask == 255))
    expected = round(stats["pattern_pixels"] / stats["total_pixels"], 4)
    assert stats["pattern_ratio"] == expected
    assert 0.0 < stats["pattern_ratio"] < 1.0


def test_ring_mask_picks_up_graticule(synthetic_datasheet):
    ring_mask = extract_ring_mask(synthetic_datasheet, TAOGLAS_RING_RANGE)
    rings = np.all(synthetic_datasheet == RING_RGB, axis=2)
    assert np.all(ring_mask[rings] == 255)
    assert ring_mask[0, 0] == 0


def test_both_consumers_share_the_same_helper(synthetic_datasheet):
    """Same range through either entry point must yield an identical mask."""
    mask, _ = extract_pattern_mask(synthetic_datasheet, TAOGLAS_RING_RANGE)
    ring_mask = extract_ring_mask(synthetic_datasheet, TAOGLAS_RING_RANGE)
    assert np.array_equal(mask, ring_mask)
