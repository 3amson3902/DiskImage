"""
admin_utils.py - Utilities for checking administrative privileges.
"""
import os
import sys
import platform

def is_admin():
    """Check if the current process has administrative/root privileges."""
    if platform.system() == "Windows":
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0
