"""Image preparation and validation module."""

import io
from pathlib import Path
from typing import Tuple, Union
from PIL import Image, ImageEnhance, ImageOps


# Magic bytes signatures
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC_PREFIX = b"\xff\xd8\xff"


def validate_image_bytes(image_bytes: bytes, max_size_bytes: int = 15 * 1024 * 1024) -> str:
    """Validate image bytes by size and magic bytes. Returns detected extension ('png' or 'jpg')."""
    if len(image_bytes) > max_size_bytes:
        raise ValueError(f"File size {len(image_bytes)} bytes exceeds limit of {max_size_bytes} bytes.")

    if image_bytes.startswith(PNG_MAGIC):
        return "png"
    elif image_bytes.startswith(JPEG_MAGIC_PREFIX):
        return "jpg"
    else:
        raise ValueError("Invalid image format. Only PNG and JPEG images are supported.")


def prepare_image(
    image_input: Union[bytes, str, Path],
    max_long_edge: int = 2048,
    enhance_contrast: bool = True,
) -> Image.Image:
    """Prepare bill image for LLM processing:
    - Validates magic bytes and size
    - Normalizes EXIF orientation
    - Converts to RGB
    - Resizes only if long edge exceeds max_long_edge (NEVER upscales, NEVER crops)
    - Mild contrast enhancement for readability of tiny table numbers
    """
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.is_file():
            raise FileNotFoundError(f"Image file not found: {path}")
        image_bytes = path.read_bytes()
    else:
        image_bytes = image_input

    # Validate magic bytes
    validate_image_bytes(image_bytes)

    # Open PIL image
    img = Image.open(io.BytesIO(image_bytes))

    # Apply EXIF transpose (handles tilted phone photos)
    img = ImageOps.exif_transpose(img)

    # Ensure RGB mode
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Downscale ONLY if long edge exceeds max_long_edge; NEVER upscale or crop
    width, height = img.size
    long_edge = max(width, height)
    if long_edge > max_long_edge:
        scale = max_long_edge / float(long_edge)
        new_width = int(round(width * scale))
        new_height = int(round(height * scale))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Mild contrast enhancement (factor 1.12 to make faint table text clearer without clipping)
    if enhance_contrast:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.12)

    return img
