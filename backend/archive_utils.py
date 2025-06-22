"""
archive_utils.py - Archiving utilities for disk images (zip/7z) for the disk imaging app.

Handles archiving images as .zip or .7z, with robust error handling and logging.
LLM prompt: This module provides user-friendly archiving and cleanup for disk images.
"""
import os
import zipfile
import logging

def archive_image(image_path, archive_type, cleanup_tools=False):
    """
    Archive the image file using zipfile (for .zip) or 7z (for .7z, requires 7z in PATH).
    Returns (archive_path, None) on success, (None, error) on failure.
    """
    logging.info(f'Archiving image: image_path={image_path}, archive_type={archive_type}')
    base, ext = os.path.splitext(image_path)

    if archive_type == "zip":
        zip_path = base + ".zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(image_path, os.path.basename(image_path))
            os.remove(image_path)
            logging.info('Archiving finished successfully')
            return zip_path, None
        except Exception as e:
            logging.exception('Exception in archive_image')
            return None, f"ZIP archive failed: {e}"
    elif archive_type == "7z":
        sevenz_path = base + ".7z"
        try:
            from backend.sevenzip_utils import extract_with_7zip
            result = extract_with_7zip(image_path, os.path.dirname(image_path), cleanup_after=cleanup_tools)
            if isinstance(result, tuple) and result[0]:
                os.remove(image_path)
                logging.info('Archiving finished successfully')
                return sevenz_path, None
            else:
                return None, result[1] if isinstance(result, tuple) else '7z archiving failed.'
        except Exception as e:
            logging.exception('Exception in archive_image')
            return None, f"7z archive failed: {e}"
    else:
        return None, "Unknown archive type"
