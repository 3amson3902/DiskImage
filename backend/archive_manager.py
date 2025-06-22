"""
Archive management for disk images.
"""
import zipfile
import logging
from pathlib import Path
from typing import Tuple, Optional

from .sevenzip_manager import SevenZipManager
from .exceptions import ArchiveError
from .validation import validate_archive_format

logger = logging.getLogger(__name__)


class ArchiveManager:
    """Manages archive creation and extraction for disk images."""
    
    def __init__(self):
        self.sevenzip_manager = SevenZipManager()
    
    def create_archive(
        self,
        source_path: str,
        archive_type: str,
        cleanup_original: bool = False
    ) -> Tuple[bool, str]:
        """
        Create an archive from a source file.
        
        Args:
            source_path: Path to source file
            archive_type: Archive type (zip, 7z)
            cleanup_original: Remove source file after successful archiving
            
        Returns:
            Tuple of (success, result_path_or_error)
        """
        try:
            # Validate inputs
            validated_type = validate_archive_format(archive_type)
            if not validated_type:
                raise ArchiveError("Archive type is required")
            
            source = Path(source_path)
            if not source.exists():
                raise ArchiveError(f"Source file does not exist: {source_path}")
            
            # Determine archive path
            archive_path = source.with_suffix(f".{validated_type}")
            
            logger.info(f"Creating {validated_type} archive: {source_path} -> {archive_path}")
            
            # Create archive based on type
            if validated_type == "zip":
                success = self._create_zip_archive(source, archive_path)
            elif validated_type == "7z":
                success = self._create_7z_archive(source, archive_path)
            else:
                raise ArchiveError(f"Unsupported archive type: {validated_type}")
            
            if not success:
                return False, f"Failed to create {validated_type} archive"
            
            # Verify archive was created
            if not archive_path.exists():
                return False, f"Archive file was not created: {archive_path}"
            
            # Clean up original if requested
            if cleanup_original:
                try:
                    source.unlink()
                    logger.info(f"Removed original file: {source_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove original file: {e}")
                    # Don't fail the operation for cleanup issues
            
            logger.info(f"Archive created successfully: {archive_path}")
            return True, str(archive_path)
            
        except Exception as e:
            logger.exception("Failed to create archive")
            return False, str(e)
    
    def _create_zip_archive(self, source: Path, archive_path: Path) -> bool:
        """
        Create a ZIP archive using Python's zipfile module.
        
        Args:
            source: Source file path
            archive_path: Target archive path
            
        Returns:
            True if successful
        """
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                zf.write(source, source.name)
            
            logger.debug(f"ZIP archive created: {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ZIP archive: {e}")
            # Clean up partial archive
            try:
                if archive_path.exists():
                    archive_path.unlink()
            except Exception:
                pass
            return False
    
    def _create_7z_archive(self, source: Path, archive_path: Path) -> bool:
        """
        Create a 7z archive using 7-Zip.
        
        Args:
            source: Source file path
            archive_path: Target archive path
            
        Returns:
            True if successful
        """
        try:
            # Initialize 7-Zip if needed
            self.sevenzip_manager.initialize()
            
            success = self.sevenzip_manager.create_archive(
                str(archive_path),
                [str(source)],
                "7z"
            )
            
            if success:
                logger.debug(f"7z archive created: {archive_path}")
            else:
                logger.error("7-Zip archive creation failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create 7z archive: {e}")
            # Clean up partial archive
            try:
                if archive_path.exists():
                    archive_path.unlink()
            except Exception:
                pass
            return False


# Legacy function for backward compatibility
def archive_image(image_path: str, archive_type: str, cleanup_tools: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Legacy function for backward compatibility.
    
    Returns:
        Tuple of (archive_path, error_message) - note the different return format
    """
    manager = ArchiveManager()
    success, result = manager.create_archive(image_path, archive_type, cleanup_original=True)
    
    if success:
        return result, None
    else:
        return None, result
