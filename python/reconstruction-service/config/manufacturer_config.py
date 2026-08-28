# manufacturer_config.py
#
# All manufacturer-specific parameters live here.
# When adding a new manufacturer, only this file changes.
#
# db_scale is read directly off the datasheet plot's radial axis labels:
#   center_db = the value at the plot center (the innermost label)
#   outer_db  = the value at the outermost graticule ring
#
# ring_count is the number of concentric graticule rings between the plot
# center and the outermost ring, counted off those same labels. The outer
# calibration radius is derived as ring_count * detected ring spacing; see
# modules/outer_ring_detector.py.
#
# max_ring_radius_px is an optional upper bound on that radius. None means
# "bounded by the image geometry", which is the right default: the previous
# fixed 128 px was smaller than the real outer ring on the larger datasheets
# (rf-elements' ring sits near 162 px) and silently hid it.
# On every datasheet in datasheets/ the center is the lowest value and the
# outer ring the highest, so center_db < outer_db. These names replace the
# earlier min_db/max_db pair, which meant "value at center" in four configs
# but "value at the outer ring" in taoglas — the same key carrying opposite
# meanings silently inverted four of the five calibrations.

MANUFACTURER_CONFIGS = {
    "taoglas": {
        "rgb_range": {
            "r_min": 25, "r_max": 35,
            "g_min": 0,  "g_max": 255,
            "b_min": 0,  "b_max": 255,
        },
        "angle_offset_deg": 0,      # degrees: where 0 deg is in the image (clockwise from top)
        "db_scale": {
            "center_db": -35,       # innermost label is -25; scale continues to -35 at center
            "outer_db": 5,
        },
        "circle_color_range": {      # color of concentric rings in this manufacturer's images
            "r_min": 0, "r_max": 80,
            "g_min": 0, "g_max": 80,
            "b_min": 0, "b_max": 80,
        },
        # ring_count: labels -25 / -10 / 5 at 10 dB per ring, center -35
        "ring_count": 4,
        "max_ring_radius_px": None,
        "center_method": "largest_cluster",
        "hough_min_radius": 20, "hough_max_radius": 110,
    },
    "rf_elements": {
        # The trace is red, (237, 28, 36) at its core. Leaving g and b
        # unbounded also matched (237, 237, 238), a near-white anti-aliasing
        # colour scattered across the whole figure, which gave every ray a
        # spurious far hit: coverage read 100% while a polar re-plot of the
        # result was a starburst of radial spikes. Bounding g and b to the
        # red's actual range is what makes the mask mean "the trace".
        "rgb_range": {
            "r_min": 200, "r_max": 255,
            "g_min": 0,   "g_max": 150,
            "b_min": 0,   "b_max": 160,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "center_db": -30,
            "outer_db": 0,
        },
        "circle_color_range": {
            "r_min": 160, "r_max": 170,
            "g_min": 160, "g_max": 170,
            "b_min": 160, "b_max": 170,
        },
        # ring_count: labels -30 / -22.5 / -15 / -7.5 / 0
        "ring_count": 4,
        "max_ring_radius_px": None,
        "center_method": "largest_cluster",
        "hough_min_radius": 20, "hough_max_radius": 110,
    },
    "molex": {
        # Exact-match bounds (r 74..74, b 187..187) caught only the core of the
        # blue stroke and none of its anti-aliased skirt; widened to the
        # measured spread of the trace's blues.
        "rgb_range": {
            "r_min": 60,  "r_max": 160,
            "g_min": 110, "g_max": 200,
            "b_min": 170, "b_max": 225,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "center_db": -25,
            "outer_db": 5,
        },
        # The 160-170 window matched only 381 pixels of this plot's graticule.
        # 150-200 recovers it, and yields the visually correct plot center.
        "circle_color_range": {
            "r_min": 150, "r_max": 200,
            "g_min": 150, "g_max": 200,
            "b_min": 150, "b_max": 200,
        },
        # ring_count: labels 5 down to -25 in 5 dB steps
        "ring_count": 6,
        "max_ring_radius_px": None,
        "center_method": "largest_cluster",
        "hough_min_radius": 20, "hough_max_radius": 110,
    },
    "alpha_wireless": {
        # KNOWN LIMITATION: this plot is greyscale and its graticule is drawn as
        # black dashed lines, i.e. in the same colour family as the trace, so no
        # rgb_range can separate the two. Widening this window raises the
        # coverage number but the extra rays land on the graticule, not the
        # trace - a re-plot of the result shows radial spikes. The window is
        # therefore kept tight, and the honest coverage is ~82%. Separating
        # trace from graticule here needs a geometric filter, not a colour one.
        "rgb_range": {
            "r_min": 3,  "r_max": 38,
            "g_min": 3,  "g_max": 38,
            "b_min": 3,  "b_max": 38,
        },
        "angle_offset_deg": 90,
        "db_scale": {
            "center_db": -35,
            "outer_db": 0,
        },
        "circle_color_range": {
            "r_min": 130, "r_max": 160,
            "g_min": 130, "g_max": 160,
            "b_min": 130, "b_max": 160,
        },
        # ring_count: labels 0 down to -35 in 5 dB steps
        "ring_count": 7,
        "max_ring_radius_px": None,
        "center_method": "median",
        "hough_min_radius": 20, "hough_max_radius": 110,
    },
    "quectel": {
        "rgb_range": {
            "r_min": 0,  "r_max": 90,
            "g_min": 130,"g_max": 150,
            "b_min": 0,  "b_max": 255,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "center_db": -40,
            "outer_db": 10,
        },
        "circle_color_range": {
            "r_min": 230, "r_max": 248,
            "g_min": 230, "g_max": 248,
            "b_min": 230, "b_max": 248,
        },
        # ring_count: labels -40 / -30 / -20 / -10 / 0 / 10
        "ring_count": 5,
        "max_ring_radius_px": None,
        "center_method": "median",
        "hough_min_radius": 70, "hough_max_radius": 110,
    },
}

VALID_CENTER_METHODS = frozenset({"median", "largest_cluster"})

REQUIRED_KEYS = (
    "rgb_range",
    "angle_offset_deg",
    "db_scale",
    "circle_color_range",
    "ring_count",
    "max_ring_radius_px",
    "center_method",
    "hough_min_radius",
    "hough_max_radius",
)

_REQUIRED_RGB_KEYS = ("r_min", "r_max", "g_min", "g_max", "b_min", "b_max")


def validate_manufacturer_config(config: dict, name: str = "<config>") -> None:
    """
    Fail loudly on a malformed manufacturer entry.

    Without this, a typo in center_method silently falls through to the
    largest_cluster branch in modules/center_detector.py, and a missing
    db_scale key only surfaces deep inside the polar sampler.

    Raises KeyError for missing keys and ValueError for invalid values.
    """
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise KeyError(f"Manufacturer '{name}' config is missing keys: {missing}")

    for range_key in ("rgb_range", "circle_color_range"):
        missing_channels = [
            key for key in _REQUIRED_RGB_KEYS if key not in config[range_key]
        ]
        if missing_channels:
            raise KeyError(
                f"Manufacturer '{name}' {range_key} is missing keys: {missing_channels}"
            )

    db_scale = config["db_scale"]
    missing_db = [key for key in ("center_db", "outer_db") if key not in db_scale]
    if missing_db:
        raise KeyError(
            f"Manufacturer '{name}' db_scale is missing keys: {missing_db}"
        )
    if db_scale["center_db"] >= db_scale["outer_db"]:
        raise ValueError(
            f"Manufacturer '{name}' db_scale expects center_db < outer_db "
            f"(plot center is the lowest value), got "
            f"center_db={db_scale['center_db']}, outer_db={db_scale['outer_db']}"
        )

    if not isinstance(config["ring_count"], int) or config["ring_count"] < 1:
        raise ValueError(
            f"Manufacturer '{name}' expects ring_count to be an integer >= 1, "
            f"got {config['ring_count']!r}"
        )

    max_radius = config["max_ring_radius_px"]
    if max_radius is not None and max_radius <= 0:
        raise ValueError(
            f"Manufacturer '{name}' expects max_ring_radius_px to be positive "
            f"or None, got {max_radius!r}"
        )

    if config["center_method"] not in VALID_CENTER_METHODS:
        raise ValueError(
            f"Manufacturer '{name}' has center_method="
            f"'{config['center_method']}'; expected one of "
            f"{sorted(VALID_CENTER_METHODS)}"
        )

    if config["hough_min_radius"] >= config["hough_max_radius"]:
        raise ValueError(
            f"Manufacturer '{name}' expects hough_min_radius < hough_max_radius, "
            f"got {config['hough_min_radius']} >= {config['hough_max_radius']}"
        )


def get_manufacturer_config(manufacturer: str) -> dict:
    """
    Retrieve config for a given manufacturer key.
    Raises KeyError with a clear message if the manufacturer is not registered.
    """
    key = manufacturer.lower().replace("-", "_").replace(" ", "_")
    if key not in MANUFACTURER_CONFIGS:
        available = list(MANUFACTURER_CONFIGS.keys())
        raise KeyError(
            f"Manufacturer '{manufacturer}' not found in config. "
            f"Available: {available}"
        )

    config = MANUFACTURER_CONFIGS[key]
    validate_manufacturer_config(config, name=key)
    return config
