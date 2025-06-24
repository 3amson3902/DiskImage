"""
Cross-platform disk listing utilities for the disk imaging app.

Provides functions to enumerate available disks on the system, 
with Windows-specific implementations using WMIC and PowerShell.
"""
import platform
import subprocess
import logging
import json
from typing import List, Dict, Optional

from .exceptions import DiskListError

logger = logging.getLogger(__name__)


def list_disks() -> List[Dict[str, str]]:
    """
    Return a list of available disks on the system (platform-specific).
    
    Returns:
        List of dictionaries containing disk information:
        - name: Human-readable disk name
        - device_id: System device identifier  
        - model: Disk model name
        - size: Formatted size string
    
    Raises:
        DiskListError: If disk enumeration fails completely
    """
    logger.debug('Listing system disks')
    system = platform.system()
    
    try:
        if system == "Windows":
            disks = _list_disks_windows()
        elif system in ["Linux", "Darwin"]:
            # TODO: Implement Linux/macOS disk listing
            disks = []
            logger.warning(f"Disk listing not implemented for {system}")
        else:
            disks = []
            logger.warning(f"Unsupported platform: {system}")
        
        logger.info(f'Found {len(disks)} disks')
        return disks
        
    except Exception as e:
        logger.exception("Failed to list disks")
        raise DiskListError(f"Failed to enumerate system disks: {e}") from e


def _list_disks_windows() -> List[Dict[str, str]]:
    """
    Use WMIC or PowerShell to enumerate physical disks on Windows.
    
    Returns:
        List of disk information dictionaries
        
    Raises:
        DiskListError: If both WMIC and PowerShell fail
    """
    logger.debug('Attempting to list Windows disks with WMIC')
    
    try:
        return _list_disks_wmic()
    except FileNotFoundError:
        logger.warning("WMIC not found, falling back to PowerShell")
        return _list_disks_powershell()
    except Exception as e:
        logger.warning(f"WMIC failed: {e}, falling back to PowerShell")
        return _list_disks_powershell()


def _list_disks_wmic() -> List[Dict[str, str]]:
    """
    Helper: Use WMIC to enumerate disks on Windows.
    
    Returns:
        List of disk information dictionaries
        
    Raises:
        DiskListError: If WMIC fails or returns invalid data
        FileNotFoundError: If WMIC is not available
    """
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "DeviceID,Model,Size,Caption,InterfaceType", "/format:csv"],
            capture_output=True,
            text=True,
            encoding='utf-8-sig',
            timeout=30
        )
        
        if result.returncode != 0:
            raise DiskListError(f"WMIC failed with return code {result.returncode}: {result.stderr}")
        
        logger.debug(f'WMIC stdout: {result.stdout[:500]}...')  # Truncated for logging
        
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            logger.warning('WMIC returned insufficient data')
            return []
        
        # Parse CSV header
        headers = [h.strip() for h in lines[0].split(',')]
        required_headers = ["Caption", "DeviceID", "Model", "Size"]
        optional_headers = ["InterfaceType"]
        
        try:
            indices = {header: headers.index(header) for header in required_headers}
            # Add optional headers if available
            for header in optional_headers:
                if header in headers:
                    indices[header] = headers.index(header)
        except ValueError as e:
            raise DiskListError(f"WMIC output missing required column: {e}")
        
        disks = []
        for line in lines[1:]:
            if not line.strip():
                continue
                
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < len(required_headers):
                continue
                
            try:
                size_bytes = int(parts[indices["Size"]])
                size_gb = round(size_bytes / (1024**3), 2)
                size_str = f"{size_gb} GB"
            except (ValueError, IndexError):
                size_str = 'Unknown'
            
            # Get interface type if available
            interface = 'Unknown'
            if "InterfaceType" in indices and len(parts) > indices["InterfaceType"]:
                interface = parts[indices["InterfaceType"]] or 'Unknown'
            
            disk_info = {
                "name": parts[indices["Caption"]],
                "device_id": parts[indices["DeviceID"]],
                "model": parts[indices["Model"]],
                "size": size_str,
                "interface": interface
            }
            disks.append(disk_info)
        
        logger.debug(f'WMIC found {len(disks)} disks')
        return disks
        
    except subprocess.TimeoutExpired:
        raise DiskListError("WMIC command timed out")
    except FileNotFoundError:
        raise FileNotFoundError("WMIC command not found")
    except Exception as e:
        raise DiskListError(f"WMIC execution failed: {e}") from e


def _list_disks_powershell() -> List[Dict[str, str]]:
    """
    Helper: Use PowerShell to enumerate disks on Windows.
    
    Returns:
        List of disk information dictionaries
        
    Raises:
        DiskListError: If PowerShell fails or returns invalid data
    """
    try:
        ps_cmd = [
            "powershell", "-Command",
            "Get-PhysicalDisk | Select-Object FriendlyName,DeviceId,Size,MediaType,BusType | ConvertTo-Json"
        ]
        
        result = subprocess.run(
            ps_cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode != 0:
            raise DiskListError(f"PowerShell failed with return code {result.returncode}: {result.stderr}")
        
        logger.debug(f'PowerShell stdout: {result.stdout[:500]}...')  # Truncated for logging
        
        try:
            disks_info = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise DiskListError(f"PowerShell returned invalid JSON: {e}")
        
        # Handle single disk (not in array)
        if isinstance(disks_info, dict):
            disks_info = [disks_info]
        
        disks = []
        for d in disks_info:
            try:
                device_id = d.get('DeviceId')
                if device_id is None:
                    continue
                    
                size_bytes = d.get('Size', 0)
                if size_bytes and isinstance(size_bytes, (int, float)):
                    size_gb = round(size_bytes / (1024**3), 2)
                    size_str = f"{size_gb} GB"
                else:
                    size_str = 'Unknown'
                
                friendly_name = d.get('FriendlyName', f"PhysicalDrive{device_id}")
                name = friendly_name if friendly_name else f"PhysicalDrive{device_id}"
                
                # Get interface type
                bus_type = d.get('BusType', 'Unknown')
                interface_map = {
                    '0': 'Unknown',
                    '1': 'SCSI',
                    '2': 'ATAPI',
                    '3': 'ATA',
                    '4': 'IEEE 1394',
                    '5': 'SSA',
                    '6': 'FC',
                    '7': 'USB',
                    '8': 'RAID',
                    '9': 'iSCSI',
                    '10': 'SAS',
                    '11': 'SATA',
                    '12': 'SD',
                    '13': 'MMC',
                    '14': 'Virtual',
                    '15': 'File Backed Virtual',
                    '16': 'Storage Spaces',
                    '17': 'NVMe'
                }
                interface = interface_map.get(str(bus_type), f"Unknown ({bus_type})")
                
                disk_info = {
                    "name": name,
                    "device_id": f"\\\\.\\PhysicalDrive{device_id}",
                    "model": d.get('MediaType', 'Unknown'),
                    "size": size_str,
                    "interface": interface
                }
                disks.append(disk_info)
                
            except Exception as e:
                logger.warning(f"Failed to parse disk info: {d}, error: {e}")
                continue
        
        logger.debug(f'PowerShell found {len(disks)} disks')
        return disks
        
    except subprocess.TimeoutExpired:
        raise DiskListError("PowerShell command timed out")
    except FileNotFoundError:
        raise DiskListError("PowerShell not found")
    except Exception as e:
        raise DiskListError(f"PowerShell execution failed: {e}") from e
