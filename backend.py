"""
backend.py - Orchestrator for disk imaging backend modules.

This file provides platform/GUI integration and disk listing logic, and imports all core disk, QEMU, and archive operations from the backend package modules.
LLM prompt: This file is the main backend entry point and should only contain high-level orchestration and platform-specific logic.
"""
import os
import sys
import platform
import subprocess
import logging
from backend.disk_ops import *
from backend.qemu_utils import *
from backend.archive_utils import *
from backend.logging_utils import *

# --- Platform/GUI integration and disk listing logic ---

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def list_disks():
    """Return a list of available disks on the system (platform-specific)."""
    logging.debug('Listing disks')
    system = platform.system()
    if system == "Windows":
        disks = list_disks_windows()
    else:
        disks = []
    logging.debug(f'Disks found: {disks}')
    return disks

def list_disks_windows():
    """Use WMIC or PowerShell to enumerate physical disks on Windows."""
    logging.debug('Attempting to list disks with WMIC')
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "DeviceID,Model,Size,Caption", "/format:csv"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8-sig'
        )
        logging.debug(f'WMIC stdout: {result.stdout}')
        logging.debug(f'WMIC stderr: {result.stderr}')
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            logging.warning('WMIC returned less than 2 lines')
            return []
        headers = [h.strip() for h in lines[0].split(',')]
        try:
            caption_idx = headers.index("Caption")
            device_id_idx = headers.index("DeviceID")
            model_idx = headers.index("Model")
            size_idx = headers.index("Size")
        except ValueError:
            logging.warning(f'WMIC header parse failed: {headers}')
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
        logging.debug(f'Disks found by WMIC: {disks}')
        return disks
    except Exception as e:
        import traceback
        logging.error(f'WMIC failed: {e}\n{traceback.format_exc()}')
        # Fallback to PowerShell Get-PhysicalDisk
        try:
            ps_cmd = [
                "powershell", "-Command",
                "Get-PhysicalDisk | Select-Object FriendlyName,DeviceId,Size,MediaType | ConvertTo-Json"
            ]
            result = subprocess.run(ps_cmd, capture_output=True, text=True, check=True)
            logging.debug(f'PowerShell stdout: {result.stdout}')
            logging.debug(f'PowerShell stderr: {result.stderr}')
            import json
            disks_info = json.loads(result.stdout)
            if isinstance(disks_info, dict):
                disks_info = [disks_info]
            disks = []
            for d in disks_info:
                size_gb = round(int(d.get('Size', 0)) / (1024**3), 2) if d.get('Size') else 'Unknown'
                disks.append({
                    "name": d.get('FriendlyName', f"PhysicalDrive{d.get('DeviceId','?')}") or f"PhysicalDrive{d.get('DeviceId','?')}",
                    "device_id": f"\\.\\PhysicalDrive{d.get('DeviceId','?')}",
                    "model": d.get('MediaType', 'Unknown'),
                    "size": f"{size_gb} GB"
                })
            logging.debug(f'Disks found by PowerShell: {disks}')
            return disks
        except Exception as e2:
            logging.error(f'PowerShell disk listing failed: {e2}\n{traceback.format_exc()}')
            return []