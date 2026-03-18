import cv2
from config.manufacturer_config import get_manufacturer_config
from modules.image_loader import load_image_rgb
from modules.pattern_mask import extract_pattern_mask
from modules.circle_detector import detect_concentric_circles
from modules.visualizer import build_annotated_image
from utils.file_utils import resolve_output_path


# Each entry: (image_path, manufacturer_key)
# Adding a new image = adding one line here + config entry if new manufacturer
PROCESSING_QUEUE = [
    ("datasheets/taoglas-1.png",         "taoglas"),
    ("datasheets/taoglas-2.png",         "taoglas"),
    ("datasheets/rf-elements-1.png",     "rf_elements"),
    ("datasheets/molex-1.png",           "molex"),
    ("datasheets/alpha-wireless-1.png",  "alpha_wireless"),
    ("datasheets/quectel-1.png",         "quectel"),
]

OUTPUT_DIR = "output"


def process_single_image(image_path: str, manufacturer: str) -> dict:
    """
    Full pipeline for one image:
        load -> mask -> detect center -> annotate -> save

    Returns a result dict with extracted data and any warnings.
    """
    config = get_manufacturer_config(manufacturer)

    img_rgb = load_image_rgb(image_path)

    mask, mask_stats = extract_pattern_mask(img_rgb, config["rgb_range"])

    circle_result = detect_concentric_circles(
        img_rgb,
        config["circle_color_range"],
    )

    center = circle_result["center"]
    radii = circle_result["radii"]

    warnings = []
    if center is None:
        warnings.append("Center detection failed: no concentric circles found.")
    if len(radii) < 2:
        warnings.append(f"Only {len(radii)} ring(s) detected. dB calibration will be imprecise.")

    annotated = build_annotated_image(img_rgb, mask, center, radii)

    filename = image_path.split("/")[-1]
    out_path = resolve_output_path(OUTPUT_DIR, filename)
    cv2.imwrite(str(out_path), annotated)

    return {
        "image": filename,
        "manufacturer": manufacturer,
        "center": center,
        "radii_px": radii,
        "mask_stats": mask_stats,
        "warnings": warnings,
        "output_path": str(out_path),
    }


def main():
    print("=== RADIATION PATTERN EXTRACTION PIPELINE ===\n")
    results = []

    for image_path, manufacturer in PROCESSING_QUEUE:
        print(f"Processing: {image_path} [{manufacturer}]")
        try:
            result = process_single_image(image_path, manufacturer)
            results.append(result)

            print(f"  center       : {result['center']}")
            print(f"  rings found  : {len(result['radii_px'])} -> radii: {result['radii_px']}")
            print(f"  pattern ratio: {result['mask_stats']['pattern_ratio']:.2%}")
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"  WARNING: {w}")
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"  ERROR: {e}")

        print()

    print(f"Done. Outputs written to: {OUTPUT_DIR}/")
    return results


if __name__ == "__main__":
    main()