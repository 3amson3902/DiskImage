"""
disk_ops.py - Disk imaging and cloning operations for the portable disk imaging app.

Contains functions for creating disk images, cloning disks, and buffer size logic.
LLM prompt: This module provides robust, low-level disk operations for physical and image disks.
"""
import logging
import platform
import tempfile
from backend.sevenzip_utils import extract_with_7zip
from backend.qemu_utils import REQUIRED_QEMU_FILES

BUFFER_SIZE = 64 * 1024 * 1024  # 64MB

def get_max_buffer_size():
    """Return the fixed buffer size for disk operations (64MB)."""
    return BUFFER_SIZE

def create_disk_clone(src_disk_info, dst_disk_info, progress_callback=None, buffer_size=None):
    """
    Clone the entire source physical drive to the destination physical drive.
    This is a sector-by-sector copy. Both src_disk_info and dst_disk_info must be dicts from list_disks().
    WARNING: This will overwrite all data on the destination disk.
    Returns (True, None) on success, (False, error) on failure.
    """
    src_path = src_disk_info['device_id']
    dst_path = dst_disk_info['device_id']
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE
    try:
        with open(src_path, 'rb', buffering=0) as src, open(dst_path, 'wb', buffering=0) as dst:
            while True:
                chunk = src.read(bs)
                if not chunk:
                    break
                dst.write(chunk)
                if progress_callback:
                    progress_callback(len(chunk))
        return True, None
    except Exception as e:
        return False, str(e)

def create_disk_image(disk_info, output_path, progress_callback=None, image_format='img', compress=False, buffer_size=None, cleanup_tools=False):
    """
    Create a disk image in the specified format, with optional compression.
    On Windows, always use QEMU for physical disk imaging (\\.\PhysicalDriveX), not Python file I/O.
    Returns (True, None) on success, (False, error) on failure.
    """
    import os
    import logging
    import shutil
    device_path = disk_info['device_id']
    # Robust Windows physical drive detection
    is_windows = platform.system() == "Windows"
    norm_path = device_path.replace('/', '\\').lower()
    is_physical = is_windows and norm_path.startswith('\\.\\physicaldrive')

    if is_windows and is_physical:
        # Use QEMU, but optimize extraction for .7z/.exe
        from backend.qemu_utils import find_qemu_archive
        qemu_archive = find_qemu_archive()
        ext = os.path.splitext(qemu_archive)[1].lower() if qemu_archive else None
        if ext in ('.7z', '.exe') and qemu_archive:
            with tempfile.TemporaryDirectory() as temp_qemu_dir:
                ok, err = extract_with_7zip(qemu_archive, temp_qemu_dir, only_files=REQUIRED_QEMU_FILES)
                if not ok:
                    return False, f"QEMU extraction failed: {err}"
                from backend.qemu_utils import find_qemu_img, run_qemu_subprocess
                qemu_img = os.path.join(temp_qemu_dir, 'qemu-img.exe')
                # Map 'img' and 'iso' to 'raw' for qemu-img
                out_fmt = 'raw' if image_format in ['img', 'iso'] else image_format
                cmd = [qemu_img, 'convert', '-O', out_fmt, '-S', '4096']
                if compress and out_fmt in ['qcow2', 'vmdk']:
                    cmd.append('-c')
                cmd += [device_path, output_path]
                logging.info(f'Running: {cmd}')
                result = run_qemu_subprocess(cmd, cwd=temp_qemu_dir, capture_output=True, text=True)
                if result.returncode != 0:
                    logging.error(f"qemu-img failed: returncode={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
                    return False, f"qemu-img failed (code {result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                logging.info('Disk image creation (QEMU, Windows physical, .7z/.exe) finished successfully')
                return True, None
        # Fallback to default QEMU logic for .zip or if above fails
        from backend.qemu_utils import create_disk_image_sparse
        result = create_disk_image_sparse(disk_info, output_path, image_format, compress=compress, cleanup_tools=cleanup_tools)
        if not result[0]:
            return False, result[1]
        logging.info('Disk image creation (QEMU, Windows physical) finished successfully')
        return True, None

    # For non-Windows or non-physical disks, use Python open()
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE
    bytes_read = 0
    raw_path = output_path
    # If not raw or iso, create a temp raw file first
    if image_format not in ('img', 'iso'):
        raw_path = output_path + '.tmp.raw'
    try:
        with open(device_path, 'rb') as disk_file, open(raw_path, 'wb') as image_file:
            logging.debug('Disk image creation started')
            while True:
                chunk = disk_file.read(bs)
                if not chunk:
                    break
                # Efficient: skip writing all-zero blocks (sparse file)
                if chunk.count(0) == len(chunk):
                    image_file.seek(len(chunk), 1)  # Seek forward, don't write
                else:
                    image_file.write(chunk)
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read)
        # Convert to requested format if needed
        if image_format not in ('img', 'iso'):
            from backend.qemu_utils import create_disk_image_sparse
            # Use qemu-img to convert
            result = create_disk_image_sparse(disk_info, output_path, image_format, compress=compress, cleanup_tools=cleanup_tools)
            os.remove(raw_path)
            if not result[0]:
                return False, result[1]
        elif compress:
            # Compress raw image with gzip
            try:
                import gzip
                gz_path = output_path + '.gz'
                with open(raw_path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(raw_path)
                os.rename(gz_path, output_path)
            except Exception as e:
                return False, f"Compression failed: {e}"
        logging.info('Disk image creation finished successfully')
        return True, None
    except Exception as e:
        logging.exception('Exception in create_disk_image')
        # User-friendly error for missing device
        if isinstance(e, FileNotFoundError) and (not is_windows or not is_physical):
            return False, (f"Could not open {device_path}. The device may not exist, is in use, or requires administrator privileges. "
                          f"Check that the disk is present and not locked by another process.")
        return False, str(e)
