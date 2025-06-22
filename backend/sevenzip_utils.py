"""
sevenzip_utils.py - 7-Zip binary detection and archive extraction utilities for the disk imaging app.

Handles finding 7z.exe and running extraction commands for QEMU and other archives.
"""
import os
import subprocess
import shutil


def find_7z_exe():
    """
    Find 7z.exe in the tools/7zip/ directory or system-wide PATH. If only installer is present, try to extract.
    Returns (exe_path, used_tools_dir: bool)
    """
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    sevenzip_dir = os.path.join(tools_dir, '7zip')
    if not os.path.exists(sevenzip_dir):
        os.makedirs(sevenzip_dir, exist_ok=True)
    sevenz_path = os.path.join(sevenzip_dir, '7z.exe')
    if os.path.exists(sevenz_path):
        return sevenz_path, True
    # Try to extract from installer if present
    installer = find_7z_installer()
    if installer:
        ok, err = extract_7z_from_installer(installer, sevenzip_dir)
        if ok and os.path.exists(sevenz_path):
            return sevenz_path, True
        else:
            return None, False
    # Try system PATH
    for path in os.environ.get('PATH', '').split(os.pathsep):
        exe_path = os.path.join(path, '7z.exe')
        if os.path.exists(exe_path):
            return exe_path, False
    return None, False


def find_7z_installer():
    """
    Find a 7-Zip installer (7z*.exe) in the tools/ directory.
    Returns the path or None.
    """
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    for fname in os.listdir(tools_dir):
        if fname.lower().startswith('7z') and fname.lower().endswith('.exe'):
            return os.path.join(tools_dir, fname)
    return None


def extract_7z_from_installer(installer_path, dest_dir):
    """
    Attempt to extract 7z.exe and 7z.dll from the 7-Zip installer using system 7z.exe or by running the installer in silent mode.
    Returns (True, None) on success, (False, error) on failure.
    """
    import time
    # Try system 7z.exe first
    for path in os.environ.get('PATH', '').split(os.pathsep):
        sys7z = os.path.join(path, '7z.exe')
        if os.path.exists(sys7z):
            try:
                result = subprocess.run([sys7z, 'x', installer_path, '7z.exe', '7z.dll', f'-o{dest_dir}', '-y'], capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(os.path.join(dest_dir, '7z.exe')):
                    return True, None
                else:
                    continue
            except Exception as e:
                continue
    # Fallback: try running the installer in silent mode to extract to dest_dir
    try:
        # Use /S for silent, /D=dir for destination (no quotes, must end with backslash)
        dest_dir_abs = os.path.abspath(dest_dir)
        if not dest_dir_abs.endswith('\\'):
            dest_dir_abs += '\\'
        result = subprocess.run([installer_path, '/S', f'/D={dest_dir_abs}'], capture_output=True, text=True, timeout=30)
        # Wait a moment for files to appear
        for _ in range(10):
            if os.path.exists(os.path.join(dest_dir, '7z.exe')) and os.path.exists(os.path.join(dest_dir, '7z.dll')):
                return True, None
            time.sleep(0.5)
        # Some installers may extract to a subfolder (e.g., '7-Zip')
        for root, dirs, files in os.walk(dest_dir):
            if '7z.exe' in files and '7z.dll' in files:
                shutil.copy(os.path.join(root, '7z.exe'), os.path.join(dest_dir, '7z.exe'))
                shutil.copy(os.path.join(root, '7z.dll'), os.path.join(dest_dir, '7z.dll'))
                return True, None
        return False, (
            "Silent installer run did not produce 7z.exe/7z.dll in tools/7zip/. "
            "Please extract manually or use a system 7z.exe."
        )
    except Exception as e:
        return False, (
            f"Could not extract 7z.exe from installer: {e}. "
            "Please extract 7z.exe and 7z.dll manually from the installer using 7-Zip on another system, "
            "and place them in the ./tools/7zip directory."
        )


def get_7zip_status_message():
    """
    Return a user-facing message about whether 7z.exe is available and what formats are supported.
    Warn if using system 7z.exe instead of ./tools/7zip.
    """
    sevenz, used_tools_dir = find_7z_exe()
    msg = []
    if sevenz:
        msg.append("7z.exe found: all formats supported (.7z, .zip, .exe)")
        if not used_tools_dir:
            msg.append(
                "WARNING: Using system-installed 7z.exe. "
                "For best portability, place 7z.exe (and 7z.dll) from the '7-Zip Extra' package in the ./tools/7zip directory."
            )
    else:
        msg.append(
            "No 7z.exe found in tools/7zip/ or PATH. "
            "Please download the '7-Zip Extra' package from https://www.7-zip.org/download.html "
            "and place 7z.exe (and 7z.dll) in the tools/7zip/ directory."
        )
    return "\n".join(msg)


def extract_with_7zip(archive_path, dest_dir, cleanup_after=True, only_files=None):
    """
    Extract an archive using 7z.exe.
    If only_files is provided, only extract those filenames (list of basenames).
    Returns (True, None) on success, (False, error) on failure.
    Warn if using system 7z.exe instead of ./tools/7zip.
    If cleanup_after is True, deletes 7z.exe/7z.dll in tools/7zip/ after extraction.
    """
    ext = os.path.splitext(archive_path)[1].lower()
    if ext not in ('.7z', '.zip', '.exe'):
        return False, f'Unsupported archive type: {ext}'
    exe, used_tools_dir = find_7z_exe()
    if not exe:
        return False, get_7zip_status_message()
    try:
        if only_files:
            os.makedirs(dest_dir, exist_ok=True)
            for fname in only_files:
                result = subprocess.run([exe, 'e', archive_path, fname, f'-o{dest_dir}', '-y'], capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"Failed to extract {fname}: {result.stderr}\n" + get_7zip_status_message()
            warn = ""
            if not used_tools_dir:
                warn = ("\nWARNING: Used system-installed 7z.exe. "
                        "For best portability, place 7z.exe (and 7z.dll) from the '7-Zip Extra' package in the ./tools/7zip directory.")
            # Clean up extracted 7z.exe/7z.dll if requested
            if cleanup_after:
                sevenzip_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', '7zip')
                for fname in ['7z.exe', '7z.dll']:
                    fpath = os.path.join(sevenzip_dir, fname)
                    try:
                        if os.path.isfile(fpath):
                            os.remove(fpath)
                    except Exception:
                        pass
            return True, warn if warn else None
        else:
            result = subprocess.run([exe, 'x', archive_path, f'-o{dest_dir}', '-y'], capture_output=True, text=True)
            if result.returncode == 0:
                warn = ""
                if not used_tools_dir:
                    warn = ("\nWARNING: Used system-installed 7z.exe. "
                            "For best portability, place 7z.exe (and 7z.dll) from the '7-Zip Extra' package in the ./tools/7zip directory.")
                # Clean up extracted 7z.exe/7z.dll if requested
                if cleanup_after:
                    sevenzip_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', '7zip')
                    for fname in ['7z.exe', '7z.dll']:
                        fpath = os.path.join(sevenzip_dir, fname)
                        try:
                            if os.path.isfile(fpath):
                                os.remove(fpath)
                        except Exception:
                            pass
                return True, warn if warn else None
            else:
                return False, result.stderr + "\n" + get_7zip_status_message()
    except Exception as e:
        return False, str(e) + "\n" + get_7zip_status_message()
