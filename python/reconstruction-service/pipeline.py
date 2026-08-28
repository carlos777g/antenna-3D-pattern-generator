# pipeline.py
"""
Image-to-pattern extraction pipeline.

Kept separate from main.py so that tests can import and run the pipeline
without triggering the CLI's processing queue.

Steps, in order:
    1  image_loader          load PNG, BGR -> RGB
    2  pattern_mask          isolate the plotted trace
    3a ring_mask_extractor   isolate the graticule rings
    3b center_detector       Hough + consensus -> (cx, cy)
    3c outer_ring_detector   densest ring radius -> outer_radius_px
    4  polar_sampler         ray cast per degree -> (angle_deg, magnitude_db)
    5  visualizer            annotated overlay for calibration review
    6  result_writer         unified-contract JSON + debug artifacts
"""
import logging
from pathlib import Path

import cv2

from config.manufacturer_config import get_manufacturer_config
from modules.center_detector import detect_center
from modules.image_loader import load_image_rgb
from modules.outer_ring_detector import detect_outer_ring
from modules.pattern_mask import extract_pattern_mask
from modules.polar_sampler import coverage_ratio, fill_angular_gaps, sample_polar
from modules.result_writer import write_extraction_debug_json, write_pattern_json
from modules.ring_mask_extractor import extract_ring_mask
from modules.visualizer import build_annotated_image

logger = logging.getLogger(__name__)

# Resolved from this file, never from the current working directory, so the
# pipeline behaves the same regardless of where it is invoked from.
SERVICE_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASHEETS_DIR = SERVICE_ROOT / "datasheets"
DEFAULT_OUTPUT_DIR = SERVICE_ROOT / "output"

# Below this fraction of the 360 rays carrying a magnitude, the extraction is
# reported as low quality: the manufacturer's rgb_range likely needs retuning.
MIN_ACCEPTABLE_COVERAGE = 0.90

# Fraction of the image that must match rgb_range for the colour filter to be
# considered plausible at all.
MIN_PATTERN_RATIO = 0.001

# Default processing queue: one entry per calibrated datasheet.
# `plane` is not inferable from pixels, so it is declared here.
PROCESSING_QUEUE = [
    {"image": "datasheets/taoglas-1.png",        "manufacturer": "taoglas",        "plane": "XZ"},
    {"image": "datasheets/rf-elements-1.png",    "manufacturer": "rf_elements",    "plane": "XZ"},
    {"image": "datasheets/molex-1.png",          "manufacturer": "molex",          "plane": "XY"},
    {"image": "datasheets/alpha-wireless-1.png", "manufacturer": "alpha_wireless", "plane": "XZ"},
    {"image": "datasheets/quectel-1.png",        "manufacturer": "quectel",        "plane": "XY"},
]


class ExtractionError(Exception):
    """Raised when an image cannot be turned into a usable pattern."""


def output_paths(output_dir: Path) -> dict:
    """Resolve and create every output directory the pipeline writes to."""
    paths = {
        "json": output_dir / "json",
        "images": output_dir / "images",
        "debug_extraction": output_dir / "debug" / "extraction",
        "debug_ring_mask": output_dir / "debug" / "ring_mask",
        "debug_center": output_dir / "debug" / "center_overlay",
        "debug_outer_ring": output_dir / "debug" / "outer_ring_overlay",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def process_single_image(
    image_path: str | Path,
    manufacturer: str,
    plane: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    debug: bool = False,
) -> dict:
    """
    Run the full extraction pipeline for one datasheet image.

    Returns a summary dict with the written paths, coverage, and warnings.
    Raises ExtractionError when the pattern cannot be extracted at all.
    """
    config = get_manufacturer_config(manufacturer)
    image_path = Path(image_path)
    if not image_path.is_absolute():
        image_path = SERVICE_ROOT / image_path
    stem = image_path.stem
    paths = output_paths(Path(output_dir))
    warnings: list[str] = []

    # -- STEP 1: Load --
    img_rgb = load_image_rgb(str(image_path))
    logger.debug("[1] loaded %s shape=%s dtype=%s", stem, img_rgb.shape, img_rgb.dtype)

    # -- STEP 2: Pattern mask --
    mask, mask_stats = extract_pattern_mask(img_rgb, config["rgb_range"])
    logger.debug(
        "[2] pattern_ratio: %.2f%% (%d/%d px)",
        mask_stats["pattern_ratio"] * 100,
        mask_stats["pattern_pixels"],
        mask_stats["total_pixels"],
    )
    if mask_stats["pattern_ratio"] < MIN_PATTERN_RATIO:
        warnings.append(
            f"pattern_ratio {mask_stats['pattern_ratio']:.4f} is below "
            f"{MIN_PATTERN_RATIO}: rgb_range may be too narrow."
        )

    # -- STEP 3a: Ring mask --
    ring_mask = extract_ring_mask(img_rgb, config["circle_color_range"])
    ring_pixels = int((ring_mask > 0).sum())
    logger.debug("[3a] ring_mask active pixels: %d", ring_pixels)
    if ring_pixels == 0:
        warnings.append("ring_mask is empty: circle_color_range may be incorrect.")
    if debug:
        cv2.imwrite(str(paths["debug_ring_mask"] / f"{stem}.png"), ring_mask)

    # -- STEP 3b: Center detection --
    center = detect_center(
        ring_mask,
        center_method=config["center_method"],
        hough_min_radius=config["hough_min_radius"],
        hough_max_radius=config["hough_max_radius"],
    )
    logger.debug("[3b] center: %s", center)
    if center is None:
        raise ExtractionError(
            f"{stem}: center not found (Hough detected no circles). "
            "Check circle_color_range and hough_min_radius/hough_max_radius."
        )
    if debug:
        overlay = build_annotated_image(mask, center)
        cv2.imwrite(str(paths["debug_center"] / f"{stem}.png"), overlay)

    # -- STEP 3c: Outer ring detection --
    outer_radius_px = detect_outer_ring(
        ring_mask,
        center,
        ring_count=config["ring_count"],
        max_ring_radius_px=config["max_ring_radius_px"],
    )
    logger.debug("[3c] outer_radius_px: %s", outer_radius_px)
    if outer_radius_px is None:
        raise ExtractionError(
            f"{stem}: outer ring not found. "
            "Check max_ring_radius_px and circle_color_range."
        )
    if debug:
        ring_overlay = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        cv2.drawMarker(
            ring_overlay, (int(center[0]), int(center[1])),
            color=(0, 0, 255), markerType=cv2.MARKER_CROSS,
            markerSize=20, thickness=2,
        )
        cv2.circle(
            ring_overlay, (int(center[0]), int(center[1])),
            int(round(outer_radius_px)), color=(255, 0, 0), thickness=2,
        )
        cv2.imwrite(str(paths["debug_outer_ring"] / f"{stem}.png"), ring_overlay)

    # -- STEP 4: Polar sampling --
    samples = sample_polar(
        mask,
        center,
        outer_radius_px,
        config["db_scale"],
        angle_offset_deg=config["angle_offset_deg"],
    )
    raw_coverage = coverage_ratio(samples)
    samples = fill_angular_gaps(samples)
    filled_coverage = coverage_ratio(samples)
    logger.debug(
        "[4] coverage: %.2f%% raw, %.2f%% after gap fill",
        raw_coverage * 100, filled_coverage * 100,
    )
    if filled_coverage < MIN_ACCEPTABLE_COVERAGE:
        warnings.append(
            f"coverage {filled_coverage:.2%} is below "
            f"{MIN_ACCEPTABLE_COVERAGE:.0%}: rgb_range may need retuning."
        )

    # -- STEP 5: Visualizer --
    annotated = build_annotated_image(mask, center, outer_radius_px)
    annotated_path = paths["images"] / f"{stem}.png"
    cv2.imwrite(str(annotated_path), annotated)

    # -- STEP 6: Result writer --
    json_path = write_pattern_json(
        paths["json"],
        stem,
        provider=manufacturer,
        plane=plane,
        samples=samples,
    )
    debug_json_path = write_extraction_debug_json(
        paths["debug_extraction"],
        stem,
        source_image=image_path.name,
        provider=manufacturer,
        center=center,
        outer_radius_px=outer_radius_px,
        coverage_ratio=filled_coverage,
        pattern_ratio=mask_stats["pattern_ratio"],
        warnings=warnings,
    )

    return {
        "image": stem,
        "manufacturer": manufacturer,
        "plane": plane,
        "center": center,
        "outer_radius_px": outer_radius_px,
        "coverage_ratio": filled_coverage,
        "json_path": json_path,
        "debug_json_path": debug_json_path,
        "annotated_path": str(annotated_path),
        "warnings": warnings,
    }


def run_pipeline(
    entries: list[dict] | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    debug: bool = False,
) -> list[dict]:
    """
    Process every entry in the queue, isolating per-image failures so one bad
    datasheet does not abort the run. Returns one summary dict per entry;
    failed entries carry an "error" key instead of results.
    """
    entries = PROCESSING_QUEUE if entries is None else entries
    results = []

    for entry in entries:
        logger.info("Processing %s [%s]", entry["image"], entry["manufacturer"])
        try:
            result = process_single_image(
                entry["image"],
                entry["manufacturer"],
                entry["plane"],
                output_dir=output_dir,
                debug=debug,
            )
        except (ExtractionError, FileNotFoundError, ValueError, KeyError) as error:
            logger.error("%s: %s", entry["image"], error)
            results.append({
                "image": Path(entry["image"]).stem,
                "manufacturer": entry["manufacturer"],
                "error": str(error),
            })
            continue

        for warning in result["warnings"]:
            logger.warning("%s: %s", result["image"], warning)
        logger.info(
            "%s: coverage %.2f%% -> %s",
            result["image"], result["coverage_ratio"] * 100, result["json_path"],
        )
        results.append(result)

    return results
