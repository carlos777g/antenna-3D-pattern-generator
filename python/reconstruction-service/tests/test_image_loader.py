# test_image_loader.py
import cv2
import numpy as np
import pytest

from modules.image_loader import load_image_rgb


def test_missing_file_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError, match="Image not found"):
        load_image_rgb(str(tmp_path / "does-not-exist.png"))


def test_undecodable_file_raises_valueerror(tmp_path):
    bogus = tmp_path / "not-an-image.png"
    bogus.write_bytes(b"this is not a PNG")
    with pytest.raises(ValueError, match="could not decode"):
        load_image_rgb(str(bogus))


def test_channels_are_returned_in_rgb_order(tmp_path):
    """
    Write a pure-red image (OpenCV expects BGR on write) and assert the loader
    hands back red in channel 0, not channel 2.
    """
    path = tmp_path / "red.png"
    bgr = np.zeros((4, 4, 3), dtype=np.uint8)
    bgr[:, :, 2] = 255  # red in BGR
    cv2.imwrite(str(path), bgr)

    rgb = load_image_rgb(str(path))
    assert rgb.shape == (4, 4, 3)
    assert np.all(rgb[:, :, 0] == 255)
    assert np.all(rgb[:, :, 1] == 0)
    assert np.all(rgb[:, :, 2] == 0)
