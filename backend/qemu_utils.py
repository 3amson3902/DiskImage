"""
qemu_utils.py - QEMU binary management and subprocess utilities for the disk imaging app.

*** DEPRECATED ***
This module is deprecated and will be removed in a future version.
Use backend.qemu_manager.QemuManager instead.

Handles finding qemu-img, just-in-time extraction, and subprocess execution with cleanup.
LLM prompt: This module manages QEMU dependencies and subprocess calls for disk image conversion.
"""
import warnings
warnings.warn(
    "qemu_utils module is deprecated. Use backend.qemu_manager.QemuManager instead.",
    DeprecationWarning,
    stacklevel=2
)

import os
import shutil
import zipfile
import subprocess
import logging
import platform
from backend.sevenzip_utils import find_7z_exe, extract_with_7zip

REQUIRED_QEMU_FILES = [
    'qemu-img.exe',
    'libwinpthread-1.dll',
    'libgcc_s_seh-1.dll',
    'libstdc++-6.dll',
    'libglib-2.0-0.dll',
    'libiconv-2.dll',
    'libintl-8.dll',
]

QEMU_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
QEMU_IMG_PATH = os.path.abspath(os.path.join(QEMU_DIR, 'qemu-img.exe'))

def list_qemu_dir_files():
    """Return a list of files in tools/qemu/ for debugging missing DLLs."""
    if not os.path.exists(QEMU_DIR):
        return []
    return os.listdir(QEMU_DIR)

def _cleanup_qemu_dir(dest_dir):
    """Remove any non-QEMU files from dest_dir."""
    for fname in os.listdir(dest_dir):
        if fname.lower() not in [f.lower() for f in REQUIRED_QEMU_FILES]:
            try:
                os.remove(os.path.join(dest_dir, fname))
            except Exception:
                pass

def _finalize_extraction(dest_dir):
    """Return list of required files present and missing after extraction."""
    extracted = [os.path.join(dest_dir, f) for f in REQUIRED_QEMU_FILES if os.path.exists(os.path.join(dest_dir, f))]
    missing = [f for f in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(dest_dir, f))]
    return extracted, missing

def extract_qemu_deps(archive_path, dest_dir=None):
    """
    Extract only the necessary files for qemu-img.exe from a QEMU Windows zip archive into the tools/qemu/ directory.
    Returns a list of extracted files (absolute paths).
    """
    if dest_dir is None:
        dest_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    extracted = []
    with zipfile.ZipFile(archive_path, 'r') as zf:
        all_files = zf.namelist()
        for req in REQUIRED_QEMU_FILES:
            # Find the shortest path that ends with the required file (prefer root, then subdirs)
            matches = sorted([f for f in all_files if f.lower().endswith(req.lower())], key=lambda x: x.count('/'))
            if matches:
                member = matches[0]
                zf.extract(member, dest_dir)
                src_path = os.path.join(dest_dir, member)
                dst_path = os.path.join(dest_dir, req)
                if src_path != dst_path:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.move(src_path, dst_path)
                extracted.append(dst_path)
                # Remove empty dirs if any
                parent = os.path.dirname(src_path)
                if parent and os.path.exists(parent) and parent != dest_dir:
                    try:
                        os.rmdir(parent)
                    except Exception:
                        pass
    _cleanup_qemu_dir(dest_dir)
    return extracted

def extract_with_7z_and_finalize(qemu_archive, dest_dir, ext):
    ok, err = extract_with_7zip(qemu_archive, dest_dir, only_files=REQUIRED_QEMU_FILES)
    if ok:
        _cleanup_qemu_dir(dest_dir)
        extracted, missing_after = _finalize_extraction(dest_dir)
        if not missing_after:
            return True, extracted
        else:
            raise RuntimeError(f'QEMU extraction from {ext} failed, missing: {missing_after}')
    else:
        raise RuntimeError(f'QEMU extraction from {ext} failed using 7-Zip: {err}')

def find_qemu_archive():
    """
    Find the best QEMU archive (.zip, .7z, or .exe) in the tools/ directory.
    Preference: .zip > .7z > .exe, and filename must contain 'qemu'.
    If multiple, pick the most recently modified.
    """
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    candidates = []
    for fname in os.listdir(tools_dir):
        lower = fname.lower()
        if (lower.endswith('.zip') or lower.endswith('.7z') or lower.endswith('.exe')) and 'qemu' in lower:
            fpath = os.path.join(tools_dir, fname)
            mtime = os.path.getmtime(fpath)
            candidates.append((lower, mtime, fpath))
    if not candidates:
        return None
    # Sort by extension priority, then by mtime (descending)
    ext_priority = {'.zip': 0, '.7z': 1, '.exe': 2}
    def sort_key(item):
        fname, mtime, _ = item
        ext = os.path.splitext(fname)[1]
        return (ext_priority.get(ext, 99), -mtime)
    candidates.sort(key=sort_key)
    return candidates[0][2]

def check_qemu_files():
    """
    Check if all required QEMU files are present in tools/qemu/.
    Returns True if all present, else False.
    """
    return all(os.path.exists(os.path.join(QEMU_DIR, f)) for f in REQUIRED_QEMU_FILES)

def extract_qemu():
    """
    Extract QEMU files from an archive if missing. Raises on failure.
    Returns (cleanup_needed, extracted_files).
    """
    if not os.path.exists(QEMU_DIR):
        os.makedirs(QEMU_DIR)
    qemu_archive = find_qemu_archive()
    if not qemu_archive:
        raise FileNotFoundError('Required QEMU files missing and no QEMU archive found in tools/.')
    ext = os.path.splitext(qemu_archive)[1].lower()
    if ext == '.zip':
        extracted = extract_qemu_deps(qemu_archive, QEMU_DIR)
        _, missing_after = _finalize_extraction(QEMU_DIR)
        if not missing_after:
            return True, extracted
        else:
            raise RuntimeError(f'QEMU extraction from zip failed, missing: {missing_after}')
    elif ext in ['.7z', '.exe']:
        try:
            return extract_with_7z_and_finalize(qemu_archive, QEMU_DIR, ext)
        except RuntimeError as e:
            if ext == '.exe':
                raise RuntimeError(
                    'QEMU .exe installer could not be extracted using 7-Zip. This is likely a standard installer, not a self-extracting archive. Please provide a .zip or .7z QEMU archive in the tools/ directory.'
                ) from e
            else:
                raise
    else:
        raise RuntimeError(f'Unsupported QEMU archive type: {ext}')

def init_qemu():
    """
    Ensure qemu-img.exe and required DLLs are present in tools/qemu/.
    If not, extract them from a QEMU archive or .exe installer in tools/.
    Always use 7-Zip to extract .exe QEMU installers (never run them).
    Returns (cleanup_needed, extracted_files) if extraction was needed, else (False, []).

    Refactored to be the main entry point for QEMU initialization.
    """
    if check_qemu_files():
        return False, []
    return extract_qemu()

def find_qemu_img():
    """
    Return the absolute path to qemu-img (cross-platform):
    - On Windows, use tools/qemu/qemu-img.exe and extract from ZIP if needed.
    - On Linux/macOS, use system qemu-img from PATH.
    """
    if platform.system() == "Windows":
        init_qemu()
        if not os.path.exists(QEMU_IMG_PATH):
            raise FileNotFoundError(f"qemu-img.exe not found in {QEMU_DIR}")
        return QEMU_IMG_PATH
    else:
        # On Linux/macOS, just use system qemu-img
        return 'qemu-img'

def run_qemu_wincmd(cmd, cleanup_tools=False, **kwargs):
    """
    Run a qemu-img command, using the persistent tools/qemu directory for dependencies.
    Returns the subprocess.CompletedProcess result.
    """
    # Use ./tools/qemu as the working directory for QEMU files
    if cmd[0].endswith('qemu-img.exe'):
        cmd[0] = QEMU_IMG_PATH
    kwargs.setdefault('cwd', QEMU_DIR)
    result = subprocess.run(cmd, **kwargs)
    return result

def run_qemu_win(device_path, output_path, image_format, compress):
    """
    Run qemu-img convert for disk imaging on Windows. Handles all command construction and execution.
    Returns (True, None) on success, (False, error) on failure.
    Retries once if error code 3221225781 (missing DLL) is encountered.
    """
    logging.info(f'Creating disk image: device_path={device_path}, output_path={output_path}, image_format={image_format}, compress={compress}')
    # Ensure qemu-img is present
    init_qemu()
    
    out_fmt = 'raw' if image_format in ['img', 'iso'] else image_format
    cmd = [QEMU_IMG_PATH, 'convert', '-p', '-O', out_fmt, '-S', '4096']

    if compress and out_fmt in ['qcow2', 'vmdk']:
        cmd.append('-c')
    cmd += [device_path, output_path]
    logging.info(f'Running: {cmd}')
    result = run_qemu_wincmd(cmd, cwd=QEMU_DIR, capture_output=True, text=True)
    if result.returncode == 3221225781:
        # Missing DLL or dependency, try re-extracting and retry once
        missing_dlls = [dll for dll in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(QEMU_DIR, dll))]
        if missing_dlls:
            logging.error(f"qemu-img.exe failed to start. Missing DLLs: {missing_dlls}")
        else:
            logging.error("qemu-img.exe failed with error 3221225781, but all DLLs appear present.")
        logging.warning('qemu-img.exe failed with error 3221225781 (missing DLL). Retrying extraction and running again.')
        try:
            init_qemu()  # Re-extract QEMU files if needed
        except Exception as e:
            logging.error(f'QEMU re-extraction failed: {e}')
            return False, f"QEMU re-extraction failed: {e}\nCheck that all required DLLs are present in tools/qemu/."
        result = run_qemu_wincmd(cmd, cwd=QEMU_DIR, capture_output=True, text=True)
        if result.returncode == 3221225781:
            # Still failing, provide user-friendly error
            qemu_files = list_qemu_dir_files()
            missing_dlls = [dll for dll in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(QEMU_DIR, dll))]
            logging.error(f"qemu-img.exe failed again with error 3221225781. DLLs in tools/qemu/: {qemu_files}. Still missing: {missing_dlls}")
            return False, (
                "qemu-img.exe failed to start due to missing DLLs (error 3221225781).\n"
                "Check that all required DLLs are present in tools/qemu/.\n"
                f"Files in tools/qemu/: {qemu_files}\n"
                f"Missing DLLs: {missing_dlls}\n"
                "Try re-extracting your QEMU archive or provide a different QEMU build."
            )
    if result.returncode != 0:
        logging.error(f"qemu-img failed: returncode={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return False, f"qemu-img failed (code {result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    logging.info('Disk image creation (QEMU, Windows physical) finished successfully')
    return True, None


