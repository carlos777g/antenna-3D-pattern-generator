# All manufacturer-specific parameters live here.
# When adding a new manufacturer, only this file changes.

MANUFACTURER_CONFIGS = {
    "taoglas": {
        "rgb_range": {
            "r_min": 25, "r_max": 35,
            "g_min": 0,  "g_max": 255,
            "b_min": 0,  "b_max": 255,
        },
        "angle_offset_deg": 0,      # degrees: where 0 deg is in the image (clockwise from top)
        "db_scale": {
            "rings": 7,              # number of concentric reference rings
            "min_db": 5,           # value at outermost ring
            "max_db": -35,             # value at center reference
        },
        "circle_color_range": {      # color of concentric rings in this manufacturer's images
            "r_min": 0, "r_max": 80,
            "g_min": 0, "g_max": 80,
            "b_min": 0, "b_max": 80,
        },
    },
    "rf_elements": {
        "rgb_range": {
            "r_min": 237, "r_max": 237,
            "g_min": 0,   "g_max": 255,
            "b_min": 0,   "b_max": 255,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "rings": 4,
            "min_db": -30,
            "max_db": 0,
        },
        "circle_color_range": {
            "r_min": 160, "r_max": 170,
            "g_min": 160, "g_max": 170,
            "b_min": 160, "b_max": 170,
        },
    },
    "molex": {
        "rgb_range": {
            "r_min": 74, "r_max": 74,
            "g_min": 0,  "g_max": 255,
            "b_min": 187,"b_max": 187,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "rings": 6,
            "min_db": -25,
            "max_db": 5,
        },
        "circle_color_range": {
            "r_min": 160, "r_max": 170,
            "g_min": 160, "g_max": 170,
            "b_min": 160, "b_max": 170,
        },
    },
    "alpha_wireless": {
        "rgb_range": {
            "r_min": 3,  "r_max": 38,
            "g_min": 3,  "g_max": 38,
            "b_min": 3,  "b_max": 38,
        },
        "angle_offset_deg": 90,
        "db_scale": {
            "rings": 8,
            "min_db": -35,
            "max_db": 0,
        },
        "circle_color_range": {
            "r_min": 130, "r_max": 160,
            "g_min": 130, "g_max": 160,
            "b_min": 130, "b_max": 160,
        },
    },
    "quectel": {
        "rgb_range": {
            "r_min": 0,  "r_max": 90,
            "g_min": 130,"g_max": 150,
            "b_min": 0,  "b_max": 255,
        },
        "angle_offset_deg": 0,
        "db_scale": {
            "rings": 5,
            "min_db": -40,
            "max_db": 10,
        },
        "circle_color_range": {
            "r_min": 135, "r_max": 170,
            "g_min": 135, "g_max": 170,
            "b_min": 135, "b_max": 170,
        },
    },
}


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
    return MANUFACTURER_CONFIGS[key]