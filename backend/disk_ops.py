"""
disk_ops.py - Disk imaging and cloning operations for the portable disk imaging app.

Contains functions for creating disk images, cloning disks, and buffer size logic.
LLM prompt: This module provides robust, low-level disk operations for physical and image disks.
"""
import shutil
import logging
import platform
import os
import subprocess
from backend.qemu_utils import REQUIRED_QEMU_FILES

BUFFER_SIZE = 64 * 1024 * 1024  # 64MB for default buffer size
is_windows = platform.system() == "Windows"

def get_buffer_size():
    """Return the fixed buffer size for disk operations (64MB)."""
    return BUFFER_SIZE

def create_disk_image(disk_info, output_path, progress_callback=None, image_format='img', compress=False, buffer_size=None, cleanup_tools=False):
    """
    Create a disk image in the specified format, with optional compression.
    On Windows, always use QEMU for physical disk imaging, not Python file I/O.
    Returns (True, None) on success, (False, error) on failure.
    """
    device_path = disk_info['device_id']

    if is_windows:
        from backend.qemu_utils import run_qemu_win
        return run_qemu_win(device_path, output_path, image_format, compress)

    # For non-Windows or non-physical disks, use Python open()
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE
    bytes_read = 0
    raw_path = output_path
    if image_format not in ('img', 'iso'):
        raw_path = output_path + '.tmp.raw'
    try:
        with open(device_path, 'rb') as disk_file, open(raw_path, 'wb') as image_file:
            logging.debug('Disk image creation started')
            while True:
                chunk = disk_file.read(bs)
                if not chunk:
                    break
                if chunk.count(0) == len(chunk):
                    image_file.seek(len(chunk), 1)
                else:
                    image_file.write(chunk)
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read)
        if image_format not in ('img', 'iso'):
            from backend.qemu_utils import create_disk_image_sparse
            result = create_disk_image_sparse(disk_info, output_path, image_format, compress=compress, cleanup_tools=cleanup_tools)
            os.remove(raw_path)
            if not result[0]:
                return False, result[1]
        elif compress:
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
        if isinstance(e, FileNotFoundError) and (not is_windows):
            return False, (f"Could not open {device_path}. The device may not exist, is in use, or requires administrator privileges. "
                          f"Check that the disk is present and not locked by another process.")
        return False, str(e)

def create_disk_image_sparse(device_path, output_path, image_format, compress=False, cleanup_tools=False):
    """
    Create a sparse disk image using qemu-img for supported formats (qcow2, vhd, vmdk).
    Returns (True, None) on success, (False, error) on failure.
    """
    import platform
    from backend.qemu_utils import find_qemu_img, run_qemu_wincmd, QEMU_DIR
    import logging
    system = platform.system()
    try:
        qemu_img = find_qemu_img()
        out_fmt = 'raw' if image_format in ['img', 'iso'] else image_format
        cmd = [qemu_img, 'convert', '-p', '-O', out_fmt, '-S', '4096']
        if compress and out_fmt in ['qcow2', 'vmdk']:
            cmd.append('-c')
        cmd += [device_path, output_path]
        logging.info(f"Running sparse imaging: {cmd}")
        if system == "Windows":
            result = run_qemu_wincmd(cmd, cwd=QEMU_DIR, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"qemu-img failed: returncode={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
            return False, f"qemu-img failed (code {result.returncode}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        logging.info('Sparse disk image creation finished successfully')
        return True, None
    except Exception as e:
        logging.exception('Exception in create_disk_image_sparse')
        return False, str(e)