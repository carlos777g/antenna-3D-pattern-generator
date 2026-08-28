# result_writer.py
import json
from pathlib import Path

# The pattern array is fixed at 1-degree resolution covering 0..359,
# per docs/data-schema.md.
EXPECTED_SAMPLE_COUNT = 360

VALID_PLANES = frozenset({"XY", "XZ", "YZ"})


def build_pattern_payload(
    *,
    provider: str,
    plane: str,
    samples: list[dict],
    antenna_type: str | None = None,
    polarization: str | None = None,
) -> dict:
    """
    Map internal snake_case sample data onto the unified camelCase contract
    defined in docs/data-schema.md.

    This function is the only camelCase boundary in the service: every module
    upstream of it works in snake_case.

    reconstructionMethod is deliberately null. Extraction does not choose a
    reconstruction method; the API layer sets it when a reconstruction runs.
    computed values are null for the same reason - they are produced by the
    reconstruction step, not by image extraction.
    """
    if plane not in VALID_PLANES:
        raise ValueError(f"plane must be one of {sorted(VALID_PLANES)}, got '{plane}'")
    if len(samples) != EXPECTED_SAMPLE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_SAMPLE_COUNT} samples at 1-degree resolution, "
            f"got {len(samples)}"
        )

    pattern = [
        {
            "angleDeg": sample["angle_deg"],
            "magnitudeDb": sample["magnitude_db"],
        }
        for sample in samples
    ]

    return {
        "sourceType": "image",
        "plane": plane,
        "metadata": {
            "provider": provider,
            "antennaType": antenna_type,
            "polarization": polarization,
        },
        "reconstructionMethod": None,
        "views": [
            {
                "plane": plane,
                "pattern": pattern,
            }
        ],
        "computed": {
            "directivityDb": None,
            "efficiency": None,
        },
    }


def write_pattern_json(
    output_dir: str | Path,
    filename_stem: str,
    *,
    provider: str,
    plane: str,
    samples: list[dict],
    antenna_type: str | None = None,
    polarization: str | None = None,
) -> str:
    """
    Write the extracted pattern as a unified-contract JSON document.
    Returns the path written.
    """
    payload = build_pattern_payload(
        provider=provider,
        plane=plane,
        samples=samples,
        antenna_type=antenna_type,
        polarization=polarization,
    )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filename_stem}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(out_path)


def write_extraction_debug_json(
    output_dir: str | Path,
    filename_stem: str,
    *,
    source_image: str,
    provider: str,
    center: tuple | None,
    outer_radius_px: float | None,
    coverage_ratio: float,
    pattern_ratio: float,
    warnings: list[str],
) -> str:
    """
    Write the pixel-space calibration artifacts that have no place in the
    unified contract but are needed to tune a manufacturer's config.

    Kept snake_case on purpose: this is an internal debug artifact, not part
    of the data contract, and treating it as such keeps the camelCase rule
    meaningful where it matters.
    """
    payload = {
        "source_image": source_image,
        "provider": provider,
        "center_px": {"x": center[0], "y": center[1]} if center is not None else None,
        "outer_radius_px": outer_radius_px,
        "coverage_ratio": coverage_ratio,
        "pattern_ratio": pattern_ratio,
        "warnings": warnings,
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filename_stem}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(out_path)
