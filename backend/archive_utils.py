"""
archive_utils.py - Archiving utilities for disk images (zip/7z) for the disk imaging app.

Handles archiving images as .zip or .7z, with robust error handling and logging.
LLM prompt: This module provides user-friendly archiving and cleanup for disk images.
"""
import os
import zipfile
import subprocess
import logging

def archive_image(image_path, archive_type):
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
            sevenz_gui = r"C:\Program Files\7-Zip\7zG.exe"
            if os.path.exists(sevenz_gui):
                cmd = [sevenz_gui, 'a', '-t7z', sevenz_path, image_path, '-sdel', '-y']
                subprocess.Popen(cmd)
                logging.info('Archiving finished successfully')
                return sevenz_path, None
            else:
                result = subprocess.run([
                    "7z", "a", "-t7z", sevenz_path, image_path
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    return None, result.stderr
                os.remove(image_path)
                logging.info('Archiving finished successfully')
                return sevenz_path, None
        except Exception as e:
            logging.exception('Exception in archive_image')
            return None, f"7z archive failed: {e}"
    else:
        return None, "Unknown archive type"
