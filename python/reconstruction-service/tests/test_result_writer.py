# test_result_writer.py
import json
import re

import pytest

from modules.result_writer import (
    EXPECTED_SAMPLE_COUNT,
    build_pattern_payload,
    write_pattern_json,
)

CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")


def make_samples(count=EXPECTED_SAMPLE_COUNT):
    return [
        {"angle_deg": float(i), "magnitude_db": -float(i) / 10}
        for i in range(count)
    ]


def all_keys(node):
    """Every mapping key anywhere in the payload."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from all_keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from all_keys(item)


def test_payload_top_level_keys_match_the_contract():
    payload = build_pattern_payload(
        provider="taoglas", plane="XZ", samples=make_samples()
    )
    assert set(payload) == {
        "sourceType", "plane", "metadata",
        "reconstructionMethod", "views", "computed",
    }
    assert set(payload["metadata"]) == {"provider", "antennaType", "polarization"}
    assert set(payload["computed"]) == {"directivityDb", "efficiency"}
    assert set(payload["views"][0]) == {"plane", "pattern"}
    assert set(payload["views"][0]["pattern"][0]) == {"angleDeg", "magnitudeDb"}


def test_every_key_is_camelcase():
    payload = build_pattern_payload(
        provider="taoglas", plane="XZ", samples=make_samples()
    )
    offenders = [key for key in all_keys(payload) if not CAMEL_CASE.match(key)]
    assert offenders == []


def test_pattern_has_360_entries_covering_0_to_359():
    payload = build_pattern_payload(
        provider="taoglas", plane="XZ", samples=make_samples()
    )
    pattern = payload["views"][0]["pattern"]
    assert len(pattern) == 360
    assert [p["angleDeg"] for p in pattern] == [float(i) for i in range(360)]


def test_reconstruction_method_and_computed_are_null():
    payload = build_pattern_payload(
        provider="taoglas", plane="XZ", samples=make_samples()
    )
    assert payload["reconstructionMethod"] is None
    assert payload["computed"] == {"directivityDb": None, "efficiency": None}


def test_metadata_is_carried_through():
    payload = build_pattern_payload(
        provider="molex", plane="XY", samples=make_samples(),
        antenna_type="patch", polarization="vertical",
    )
    assert payload["metadata"] == {
        "provider": "molex", "antennaType": "patch", "polarization": "vertical",
    }
    assert payload["sourceType"] == "image"
    assert payload["plane"] == "XY"
    assert payload["views"][0]["plane"] == "XY"


def test_null_magnitudes_survive_the_mapping():
    samples = make_samples()
    samples[7]["magnitude_db"] = None
    payload = build_pattern_payload(provider="taoglas", plane="XZ", samples=samples)
    assert payload["views"][0]["pattern"][7]["magnitudeDb"] is None


def test_wrong_sample_count_is_rejected():
    with pytest.raises(ValueError, match="Expected 360 samples"):
        build_pattern_payload(provider="taoglas", plane="XZ", samples=make_samples(180))


def test_invalid_plane_is_rejected():
    with pytest.raises(ValueError, match="plane must be one of"):
        build_pattern_payload(provider="taoglas", plane="AB", samples=make_samples())


def test_write_pattern_json_round_trips(tmp_path):
    path = write_pattern_json(
        tmp_path / "json", "taoglas-1",
        provider="taoglas", plane="XZ", samples=make_samples(),
    )
    with open(path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["metadata"]["provider"] == "taoglas"
    assert len(loaded["views"][0]["pattern"]) == 360
    assert path.endswith("taoglas-1.json")
