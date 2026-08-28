# test_manufacturer_config.py
import copy

import pytest

from config.manufacturer_config import (
    MANUFACTURER_CONFIGS,
    VALID_CENTER_METHODS,
    get_manufacturer_config,
    validate_manufacturer_config,
)


@pytest.mark.parametrize("name", sorted(MANUFACTURER_CONFIGS))
def test_every_shipped_config_is_valid(name):
    validate_manufacturer_config(MANUFACTURER_CONFIGS[name], name=name)


@pytest.mark.parametrize("name", sorted(MANUFACTURER_CONFIGS))
def test_every_db_scale_has_center_below_outer(name):
    """
    Every datasheet in datasheets/ plots the lowest value at the center and
    the highest at the outermost ring. A config that violates this is the
    inverted-calibration bug coming back.
    """
    db_scale = MANUFACTURER_CONFIGS[name]["db_scale"]
    assert db_scale["center_db"] < db_scale["outer_db"]


def test_unknown_manufacturer_raises_keyerror():
    with pytest.raises(KeyError, match="not found in config"):
        get_manufacturer_config("not-a-vendor")


@pytest.mark.parametrize("given", ["RF-Elements", "rf elements", "RF_ELEMENTS"])
def test_key_normalization(given):
    assert get_manufacturer_config(given) is MANUFACTURER_CONFIGS["rf_elements"]


def test_invalid_center_method_is_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    config["center_method"] = "Largest_Cluster"  # wrong case: used to pass silently
    assert config["center_method"] not in VALID_CENTER_METHODS
    with pytest.raises(ValueError, match="center_method"):
        validate_manufacturer_config(config, name="taoglas")


def test_missing_top_level_key_is_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    del config["max_ring_radius_px"]
    with pytest.raises(KeyError, match="max_ring_radius_px"):
        validate_manufacturer_config(config, name="taoglas")


def test_missing_db_scale_key_is_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    del config["db_scale"]["outer_db"]
    with pytest.raises(KeyError, match="outer_db"):
        validate_manufacturer_config(config, name="taoglas")


def test_inverted_db_scale_is_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    config["db_scale"] = {"center_db": 5, "outer_db": -35}
    with pytest.raises(ValueError, match="center_db < outer_db"):
        validate_manufacturer_config(config, name="taoglas")


def test_missing_rgb_channel_is_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    del config["rgb_range"]["b_max"]
    with pytest.raises(KeyError, match="b_max"):
        validate_manufacturer_config(config, name="taoglas")


def test_inverted_hough_radii_are_rejected():
    config = copy.deepcopy(MANUFACTURER_CONFIGS["taoglas"])
    config["hough_min_radius"] = 200
    with pytest.raises(ValueError, match="hough_min_radius"):
        validate_manufacturer_config(config, name="taoglas")
