import os
import sys
import platform
import subprocess
from datetime import datetime

# --- Backend logic for disk imaging ---

# Checks if the script is running with administrator privileges.
# On Windows, uses ctypes; on Unix, checks effective user id.
def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

# Returns a list of available disks on the system.
# Dispatches to the correct platform-specific implementation.
def list_disks():
    system = platform.system()
    if system == "Windows":
        return list_disks_windows()
    else:
        return []

# Uses WMIC to enumerate physical disks on Windows.
# Returns a list of dicts with disk info (name, device_id, model, size).
def list_disks_windows():
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "DeviceID,Model,Size,Caption", "/format:csv"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8-sig'
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return []
        headers = [h.strip() for h in lines[0].split(',')]
        try:
            caption_idx = headers.index("Caption")
            device_id_idx = headers.index("DeviceID")
            model_idx = headers.index("Model")
            size_idx = headers.index("Size")
        except ValueError:
            return []
        disks = []
        for line in lines[1:]:
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            try:
                size_bytes = int(parts[size_idx])
                size_gb = round(size_bytes / (1024**3), 2)
            except Exception:
                size_gb = 'Unknown'
            disks.append({
                "name": parts[caption_idx],
                "device_id": parts[device_id_idx],
                "model": parts[model_idx],
                "size": f"{size_gb} GB"
            })
        return disks
    except Exception:
        return []

# Creates a disk image in the specified format, with optional compression.
# Now supports 'iso' as a raw sector-by-sector image with .iso extension.
def create_disk_image(disk_info, output_path, progress_callback=None, image_format='img', compress=False):
    """
    Create a disk image in the specified format, with optional compression.
    Supported formats: 'img' (raw), 'vhd', 'vmdk', 'qcow2', 'iso'.
    If compress=True, output will be compressed (gzip for raw, qemu-img for others).
    For 'iso', creates a raw image with .iso extension (no filesystem conversion).
    """
    import shutil
    device_path = disk_info['device_id']
    bs = 4 * 1024 * 1024
    bytes_read = 0
    raw_path = output_path
    # If not raw or iso, create a temp raw file first
    if image_format not in ('img', 'iso'):
        raw_path = output_path + '.tmp.raw'
    try:
        with open(device_path, 'rb') as disk_file, open(raw_path, 'wb') as image_file:
            while True:
                chunk = disk_file.read(bs)
                if not chunk:
                    break
                image_file.write(chunk)
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read)
        # Convert to requested format if needed
        if image_format not in ('img', 'iso'):
            result = convert_image_format(raw_path, output_path, image_format, compress=compress)
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
        return True, None
    except Exception as e:
        return False, str(e)

# Converts a raw disk image to another format using qemu-img.
# Supported formats: vhd, vmdk, qcow2.
# If compress=True, uses qemu-img's -c option for supported formats.
def convert_image_format(src_path, dest_path, image_format, compress=False):
    """
    Convert a raw image to the specified format using qemu-img.
    If compress=True, use qemu-img's -c option for supported formats (qcow2, vmdk).
    """
    qemu_img = 'qemu-img.exe' if platform.system() == 'Windows' else 'qemu-img'
    if image_format not in ['vhd', 'vmdk', 'qcow2']:
        return False, f"Unsupported format: {image_format}"
    try:
        cmd = [qemu_img, 'convert', '-f', 'raw', '-O', image_format]
        if compress and image_format in ['qcow2', 'vmdk']:
            cmd.append('-c')
        cmd += [src_path, dest_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
        return True, None
    except Exception as e:
        return False, str(e)

# Uses qemu-img to create a sparse image directly from the physical disk, with optional compression.
# Only supported for vhd, vmdk, qcow2 formats.
def create_disk_image_sparse(disk_info, output_path, image_format='qcow2', compress=False):
    """
    Use qemu-img to create a sparse image directly from the physical disk.
    If compress=True, use qemu-img's -c option for supported formats (qcow2, vmdk).
    """
    device_path = disk_info['device_id']
    qemu_img = 'qemu-img.exe' if platform.system() == 'Windows' else 'qemu-img'
    if image_format not in ['vhd', 'vmdk', 'qcow2']:
        return False, f"Sparse imaging not supported for format: {image_format}"
    try:
        cmd = [qemu_img, 'convert', '-O', image_format, '-S', '4096']
        if compress and image_format in ['qcow2', 'vmdk']:
            cmd.append('-c')
        cmd += [device_path, output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
        return True, None
    except Exception as e:
        return False, str(e)
