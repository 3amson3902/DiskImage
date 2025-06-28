"""
Backend logic for disk imaging and archiving operations.
Separated from PyQt UI for better testability and reusability.
"""
import logging
from typing import Tuple, Optional, Callable, Dict, Any
from pathlib import Path

from .qemu import QemuManager
from .archive import ArchiveManager
from .validation import (
    validate_disk_info, validate_output_path, validate_image_format,
    validate_archive_format, validate_buffer_size
)
from .exceptions import DiskImageError, ValidationError
from .constants import SPARSE_FORMATS

logger = logging.getLogger(__name__)


class ImagingWorker:
    """Handles disk imaging operations with proper error handling and logging."""
    
    def __init__(self):
        self.qemu_manager = QemuManager()
        self.archive_manager = ArchiveManager()
    
    def run_imaging_job(
        self,
        disk_info: Dict[str, str],
        output_path: str,
        image_format: str,
        use_sparse: bool = True,
        use_compress: bool = False,
        archive_after: bool = False,
        archive_type: Optional[str] = None,
        buffer_size: Optional[int] = None,
        cleanup_tools: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, str, str]:
        """
        Run the complete imaging and optional archiving job.
        
        Args:
            disk_info: Dictionary with disk information
            output_path: Path for output image file
            image_format: Target image format
            use_sparse: Enable sparse imaging for supported formats
            use_compress: Enable compression if supported
            archive_after: Create archive after imaging
            archive_type: Archive format (zip, 7z)
            buffer_size: Buffer size in bytes for raw operations
            cleanup_tools: Clean up extracted tools after operation
            progress_callback: Function to call with progress updates
            
        Returns:
            Tuple of (success, message, log_output)
        """
        log_messages = []
        
        def log_and_capture(level: int, message: str) -> None:
            """Log message and capture it for return."""
            logger.log(level, message)
            log_messages.append(f"{logging.getLevelName(level)}: {message}")
        
        try:
            # Validate all inputs
            log_and_capture(logging.INFO, "Starting imaging job validation")
            
            validated_disk = validate_disk_info(disk_info)
            validated_output = validate_output_path(output_path)
            validated_format = validate_image_format(image_format)
            validated_archive = validate_archive_format(archive_type) if archive_after else None
            validated_buffer = validate_buffer_size(buffer_size)
            
            log_and_capture(logging.INFO, f"Imaging disk: {validated_disk['name']} -> {validated_output}")
            log_and_capture(logging.INFO, f"Format: {validated_format}, Sparse: {use_sparse}, Compress: {use_compress}")
            
            # Determine imaging method
            if use_sparse and validated_format in SPARSE_FORMATS:
                log_and_capture(logging.INFO, "Using QEMU sparse imaging")
                success, error = self._run_qemu_imaging(
                    validated_disk,
                    str(validated_output),
                    validated_format,
                    use_compress,
                    progress_callback
                )
            else:
                log_and_capture(logging.INFO, "Using direct disk imaging")
                success, error = self._run_direct_imaging(
                    validated_disk,
                    str(validated_output),
                    validated_format,
                    use_compress,
                    validated_buffer,
                    progress_callback
                )
            
            if not success:
                log_and_capture(logging.ERROR, f"Imaging failed: {error}")
                return False, f"Imaging failed: {error}", "\\n".join(log_messages)
            
            log_and_capture(logging.INFO, "Imaging completed successfully")
            
            # Handle archiving if requested
            if archive_after and validated_archive:
                log_and_capture(logging.INFO, f"Creating {validated_archive} archive")
                
                archive_success, archive_result = self.archive_manager.create_archive(
                    str(validated_output),
                    validated_archive,
                    cleanup_original=True
                )
                
                if archive_success:
                    log_and_capture(logging.INFO, f"Archive created: {archive_result}")
                    return True, f"Imaging and archiving completed: {archive_result}", "\\n".join(log_messages)
                else:
                    log_and_capture(logging.WARNING, f"Archive creation failed: {archive_result}")
                    return False, f"Imaging completed, but archiving failed: {archive_result}", "\\n".join(log_messages)
            
            return True, "Imaging completed successfully", "\\n".join(log_messages)
            
        except ValidationError as e:
            log_and_capture(logging.ERROR, f"Validation error: {e}")
            return False, f"Invalid input: {e}", "\\n".join(log_messages)
            
        except DiskImageError as e:
            log_and_capture(logging.ERROR, f"Disk imaging error: {e}")
            return False, str(e), "\\n".join(log_messages)
            
        except Exception as e:
            log_and_capture(logging.CRITICAL, f"Unexpected error: {e}")
            logger.exception("Unexpected error in imaging job")
            return False, f"Unexpected error: {e}", "\\n".join(log_messages)
    
    def _run_qemu_imaging(
        self,
        disk_info: Dict[str, str],
        output_path: str,
        image_format: str,
        compress: bool,
        progress_callback: Optional[Callable[[int], None]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Run QEMU-based imaging for sparse formats.
        
        Args:
            disk_info: Validated disk information
            output_path: Validated output path
            image_format: Validated image format
            compress: Enable compression
            progress_callback: Progress callback function
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.qemu_manager.initialize()
            
            return self.qemu_manager.create_image(
                disk_info['device_id'],
                output_path,
                image_format,
                compress=compress,
                sparse=True,
                progress_callback=progress_callback
            )
            
        except Exception as e:
            return False, str(e)
    
    def _run_direct_imaging(
        self,
        disk_info: Dict[str, str],
        output_path: str,
        image_format: str,
        compress: bool,
        buffer_size: int,
        progress_callback: Optional[Callable[[int], None]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Run direct file-based imaging for raw formats.
        
        Args:
            disk_info: Validated disk information
            output_path: Validated output path
            image_format: Validated image format
            compress: Enable compression
            buffer_size: Buffer size in bytes
            progress_callback: Progress callback function
            
        Returns:
            Tuple of (success, error_message)
        """        # For now, delegate to QEMU as it's more reliable for physical disks
        # TODO: Implement direct imaging for special cases
        return self._run_qemu_imaging(disk_info, output_path, image_format, compress, progress_callback)


# Legacy function for backward compatibility
def run_imaging_job(
    disk: Dict[str, str],
    out_path: str,
    image_format: str,
    use_sparse: bool,
    use_compress: bool,
    archive_after: bool,
    archive_type: Optional[str],
    buffer_size: Optional[int],
    cleanup_tools: bool,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Tuple[bool, str, str]:
    """
    Legacy function for backward compatibility.
    
    Returns:
        Tuple of (success, message, log_output)
    """
    worker = ImagingWorker()
    return worker.run_imaging_job(
        disk_info=disk,
        output_path=out_path,
        image_format=image_format,
        use_sparse=use_sparse,
        use_compress=use_compress,
        archive_after=archive_after,
        archive_type=archive_type,
        buffer_size=buffer_size,
        cleanup_tools=cleanup_tools,
        progress_callback=progress_callback
    )
