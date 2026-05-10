import cv2
from pathlib import Path

from config.manufacturer_config import get_manufacturer_config
from modules.image_loader import load_image_rgb
from modules.pattern_mask import extract_pattern_mask
# from modules.circle_detector import detect_concentric_circles
from modules.circle_detector import detect_pattern_center_and_outer_ring

from modules.polar_sampler import sample_polar
from modules.visualizer import build_annotated_image
from modules.result_writer import write_pattern_json
from utils.file_utils import resolve_output_path


PROCESSING_QUEUE = [
    ("datasheets/taoglas-1.png",        "taoglas"),
    ("datasheets/taoglas-2.png",        "taoglas"),
    ("datasheets/rf-elements-1.png",    "rf_elements"),
    ("datasheets/molex-1.png",          "molex"),
    ("datasheets/alpha-wireless-1.png", "alpha_wireless"),
    ("datasheets/quectel-1.png",        "quectel"),
]

OUTPUT_IMAGES_DIR = "output/images"
OUTPUT_JSON_DIR   = "output/json"


def process_single_image(image_path: str, manufacturer: str) -> dict:
    config = get_manufacturer_config(manufacturer)

    img_rgb = load_image_rgb(image_path)
    mask, mask_stats = extract_pattern_mask(img_rgb, config["rgb_range"])

    circle_result = detect_pattern_center_and_outer_ring(
    img_rgb,
    config["circle_color_range"],
    max_ring_radius_px=config["max_ring_radius_px"],
    )
    center = circle_result["center"]
    outer_radius_px = circle_result["outer_radius_px"]

    print(f"  accepted radii  : {circle_result['all_radii']}")
    print(f"  rejected radii  : {circle_result['rejected_radii']}")
    print(f"  center          : {center}")
    print(f"  outer_radius_px : {outer_radius_px}")
    warnings = []
    if center is None:
        warnings.append("Center detection failed. JSON will have null center.")

    samples = []
    if center is not None:
        samples = sample_polar(
            mask=mask,
            center=center,
            db_scale=config["db_scale"],
            angle_offset_deg=config["angle_offset_deg"],
            angle_step_deg=1.0,
        )

    annotated = build_annotated_image(mask, center)
    filename_stem = Path(image_path).stem
    img_out_path = resolve_output_path(OUTPUT_IMAGES_DIR, filename_stem + ".png")
    cv2.imwrite(str(img_out_path), annotated)

    json_path = write_pattern_json(
        output_dir=OUTPUT_JSON_DIR,
        filename_stem=filename_stem,
        manufacturer=manufacturer,
        center=center,
        samples=samples,
    )

    return {
        "image": filename_stem,
        "manufacturer": manufacturer,
        "center": center,
        "mask_stats": mask_stats,
        "samples_count": len(samples),
        "warnings": warnings,
        "output_image": str(img_out_path),
        "output_json": json_path,
    }


def main():
    print("=== RADIATION PATTERN EXTRACTION PIPELINE ===\n")

    for image_path, manufacturer in PROCESSING_QUEUE:
        print(f"Processing: {image_path} [{manufacturer}]")
        try:
            result = process_single_image(image_path, manufacturer)
            print(f"  center        : {result['center']}")
            print(f"  pattern ratio : {result['mask_stats']['pattern_ratio']:.2%}")
            print(f"  samples       : {result['samples_count']}")
            print(f"  json output   : {result['output_json']}")
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"  WARNING: {w}")
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"  ERROR: {e}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()