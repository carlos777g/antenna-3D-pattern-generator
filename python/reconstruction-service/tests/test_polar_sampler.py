# test_polar_sampler.py
"""
Regression tests for the polar sampler.

The polarity test below exists because commit 978d3af changed the mask
convention to 255 = pattern without updating this module, which silently
inverted every extraction. Keep it.
"""
import numpy as np
import pytest

from modules.polar_sampler import (
    PATTERN_PIXEL,
    coverage_ratio,
    fill_angular_gaps,
    sample_polar,
)

from conftest import SYNTHETIC_CENTER, SYNTHETIC_OUTER_RADIUS

DB_SCALE = {"center_db": -40.0, "outer_db": 10.0}


def test_pattern_pixel_constant_is_255():
    """Guards the module-wide mask convention against another silent flip."""
    assert PATTERN_PIXEL == 255


def test_full_disc_yields_360_samples_with_no_gaps(synthetic_pattern_mask):
    samples = sample_polar(
        synthetic_pattern_mask, SYNTHETIC_CENTER, SYNTHETIC_OUTER_RADIUS, DB_SCALE
    )
    assert len(samples) == 360
    assert [s["angle_deg"] for s in samples] == [float(a) for a in range(360)]
    assert all(s["magnitude_db"] is not None for s in samples)


def test_disc_edge_maps_to_outer_db(synthetic_pattern_mask):
    """
    The disc radius equals outer_radius_px, so every ray's outermost pattern
    pixel sits on the calibration ring and must read as outer_db.
    """
    samples = sample_polar(
        synthetic_pattern_mask, SYNTHETIC_CENTER, SYNTHETIC_OUTER_RADIUS, DB_SCALE
    )
    magnitudes = [s["magnitude_db"] for s in samples]
    assert all(abs(m - DB_SCALE["outer_db"]) <= 0.6 for m in magnitudes)


def test_half_radius_disc_maps_to_midpoint_db():
    """Linear radial calibration: half the radius is half the dB span."""
    size = 301
    cx, cy = 150, 150
    half_radius = SYNTHETIC_OUTER_RADIUS // 2
    ys, xs = np.mgrid[0:size, 0:size]
    mask = np.zeros((size, size), dtype=np.uint8)
    mask[(xs - cx) ** 2 + (ys - cy) ** 2 <= half_radius ** 2] = 255

    samples = sample_polar(mask, (cx, cy), SYNTHETIC_OUTER_RADIUS, DB_SCALE)
    midpoint = (DB_SCALE["center_db"] + DB_SCALE["outer_db"]) / 2
    magnitudes = [s["magnitude_db"] for s in samples]
    assert all(abs(m - midpoint) <= 0.8 for m in magnitudes)


def test_inverted_polarity_mask_finds_nothing(synthetic_pattern_mask):
    """
    A mask using the OLD convention (0 = pattern) must yield no samples, not
    silently inverted ones. This is the shape the bug took.
    """
    inverted = np.where(synthetic_pattern_mask == 255, 0, 255).astype(np.uint8)
    samples = sample_polar(inverted, SYNTHETIC_CENTER, SYNTHETIC_OUTER_RADIUS, DB_SCALE)
    # Only the background-turned-pattern outside the disc is matched, so the
    # readings saturate at outer_db rather than tracing the disc.
    assert all(
        s["magnitude_db"] is None or s["magnitude_db"] == DB_SCALE["outer_db"]
        for s in samples
    )


def test_blank_mask_yields_360_nulls(blank_mask):
    samples = sample_polar(blank_mask, SYNTHETIC_CENTER, SYNTHETIC_OUTER_RADIUS, DB_SCALE)
    assert len(samples) == 360
    assert all(s["magnitude_db"] is None for s in samples)
    assert coverage_ratio(samples) == 0.0


def test_angle_offset_rotates_the_reading():
    """
    A single-lobe mask along +x must move by exactly the applied offset.
    """
    size = 301
    cx, cy = 150, 150
    mask = np.zeros((size, size), dtype=np.uint8)
    # A thin wedge pointing right (+x, image row cy), 60 px long.
    mask[cy - 1:cy + 2, cx:cx + 60] = 255

    without = sample_polar(mask, (cx, cy), 100, DB_SCALE, angle_offset_deg=0)
    with_offset = sample_polar(mask, (cx, cy), 100, DB_SCALE, angle_offset_deg=90)

    # 0 deg reads the wedge when there is no offset.
    assert without[0]["magnitude_db"] is not None
    # With +90 deg offset, the ray that reads the wedge is the one at 270 deg.
    assert with_offset[270]["magnitude_db"] is not None
    assert with_offset[0]["magnitude_db"] != without[0]["magnitude_db"]


def test_magnitude_saturates_instead_of_extrapolating():
    """A trace overshooting the outer ring must clamp at outer_db."""
    size = 301
    cx, cy = 150, 150
    mask = np.zeros((size, size), dtype=np.uint8)
    ys, xs = np.mgrid[0:size, 0:size]
    mask[(xs - cx) ** 2 + (ys - cy) ** 2 <= 120 ** 2] = 255

    samples = sample_polar(mask, (cx, cy), 100, DB_SCALE)
    magnitudes = [s["magnitude_db"] for s in samples if s["magnitude_db"] is not None]
    assert magnitudes
    assert max(magnitudes) <= DB_SCALE["outer_db"]


def test_missing_center_raises():
    with pytest.raises(ValueError, match="center is required"):
        sample_polar(np.zeros((10, 10), dtype=np.uint8), None, 5, DB_SCALE)


@pytest.mark.parametrize("bad_radius", [0, -3, None])
def test_invalid_outer_radius_raises(bad_radius):
    with pytest.raises(ValueError, match="outer_radius_px"):
        sample_polar(np.zeros((10, 10), dtype=np.uint8), (5, 5), bad_radius, DB_SCALE)


def make_samples(magnitudes):
    return [
        {"angle_deg": float(i), "magnitude_db": m}
        for i, m in enumerate(magnitudes)
    ]


def test_fill_angular_gaps_fills_a_short_gap():
    magnitudes = [0.0] * 360
    for angle in (10, 11, 12):
        magnitudes[angle] = None
    magnitudes[9] = -10.0
    magnitudes[13] = -2.0

    filled = fill_angular_gaps(make_samples(magnitudes), max_gap_deg=5)
    interpolated = [filled[a]["magnitude_db"] for a in (10, 11, 12)]
    assert all(m is not None for m in interpolated)
    # Monotonic between the two neighbours -10 -> -2
    assert interpolated == sorted(interpolated)
    assert -10.0 < interpolated[0] < interpolated[-1] < -2.0


def test_fill_angular_gaps_leaves_a_long_gap():
    magnitudes = [0.0] * 360
    for angle in range(30, 60):  # a 30-degree run
        magnitudes[angle] = None

    filled = fill_angular_gaps(make_samples(magnitudes), max_gap_deg=5)
    assert all(filled[a]["magnitude_db"] is None for a in range(30, 60))


def test_fill_angular_gaps_wraps_around_zero():
    magnitudes = [0.0] * 360
    magnitudes[359] = None
    magnitudes[0] = None
    magnitudes[358] = -4.0
    magnitudes[1] = -6.0

    filled = fill_angular_gaps(make_samples(magnitudes), max_gap_deg=5)
    assert filled[359]["magnitude_db"] is not None
    assert filled[0]["magnitude_db"] is not None


def test_fill_angular_gaps_does_not_mutate_input():
    samples = make_samples([None if i == 5 else 0.0 for i in range(360)])
    fill_angular_gaps(samples)
    assert samples[5]["magnitude_db"] is None


def test_fill_angular_gaps_on_all_null_input_is_a_no_op(blank_mask):
    samples = make_samples([None] * 360)
    filled = fill_angular_gaps(samples)
    assert all(s["magnitude_db"] is None for s in filled)


def test_coverage_ratio():
    assert coverage_ratio([]) == 0.0
    assert coverage_ratio(make_samples([0.0] * 360)) == 1.0
    half = make_samples([0.0 if i % 2 else None for i in range(360)])
    assert coverage_ratio(half) == 0.5
