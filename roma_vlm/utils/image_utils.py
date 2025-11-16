"""Utility functions for image handling in ROMA-VLM."""

import base64
from pathlib import Path
from typing import Tuple, Optional, Union
from PIL import Image
import io


def load_image(image_path: Union[str, Path]) -> Image.Image:
    """
    Load image from file path.
    
    Args:
        image_path: Path to image file
        
    Returns:
        PIL Image object
        
    Raises:
        FileNotFoundError: If image doesn't exist
        ValueError: If file is not a valid image
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    try:
        img = Image.open(path)
        img.load()  # Verify image can be loaded
        return img
    except Exception as e:
        raise ValueError(f"Failed to load image {image_path}: {e}")


def encode_image_base64(
    image_path: Union[str, Path],
    max_size_mb: float = 5.0
) -> str:
    """
    Encode image to base64 string for VLM API calls.
    
    Args:
        image_path: Path to image file
        max_size_mb: Maximum file size in MB (default 5MB)
        
    Returns:
        Base64 encoded string
        
    Raises:
        ValueError: If image exceeds max size
    """
    path = Path(image_path)
    file_size_mb = path.stat().st_size / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        raise ValueError(
            f"Image {image_path} is {file_size_mb:.2f}MB, "
            f"exceeds max {max_size_mb}MB"
        )
    
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    return encoded


def validate_image(
    image_path: Union[str, Path],
    allowed_formats: Optional[list] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate image file.
    
    Args:
        image_path: Path to image
        allowed_formats: List of allowed formats (e.g., ['JPEG', 'PNG'])
        
    Returns:
        (is_valid, error_message)
    """
    if allowed_formats is None:
        allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP', 'BMP']
    
    path = Path(image_path)
    
    if not path.exists():
        return False, f"File not found: {image_path}"
    
    try:
        img = Image.open(path)
        img.load()
        
        if img.format not in allowed_formats:
            return False, f"Format {img.format} not in allowed: {allowed_formats}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid image: {e}"


def get_image_info(image_path: Union[str, Path]) -> dict:
    """
    Get image metadata and info.
    
    Args:
        image_path: Path to image
        
    Returns:
        Dict with image info (size, format, mode, etc.)
    """
    path = Path(image_path)
    img = Image.open(path)
    
    return {
        "path": str(path.absolute()),
        "size": img.size,  # (width, height)
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
        "file_size_kb": path.stat().st_size / 1024,
        "file_size_mb": path.stat().st_size / (1024 * 1024),
    }


def resize_image_if_needed(
    image_path: Union[str, Path],
    max_dimension: int = 2048,
    output_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Resize image if it exceeds max dimension (for VLM optimization).
    
    Args:
        image_path: Input image path
        max_dimension: Maximum width or height
        output_path: Output path (defaults to input_resized.ext)
        
    Returns:
        Path to resized image (or original if no resize needed)
    """
    img = Image.open(image_path)
    
    if max(img.size) <= max_dimension:
        return Path(image_path)
    
    # Calculate new size maintaining aspect ratio
    ratio = max_dimension / max(img.size)
    new_size = tuple(int(dim * ratio) for dim in img.size)
    
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    
    if output_path is None:
        path = Path(image_path)
        output_path = path.parent / f"{path.stem}_resized{path.suffix}"
    
    resized.save(output_path)
    return Path(output_path)

