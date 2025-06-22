"""
disk_ops.py - Disk imaging and cloning operations for the portable disk imaging app.

Contains functions for creating disk images, cloning disks, and buffer size logic.
LLM prompt: This module provides robust, low-level disk operations for physical and image disks.
"""
import logging

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
