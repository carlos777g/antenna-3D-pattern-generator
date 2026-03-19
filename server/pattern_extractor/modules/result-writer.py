import json
from pathlib import Path


def write_pattern_json(
    output_dir: str,
    filename_stem: str,
    manufacturer: str,
    center: tuple,
    samples: list[dict],
) -> str:
    """
    Write the polar sample data to a JSON file.

    Output schema:
    {
        "source_image": "taoglas-1.png",
        "manufacturer": "taoglas",
        "center_px": {"x": 312, "y": 298},
        "samples": [
            {"angle_deg": 0.0, "magnitude_db": -3.5},
            ...
        ]
    }
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "source_image": filename_stem + ".png",
        "manufacturer": manufacturer,
        "center_px": {"x": center[0], "y": center[1]} if center else None,
        "samples": samples,
    }

    out_path = out_dir / f"{filename_stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(out_path)