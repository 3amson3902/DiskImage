# DiskImage

A cross-platform, portable disk imaging tool with GUI and CLI, using QEMU and 7-Zip for robust disk image creation and management.

## Project Structure

```
DiskImage/
│
├── backend/
│   ├── __init__.py
│   ├── disk_ops.py
│   ├── qemu_utils.py
│   ├── archive_utils.py
│   ├── logging_utils.py
│   └── sevenzip_utils.py
│
├── gui/
│   ├── __init__.py
│   └── app.py         # GUI application and entry point
│
├── cli/
│   ├── __init__.py
│   └── main.py        # CLI entry point (future)
│
├── tools/
│   └── ...            # QEMU, 7z.exe, installer, etc.
│
├── tests/
│   └── ...            # (unit tests)
│
├── main.py            # Top-level entry point, dispatches to GUI or CLI
├── requirements.txt
├── LICENSE
└── README.md
```

## Setup Instructions

### 1. Python Environment
- Install Python 3.8+ (recommended: use a virtual environment)
- Create a virtual environment:
  ```
  python -m venv .venv
  ```
- Activate the virtual environment:
  - Windows: `.venv\Scripts\activate`
  - Linux/macOS: `source .venv/bin/activate`
- Install required Python packages:
  ```
  pip install -r requirements.txt
  ```

### 2. 3rd Party Tools
- Download qemu-img.exe (for Windows) from https://qemu.weilnetz.de/w64/ or the official QEMU site.
- Place qemu-img.exe in the `tools/` directory at the project root (create the folder if it does not exist).
- (Optional) Download 7-Zip (for .7z archiving) and ensure 7z.exe is in your system PATH or tools/.

### 3. Running the Program
- Activate your virtual environment (see above).
- Run the program:
  ```
  python main.py
  ```
- The GUI will launch. You can image disks, convert formats, and archive images.

### 4. Notes
- All disk images and archives are ignored by git (see .gitignore).
- The tools/ directory is for 3rd party binaries and is also ignored by git.
- Run as administrator for full disk access on Windows.

### 5. Troubleshooting & Advanced Usage
- If imaging fails, check the error message shown in the GUI and in the log files (`diskimager_backend.log`, `diskimager_main.log`).
- The app now displays and logs both the standard output and error output from `qemu-img.exe` if a failure occurs. This helps diagnose issues such as:
    - `qemu-img.exe` not found: Ensure it is present in the `tools/` directory or in your system PATH.
    - Permission denied: Run the app as administrator for full disk access.
    - Disk in use: Make sure the disk is not being used by another process.
    - Invalid parameters: Double-check the selected disk and output path.
- For more details, open the log files in a text editor and look for lines containing `qemu-img failed` or `Imaging failed`.
- To enable more verbose logging, edit the `logging.basicConfig` line in `main.py` or `backend.py` and set `level=logging.DEBUG` (already set by default).
- Advanced users:
    - You can manually run the `qemu-img` command shown in the logs to test or debug outside the app.
    - You may add custom qemu-img options by editing the backend code if needed.
    - The app supports archiving images as `.zip` or `.7z` after imaging. Ensure 7-Zip is installed and in PATH for `.7z` support.

If you encounter persistent issues, please provide the relevant log excerpts when seeking help.

For more help, see README.txt in the tools/ directory or contact the project maintainer.

---

## QEMU & 7-Zip Extraction Logic (Windows)

To use QEMU-based imaging features, the app needs `qemu-img.exe` and its DLLs. The app will look for these in the following order:

1. If all required QEMU binaries are present in `tools/`, they are used directly.
2. If a QEMU `.zip` or `.7z` archive is found in `tools/`, the app will extract only the needed files.
3. If a QEMU Windows `.exe` installer is found in `tools/`, the app will try to extract the needed files using:
   - `7z.exe` (portable, if present in `tools/`)
   - System `7z` (if available in PATH)

**Recommended:**
- Download the QEMU Windows installer `.exe` or a `.zip` archive.
- Place it in the `tools/` directory.
- Download the portable `7z.exe` from https://www.7-zip.org/download.html and place it in `tools/` as well.
- The app will extract the required files automatically.

If none of these are available, you will see an error about missing QEMU files.

---

## Linux/macOS

- The app will use the system `qemu-img` from your PATH. Make sure QEMU is installed (e.g., via your package manager).
- No extraction or `tools/` setup is needed on Linux/macOS.

---

## Advanced: Custom QEMU Path

If you want to use a custom QEMU binary, place it and its DLLs in `tools/` or ensure it is in your system PATH.

---

## Troubleshooting

- If extraction fails, ensure `7z.exe` is present in `tools/`, or that 7-Zip is installed and available in your PATH.
- If you see a FileNotFoundError for QEMU, check that a QEMU archive or installer is present in `tools/`.
- For cross-platform use, always check the latest instructions in this file.
