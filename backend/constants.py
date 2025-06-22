"""
Constants and configuration values for DiskImage application.
"""
from pathlib import Path
from typing import List

# File sizes
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024
DEFAULT_BUFFER_SIZE = 64 * BYTES_PER_MB

# Windows error codes
WINDOWS_DLL_NOT_FOUND = 3221225781

# Required QEMU files for Windows
REQUIRED_QEMU_FILES: List[str] = [
    'qemu-img.exe',
    'libwinpthread-1.dll',
    'libgcc_s_seh-1.dll',
    'libstdc++-6.dll',
    'libglib-2.0-0.dll',
    'libiconv-2.dll',
    'libintl-8.dll',
]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
QEMU_DIR = TOOLS_DIR / "qemu"
SEVENZIP_DIR = TOOLS_DIR / "7zip"
CONFIG_FILE = PROJECT_ROOT / "config.json"
LOG_FILE = PROJECT_ROOT / "diskimager_main.log"

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    "Raw (.img)": "img",
    "VHD (.vhd)": "vhd", 
    "VMDK (.vmdk)": "vmdk",
    "QCOW2 (.qcow2)": "qcow2",
    "ISO (.iso)": "iso"
}

# Archive formats
SUPPORTED_ARCHIVE_FORMATS = ["zip", "7z"]

# Sparse image formats (formats that support compression)
SPARSE_FORMATS = {"qcow2", "vhd", "vmdk"}
COMPRESSIBLE_FORMATS = {"qcow2", "vmdk"}

# Default configuration
DEFAULT_CONFIG = {
    "cleanup_tools": True,
    "last_output_dir": "",
    "theme": "auto",
    "window_size": [1024, 768],
    "buffer_size_mb": 64
}

# Archive preferences (.zip > .7z > .exe for QEMU)
ARCHIVE_PRIORITY = {'.zip': 0, '.7z': 1, '.exe': 2}
