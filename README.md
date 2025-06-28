# DiskImage

A modern, cross-platform disk imaging tool with both GUI and CLI interfaces. Built with Python, PyQt6, and using QEMU and 7-Zip for robust disk image creation and management.

![CI/CD Status](https://github.com/3amson3902/diskimage/workflows/CI/CD%20Pipeline/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **🖥️ Dual Interface**: Both graphical (PyQt6) and command-line interfaces
- **🌍 Cross-platform**: Works on Windows, Linux, and macOS
- **📀 Multiple formats**: Support for IMG, VHD, VMDK, QCOW2, and ISO formats
- **🗜️ Compression**: Built-in compression support for supported formats
- **📦 Archiving**: Automatic archiving to ZIP or 7z formats
- **💾 Sparse imaging**: Efficient handling of empty disk space
- **📊 Progress tracking**: Real-time progress updates during imaging
- **🛡️ Robust error handling**: Comprehensive error reporting and recovery
- **🔒 Admin privilege management**: Automatic privilege checking
- **🧪 Type-safe**: Full type hints and mypy compatibility
- **✅ Well-tested**: Comprehensive test suite with pytest

## 🏗️ Project Structure

```
DiskImage/
├── backend/                    # Core backend modules (refactored)
│   ├── constants.py           # Application constants  
│   ├── exceptions.py          # Custom exception hierarchy
│   ├── config_utils.py        # Configuration management (dataclass-based)
│   ├── logging_utils.py       # Logging setup and utilities
│   ├── validation.py          # Input validation with type safety
│   ├── admin_utils.py         # Admin privilege utilities
│   ├── cleanup_utils.py       # Cleanup operations
│   ├── disk_list_utils.py     # Disk enumeration
│   ├── qemu_manager.py        # QEMU management (class-based)
│   ├── sevenzip_manager.py    # 7-Zip management (class-based)
│   ├── archive_manager.py     # Archive operations (class-based)
│   ├── imaging_worker.py      # Main imaging logic (class-based)
│   ├── app_entry.py          # Application entry point
│   └── __init__.py           # Clean imports
├── gui/                       # GUI components  
│   └── pyqt_app.py           # PyQt6 GUI application (updated)
├── cli/                       # CLI components (implemented)
│   └── main.py               # Full CLI with argparse
├── tests/                     # Comprehensive test suite
│   ├── test_backend.py       # Backend module tests
│   ├── test_cli.py           # CLI interface tests
│   └── test_gui.py           # GUI tests (PyQt6)
├── tools/                     # 3rd party tools (extracted)
├── .github/workflows/         # CI/CD pipeline
│   └── ci.yml               # GitHub Actions workflow
├── main.py                   # Application launcher (updated)
├── diskimage.py             # Direct CLI entry point
├── setup_dev.py             # Development setup script
├── requirements.txt          # Dependencies (updated)
├── pyproject.toml           # Modern Python project config
├── setup.cfg                # Tool configurations
├── .pre-commit-config.yaml  # Pre-commit hooks
└── README.md                # This file
```

## 🚀 Quick Start

### Installation

#### Prerequisites

- Python 3.9 or higher
- Windows: Administrator privileges for disk access
- Linux/macOS: Root privileges for direct disk access

#### Install from Source

```bash
git clone https://github.com/yourusername/diskimage.git
cd diskimage
pip install -r requirements.txt
```

#### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/diskimage.git
cd diskimage
python setup_dev.py
```

### Usage

#### GUI Mode (Default)

```bash
# Launch GUI
python main.py

# Or explicitly
python main.py --gui
```

#### CLI Mode

```bash
# Show help
python main.py --help

# List available disks
python main.py --list

# Create a basic disk image
python main.py --disk "\\.\PHYSICALDRIVE1" --output backup.img

# Create compressed QCOW2 image with archive
python main.py --disk "USB Drive" --output usb.qcow2 --format qcow2 --compress --archive --archive-type 7z

# Direct CLI access
python diskimage.py --help
```

#### Examples

```bash
# List all available disks
python main.py --list

# Image a USB drive to raw format
python main.py -d "\\.\PHYSICALDRIVE1" -o usb_backup.img

# Create compressed VMDK with verbose output  
python main.py -d "My USB Drive" -o backup.vmdk -f vmdk --compress --verbose

# Create image and archive it
python main.py -d "\\.\PHYSICALDRIVE0" -o system.raw --archive -a 7z

# Custom buffer size for better performance
python main.py -d "\\.\PHYSICALDRIVE1" -o large_disk.img --buffer-size 128
```
- Administrator/root privileges (for disk access)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DiskImage
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   - **Windows:** `.venv\\Scripts\\activate`
   - **Linux/macOS:** `source .venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download required tools:**
   - **QEMU**: Download QEMU Windows build from [QEMU Downloads](https://qemu.weilnetz.de/w64/) and place the installer/archive in the `tools/` directory
   - **7-Zip** (optional): Download 7-Zip from [7-zip.org](https://www.7-zip.org/) for enhanced archive support

## Usage

### GUI Application

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Select a disk** from the dropdown menu

3. **Choose output settings:**
   - Output file path and name
   - Image format (IMG, VHD, VMDK, QCOW2, ISO)
   - Enable sparse imaging for faster processing
   - Enable compression (if supported by format)
   - Optional archiving after imaging

4. **Start imaging** and monitor progress

### Configuration

The application saves settings to `config.json`:

```json
{
  "cleanup_tools": true,        // Clean up extracted tools on exit
  "last_output_dir": "",        // Remember last output directory
  "theme": "auto",              // UI theme
  "window_size": [1024, 768],   // Window dimensions
  "buffer_size_mb": 64          // Buffer size for operations
}
```

## Supported Formats

| Format | Extension | Sparse | Compression | Description |
|--------|-----------|--------|-------------|-------------|
| Raw    | .img      | No     | External    | Raw disk image |
| VHD    | .vhd      | Yes    | No          | Virtual Hard Disk |
| VMDK   | .vmdk     | Yes    | Yes         | VMware Virtual Disk |
| QCOW2  | .qcow2    | Yes    | Yes         | QEMU Copy-on-Write |
| ISO    | .iso      | No     | External    | ISO 9660 image |

## Architecture

The refactored codebase follows modern software engineering principles:

### Key Components

- **QemuManager**: Handles QEMU installation, extraction, and execution
- **SevenZipManager**: Manages 7-Zip operations for archive handling
- **ArchiveManager**: Provides unified archive creation interface
- **ImagingWorker**: Orchestrates the complete imaging workflow
- **AppConfig**: Type-safe configuration management
- **Validation**: Comprehensive input validation with custom exceptions

### Error Handling

The application uses a custom exception hierarchy:

```python
DiskImageError (base)
├── ConfigError
├── DiskOperationError  
├── QemuError
│   ├── QemuNotFoundError
│   └── QemuExtractionError
├── SevenZipError
├── ArchiveError
├── DiskListError
├── PermissionError
└── ValidationError
```

### Logging

Comprehensive logging with configurable levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Important notices
- **ERROR**: Error conditions
- **CRITICAL**: Serious errors requiring attention

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=backend
```

### Code Style

The project follows PEP 8 guidelines:

```bash
# Install linting tools
pip install flake8 mypy

# Run linting
flake8 backend/ gui/ tests/
mypy backend/
```

### Adding New Features

1. Create feature branch from main
2. Add appropriate tests in `tests/`
3. Implement feature with proper error handling
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues

**"Administrator privileges required"**
- Run the application as administrator on Windows
- Use `sudo` on Linux/macOS

**"QEMU not found"**
- Download QEMU Windows build and place in `tools/` directory
- On Linux/macOS, install QEMU via package manager

**"7-Zip not found"**
- Download 7-Zip and place `7z.exe` in `tools/7zip/` directory
- Or install 7-Zip system-wide

**"Disk not found" or "Permission denied"**
- Ensure disk is not in use by another process
- Check that the disk exists and is accessible
- Verify administrator privileges

### Debug Mode

Enable debug logging by modifying the logging level:

```python
# In main.py or app_entry.py
setup_logging(level=logging.DEBUG)
```

### Log Files

Check log files for detailed error information:
- `diskimager_main.log` - Main application log
- Console output for immediate feedback

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **QEMU** project for disk imaging capabilities
- **7-Zip** for archive support
- **PyQt6** for the GUI framework
- **psutil** for system information
