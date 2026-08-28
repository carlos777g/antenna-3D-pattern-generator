# visualizer.py
import cv2
import numpy as np


def build_annotated_image(
    mask: np.ndarray,
    center: tuple | None,
    outer_radius_px: float | None = None,
) -> np.ndarray:
    """
    Produce an annotated BGR image showing:
        - Pattern pixels in white on a black background (the mask as-is)
        - Estimated center as a red crosshair
        - The detected outer calibration ring in blue, when available

    The ring is drawn from the detected outer_radius_px, which is the radius
    the polar sampler calibrates against - so this overlay is what to look at
    when a manufacturer's magnitudes come out wrong.
    """
    annotated = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    if center is None:
        return annotated

    cx, cy = int(center[0]), int(center[1])

    if outer_radius_px is not None:
        cv2.circle(
            annotated, (cx, cy),
            int(round(outer_radius_px)),
            color=(255, 0, 0),
            thickness=1,
        )

    cv2.drawMarker(
        annotated, (cx, cy),
        color=(0, 0, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=20,
        thickness=2,
    )

    return annotated
