"""
7-Zip management and operations for archive handling.
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Tuple

from .constants import SEVENZIP_DIR, TOOLS_DIR
from .exceptions import SevenZipError, SevenZipNotFoundError

logger = logging.getLogger(__name__)


class SevenZipManager:
    """Manages 7-Zip installation and operations."""
    
    def __init__(self):
        self.sevenzip_dir = SEVENZIP_DIR
        self.sevenzip_exe = self.sevenzip_dir / "7z.exe"
    
    def initialize(self) -> None:
        """
        Initialize 7-Zip - ensure it's available.
        
        Raises:
            SevenZipError: If 7-Zip cannot be initialized
        """
        if not self.is_available():
            self._try_extract_from_installer()
            
        if not self.is_available():
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
        # Check local installation first
        if self.sevenzip_exe.exists():
            return True
        
        # Check system PATH
        return self._check_system_7zip()
    
    def get_executable_path(self) -> Path:
        """
        Get path to 7z.exe.
        
        Returns:
            Path to 7z.exe
            
        Raises:
            SevenZipNotFoundError: If 7z.exe not found
        """
        if self.sevenzip_exe.exists():
            return self.sevenzip_exe
        
        if self._check_system_7zip():
            return Path("7z")  # Use system command
        
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
    
    def _check_system_7zip(self) -> bool:
        """Check if 7z.exe is available in system PATH."""
        try:
            result = subprocess.run(
                ['7z'], 
                capture_output=True, 
                timeout=10
            )
            # 7z returns 0 when run without arguments and shows help
            return result.returncode == 0
        except Exception:
            return False
    
    def _find_7zip_installer(self) -> Optional[Path]:
        """Find 7-Zip installer in tools directory."""
        if not TOOLS_DIR.exists():
            return None
        
        for file_path in TOOLS_DIR.iterdir():
            name_lower = file_path.name.lower()
            if (name_lower.startswith('7z') and 
                name_lower.endswith('.exe') and 
                file_path.is_file()):
                return file_path
        
        return None
    
    def _try_extract_from_installer(self) -> None:
        """Try to extract 7z.exe from installer."""
        installer = self._find_7zip_installer()
        if not installer:
            return
        
        logger.info(f"Attempting to extract 7-Zip from installer: {installer}")
        
        # Create directory
        self.sevenzip_dir.mkdir(parents=True, exist_ok=True)
        
        # Try using system 7z.exe to extract from installer
        if self._check_system_7zip():
            try:
                result = subprocess.run([
                    '7z', 'x', str(installer), '7z.exe', '7z.dll',
                    f'-o{self.sevenzip_dir}', '-y'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and self.sevenzip_exe.exists():
                    logger.info("Successfully extracted 7-Zip using system 7z.exe")
                    return
            except Exception as e:
                logger.debug(f"System 7z.exe extraction failed: {e}")
        
        # Try running installer in silent mode
        try:
            dest_abs = self.sevenzip_dir.resolve()
            result = subprocess.run([
                str(installer), '/S', f'/D={dest_abs}\\\\'
            ], capture_output=True, text=True, timeout=60)
            
            # Wait and check for files
            import time
            for _ in range(10):
                if self.sevenzip_exe.exists():
                    logger.info("Successfully extracted 7-Zip using silent installer")
                    return
                time.sleep(0.5)
            
            # Check subdirectories
            for item in self.sevenzip_dir.rglob("7z.exe"):
                if item.is_file():
                    item.replace(self.sevenzip_exe)
                    # Also try to find 7z.dll
                    dll_path = item.parent / "7z.dll"
                    if dll_path.exists():
                        dll_path.replace(self.sevenzip_dir / "7z.dll")
                    logger.info("Found and moved 7-Zip files from subdirectory")
                    return
                    
        except Exception as e:
            logger.debug(f"Silent installer extraction failed: {e}")
        
        logger.warning("Could not extract 7-Zip from installer")
