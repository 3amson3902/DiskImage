# C++ Disk Imaging Tool for Windows

This project is a high-performance disk imaging tool written in C++ for Windows. It supports:
- Sector-by-sector disk imaging (raw, vhd, vmdk, qcow2)
- Optional compression (gzip for raw, qemu-img for others)
- Format conversion (raw <-> vhd/vmdk/qcow2 using qemu-img)
- Console progress bar
- Sparse file support (skip zero blocks)
- Large buffer for speed
- Logging to file
- CMake build system

## Building

1. Install [CMake](https://cmake.org/download/) and a C++17-compatible compiler (e.g., MSVC).
2. Open a Developer Command Prompt for VS or use CMake Tools in VS Code.
3. Run:
   ```powershell
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```

## Usage

Run as Administrator:
```powershell
disk_imager.exe <source_disk> <output_image> [--format raw|vhd|vmdk|qcow2] [--compress] [--progress] [--sparse]
```

- `<source_disk>`: e.g., `\\.\PhysicalDrive1`
- `<output_image>`: e.g., `backup.img`
- `--format`: Output format (default: raw)
- `--compress`: Enable compression (gzip for raw, qemu-img for others)
- `--progress`: Show progress bar
- `--sparse`: Skip zero blocks for sparse output

## Requirements
- Windows 10/11
- Run as Administrator for raw disk access
- [qemu-img](https://qemu.weilnetz.de/w64/) in PATH for format conversion
- [7-Zip](https://www.7-zip.org/) in PATH for 7z compression (optional)

## Next Steps
- Add Qt GUI skeleton (cross-platform ready)
- CMake: Add Qt5/6 option, add new sources
- README: Update with new build and GUI info

## License
MIT
