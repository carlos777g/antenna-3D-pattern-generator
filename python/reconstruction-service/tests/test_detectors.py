# test_detectors.py
import numpy as np
import pytest

from modules.center_detector import detect_center
from modules.outer_ring_detector import detect_outer_ring
from modules.ring_mask_extractor import extract_ring_mask

from conftest import (
    SYNTHETIC_CENTER,
    SYNTHETIC_OUTER_RADIUS,
    SYNTHETIC_RING_RADII,
    SYNTHETIC_SIZE,
    draw_circle_outline,
)

# The synthetic datasheet draws SYNTHETIC_RING_RADII as an evenly spaced comb,
# which is what detect_outer_ring fits against.
SYNTHETIC_RING_COUNT = len(SYNTHETIC_RING_RADII)

RING_RANGE = {
    "r_min": 0, "r_max": 80, "g_min": 0, "g_max": 80, "b_min": 0, "b_max": 80,
}


def ring_mask_from(datasheet):
    return extract_ring_mask(datasheet, RING_RANGE)


def test_center_detected_within_tolerance_largest_cluster(synthetic_datasheet):
    center = detect_center(
        ring_mask_from(synthetic_datasheet),
        center_method="largest_cluster",
        hough_min_radius=20,
        hough_max_radius=110,
    )
    assert center is not None
    assert abs(center[0] - SYNTHETIC_CENTER[0]) <= 3
    assert abs(center[1] - SYNTHETIC_CENTER[1]) <= 3


def test_center_detected_within_tolerance_median(synthetic_datasheet):
    center = detect_center(
        ring_mask_from(synthetic_datasheet),
        center_method="median",
        hough_min_radius=20,
        hough_max_radius=110,
    )
    assert center is not None
    assert abs(center[0] - SYNTHETIC_CENTER[0]) <= 3
    assert abs(center[1] - SYNTHETIC_CENTER[1]) <= 3


def test_center_is_none_on_blank_mask(blank_mask):
    assert detect_center(blank_mask) is None


def test_outer_ring_radius_recovered(synthetic_datasheet):
    radius = detect_outer_ring(
        ring_mask_from(synthetic_datasheet),
        SYNTHETIC_CENTER,
        ring_count=SYNTHETIC_RING_COUNT,
    )
    assert radius is not None
    assert abs(radius - SYNTHETIC_OUTER_RADIUS) <= 2


def test_outer_ring_is_none_on_blank_mask(blank_mask):
    assert detect_outer_ring(
        blank_mask, SYNTHETIC_CENTER, ring_count=SYNTHETIC_RING_COUNT
    ) is None


def test_ring_beyond_max_radius_is_not_returned():
    """
    max_ring_radius_px bounds the answer. A single ring at r=120 with a cap of
    80 must not be reported, since the cap is the caller's statement that the
    graticule cannot be that large.
    """
    img = np.full((SYNTHETIC_SIZE, SYNTHETIC_SIZE, 3), 255, dtype=np.uint8)
    draw_circle_outline(img, SYNTHETIC_CENTER, 120, (40, 40, 40), thickness=2)
    ring_mask = extract_ring_mask(img, RING_RANGE)

    radius = detect_outer_ring(
        ring_mask, SYNTHETIC_CENTER, ring_count=1, max_ring_radius_px=80
    )
    assert radius is None or radius <= 80


def test_comb_fit_prefers_the_evenly_spaced_rings(synthetic_datasheet):
    """
    A sparse arc drawn outside the graticule must not drag the fit outward:
    the comb score averages density over all ring_count multiples, so a single
    20-degree arc cannot outscore four complete rings.
    """
    img = synthetic_datasheet.copy()
    cx, cy = SYNTHETIC_CENTER
    angles = np.deg2rad(np.arange(0, 20, 0.25))
    xs = np.round(cx + 130 * np.cos(angles)).astype(int)
    ys = np.round(cy + 130 * np.sin(angles)).astype(int)
    img[ys, xs] = (40, 40, 40)

    ring_mask = extract_ring_mask(img, RING_RANGE)
    radius = detect_outer_ring(
        ring_mask, SYNTHETIC_CENTER, ring_count=SYNTHETIC_RING_COUNT
    )
    assert radius is not None
    assert abs(radius - SYNTHETIC_OUTER_RADIUS) <= 2


def test_ring_count_must_be_positive(synthetic_datasheet):
    with pytest.raises(ValueError):
        detect_outer_ring(
            ring_mask_from(synthetic_datasheet), SYNTHETIC_CENTER, ring_count=0
        )
