import os
import sys
import platform
import subprocess
from datetime import datetime
import logging

# Initialize logging
logging.basicConfig(filename='diskimager_main.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# --- Platform Agnostic Main Logic ---

def main():
    """Main function to drive the disk imaging process."""
    # On Windows, raw disk access requires administrator privileges.
    if platform.system() == "Windows":
        if not is_admin():
            print("Error: This script requires administrator privileges on Windows.")
            print("Please re-run it in an elevated Command Prompt or PowerShell.")
            sys.exit(1)
    # The sudo check for Linux/macOS would go here if combined
    elif os.geteuid() != 0:
        print("Error: This script requires sudo/root privileges.")
        sys.exit(1)

    disks = list_disks()
    if not disks:
        print("No physical disks found or an error occurred.", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable Physical Disks:")
    for i, disk_info in enumerate(disks, 1):
        print(f"{i}. {disk_info['name']} ({disk_info['device_id']}) - Size: {disk_info['size']}, Model: {disk_info['model']}")

    selected_disk = None
    while True:
        try:
            choice_str = input("\nSelect the number of the disk to image: ")
            choice = int(choice_str)
            if 1 <= choice <= len(disks):
                selected_disk = disks[choice - 1]
                break
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)

    # Get output path
    default_filename = f"{selected_disk['name']}_{datetime.now().strftime('%Y%m%d')}.img"
    while True:
        output_path = input(f"Enter the output file path [{default_filename}]: ").strip()
        if not output_path:
            output_path = default_filename
        if os.path.exists(output_path):
            confirm = input(f"File '{output_path}' exists. Overwrite? (y/N): ").strip().lower()
            if confirm == 'y':
                break
            else:
                print("Please enter a different file name or confirm overwrite.")
        else:
            break

    create_disk_image(selected_disk, output_path)

# --- Windows Specific Functions ---

def is_admin():
    """Check if the script is running with administrator privileges on Windows."""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def list_disks_windows():
    """List available physical disks using WMIC or PowerShell on Windows."""
    print("Discovering disks...")
    try:
        # Try WMIC first
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "DeviceID,Model,Size,Caption", "/format:csv"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8-sig' # Handle encoding from WMIC
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
            print("Error: Could not parse WMIC output headers.", file=sys.stderr)
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
        # Fallback to PowerShell Get-PhysicalDisk
        try:
            ps_cmd = [
                "powershell", "-Command",
                "Get-PhysicalDisk | Select-Object FriendlyName,DeviceId,Size,MediaType | ConvertTo-Json"
            ]
            result = subprocess.run(ps_cmd, capture_output=True, text=True, check=True)
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
            return disks
        except Exception as e:
            print(f"Error listing disks with PowerShell: {e}", file=sys.stderr)
            return []


def create_disk_image_windows(disk_info, output_path):
    """Create a raw disk image on Windows by reading from the physical drive handle."""
    device_path = disk_info['device_id']

    print("\n" + "="*60)
    print("!!! WARNING: YOU ARE ABOUT TO PERFORM A DANGEROUS OPERATION !!!")
    print(f"This will create a bit-by-bit copy of the disk '{disk_info['name']}'.")
    print(f"This can lead to IRREVERSIBLE DATA LOSS if you select the wrong disk.")
    print("="*60 + "\n")

    try:
        # For Windows, confirming with the drive name (e.g., "WDC WD10EZEX-00BN5A0") is best
        confirm = input(f"To proceed, please type the disk model name '{disk_info['name']}': ")
        if confirm.strip() != disk_info['name']:
            print("Confirmation failed. Aborting.")
            return
    except KeyboardInterrupt:
        print("\nOperation aborted by user.")
        return

    print(f"\nCreating image of {device_path} to {output_path}...")
    print("This may take a long time. Do NOT interrupt the process!\n")

    try:
        # Buffer size for reading, 4MB is a reasonable default
        bs = 4 * 1024 * 1024
        bytes_read = 0
        with open(device_path, 'rb') as disk_file, open(output_path, 'wb') as image_file:
            while True:
                chunk = disk_file.read(bs)
                if not chunk:
                    break
                image_file.write(chunk)
                bytes_read += len(chunk)
                # Simple progress indicator
                print(f"\rWritten: {round(bytes_read / (1024**3), 2)} GB", end="")

        print("\n\nDisk image created successfully!")

    except PermissionError:
        print(f"\nError: Access denied to '{device_path}'. Ensure you are running as an administrator.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"\nError: The device path '{device_path}' was not found.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nImage creation interrupted by user. The output file may be incomplete or corrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during imaging: {e}", file=sys.stderr)
        sys.exit(1)

# --- Platform Dispatcher ---

def list_disks():
    """Dispatcher to call the correct list_disks function for the OS."""
    system = platform.system()
    if system == "Windows":
        return list_disks_windows()
    # Placeholder for Linux/macOS functions if combined
    # elif system in ["Linux", "Darwin"]:
    #     return list_disks_unix()
    else:
        print(f"Unsupported OS: {system}", file=sys.stderr)
        sys.exit(1)

def create_disk_image(disk_info, output_path):
    """Dispatcher to call the correct image creation function for the OS."""
    system = platform.system()
    if system == "Windows":
        return create_disk_image_windows(disk_info, output_path)
    # Placeholder for Linux/macOS functions if combined
    # elif system in ["Linux", "Darwin"]:
    #     return create_disk_image_unix(disk_info['name'], output_path)
    else:
        print(f"Unsupported OS: {system}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we are on Windows before running the Windows-specific logic
    if platform.system() != "Windows":
        print("This script is configured for Windows. For Linux/macOS, use the other version.")
        sys.exit(1)
    main()
