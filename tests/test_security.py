"""Tests for upload validation, magic bytes, and security constraints."""

import pytest
from billdecoder.image_prep import validate_image_bytes


def test_magic_bytes_detection():
    # Valid PNG header
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    assert validate_image_bytes(png_bytes) == "png"

    # Valid JPEG header
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 50
    assert validate_image_bytes(jpeg_bytes) == "jpg"

    # Invalid executable or text file
    exe_bytes = b"MZ\x90\x00" + b"\x00" * 50
    with pytest.raises(ValueError, match="Invalid image format"):
        validate_image_bytes(exe_bytes)

    # Size limit exceeded
    huge_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * (16 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds limit"):
        validate_image_bytes(huge_bytes, max_size_bytes=15 * 1024 * 1024)
