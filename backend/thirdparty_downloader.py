"""
Third-party software downloader for DiskImage application.
Handles downloading and extracting QEMU and 7-Zip if not present.

This module creates portable installations by extracting files from installers
rather than running system-wide installations. This ensures:
- No administrative privileges required
- No system registry modifications
- Easy cleanup and removal
- Isolated from system installations
"""
import urllib.request
import subprocess
import tempfile
import shutil
import os
from pathlib import Path
import logging

# Archive extraction libraries
try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

try:
    import patoolib
    HAS_PATOOL = True
except ImportError:
    HAS_PATOOL = False

from .constants import (
    QEMU_WINDOWS_URL, 
    SEVENZIP_WINDOWS_URL, 
    TOOLS_DIR, 
    QEMU_DIR, 
    SEVENZIP_DIR
)

logger = logging.getLogger(__name__)


class ThirdPartyDownloader:
    """
    Downloads and verifies third-party software (QEMU, 7-Zip) if not present.
    """
    
    @staticmethod
    def ensure_qemu() -> bool:
        """
        Ensure QEMU is available in the tools directory.
        
        Returns:
            bool: True if QEMU is available or successfully downloaded
        """
        if ThirdPartyDownloader._verify_qemu():
            logger.info("QEMU installation verified")
            return True
            
        logger.info("QEMU not found or incomplete, attempting download...")
        logger.debug(ThirdPartyDownloader._check_extraction_capabilities())
        
        # Create tools directory if it doesn't exist
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download QEMU installer/archive
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
            ThirdPartyDownloader._download_with_progress(QEMU_WINDOWS_URL, temp_path)
            
            # Extract QEMU files from the installer using 7-Zip (if available)
            logger.info("Extracting QEMU files...")
            
            # Try to extract using built-in Windows tools first
            success = ThirdPartyDownloader._extract_qemu_portable(temp_path)
            
            if not success:
                logger.error("Failed to extract QEMU files")
                return False
                
            # Clean up installer
            temp_path.unlink(missing_ok=True)
            
            # Verify installation
            if ThirdPartyDownloader._verify_qemu():
                logger.info("QEMU extracted and verified successfully")
                return True
            else:
                logger.error("QEMU extraction verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download/extract QEMU: {e}")
            return False

    @staticmethod
    def ensure_sevenzip() -> bool:
        """
        Ensure 7-Zip is available in the tools directory.
        
        Returns:
            bool: True if 7-Zip is available or successfully downloaded
        """
        sevenzip_exe = SEVENZIP_DIR / "7z.exe"
        
        if sevenzip_exe.exists():
            logger.info("7-Zip installation verified")
            return True
            
        logger.info("7-Zip not found, attempting download...")
        logger.debug(ThirdPartyDownloader._check_extraction_capabilities())
        
        # Create tools directory if it doesn't exist
        SEVENZIP_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download 7-Zip installer
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
            ThirdPartyDownloader._download_with_progress(SEVENZIP_WINDOWS_URL, temp_path)
            
            # Extract 7-Zip files from installer
            logger.info("Extracting 7-Zip files...")
            success = ThirdPartyDownloader._extract_sevenzip_portable(temp_path)
            
            if not success:
                logger.error("Failed to extract 7-Zip files")
                return False
                
            # Clean up installer
            temp_path.unlink(missing_ok=True)
            
            # Verify installation
            if sevenzip_exe.exists():
                logger.info("7-Zip extracted and verified successfully")
                return True
            else:
                logger.error("7-Zip extraction verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download/extract 7-Zip: {e}")
            return False

    @staticmethod
    def _verify_qemu() -> bool:
        """
        Verify QEMU installation by checking for required files.
        
        Returns:
            bool: True if QEMU installation is complete
        """
        if not QEMU_DIR.exists():
            return False
            
        # Check for qemu-img.exe as the primary indicator
        qemu_img = QEMU_DIR / "qemu-img.exe"
        if not qemu_img.exists():
            return False
            
        # Check a sample of critical files
        critical_files = ["qemu-img.exe", "qemu-system-x86_64.exe", "zlib1.dll"]
        for file_name in critical_files:
            if not (QEMU_DIR / file_name).exists():
                logger.warning(f"Missing critical QEMU file: {file_name}")
                return False
                
        return True

    @staticmethod
    def _download_with_progress(url: str, dest: Path):
        """
        Download a file with progress logging.
        
        Args:
            url: URL to download from
            dest: Destination file path
        """
        try:
            logger.info(f"Downloading from {url}")
            logger.info(f"Destination: {dest}")
            
            with urllib.request.urlopen(url) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                
                with open(dest, 'wb') as out_file:
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                            
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (chunk_size * 100) == 0:  # Log every ~800KB
                                logger.info(f"Download progress: {percent:.1f}%")
                                
            logger.info(f"Download completed: {dest.name}")
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if dest.exists():
                dest.unlink()  # Clean up partial download
            raise

    @staticmethod
    def _extract_qemu_portable(installer_path: Path) -> bool:
        """
        Extract QEMU files from the installer to create a portable installation.
        
        Args:
            installer_path: Path to the downloaded QEMU installer
            
        Returns:
            bool: True if extraction was successful
        """
        try:
            # Create QEMU directory
            QEMU_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info("Extracting QEMU installer using Python libraries...")
            
            # Method 1: Try py7zr (pure Python)
            if HAS_PY7ZR:
                try:
                    logger.info("Attempting extraction with py7zr...")
                    with py7zr.SevenZipFile(installer_path, mode='r') as archive:
                        archive.extractall(path=QEMU_DIR)
                    logger.info("QEMU extracted successfully using py7zr")
                    ThirdPartyDownloader._cleanup_extracted_qemu()
                    return True
                except Exception as e:
                    logger.debug(f"py7zr extraction failed: {e}")
            
            # Method 2: Try patoolib (universal extractor)
            if HAS_PATOOL:
                try:
                    logger.info("Attempting extraction with patoolib...")
                    patoolib.extract_archive(str(installer_path), outdir=str(QEMU_DIR))
                    logger.info("QEMU extracted successfully using patoolib")
                    ThirdPartyDownloader._cleanup_extracted_qemu()
                    return True
                except Exception as e:
                    logger.debug(f"patoolib extraction failed: {e}")
            
            # Method 3: Fallback to subprocess methods
            logger.info("Falling back to subprocess extraction methods...")
            return ThirdPartyDownloader._extract_with_subprocess_fallback(installer_path, QEMU_DIR)
            
        except Exception as e:
            logger.error(f"Failed to extract QEMU: {e}")
            return False
    
    @staticmethod
    def _cleanup_extracted_qemu():
        """Clean up unnecessary files from extracted QEMU installation."""
        try:
            # Remove uninstaller and other unnecessary files
            cleanup_files = [
                "qemu-uninstall.exe",
                "Uninstall.exe",
                "$PLUGINSDIR",
                "$TEMP"
            ]
            
            for cleanup_file in cleanup_files:
                cleanup_path = QEMU_DIR / cleanup_file
                if cleanup_path.exists():
                    if cleanup_path.is_file():
                        cleanup_path.unlink()
                    elif cleanup_path.is_dir():
                        shutil.rmtree(cleanup_path, ignore_errors=True)
                        
        except Exception as e:
            logger.warning(f"Could not clean up extracted files: {e}")
    
    @staticmethod
    def _extract_with_subprocess_fallback(installer_path: Path, dest_dir: Path) -> bool:
        """
        Fallback extraction method using subprocess calls.
        
        Args:
            installer_path: Path to the installer file
            dest_dir: Destination directory
            
        Returns:
            bool: True if extraction succeeded
        """
        try:
            # Try using PowerShell Expand-Archive if it's a ZIP-based installer
            logger.info("Attempting PowerShell extraction...")
            result = subprocess.run([
                'powershell', '-Command',
                f'try {{ Expand-Archive -Path "{installer_path}" -DestinationPath "{dest_dir}" -Force; exit 0 }} catch {{ exit 1 }}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Extracted using PowerShell")
                return True
                
            logger.warning("PowerShell extraction failed, trying installer silent mode...")
            
            # Try running installer with silent flags
            with tempfile.TemporaryDirectory() as temp_dir:
                for flags in ['/VERYSILENT /DIR=', '/S /D=', '/SILENT /DIR=']:
                    try:
                        cmd_flag, dir_flag = flags.split(' ', 1)
                        result = subprocess.run([
                            str(installer_path),
                            cmd_flag,
                            f'{dir_flag}{temp_dir}'
                        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                        
                        temp_path = Path(temp_dir)
                        if temp_path.exists() and any(temp_path.iterdir()):
                            # Copy all files to dest_dir
                            for item in temp_path.rglob('*'):
                                if item.is_file():
                                    relative_path = item.relative_to(temp_path)
                                    dest_path = dest_dir / relative_path
                                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(item, dest_path)
                            logger.info(f"Extracted using installer flags: {flags}")
                            return True
                            
                    except (subprocess.TimeoutExpired, Exception) as e:
                        logger.debug(f"Extraction attempt with {flags} failed: {e}")
                        continue
                        
            return False
            
        except Exception as e:
            logger.error(f"Subprocess fallback extraction failed: {e}")
            return False

    @staticmethod
    def _extract_sevenzip_portable(installer_path: Path) -> bool:
        """
        Extract 7-Zip files from the installer to create a portable installation.
        
        Args:
            installer_path: Path to the downloaded 7-Zip installer
            
        Returns:
            bool: True if extraction was successful
        """
        try:
            # Create 7-Zip directory
            SEVENZIP_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info("Extracting 7-Zip installer using Python libraries...")
            
            # Method 1: Try py7zr (pure Python)
            if HAS_PY7ZR:
                try:
                    logger.info("Attempting extraction with py7zr...")
                    with py7zr.SevenZipFile(installer_path, mode='r') as archive:
                        archive.extractall(path=SEVENZIP_DIR)
                    logger.info("7-Zip extracted successfully using py7zr")
                    return True
                except Exception as e:
                    logger.debug(f"py7zr extraction failed: {e}")
            
            # Method 2: Try patoolib (universal extractor)
            if HAS_PATOOL:
                try:
                    logger.info("Attempting extraction with patoolib...")
                    patoolib.extract_archive(str(installer_path), outdir=str(SEVENZIP_DIR))
                    logger.info("7-Zip extracted successfully using patoolib")
                    return True
                except Exception as e:
                    logger.debug(f"patoolib extraction failed: {e}")
            
            # Method 3: Fallback to subprocess methods
            logger.info("Falling back to subprocess extraction methods...")
            return ThirdPartyDownloader._extract_with_subprocess_fallback(installer_path, SEVENZIP_DIR)
            
        except Exception as e:
            logger.error(f"Failed to extract 7-Zip: {e}")
            return False

    @staticmethod
    def _check_extraction_capabilities() -> str:
        """
        Check what extraction capabilities are available.
        
        Returns:
            str: A message describing available extraction methods
        """
        methods = []
        
        if HAS_PY7ZR:
            methods.append("py7zr (pure Python 7-Zip)")
        if HAS_PATOOL:
            methods.append("patoolib (universal archive extractor)")
        
        methods.append("subprocess fallback (PowerShell, installer silent mode)")
        
        return f"Available extraction methods: {', '.join(methods)}"
    