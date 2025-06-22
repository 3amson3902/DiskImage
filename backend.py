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
def create_disk_image(disk_info, output_path, progress_callback=None, image_format='img', compress=False, buffer_size=None):
    """
    Create a disk image in the specified format, with optional compression.
    Efficient for mostly-empty disks: skips writing all-zero blocks in raw/img/iso output (creates sparse file if supported).
    Supported formats: 'img' (raw), 'vhd', 'vmdk', 'qcow2', 'iso'.
    If compress=True, output will be compressed (gzip for raw, qemu-img for others).
    For 'iso', creates a raw image with .iso extension (no filesystem conversion).
    """
    import shutil
    device_path = disk_info['device_id']
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE
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
    For raw (.img) and iso, use qemu-img to create a sparse raw image.
    """
    device_path = disk_info['device_id']
    qemu_img = 'qemu-img.exe' if platform.system() == 'Windows' else 'qemu-img'
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
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
        return True, None
    except Exception as e:
        return False, str(e)

# Archives the given image file as a zip or 7z archive.
def archive_image(image_path, archive_type):
    """
    Archive the image file using zipfile (for .zip) or 7z (for .7z, requires 7z in PATH).
    Returns (archive_path, None) on success, (None, error) on failure.
    """
    import shutil
    import os
    base, ext = os.path.splitext(image_path)
    if archive_type == "zip":
        import zipfile
        zip_path = base + ".zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(image_path, os.path.basename(image_path))
            os.remove(image_path)
            return zip_path, None
        except Exception as e:
            return None, f"ZIP archive failed: {e}"
    elif archive_type == "7z":
        sevenz_path = base + ".7z"
        try:
            # Try to use 7z GUI if available
            sevenz_gui = r"C:\Program Files\7-Zip\7zG.exe"
            if os.path.exists(sevenz_gui):
                # 7zG.exe is the 7-Zip GUI version
                # /a: add to archive, /t7z: 7z format, /m0=lzma2: use LZMA2, /sdel: delete source after archiving
                # /q: quiet, /y: assume Yes on all queries
                cmd = [sevenz_gui, 'a', '-t7z', sevenz_path, image_path, '-sdel', '-y']
                subprocess.Popen(cmd)
                return sevenz_path, None
            else:
                # Fallback to CLI
                result = subprocess.run([
                    "7z", "a", "-t7z", sevenz_path, image_path
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    return None, result.stderr
                os.remove(image_path)
                return sevenz_path, None
        except Exception as e:
            return None, f"7z archive failed: {e}"
    else:
        return None, "Unknown archive type"

def create_disk_clone(src_disk_info, dst_disk_info, progress_callback=None, buffer_size=None):
    """
    Clone the entire source physical drive to the destination physical drive.
    This is a sector-by-sector copy. Both src_disk_info and dst_disk_info must be dicts from list_disks().
    WARNING: This will overwrite all data on the destination disk.
    """
    src_path = src_disk_info['device_id']
    dst_path = dst_disk_info['device_id']
    bs = buffer_size if buffer_size is not None else BUFFER_SIZE  # 64MB buffer for max speed
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

def get_max_buffer_size():
    # Fixed 64MB buffer size for embedded Python version
    return 64 * 1024 * 1024  # 64MB

BUFFER_SIZE = get_max_buffer_size()
