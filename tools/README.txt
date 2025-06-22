Place all required 3rd party tools for this project in this folder.

For example:
- qemu-img.exe (required for VHD/VMDK/QCOW2 image conversion and sparse imaging)
- Any other external utilities needed by the backend

This keeps the project portable and avoids polluting the system PATH or .venv.

To update qemu-img.exe:
1. Download the latest Windows build from https://qemu.weilnetz.de/w64/ or the official QEMU site.
2. Copy qemu-img.exe into this tools directory.

The backend will automatically use the tool from this folder if present.
