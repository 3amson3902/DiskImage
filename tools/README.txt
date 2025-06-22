Place all required 3rd party tools for this project in this folder.

For example:
- qemu-img.exe (required for VHD/VMDK/QCOW2 image conversion and sparse imaging)
- Any other external utilities needed by the backend

This keeps the project portable and avoids polluting the system PATH or .venv.

To install or update qemu-img.exe (Windows):
1. Go to https://qemu.weilnetz.de/w64/ or the official QEMU site.
2. Download the latest archive (e.g., qemu-w64-setup-*.zip or .exe).
3. Extract the archive. Inside, find qemu-img.exe (usually in the root or bin/ folder).
4. Copy only qemu-img.exe into this tools directory (do not copy the whole QEMU package).

The backend will automatically use the tool from this folder if present.
