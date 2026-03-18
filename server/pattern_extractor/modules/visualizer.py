import cv2
import numpy as np


def build_annotated_image(
    img_rgb: np.ndarray,
    mask: np.ndarray,
    center: tuple,
    radii: list,
) -> np.ndarray:
    """
    Produce an annotated BGR image showing:
        - Pattern pixels in black
        - Background in white
        - Detected concentric rings in blue
        - Estimated center as a red crosshair
    """
    # Convert mask to 3-channel BGR for color annotation
    annotated = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    if center is not None:
        cx, cy = center
        for r in radii:
            cv2.circle(annotated, (cx, cy), r, (255, 0, 0), 1)  # blue rings
        # Red crosshair
        cv2.drawMarker(
            annotated, (cx, cy),
            color=(0, 0, 255),
            markerType=cv2.MARKER_CROSS,
            markerSize=20,
            thickness=2,
        )

    return annotated