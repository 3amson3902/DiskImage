"""
7-Zip management and operations for archive handling.
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Tuple

from .constants import SEVENZIP_DIR, TOOLS_DIR
from .exceptions import SevenZipError, SevenZipNotFoundError
from .sevenzip_ops import find_7z_exe, extract_7z_from_installer, find_7z_installer

logger = logging.getLogger(__name__)


class SevenZipManager:
    """Manages 7-Zip installation and operations."""
    
    def __init__(self):
        self.sevenzip_dir = SEVENZIP_DIR
        self._exe_path = None
    
    def initialize(self) -> None:
        """
        Initialize 7-Zip - ensure it's available.
        
        Raises:
            SevenZipError: If 7-Zip cannot be initialized
        """
        exe_path, used_tools_dir = find_7z_exe()
        if exe_path:
            self._exe_path = exe_path
            logger.info(f"7-Zip found: {exe_path} (tools dir: {used_tools_dir})")
            return
            
        # Try to extract from installer
        installer = find_7z_installer()
        if installer:
            logger.info(f"Attempting to extract 7-Zip from installer: {installer}")
            success, error = extract_7z_from_installer(installer, str(self.sevenzip_dir))
            if success:
                # Try again after extraction
                exe_path, used_tools_dir = find_7z_exe()
                if exe_path:
                    self._exe_path = exe_path
                    logger.info(f"7-Zip extracted and found: {exe_path}")
                    return
            
        raise SevenZipNotFoundError(
            "7z.exe not found. Please download 7-Zip and place 7z.exe "
            "in the tools/7zip/ directory or install it system-wide."
        )
    
    def is_available(self) -> bool:
        """
        Check if 7-Zip is available.
        
        Returns:
            True if 7z.exe is available
        """
        if self._exe_path and Path(self._exe_path).exists():
            return True
            
        exe_path, _ = find_7z_exe()
        if exe_path:
            self._exe_path = exe_path
            return True
            
        return False    
    def get_executable_path(self) -> str:
        """
        Get path to 7z.exe.
        
        Returns:
            Path to 7z.exe
            
        Raises:
            SevenZipNotFoundError: If 7z.exe not found
        """
        if not self.is_available():
            self.initialize()
            
        if self._exe_path:
            return self._exe_path
        
        raise SevenZipNotFoundError("7z.exe not found")
    
    def extract_files(
        self, 
        archive_path: str, 
        dest_dir: str, 
        files: Optional[List[str]] = None
    ) -> bool:
        """
        Extract files from archive.
        
        Args:
            archive_path: Path to archive file
            dest_dir: Destination directory
            files: List of specific files to extract (None for all)
            
        Returns:
            True if extraction successful
            
        Raises:
            SevenZipError: If extraction fails
        """
        try:
            exe_path = self.get_executable_path()
            dest_path = Path(dest_dir)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            if files:
                # Extract specific files
                for filename in files:
                    command = [
                        str(exe_path), 'e', archive_path, filename,
                        f'-o{dest_dir}', '-y'
                    ]
                    
                    result = subprocess.run(
                        command, 
                        capture_output=True, 
                        text=True, 
                        timeout=120
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to extract {filename}: {result.stderr}")
                        return False
                        
                logger.info(f"Extracted {len(files)} files from {archive_path}")
            else:
                # Extract all files
                command = [
                    str(exe_path), 'x', archive_path,
                    f'-o{dest_dir}', '-y'
                ]
                
                result = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to extract archive: {result.stderr}")
                    return False
                    
                logger.info(f"Extracted all files from {archive_path}")
            
            return True
        except subprocess.TimeoutExpired:
            raise SevenZipError("7-Zip extraction timed out")
        except Exception as e:
            raise SevenZipError(f"7-Zip extraction failed: {e}") from e
    
    def create_archive(
        self, 
        archive_path: str, 
        source_files: List[str],
        archive_type: str = "7z"
    ) -> bool:
        """
        Create archive from files.
        
        Args:
            archive_path: Output archive path
            source_files: List of files to archive
            archive_type: Archive type (7z, zip)
            
        Returns:
            True if creation successful
            
        Raises:
            SevenZipError: If archive creation fails
        """
        try:
            exe_path = self.get_executable_path()
            
            command = [str(exe_path), 'a', archive_path]
            
            if archive_type == "7z":
                command.extend(['-t7z'])
            elif archive_type == "zip":
                command.extend(['-tzip'])
            
            command.extend(source_files)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create archive: {result.stderr}")
                return False
            
            logger.info(f"Created {archive_type} archive: {archive_path}")
            return True
            
        except subprocess.TimeoutExpired:
            raise SevenZipError("Archive creation timed out")
        except Exception as e:
            raise SevenZipError(f"Archive creation failed: {e}") from e
