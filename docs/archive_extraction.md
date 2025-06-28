# Archive Extraction with Python Libraries

This document explains the improved archive extraction system used in the DiskImage application.

## Overview

The `thirdparty_downloader.py` module now uses Python libraries for extracting QEMU and 7-Zip installers instead of running system-wide installations. This provides several benefits:

- **No Administrator Rights Required**: Extracts files instead of installing
- **No System Registry Changes**: Completely portable
- **Easy Cleanup**: All files contained in tools directory
- **Better Error Handling**: More robust extraction with multiple fallback methods

## Python Libraries Used

### 1. py7zr (Pure Python 7-Zip Library)
- **Installation**: `pip install py7zr>=0.20.0`
- **Purpose**: Extract 7-Zip, ZIP, and other archives natively in Python
- **Advantages**: No external dependencies, cross-platform

### 2. patoolib (Universal Archive Extractor)
- **Installation**: `pip install patoolib>=1.12.0`
- **Purpose**: Universal archive extraction supporting many formats
- **Advantages**: Handles various archive types automatically

## Extraction Process

The extraction process follows this hierarchy:

1. **py7zr extraction** (if available)
   - Pure Python implementation
   - Fast and reliable for 7z/zip files

2. **patoolib extraction** (if available)
   - Universal extractor
   - Handles various installer formats

3. **Subprocess fallback**
   - PowerShell Expand-Archive
   - Installer silent mode extraction
   - Multiple extraction flags

## Installation

### Quick Install
Run the provided installation script:
```bash
python install_dependencies.py
```

### Manual Install
```bash
pip install py7zr>=0.20.0 patoolib>=1.12.0
```

### Using requirements.txt
```bash
pip install -r requirements.txt
```

## Fallback Behavior

If the Python libraries are not available, the system automatically falls back to subprocess-based extraction methods:

- PowerShell `Expand-Archive` cmdlet
- Installer silent mode execution
- Various installer flags (`/VERYSILENT`, `/S`, `/SILENT`)

## Error Handling

The system provides comprehensive error handling:

- Multiple extraction methods are tried in sequence
- Detailed logging for debugging
- Graceful fallback to alternative methods
- Clean error messages for end users

## Benefits Over Previous Approach

### Old Approach (subprocess-only)
- Complex subprocess calls
- Platform-dependent
- Limited error handling
- Relied heavily on external tools

### New Approach (Python libraries + fallback)
- Pure Python implementation preferred
- Cross-platform compatibility
- Robust error handling
- Multiple fallback strategies
- Better logging and debugging

## Debugging

To check what extraction capabilities are available, the system logs this information:
```
Available extraction methods: py7zr (pure Python 7-Zip), patoolib (universal archive extractor), subprocess fallback (PowerShell, installer silent mode)
```

## File Structure

After extraction, files are organized as:
```
tools/
├── qemu/
│   ├── qemu-img.exe
│   ├── qemu-system-x86_64.exe
│   ├── *.dll files
│   └── share/
└── 7zip/
    ├── 7z.exe
    ├── 7z.dll
    └── other files
```

## Future Improvements

Potential enhancements:
- Add support for more archive formats
- Implement progress callbacks for large extractions
- Add verification checksums
- Support for incremental updates
