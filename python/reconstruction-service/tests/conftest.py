# conftest.py
import sys
from pathlib import Path

import numpy as np
import pytest

SERVICE_ROOT = Path(__file__).resolve().parent.parent

# Modules are imported as `modules.x` / `config.x`, matching how the pipeline
# imports them, so the service root must be importable.
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

# Colours used by the synthetic fixtures. Both sit inside the taoglas config
# ranges (rgb_range r in 25..35, circle_color_range all channels 0..80).
PATTERN_RGB = (30, 100, 200)
RING_RGB = (40, 40, 40)
BACKGROUND_RGB = (255, 255, 255)

SYNTHETIC_SIZE = 301
SYNTHETIC_CENTER = (150, 150)
SYNTHETIC_OUTER_RADIUS = 100
SYNTHETIC_RING_RADII = (25, 50, 75, 100)


def draw_circle_outline(img, center, radius, color, thickness=1):
    """Draw a circle outline without depending on OpenCV drawing behaviour."""
    cx, cy = center
    # Dense angular sampling so the outline has no gaps at large radii.
    angles = np.linspace(0, 2 * np.pi, int(16 * radius) + 16, endpoint=False)
    for offset in range(thickness):
        r = radius + offset
        xs = np.round(cx + r * np.cos(angles)).astype(int)
        ys = np.round(cy + r * np.sin(angles)).astype(int)
        valid = (
            (xs >= 0) & (xs < img.shape[1]) &
            (ys >= 0) & (ys < img.shape[0])
        )
        img[ys[valid], xs[valid]] = color
    return img


def make_synthetic_datasheet(
    size=SYNTHETIC_SIZE,
    center=SYNTHETIC_CENTER,
    pattern_radius=SYNTHETIC_OUTER_RADIUS,
    ring_radii=SYNTHETIC_RING_RADII,
):
    """
    Build an RGB image resembling a polar datasheet plot: concentric graticule
    rings in RING_RGB plus a circular pattern trace in PATTERN_RGB.

    The pattern trace sits exactly on the outermost ring, so a correct
    calibration must report outer_db at every angle.
    """
    img = np.full((size, size, 3), BACKGROUND_RGB, dtype=np.uint8)

    # Two pixels wide, like a real anti-aliased graticule. A one-pixel ring is
    # too thin for cv2.HoughCircles to lock onto: it returns a scatter of
    # spurious circles, and `largest_cluster` then settles on the wrong one.
    for radius in ring_radii:
        draw_circle_outline(img, center, radius, RING_RGB, thickness=2)

    draw_circle_outline(img, center, pattern_radius, PATTERN_RGB, thickness=2)
    return img


@pytest.fixture
def synthetic_datasheet():
    return make_synthetic_datasheet()


@pytest.fixture
def synthetic_pattern_mask():
    """
    Binary mask, module convention (255 = pattern), holding a filled disc of
    radius SYNTHETIC_OUTER_RADIUS centred at SYNTHETIC_CENTER.

    A filled disc means every ray finds its outermost pattern pixel at exactly
    the disc radius, which makes the dB mapping analytically checkable.
    """
    cx, cy = SYNTHETIC_CENTER
    ys, xs = np.mgrid[0:SYNTHETIC_SIZE, 0:SYNTHETIC_SIZE]
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 <= SYNTHETIC_OUTER_RADIUS ** 2
    mask = np.zeros((SYNTHETIC_SIZE, SYNTHETIC_SIZE), dtype=np.uint8)
    mask[inside] = 255
    return mask


@pytest.fixture
def blank_mask():
    return np.zeros((SYNTHETIC_SIZE, SYNTHETIC_SIZE), dtype=np.uint8)


@pytest.fixture
def datasheets_dir():
    path = SERVICE_ROOT / "datasheets"
    if not path.is_dir():
        pytest.skip("datasheets/ directory is not available")
    return path
