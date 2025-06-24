"""
Input validation utilities for DiskImage application.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Mapping
import re

from .exceptions import ValidationError
from .constants import SUPPORTED_IMAGE_FORMATS, SUPPORTED_ARCHIVE_FORMATS


def validate_disk_info(disk_info: Mapping[str, str]) -> Dict[str, str]:
    """
    Validate disk information dictionary.
    
    Args:
        disk_info: Disk information to validate
        
    Returns:
        Validated disk info dict
        
    Raises:
        ValidationError: If disk info is invalid
    """
    if not isinstance(disk_info, dict):
        raise ValidationError("Disk info must be a dictionary")
    
    required_keys = ['device_id', 'name', 'size', 'model']
    for key in required_keys:
        if key not in disk_info:
            raise ValidationError(f"Disk info missing required key: {key}")
    
    # Validate device_id format
    device_id: str = disk_info['device_id']
    if not device_id:
        raise ValidationError("Device ID cannot be empty")
    
    return dict(disk_info)


def validate_output_path(output_path: str) -> Path:
    """
    Validate and normalize output file path.
    
    Args:
        output_path: Output file path string
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if not output_path:
        raise ValidationError("Output path must be a non-empty string")
    
    path = Path(output_path).resolve()
    
    # Check if parent directory exists or can be created
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValidationError(f"Cannot create output directory: {e}")
    
    # Check for valid filename
    if not path.name:
        raise ValidationError("Output path must include a filename")
    
    # Basic filename validation (no invalid characters)
    invalid_chars = r'[<>:"|?*]'
    if re.search(invalid_chars, path.name):
        raise ValidationError("Filename contains invalid characters")
    
    return path


def validate_image_format(image_format: str) -> str:
    """
    Validate image format.
    
    Args:
        image_format: Image format string
        
    Returns:
        Validated format string
        
    Raises:
        ValidationError: If format is unsupported
    """
    # Check if it's a key or value in SUPPORTED_IMAGE_FORMATS
    if image_format in SUPPORTED_IMAGE_FORMATS:
        return SUPPORTED_IMAGE_FORMATS[image_format]
    elif image_format in SUPPORTED_IMAGE_FORMATS.values():
        return image_format
    else:
        supported = list(SUPPORTED_IMAGE_FORMATS.values())
        raise ValidationError(f"Unsupported image format: {image_format}. "
                            f"Supported formats: {supported}")


def validate_archive_format(archive_format: Optional[str]) -> Optional[str]:
    """
    Validate archive format.
    
    Args:
        archive_format: Archive format string or None
        
    Returns:
        Validated format string or None
        
    Raises:
        ValidationError: If format is unsupported
    """
    if archive_format is None:
        return None
    
    if archive_format not in SUPPORTED_ARCHIVE_FORMATS:
        raise ValidationError(f"Unsupported archive format: {archive_format}. "
                            f"Supported formats: {SUPPORTED_ARCHIVE_FORMATS}")
    
    return archive_format


def validate_buffer_size(buffer_size: Any) -> int:
    """
    Validate buffer size in bytes.
    
    Args:
        buffer_size: Buffer size to validate
        
    Returns:
        Validated buffer size in bytes
        
    Raises:
        ValidationError: If buffer size is invalid
    """
    if buffer_size is None:
        return 64 * 1024 * 1024  # Default 64MB
    
    try:
        size = int(buffer_size)
    except (ValueError, TypeError):
        raise ValidationError("Buffer size must be an integer")
    
    if size <= 0:
        raise ValidationError("Buffer size must be positive")
    
    if size > 1024 * 1024 * 1024:  # 1GB limit
        raise ValidationError("Buffer size too large (max 1GB)")
    
    return size


def sanitize_path_for_subprocess(path: str) -> str:
    """
    Sanitize a path string for safe use in subprocess calls.
    
    Args:
        path: Path string to sanitize
        
    Returns:
        Sanitized path string
        
    Raises:
        ValidationError: If path contains dangerous characters
    """
    # Check for potential injection attempts
    dangerous_chars = ['&', '|', ';', '$', '`', '(', ')', '{', '}']
    for char in dangerous_chars:
        if char in path:
            raise ValidationError(f"Path contains potentially dangerous character: {char}")
    
    return path
