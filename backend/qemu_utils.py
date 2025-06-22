"""
qemu_utils.py - QEMU binary management and subprocess utilities for the disk imaging app.

Handles finding qemu-img, just-in-time extraction, and subprocess execution with cleanup.
LLM prompt: This module manages QEMU dependencies and subprocess calls for disk image conversion.
"""
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

def list_qemu_dir_files():
    """Return a list of files in tools/qemu/ for debugging missing DLLs."""
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    if not os.path.exists(tools_dir):
        return []
    return os.listdir(tools_dir)

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
    # Remove any non-QEMU files from dest_dir
    for fname in os.listdir(dest_dir):
        if fname.lower() not in [f.lower() for f in REQUIRED_QEMU_FILES]:
            try:
                os.remove(os.path.join(dest_dir, fname))
            except Exception:
                pass
    return extracted

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
    # Sort by extension preference, then by mtime (descending)
    ext_priority = {'.zip': 0, '.7z': 1, '.exe': 2}
    def sort_key(item):
        fname, mtime, _ = item
        ext = os.path.splitext(fname)[1]
        return (ext_priority.get(ext, 99), -mtime)
    candidates.sort(key=sort_key)
    return candidates[0][2]

def init_qemu():
    """
    Ensure qemu-img.exe and required DLLs are present in tools/qemu/.
    If not, extract them from a QEMU archive or .exe installer in tools/.
    Always use 7-Zip to extract .exe QEMU installers (never run them).
    Returns (cleanup_needed, extracted_files).
    """
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)
    missing = [f for f in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(tools_dir, f))]
    if not missing:
        return False, []
    qemu_archive = find_qemu_archive()
    if not qemu_archive:
        raise FileNotFoundError('Required QEMU files missing and no QEMU archive found in tools/.')
    ext = os.path.splitext(qemu_archive)[1].lower()
    if ext == '.zip':
        # Use custom zip extraction for .zip
        extracted = extract_qemu_deps(qemu_archive, tools_dir)
        missing_after = [f for f in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(tools_dir, f))]
        if not missing_after:
            return True, extracted
        else:
            raise RuntimeError(f'QEMU extraction from zip failed, missing: {missing_after}')
    elif ext == '.7z':
        # Use 7zip extraction for .7z
        ext_preference = [find_7z_exe]
        ok, err = extract_with_7zip(qemu_archive, tools_dir, ext_preference)
        if ok:
            for fname in os.listdir(tools_dir):
                if fname.lower() not in [f.lower() for f in REQUIRED_QEMU_FILES]:
                    try:
                        os.remove(os.path.join(tools_dir, fname))
                    except Exception:
                        pass
            extracted = [os.path.join(tools_dir, f) for f in REQUIRED_QEMU_FILES if os.path.exists(os.path.join(tools_dir, f))]
            missing_after = [f for f in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(tools_dir, f))]
            if not missing_after:
                return True, extracted
            else:
                raise RuntimeError(f'QEMU extraction from 7z failed, missing: {missing_after}')
        else:
            raise RuntimeError(f'QEMU extraction from .7z failed using 7-Zip: {err}')
    elif ext == '.exe':
        # Always use 7-Zip to extract .exe QEMU installers (never run them)
        ext_preference = [find_7z_exe]
        ok, err = extract_with_7zip(qemu_archive, tools_dir, ext_preference)
        if ok:
            for fname in os.listdir(tools_dir):
                if fname.lower() not in [f.lower() for f in REQUIRED_QEMU_FILES]:
                    try:
                        os.remove(os.path.join(tools_dir, fname))
                    except Exception:
                        pass
            extracted = [os.path.join(tools_dir, f) for f in REQUIRED_QEMU_FILES if os.path.exists(os.path.join(tools_dir, f))]
            missing_after = [f for f in REQUIRED_QEMU_FILES if not os.path.exists(os.path.join(tools_dir, f))]
            if not missing_after:
                return True, extracted
            else:
                raise RuntimeError(
                    'QEMU .exe installer could not be extracted using 7-Zip. This is a standard installer, not a self-extracting archive. Please provide a .zip or .7z QEMU archive in the tools/ directory.'
                )
        else:
            raise RuntimeError(
                'QEMU .exe installer could not be extracted using 7-Zip. This is likely a standard installer, not a self-extracting archive. Please provide a .zip or .7z QEMU archive in the tools/ directory.'
            )
    else:
        raise RuntimeError(f'Unsupported QEMU archive type: {ext}')

def find_qemu_img():
    """
    Return the absolute path to qemu-img (cross-platform):
    - On Windows, use tools/qemu/qemu-img.exe and extract from ZIP if needed.
    - On Linux/macOS, use system qemu-img from PATH.
    """
    if platform.system() == "Windows":
        tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
        qemu_path = os.path.abspath(os.path.join(tools_dir, 'qemu-img.exe'))
        if not os.path.exists(qemu_path):
            init_qemu()
        if not os.path.exists(qemu_path):
            raise FileNotFoundError(f"qemu-img.exe not found in {tools_dir}")
        return qemu_path
    else:
        # On Linux/macOS, just use system qemu-img
        return 'qemu-img'

def run_qemu_wincmd(cmd, cleanup_tools=False, **kwargs):
    """
    Run a qemu-img command, using the persistent tools/qemu directory for dependencies.
    Returns the subprocess.CompletedProcess result.
    """
    # Use ./tools/qemu as the working directory for QEMU files
    qemu_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    if cmd[0].endswith('qemu-img.exe'):
        cmd[0] = os.path.join(qemu_dir, 'qemu-img.exe')
    kwargs.setdefault('cwd', qemu_dir)
    result = subprocess.run(cmd, **kwargs)
    return result

def run_qemu_win(device_path, output_path, image_format, compress):
    """
    Run qemu-img convert for disk imaging on Windows. Handles all command construction and execution.
    Returns (True, None) on success, (False, error) on failure.
    """
    logging.info(f'Creating disk image: device_path={device_path}, output_path={output_path}, image_format={image_format}, compress={compress}')
    # Ensure qemu-img is present
    init_qemu()
    
    qemu_img = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu', 'qemu-img.exe')
    out_fmt = 'raw' if image_format in ['img', 'iso'] else image_format
    cmd = [qemu_img, 'convert', '-p', '-O', out_fmt, '-S', '4096']

    if compress and out_fmt in ['qcow2', 'vmdk']:
        cmd.append('-c')
    cmd += [device_path, output_path]
    logging.info(f'Running: {cmd}')
    result = run_qemu_wincmd(cmd, cwd=os.path.dirname(qemu_img), capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"qemu-img failed: returncode={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return False, f"qemu-img failed (code {result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    logging.info('Disk image creation (QEMU, Windows physical) finished successfully')
    return True, None


