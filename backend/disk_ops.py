"""
disk_ops.py - Disk imaging and cloning operations for the portable disk imaging app.

Contains functions for creating disk images, cloning disks, and buffer size logic.
LLM prompt: This module provides robust, low-level disk operations for physical and image disks.
"""
import logging
import platform

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
    On Windows, always use QEMU for physical disk imaging (\\.\\PhysicalDriveX), not Python file I/O.
    Returns (True, None) on success, (False, error) on failure.
    """
    import os
    import logging
    import shutil
    device_path = disk_info['device_id']
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE
    bytes_read = 0
    raw_path = output_path
    is_windows = platform.system() == 'Windows'
    is_physical = device_path.lower().startswith('\\.\physicaldrive') if is_windows else False

    if is_windows and is_physical:
        from backend.qemu_utils import create_disk_image_sparse
        result = create_disk_image_sparse(disk_info, output_path, image_format, compress=compress, cleanup_tools=cleanup_tools)
        if not result[0]:
            return False, result[1]
        logging.info('Disk image creation (QEMU, Windows physical) finished successfully')
        return True, None

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
        return False, str(e)
