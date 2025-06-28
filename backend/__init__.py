"""
Backend package for DiskImage.

Provides core functionality for disk imaging, archiving, and tool management.
"""

# Core managers
from .qemu import QemuManager
from .sevenzip import SevenZipManager  
from .archive import ArchiveManager

# Worker classes
from .imaging import ImagingWorker

# Utilities
from .config import AppConfig
from .logging_config import setup_logging, get_logger
from .disk_list import list_disks
from .admin import is_admin, require_admin
from .cleanup import cleanup_qemu_files, cleanup_sevenzip_files, cleanup_all_tools
from .validation import (
    validate_disk_info, validate_output_path, validate_image_format,
    validate_archive_format, validate_buffer_size
)

# Exceptions
from .exceptions import (
    DiskImageError, ConfigError, DiskOperationError, QemuError,
    QemuNotFoundError, QemuExtractionError, SevenZipError,
    SevenZipNotFoundError, ArchiveError, DiskListError,
    PermissionError, ValidationError
)

# Constants
from .constants import (
    SUPPORTED_IMAGE_FORMATS, SUPPORTED_ARCHIVE_FORMATS,
    DEFAULT_BUFFER_SIZE, SPARSE_FORMATS, COMPRESSIBLE_FORMATS
)

# Legacy imports for backward compatibility
from .imaging import run_imaging_job
from .archive import archive_image
from .config import load_config, save_config, update_config

__all__ = [
    # Core managers
    'QemuManager', 'SevenZipManager', 'ArchiveManager',
    
    # Worker classes  
    'ImagingWorker',
    
    # Utilities
    'AppConfig', 'setup_logging', 'get_logger', 'list_disks',
    'is_admin', 'require_admin', 'cleanup_qemu_files',
    'cleanup_sevenzip_files', 'cleanup_all_tools',
    
    # Validation
    'validate_disk_info', 'validate_output_path', 'validate_image_format',
    'validate_archive_format', 'validate_buffer_size',
    
    # Exceptions
    'DiskImageError', 'ConfigError', 'DiskOperationError', 'QemuError',
    'QemuNotFoundError', 'QemuExtractionError', 'SevenZipError', 
    'SevenZipNotFoundError', 'ArchiveError', 'DiskListError',
    'PermissionError', 'ValidationError',
    
    # Constants
    'SUPPORTED_IMAGE_FORMATS', 'SUPPORTED_ARCHIVE_FORMATS',
    'DEFAULT_BUFFER_SIZE', 'SPARSE_FORMATS', 'COMPRESSIBLE_FORMATS',
    
    # Legacy functions
    'run_imaging_job', 'archive_image', 'load_config', 'save_config', 'update_config'
]
