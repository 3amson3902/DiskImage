"""
QEMU management and operations for disk imaging.
"""
import platform
import subprocess
import logging
import threading
import time
import os
from pathlib import Path
from typing import Tuple, Optional, List, Callable

from .constants import (
    REQUIRED_QEMU_FILES, QEMU_DIR, TOOLS_DIR, WINDOWS_DLL_NOT_FOUND,
    ARCHIVE_PRIORITY
)
from .exceptions import QemuError, QemuNotFoundError, QemuExtractionError
from .validation import validate_output_path, sanitize_path_for_subprocess

logger = logging.getLogger(__name__)


class QemuManager:
    """Manages QEMU installation, extraction, and execution."""
    
    def __init__(self):
        self.qemu_dir = QEMU_DIR
        self.qemu_executable = self.qemu_dir / "qemu-img.exe"
        self.is_windows = platform.system() == "Windows"
    
    def initialize(self) -> None:
        """
        Initialize QEMU - ensure it's available and ready to use.
        
        Raises:
            QemuError: If QEMU cannot be initialized
        """
        if self.is_windows:
            if not self.check_files_present():
                self._extract_qemu()
            logger.info("QEMU initialized for Windows")
        else:
            # On Unix systems, use system qemu-img
            if not self._check_system_qemu():
                raise QemuNotFoundError(
                    "qemu-img not found in system PATH. "
                    "Please install QEMU using your package manager."
                )
            logger.info("Using system QEMU")
    
    def check_files_present(self) -> bool:
        """
        Check if all required QEMU files are present.
        
        Returns:
            True if all files present, False otherwise
        """
        if not self.qemu_dir.exists():
            return False
            
        for filename in REQUIRED_QEMU_FILES:
            if not (self.qemu_dir / filename).exists():
                logger.debug(f"Missing QEMU file: {filename}")
                return False
        
        return True
    
    def get_executable_path(self) -> Path:
        """
        Get the path to qemu-img executable.
        
        Returns:
            Path to qemu-img executable
            
        Raises:
            QemuNotFoundError: If qemu-img not found
        """
        if self.is_windows:
            if not self.qemu_executable.exists():
                raise QemuNotFoundError(f"qemu-img.exe not found at {self.qemu_executable}")
            return self.qemu_executable
        else:
            # Return string for system command
            return Path("qemu-img")
    
    def run_command(
        self, 
        command: List[str], 
        timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Run a qemu-img command.
        
        Args:
            command: Command arguments (qemu-img will be prepended)
            timeout: Command timeout in seconds
            
        Returns:
            Subprocess result
            
        Raises:
            QemuError: If command fails
        """
        try:
            qemu_path = self.get_executable_path()
            full_command = [str(qemu_path)] + command
            
            logger.info(f"Running QEMU command: {' '.join(full_command)}")
            
            kwargs = {
                'capture_output': True,
                'text': True,
                'timeout': timeout
            }
            
            if self.is_windows:
                kwargs['cwd'] = str(self.qemu_dir)
            
            result = subprocess.run(full_command, **kwargs)
            
            if result.returncode == WINDOWS_DLL_NOT_FOUND and self.is_windows:
                logger.warning("DLL missing error detected, attempting recovery")
                self._handle_dll_error()
                # Retry once
                result = subprocess.run(full_command, **kwargs)
            
            return result            
        except subprocess.TimeoutExpired as e:
            raise QemuError(f"QEMU command timed out after {timeout} seconds") from e
        except Exception as e:
            raise QemuError(f"Failed to run QEMU command: {e}") from e
    
    def create_image(
        self,
        source_path: str,
        output_path: str,
        image_format: str = "raw",
        compress: bool = False,
        sparse: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Create a disk image using qemu-img.
        
        Args:
            source_path: Source device or file path
            output_path: Output image path
            image_format: Output format (raw, qcow2, vhd, vmdk)
            compress: Enable compression if supported
            sparse: Use sparse allocation
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate inputs
            validated_output = validate_output_path(output_path)
            sanitized_source = sanitize_path_for_subprocess(source_path)
              # Build command with performance optimizations
            command = ['convert', '-p']
            
            # Performance optimizations
            command.extend(['-m', '16'])  # Use 16 parallel coroutines for better I/O
            command.extend(['-W'])        # Allow unsafe cache operations for speed
            
            # Buffer size optimization - use larger buffers for better throughput
            if self.is_windows:
                # Windows-specific optimizations for physical disks
                command.extend(['-T', 'none'])  # Disable source cache for direct I/O
                command.extend(['-f', 'raw'])   # Explicitly set source format
            
            if sparse:
                command.extend(['-S', '4096'])
            
            command.extend(['-O', image_format])
            
            # Target cache optimizations
            if image_format == 'raw':
                command.extend(['-t', 'none'])  # Disable target cache for raw images
            else:
                command.extend(['-t', 'writeback'])  # Use writeback cache for other formats
            
            if compress and image_format in ['qcow2', 'vmdk']:
                command.append('-c')
            
            command.extend([sanitized_source, str(validated_output)])
            
            # If progress callback is provided, use enhanced monitoring
            if progress_callback:
                return self._run_command_with_progress(command, validated_output, progress_callback)
            else:
                # Run command normally
                result = self.run_command(command)
                
                if result.returncode == 0:
                    logger.info("QEMU image creation completed successfully")
                    return True, None
                else:
                    error_msg = f"qemu-img failed (code {result.returncode}):\\n"
                    if result.stdout:
                        error_msg += f"STDOUT:\\n{result.stdout}\\n"
                    if result.stderr:
                        error_msg += f"STDERR:\\n{result.stderr}"
                    
                    logger.error(error_msg)
                    return False, error_msg
                if result.stdout:
                    error_msg += f"STDOUT:\\n{result.stdout}\\n"
                if result.stderr:
                    error_msg += f"STDERR:\\n{result.stderr}"
                
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            logger.exception("Exception in QEMU image creation")
            return False, str(e)
    
    def _extract_qemu(self) -> None:
        """
        Extract QEMU files from archive.
        
        Raises:
            QemuExtractionError: If extraction fails
        """
        archive_path = self._find_qemu_archive()
        if not archive_path:
            raise QemuExtractionError(
                "No QEMU archive found in tools directory. "
                "Please download a QEMU Windows build and place it in the tools/ directory."
            )
        
        logger.info(f"Extracting QEMU from: {archive_path}")
        
        # Create directory
        self.qemu_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract based on file type
        if archive_path.suffix.lower() == '.zip':
            self._extract_zip(archive_path)
        elif archive_path.suffix.lower() in ['.7z', '.exe']:
            self._extract_with_7zip(archive_path)
        else:
            raise QemuExtractionError(f"Unsupported archive format: {archive_path.suffix}")
        
        # Verify extraction
        if not self.check_files_present():
            missing = [f for f in REQUIRED_QEMU_FILES 
                      if not (self.qemu_dir / f).exists()]
            raise QemuExtractionError(f"Extraction incomplete, missing files: {missing}")
        
        logger.info("QEMU extraction completed successfully")
    
    def _find_qemu_archive(self) -> Optional[Path]:
        """
        Find the best QEMU archive in tools directory.
        
        Returns:
            Path to archive or None if not found
        """
        if not TOOLS_DIR.exists():
            return None
        
        candidates = []
        
        for file_path in TOOLS_DIR.iterdir():
            if not file_path.is_file():
                continue
                
            name_lower = file_path.name.lower()
            if 'qemu' not in name_lower:
                continue
                
            suffix = file_path.suffix.lower()
            if suffix in ARCHIVE_PRIORITY:
                mtime = file_path.stat().st_mtime
                priority = ARCHIVE_PRIORITY[suffix]
                candidates.append((priority, -mtime, file_path))
        
        if not candidates:
            return None
        
        # Sort by priority, then by modification time (newest first)
        candidates.sort()
        return candidates[0][2]
    
    def _extract_zip(self, archive_path: Path) -> None:
        """Extract QEMU files from ZIP archive."""
        import zipfile
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                all_files = zf.namelist()
                
                for required_file in REQUIRED_QEMU_FILES:
                    # Find file in archive (case-insensitive, prefer shorter paths)
                    matches = [f for f in all_files 
                              if f.lower().endswith(required_file.lower())]
                    
                    if not matches:
                        continue
                    
                    # Prefer files in root over subdirectories
                    best_match = min(matches, key=lambda x: x.count('/'))
                    
                    # Extract to temporary location then move to final location
                    zf.extract(best_match, self.qemu_dir)
                    
                    extracted_path = self.qemu_dir / best_match
                    final_path = self.qemu_dir / required_file
                    
                    if extracted_path != final_path:
                        extracted_path.replace(final_path)
                        
                        # Clean up empty directories
                        try:
                            extracted_path.parent.rmdir()
                        except OSError:
                            pass
                            
        except Exception as e:
            raise QemuExtractionError(f"Failed to extract ZIP archive: {e}") from e
    
    def _extract_with_7zip(self, archive_path: Path) -> None:
        """Extract QEMU files using 7-Zip."""
        from .sevenzip_manager import SevenZipManager
        
        sevenzip = SevenZipManager()
        try:
            success = sevenzip.extract_files(
                str(archive_path), 
                str(self.qemu_dir), 
                REQUIRED_QEMU_FILES
            )
            if not success:
                raise QemuExtractionError("7-Zip extraction failed")
                
        except Exception as e:
            raise QemuExtractionError(f"Failed to extract with 7-Zip: {e}") from e
    
    def _check_system_qemu(self) -> bool:
        """Check if qemu-img is available in system PATH."""
        try:
            result = subprocess.run(
                ['qemu-img', '--version'], 
                capture_output=True, 
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _handle_dll_error(self) -> None:
        """Handle DLL missing error by re-extracting QEMU."""
        logger.warning("Attempting to fix DLL error by re-extracting QEMU")
        
        try:
            # List current files for debugging
            if self.qemu_dir.exists():
                current_files = [f.name for f in self.qemu_dir.iterdir() if f.is_file()]
                logger.debug(f"Current QEMU files: {current_files}")
            
            # Re-extract
            self._extract_qemu()
            
        except Exception as e:
            logger.error(f"Failed to fix DLL error: {e}")
            raise QemuError(
                f"QEMU failed with DLL error and recovery failed: {e}. "
                "Try providing a different QEMU build or check your antivirus software."
            ) from e
    
    def _run_command_with_progress(
        self, 
        command: List[str], 
        output_path: Path, 
        progress_callback: Callable[[int], None]
    ) -> Tuple[bool, Optional[str]]:
        """
        Run QEMU command with progress monitoring by tracking output file size.
        
        Args:
            command: QEMU command arguments
            output_path: Path to output file being created
            progress_callback: Function to call with progress updates (bytes written)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get source size to calculate progress percentage
            source_path = command[-2]  # Second to last argument is source
            source_size = 0
            
            try:
                if source_path.startswith('\\\\.\\PhysicalDrive'):
                    # For Windows physical drives, try to get size via WMI
                    import re
                    drive_match = re.search(r'PhysicalDrive(\d+)', source_path)
                    if drive_match:
                        drive_num = drive_match.group(1)
                        # Use PowerShell to get drive size
                        ps_cmd = [
                            "powershell", "-Command",
                            f"(Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq {drive_num}}}).Size"
                        ]
                        result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=10)
                        if result.returncode == 0 and result.stdout.strip():
                            source_size = int(result.stdout.strip())
                else:
                    # Regular file
                    source_size = os.path.getsize(source_path)
            except Exception as e:
                logger.warning(f"Could not determine source size: {e}")
                source_size = 0
            
            # Prepare command
            qemu_path = self.get_executable_path()
            full_command = [str(qemu_path)] + command
            
            # Start the QEMU process
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress in a separate thread
            progress_stop = threading.Event()
            
            def monitor_progress():
                last_size = 0
                while not progress_stop.is_set() and process.poll() is None:
                    try:
                        if output_path.exists():
                            current_size = output_path.stat().st_size
                            if current_size > last_size:
                                progress_callback(current_size)
                                last_size = current_size
                    except Exception:
                        pass
                    time.sleep(0.5)  # Check every 500ms
            
            progress_thread = threading.Thread(target=monitor_progress)
            progress_thread.start()
            
            try:
                # Wait for process completion
                stdout, stderr = process.communicate(timeout=3600)  # 1 hour timeout
                
                # Stop progress monitoring
                progress_stop.set()
                progress_thread.join(timeout=1)
                
                if process.returncode == 0:
                    # Send final progress update
                    if output_path.exists():
                        final_size = output_path.stat().st_size
                        progress_callback(final_size)
                    
                    logger.info("QEMU image creation completed successfully")
                    return True, None
                else:
                    error_msg = f"qemu-img failed (code {process.returncode}):\\n"
                    if stdout:
                        error_msg += f"STDOUT:\\n{stdout}\\n"
                    if stderr:
                        error_msg += f"STDERR:\\n{stderr}"
                    
                    logger.error(error_msg)
                    return False, error_msg
                    
            except subprocess.TimeoutExpired:
                process.kill()
                progress_stop.set()
                progress_thread.join(timeout=1)
                return False, "QEMU imaging process timed out"
                
        except Exception as e:
            logger.exception("Exception in QEMU image creation with progress")
            return False, str(e)
