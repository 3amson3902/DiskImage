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
            matches = [f for f in all_files if f.lower().endswith(req.lower())]
            if matches:
                zf.extract(matches[0], dest_dir)
                src_path = os.path.join(dest_dir, matches[0])
                dst_path = os.path.join(dest_dir, req)
                if src_path != dst_path:
                    shutil.move(src_path, dst_path)
                extracted.append(dst_path)
                # Remove empty dirs
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
    Find a QEMU archive (.zip, .7z, or .exe) in the tools/ directory.
    """
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    for fname in os.listdir(tools_dir):
        if fname.lower().endswith(('.zip', '.7z', '.exe')):
            return os.path.join(tools_dir, fname)
    return None

def ensure_qemu_present():
    """
    Ensure qemu-img.exe and required DLLs are present in tools/qemu/. If not, extract them from a QEMU archive or .exe installer in tools/.
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
            raise RuntimeError(f'QEMU extraction from .7z failed: {err}')
    elif ext == '.exe':
        # Try to extract with 7zip, but warn if not possible
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
                    'QEMU .exe installer could not be extracted. This is a standard installer, not a self-extracting archive. Please run the installer manually, or provide a .zip or .7z QEMU archive in the tools/ directory.'
                )
        else:
            raise RuntimeError(
                'QEMU .exe installer could not be extracted with 7-Zip. This is likely a standard installer, not a self-extracting archive. Please run the installer manually, or provide a .zip or .7z QEMU archive in the tools/ directory.'
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
            ensure_qemu_present()
        if not os.path.exists(qemu_path):
            raise FileNotFoundError(f"qemu-img.exe not found in {tools_dir}")
        return qemu_path
    else:
        # On Linux/macOS, just use system qemu-img
        return 'qemu-img'

def run_qemu_subprocess(cmd, cleanup_tools=False, **kwargs):
    """
    Run a qemu-img command, extracting dependencies just-in-time and cleaning up after if needed.
    Deletes all QEMU files in tools/qemu/ after use if cleanup_tools is True.
    Returns the subprocess.CompletedProcess result.
    """
    cleanup_needed, extracted_files = ensure_qemu_present()
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    try:
        result = subprocess.run(cmd, **kwargs)
    finally:
        if cleanup_tools:
            for fname in os.listdir(tools_dir):
                fpath = os.path.join(tools_dir, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                except Exception:
                    pass
    return result

def create_disk_image_sparse(disk_info, output_path, image_format='qcow2', compress=False, cleanup_tools=False):
    """
    Use qemu-img to create a sparse image directly from the physical disk.
    If compress=True, use qemu-img's -c option for supported formats (qcow2, vmdk).
    For raw (.img) and iso, use qemu-img to create a sparse raw image.
    Returns (True, None) on success, (False, error) on failure.
    """
    device_path = disk_info['device_id']
    qemu_img = find_qemu_img()
    # Map 'img' and 'iso' to 'raw' for qemu-img
    if image_format in ['img', 'iso']:
        out_fmt = 'raw'
    else:
        out_fmt = image_format
    try:
        cmd = [qemu_img, 'convert', '-O', out_fmt, '-S', '4096']
        if compress and out_fmt in ['qcow2', 'vmdk']:
            cmd.append('-c')
        cmd += [device_path, output_path]
        logging.info(f'Running: {cmd}')
        result = run_qemu_subprocess(cmd, capture_output=True, text=True, cleanup_tools=cleanup_tools)
        if result.returncode != 0:
            logging.error(f"qemu-img failed: returncode={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
            return False, f"qemu-img failed (code {result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        return True, None
    except Exception as e:
        logging.exception('Exception in create_disk_image_sparse')
        return False, str(e)
