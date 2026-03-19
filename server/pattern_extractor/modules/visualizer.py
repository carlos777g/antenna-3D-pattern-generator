import cv2
import numpy as np


def build_annotated_image(
    mask: np.ndarray,
    center: tuple,
) -> np.ndarray:
    """
    Produce an annotated BGR image showing:
        - Pattern pixels in black on white background
        - Estimated center as a red crosshair
    No ring overlays: ring radii are derived from config, not from Hough output.
    """
    annotated = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    if center is not None:
        cx, cy = center
        cv2.drawMarker(
            annotated, (cx, cy),
            color=(0, 0, 255),
            markerType=cv2.MARKER_CROSS,
            markerSize=20,
            thickness=2,
        )

    return annotated