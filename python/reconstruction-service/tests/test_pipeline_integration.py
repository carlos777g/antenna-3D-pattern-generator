# test_pipeline_integration.py
"""
End-to-end runs over the real datasheets. These are the tests that would have
caught the broken steps 4-6, since they exercise the actual call signatures.
"""
import json

import pytest

from pipeline import PROCESSING_QUEUE, ExtractionError, process_single_image, run_pipeline

# Coverage floor for the calibrated datasheets. Documented rather than tight:
# below this the extraction is not usable and the config needs retuning.
MIN_COVERAGE = 0.90

QUEUE_IDS = [entry["manufacturer"] for entry in PROCESSING_QUEUE]

# Manufacturers whose extraction is knowingly not usable yet, with the specific
# reason each one is unresolved. They are xfailed rather than quietly excluded,
# so that a fix flips the test to XPASS instead of going unnoticed.
#
# molex: the graticule is drawn with radial spoke lines every 10 degrees in the
#   same grey as the concentric rings, so the ring mask has a high hit rate at
#   *every* radius, not only on the rings. The comb fit in
#   modules/outer_ring_detector.py scores a candidate spacing by mean density
#   over its ring_count multiples, and against a radially uniform mask that
#   score barely varies, so the fit collapses onto the smallest allowed period
#   (MIN_RING_PERIOD_PX): it reports outer_radius_px = 36 where the plot's outer
#   ring is near 135 px. The sampler then stops 10 px past 36 and never reaches
#   the trace, giving ~12% coverage. Fixing this needs the detector to separate
#   concentric rings from radial spokes - e.g. by scoring the angular
#   *uniformity* of the hits at a radius rather than their count.
#
# alpha_wireless: a greyscale plot whose graticule is black dashed lines, i.e.
#   the same colour family as the trace, so no rgb_range can separate the two.
#   The tight window used here reaches ~85% coverage; widening it raises the
#   number but the extra rays land on the graticule, which a polar re-plot shows
#   as radial spikes. Separating them needs a geometric filter, not a colour one.
UNCALIBRATED_MANUFACTURERS = {
    "molex": "outer-ring detection defeated by radial graticule spokes",
    "alpha_wireless": "trace and dashed graticule share a colour",
}


def queue_params():
    """PROCESSING_QUEUE as pytest params, with uncalibrated vendors xfailed."""
    params = []
    for entry, name in zip(PROCESSING_QUEUE, QUEUE_IDS):
        reason = UNCALIBRATED_MANUFACTURERS.get(name)
        marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
        params.append(pytest.param(entry, marks=marks, id=name))
    return params


@pytest.mark.parametrize("entry", queue_params())
def test_each_queued_datasheet_extracts(entry, tmp_path, datasheets_dir):
    result = process_single_image(
        entry["image"], entry["manufacturer"], entry["plane"], output_dir=tmp_path
    )

    assert result["center"] is not None
    assert result["outer_radius_px"] is not None and result["outer_radius_px"] > 0
    assert result["coverage_ratio"] >= MIN_COVERAGE, (
        f"{entry['manufacturer']} coverage {result['coverage_ratio']:.2%} "
        f"below {MIN_COVERAGE:.0%}; rgb_range likely needs retuning"
    )


@pytest.mark.parametrize("entry", PROCESSING_QUEUE, ids=QUEUE_IDS)
def test_emitted_json_satisfies_the_contract(entry, tmp_path, datasheets_dir):
    result = process_single_image(
        entry["image"], entry["manufacturer"], entry["plane"], output_dir=tmp_path
    )

    with open(result["json_path"], encoding="utf-8") as f:
        payload = json.load(f)

    assert payload["sourceType"] == "image"
    assert payload["plane"] == entry["plane"]
    assert payload["metadata"]["provider"] == entry["manufacturer"]
    assert payload["reconstructionMethod"] is None

    pattern = payload["views"][0]["pattern"]
    assert len(pattern) == 360
    assert [p["angleDeg"] for p in pattern] == [float(i) for i in range(360)]


@pytest.mark.parametrize("entry", PROCESSING_QUEUE, ids=QUEUE_IDS)
def test_magnitudes_stay_inside_the_declared_db_scale(entry, tmp_path, datasheets_dir):
    """
    Extracted values must lie within the manufacturer's own dB scale. This is
    what catches an inverted or mis-anchored calibration, which the previous
    center->max_db mapping produced for four of the five manufacturers.
    """
    from config.manufacturer_config import get_manufacturer_config

    db_scale = get_manufacturer_config(entry["manufacturer"])["db_scale"]
    result = process_single_image(
        entry["image"], entry["manufacturer"], entry["plane"], output_dir=tmp_path
    )
    with open(result["json_path"], encoding="utf-8") as f:
        pattern = json.load(f)["views"][0]["pattern"]

    magnitudes = [p["magnitudeDb"] for p in pattern if p["magnitudeDb"] is not None]
    assert magnitudes
    assert min(magnitudes) >= db_scale["center_db"] - 0.01
    assert max(magnitudes) <= db_scale["outer_db"] + 0.01


def test_artifacts_are_written(tmp_path, datasheets_dir):
    entry = PROCESSING_QUEUE[0]
    result = process_single_image(
        entry["image"], entry["manufacturer"], entry["plane"],
        output_dir=tmp_path, debug=True,
    )

    assert (tmp_path / "json" / "taoglas-1.json").is_file()
    assert (tmp_path / "images" / "taoglas-1.png").is_file()
    assert (tmp_path / "debug" / "extraction" / "taoglas-1.json").is_file()
    assert (tmp_path / "debug" / "ring_mask" / "taoglas-1.png").is_file()
    assert (tmp_path / "debug" / "outer_ring_overlay" / "taoglas-1.png").is_file()

    with open(result["debug_json_path"], encoding="utf-8") as f:
        debug = json.load(f)
    assert debug["center_px"] is not None
    assert debug["outer_radius_px"] > 0


def test_relative_paths_resolve_against_the_service_not_the_cwd(
    tmp_path, monkeypatch, datasheets_dir
):
    """Running from an unrelated working directory must still find datasheets/."""
    monkeypatch.chdir(tmp_path)
    entry = PROCESSING_QUEUE[0]
    result = process_single_image(
        entry["image"], entry["manufacturer"], entry["plane"], output_dir=tmp_path
    )
    assert result["center"] is not None


def test_unknown_manufacturer_raises(tmp_path, datasheets_dir):
    with pytest.raises(KeyError):
        process_single_image(
            "datasheets/taoglas-1.png", "not-a-vendor", "XZ", output_dir=tmp_path
        )


def test_missing_image_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_single_image(
            "datasheets/nope.png", "taoglas", "XZ", output_dir=tmp_path
        )


def test_run_pipeline_isolates_a_failing_entry(tmp_path, datasheets_dir):
    entries = [
        {"image": "datasheets/nope.png", "manufacturer": "taoglas", "plane": "XZ"},
        PROCESSING_QUEUE[0],
    ]
    results = run_pipeline(entries, output_dir=tmp_path)

    assert len(results) == 2
    assert "error" in results[0]
    assert "error" not in results[1]
    assert results[1]["coverage_ratio"] >= MIN_COVERAGE


def test_run_pipeline_processes_the_whole_queue(tmp_path, datasheets_dir):
    results = run_pipeline(output_dir=tmp_path)
    assert len(results) == len(PROCESSING_QUEUE)
    failures = [r for r in results if "error" in r]
    assert failures == [], f"queued datasheets failed: {failures}"
