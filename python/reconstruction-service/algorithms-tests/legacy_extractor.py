# legacy_extractor.py
"""
Superseded reference code. NOT part of the pipeline.

This is the original single-file prototype that the modules/ package replaced.
It is kept only to document the first working RGB-threshold approach; nothing
in the service imports it, and it is not covered by tests.

Note the polarity: this script writes 0 (black) for pattern pixels and 255
(white) for background - the OLD convention. The pipeline now uses the
opposite everywhere (255 = pattern, 0 = background, see modules/rgb_range.py).
Do not copy the thresholding from here into new code; call
modules.rgb_range.apply_rgb_range instead.

The per-manufacturer RGB ranges that used to be hardcoded in this file now
live in config/manufacturer_config.py.
"""
import argparse
import os
from pathlib import Path

import cv2
import numpy as np

# Permissive default range: matches every pixel. Override per image.
DEFAULT_RGB_RANGE = {
    "r_min": 0, "r_max": 255,
    "g_min": 0, "g_max": 255,
    "b_min": 0, "b_max": 255,
}


def extract_pattern_simple(
    image_path: str,
    output_path: str,
    r_min: int = 0, r_max: int = 255,
    g_min: int = 0, g_max: int = 255,
    b_min: int = 0, b_max: int = 255,
) -> np.ndarray | None:
    """
    Extract a pattern trace using plain per-channel RGB interval thresholds.

    Writes a binary image where:
      - 0   (black) = pixels inside the given RGB ranges (the pattern)
      - 255 (white) = pixels outside them (the background)

    Returns the mask, or None if the image could not be loaded.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: could not load {image_path}")
        return None

    # OpenCV reads BGR by default
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]

    # Start fully white (background)
    mask = np.ones(r.shape, dtype=np.uint8) * 255

    matched = (
        (r >= r_min) & (r <= r_max) &
        (g >= g_min) & (g <= g_max) &
        (b >= b_min) & (b <= b_max)
    )

    mask[matched] = 0  # black where the pattern is

    cv2.imwrite(output_path, mask)

    total_pixels = mask.size
    pattern_pixels = int(np.count_nonzero(mask == 0))
    percentage = (pattern_pixels / total_pixels) * 100

    print(f"Processed: {os.path.basename(image_path)}")
    print(f"  - Pattern pixels: {pattern_pixels}/{total_pixels} ({percentage:.2f}%)")
    print(f"  - Ranges used: R({r_min}-{r_max}), G({g_min}-{g_max}), B({b_min}-{b_max})")

    return mask


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Legacy RGB-threshold pattern extractor (reference only).",
    )
    parser.add_argument("image", help="Path to the input image.")
    parser.add_argument(
        "-o", "--output",
        help="Output path (default: <stem>_mask.png next to the input).",
    )
    for channel in ("r", "g", "b"):
        parser.add_argument(f"--{channel}-min", type=int, default=0)
        parser.add_argument(f"--{channel}-max", type=int, default=255)
    args = parser.parse_args(argv)

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return 1

    output_path = Path(args.output) if args.output else (
        image_path.with_name(f"{image_path.stem}_mask.png")
    )

    result = extract_pattern_simple(
        str(image_path), str(output_path),
        r_min=args.r_min, r_max=args.r_max,
        g_min=args.g_min, g_max=args.g_max,
        b_min=args.b_min, b_max=args.b_max,
    )
    if result is None:
        return 1

    print(f"Mask written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
