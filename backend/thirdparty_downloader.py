"""
Third-party software downloader for DiskImage application.
Handles downloading and extracting QEMU and 7-Zip if not present.
"""
import urllib.request
import subprocess
import tempfile
from pathlib import Path
import logging

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
        
        # Create tools directory if it doesn't exist
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download QEMU installer
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
            ThirdPartyDownloader._download_with_progress(QEMU_WINDOWS_URL, temp_path)
            
            # Run installer silently
            logger.info("Running QEMU installer...")
            result = subprocess.run([
                str(temp_path), 
                '/S',  # Silent install
                f'/D={QEMU_DIR}'  # Install directory
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"QEMU installer failed: {result.stderr}")
                return False
                
            # Clean up installer
            temp_path.unlink(missing_ok=True)
            
            # Verify installation
            if ThirdPartyDownloader._verify_qemu():
                logger.info("QEMU installed and verified successfully")
                return True
            else:
                logger.error("QEMU installation verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download/install QEMU: {e}")
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
        
        # Create tools directory if it doesn't exist
        SEVENZIP_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download 7-Zip installer
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
            ThirdPartyDownloader._download_with_progress(SEVENZIP_WINDOWS_URL, temp_path)
            
            # Run installer silently
            logger.info("Running 7-Zip installer...")
            result = subprocess.run([
                str(temp_path), 
                '/S',  # Silent install
                f'/D={SEVENZIP_DIR}'  # Install directory
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"7-Zip installer failed: {result.stderr}")
                return False
                
            # Clean up installer
            temp_path.unlink(missing_ok=True)
            
            # Verify installation
            if sevenzip_exe.exists():
                logger.info("7-Zip installed and verified successfully")
                return True
            else:
                logger.error("7-Zip installation verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download/install 7-Zip: {e}")
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
