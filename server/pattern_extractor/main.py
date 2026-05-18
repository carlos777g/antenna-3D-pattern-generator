import cv2
import numpy as np
from pathlib import Path
from config.manufacturer_config import get_manufacturer_config
from modules.image_loader import load_image_rgb
from modules.pattern_mask import extract_pattern_mask
from modules.ring_mask_extractor import extract_ring_mask

# ------------------------------------------------------------
# DEBUG FLAG
# Set to True to write intermediate images for STEP 3 modules.
# ------------------------------------------------------------
DEBUG_STEPS = True

# ------------------------------------------------------------
# PROCESSING QUEUE
# Each entry: (image_path, manufacturer_key)
# ------------------------------------------------------------
PROCESSING_QUEUE = [
    ("datasheets/taoglas-1.png",        "taoglas"),
    ("datasheets/rf-elements-1.png",    "rf_elements"),
    ("datasheets/molex-1.png",          "molex"),
    ("datasheets/alpha-wireless-1.png", "alpha_wireless"),
    ("datasheets/quectel-1.png",        "quectel"),
]

# ------------------------------------------------------------
# OUTPUT PATHS
# ------------------------------------------------------------
OUTPUT_IMAGES_DIR       = Path("output/images")
OUTPUT_JSON_DIR         = Path("output/json")
OUTPUT_DEBUG_RINGMASK   = Path("output/debug/ring_mask")
OUTPUT_DEBUG_CENTER     = Path("output/debug/center_overlay")
OUTPUT_DEBUG_OUTER      = Path("output/debug/outer_ring_overlay")


def create_output_dirs() -> None:
    for path in [
        OUTPUT_IMAGES_DIR,
        OUTPUT_JSON_DIR,
        OUTPUT_DEBUG_RINGMASK,
        OUTPUT_DEBUG_CENTER,
        OUTPUT_DEBUG_OUTER,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def process_single_image(image_path: str, manufacturer: str) -> dict:
    config = get_manufacturer_config(manufacturer)
    stem = Path(image_path).stem
    warnings = []

    # -- STEP 1: Load --
    img_rgb = load_image_rgb(image_path)
    ## Structural propieties on matriz (uncomment next line if wanna see)
    # print(f"  [1] loaded: {img_rgb.shape} dtype={img_rgb.dtype}") 


    # -- STEP 2: Pattern mask --
    mask, mask_stats = extract_pattern_mask(img_rgb, config["rgb_range"])
    ## Uncomment next lines if wanna see the amount of pattern pixels against the total pixels from the image
    # print(f"  [2] pattern_ratio: {mask_stats['pattern_ratio']:.2%} "
    #       f"({mask_stats['pattern_pixels']}/{mask_stats['total_pixels']} px)")
    # if mask_stats["pattern_ratio"] < 0.001:
    #     warnings.append("pattern_ratio below 0.1%: rgb_range may be too narrow.")


    # -- STEP 3a: Ring mask --
    ring_mask = extract_ring_mask(img_rgb, config["circle_color_range"])
    ring_pixel_count = int(np.sum(ring_mask > 0))
    print(f"  [3a] ring_mask active pixels: {ring_pixel_count}")
    if ring_pixel_count == 0:
        warnings.append("ring_mask is empty: circle_color_range may be incorrect.")
    if DEBUG_STEPS:
        debug_path = OUTPUT_DEBUG_RINGMASK / f"{stem}.png"
        cv2.imwrite(str(debug_path), ring_mask)
        print(f"  [3a] debug image saved: {debug_path}")

    # -- STEP 3b: Center detection --
    # center = detect_center(ring_mask)

    # -- STEP 3c: Outer ring detection --
    # outer_radius_px = detect_outer_ring(ring_mask, center, config["max_ring_radius_px"])

    # -- STEP 4: Polar sampling --
    # samples = sample_polar(
    #     mask, center, outer_radius_px,
    #     config["db_scale"]["min_db"],
    #     config["db_scale"]["max_db"],
    #     config["angle_offset_deg"],
    # )

    # -- STEP 5: Visualizer --
    # save_annotated_image(mask, center, outer_radius_px, OUTPUT_IMAGES_DIR / f"{stem}.png")

    # -- STEP 6: Result writer --
    # write_pattern_json(
    #     output_dir=OUTPUT_JSON_DIR,
    #     filename_stem=stem,
    #     manufacturer=manufacturer,
    #     center=center,
    #     outer_radius_px=outer_radius_px,
    #     samples=samples,
    # )

    return {
        "image": stem,
        "manufacturer": manufacturer,
        "warnings": warnings,
    }


def main() -> None:
    print("=== RADIATION PATTERN EXTRACTION PIPELINE ===\n")
    create_output_dirs()

    for image_path, manufacturer in PROCESSING_QUEUE:
        print(f"Processing: {image_path} [{manufacturer}]")
        try:
            result = process_single_image(image_path, manufacturer)
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"  WARNING: {w}")
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"  ERROR: {e}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()