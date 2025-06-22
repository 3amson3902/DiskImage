"""
Utilities for checking administrative privileges.
"""
import os
import platform
import logging

from .exceptions import PermissionError as DiskImagePermissionError

logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """
    Check if the current process has administrative/root privileges.
    
    Returns:
        True if running with admin/root privileges, False otherwise
    """
    system = platform.system()
    
    try:
        if system == "Windows":
            return _is_admin_windows()
        elif system in ["Linux", "Darwin"]:
            return _is_admin_unix()
        else:
            logger.warning(f"Unknown platform: {system}, assuming no admin privileges")
            return False
            
    except Exception as e:
        logger.error(f"Failed to check admin privileges: {e}")
        return False


def _is_admin_windows() -> bool:
    """
    Check admin privileges on Windows using ctypes.
    
    Returns:
        True if running as administrator
    """
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.warning(f"Failed to check Windows admin status: {e}")
        return False


def _is_admin_unix() -> bool:
    """
    Check root privileges on Unix-like systems.
    
    Returns:
        True if running as root (UID 0)
    """
    try:
        return os.geteuid() == 0
    except AttributeError:
        # geteuid not available on this platform
        logger.warning("geteuid() not available, cannot check root privileges")
        return False
    except Exception as e:
        logger.warning(f"Failed to check Unix admin status: {e}")
        return False


def require_admin() -> None:
    """
    Raise an exception if not running with admin privileges.
    
    Raises:
        DiskImagePermissionError: If not running with admin privileges
    """
    if not is_admin():
        system = platform.system()
        if system == "Windows":
            msg = "Administrator privileges required. Please run as administrator."
        else:
            msg = "Root privileges required. Please run with sudo."
        
        raise DiskImagePermissionError(msg)
