import cv2
import numpy as np
from pathlib import Path


def load_image_rgb(image_path: str) -> np.ndarray:
    """
    Load an image from disk and return it as an RGB numpy array.
    Raises FileNotFoundError if the path does not exist.
    Raises ValueError if OpenCV fails to decode the file.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img_bgr = cv2.imread(str(path))
    if img_bgr is None:
        raise ValueError(
            f"OpenCV could not decode the file: {image_path}. "
            "Check that it is a valid image format."
        )

    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)