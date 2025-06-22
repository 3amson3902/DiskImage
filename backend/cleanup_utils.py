"""
Cleanup utilities for DiskImage application.
"""
import logging
from pathlib import Path
from typing import List, Optional

from .constants import QEMU_DIR, SEVENZIP_DIR

logger = logging.getLogger(__name__)


def cleanup_qemu_files() -> bool:
    """
    Remove QEMU files from tools/qemu directory.
    
    Returns:
        True if cleanup was successful, False otherwise
    """
    return _cleanup_directory(QEMU_DIR, "QEMU")


def cleanup_sevenzip_files() -> bool:
    """
    Remove 7-Zip files from tools/7zip directory.
    
    Returns:
        True if cleanup was successful, False otherwise
    """
    return _cleanup_directory(SEVENZIP_DIR, "7-Zip")


def cleanup_all_tools() -> bool:
    """
    Clean up all extracted tool files.
    
    Returns:
        True if all cleanups were successful, False otherwise
    """
    qemu_success = cleanup_qemu_files()
    sevenzip_success = cleanup_sevenzip_files()
    
    return qemu_success and sevenzip_success


def _cleanup_directory(directory: Path, tool_name: str) -> bool:
    """
    Remove all files from the specified directory.
    
    Args:
        directory: Directory to clean up
        tool_name: Name of the tool for logging
        
    Returns:
        True if cleanup was successful, False otherwise
    """
    if not directory.exists():
        logger.debug(f"{tool_name} directory does not exist: {directory}")
        return True
    
    if not directory.is_dir():
        logger.warning(f"{tool_name} path is not a directory: {directory}")
        return False
    
    success = True
    files_removed = 0
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    files_removed += 1
                    logger.debug(f"Removed {tool_name} file: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove {tool_name} file {file_path.name}: {e}")
                    success = False
            elif file_path.is_dir():
                logger.debug(f"Skipping {tool_name} subdirectory: {file_path.name}")
        
        logger.info(f"{tool_name} cleanup completed - removed {files_removed} files")
        
        # Try to remove the directory if it's empty
        try:
            if not any(directory.iterdir()):
                directory.rmdir()
                logger.debug(f"Removed empty {tool_name} directory: {directory}")
        except Exception as e:
            logger.debug(f"Could not remove {tool_name} directory: {e}")
        
    except Exception as e:
        logger.error(f"Failed to clean up {tool_name} directory: {e}")
        success = False
    
    return success


def get_cleanup_info() -> dict:
    """
    Get information about files that would be cleaned up.
    
    Returns:
        Dictionary with cleanup information
    """
    info = {
        "qemu": _get_directory_info(QEMU_DIR),
        "sevenzip": _get_directory_info(SEVENZIP_DIR)
    }
    
    total_files = info["qemu"]["file_count"] + info["sevenzip"]["file_count"]
    total_size = info["qemu"]["total_size"] + info["sevenzip"]["total_size"]
    
    info["total"] = {
        "file_count": total_files,
        "total_size": total_size,
        "size_formatted": _format_bytes(total_size)
    }
    
    return info


def _get_directory_info(directory: Path) -> dict:
    """
    Get information about files in a directory.
    
    Args:
        directory: Directory to analyze
        
    Returns:
        Dictionary with directory information
    """
    info = {
        "exists": directory.exists(),
        "file_count": 0,
        "total_size": 0,
        "files": []
    }
    
    if not directory.exists() or not directory.is_dir():
        return info
    
    try:
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    info["files"].append({
                        "name": file_path.name,
                        "size": size,
                        "size_formatted": _format_bytes(size)
                    })
                    info["file_count"] += 1
                    info["total_size"] += size
                except Exception as e:
                    logger.warning(f"Could not get info for file {file_path}: {e}")
                    
        info["size_formatted"] = _format_bytes(info["total_size"])
        
    except Exception as e:
        logger.error(f"Failed to get directory info for {directory}: {e}")
    
    return info


def _format_bytes(size: int) -> str:
    """
    Format byte size in human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
