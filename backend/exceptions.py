"""
Custom exceptions for the DiskImage application.
"""


class DiskImageError(Exception):
    """Base exception for all disk imaging operations."""
    pass


class ConfigError(DiskImageError):
    """Configuration-related errors."""
    pass


class DiskOperationError(DiskImageError):
    """Errors during disk imaging operations."""
    pass


class QemuError(DiskImageError):
    """QEMU-related errors."""
    pass


class QemuNotFoundError(QemuError):
    """QEMU executable or dependencies not found."""
    pass


class QemuExtractionError(QemuError):
    """Failed to extract QEMU from archive."""
    pass


class SevenZipError(DiskImageError):
    """7-Zip related errors."""
    pass


class SevenZipNotFoundError(SevenZipError):
    """7-Zip executable not found."""
    pass


class ArchiveError(DiskImageError):
    """Archive creation/extraction errors."""
    pass


class DiskListError(DiskImageError):
    """Errors when listing system disks."""
    pass


class PermissionError(DiskImageError):
    """Permission/privilege errors."""
    pass


class ValidationError(DiskImageError):
    """Input validation errors."""
    pass
