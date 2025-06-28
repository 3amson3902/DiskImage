"""
cli/main.py - CLI entry point for DiskImage

Provides a command-line interface for disk imaging operations.
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from backend import (
    AppConfig, list_disks, is_admin, require_admin, ImagingWorker,
    DiskImageError, ValidationError, SUPPORTED_IMAGE_FORMATS,
    setup_logging
)


def setup_cli_logging(verbose: bool = False) -> None:
    """Set up logging for CLI mode."""
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(
        log_level=level,
        log_to_file=True,
        log_to_console=True
    )


def list_available_disks() -> None:
    """List all available disks."""
    try:
        disks = list_disks()
        if not disks:
            print("No disks found.")
            return
        
        print("Available disks:")
        for i, disk in enumerate(disks, 1):
            print(f"{i:2d}. {disk.get('name', 'Unknown')} - {disk.get('size', 'Unknown size')}")
            print(f"     ID: {disk.get('id', 'Unknown')}")
            print(f"     Type: {disk.get('type', 'Unknown')}")
            print()
    except Exception as e:
        print(f"Error listing disks: {e}")
        sys.exit(1)


def create_disk_image(
    disk_id: str,
    output_path: str,
    image_format: str = "raw",
    sparse: bool = True,
    compress: bool = False,
    archive: bool = False,
    archive_type: Optional[str] = None,
    buffer_size: int = 64,
    cleanup: bool = True,
    verbose: bool = False
) -> None:
    """Create a disk image with the specified parameters."""
    setup_cli_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate admin privileges
        if not is_admin():
            print("Error: Administrator privileges required for disk imaging.")
            sys.exit(1)
        
        # Find the disk
        disks = list_disks()
        disk_info = None
        for disk in disks:
            if disk.get('id') == disk_id or disk.get('name') == disk_id:
                disk_info = disk
                break
        
        if not disk_info:
            print(f"Error: Disk '{disk_id}' not found.")
            print("Use --list to see available disks.")
            sys.exit(1)
        
        # Validate output path
        output_path_obj = Path(output_path)
        if output_path_obj.exists():
            response = input(f"Output file '{output_path}' exists. Overwrite? [y/N]: ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
        
        # Create output directory if needed
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Creating image of disk: {disk_info.get('name', 'Unknown')}")
        print(f"Output: {output_path}")
        print(f"Format: {image_format}")
        print(f"Sparse: {sparse}")
        print(f"Compress: {compress}")
        if archive:
            print(f"Archive: {archive_type}")
        print()
        
        # Create imaging worker
        worker = ImagingWorker()
        
        # Define progress callback
        def progress_callback(progress: float) -> None:
            # Simple progress bar
            bar_length = 50
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\rProgress: [{bar}] {progress:.1f}%", end='', flush=True)
        
        # Define log callback
        def log_callback(message: str) -> None:
            if verbose:
                print(f"\n{message}")
        
        # Start imaging
        success, message = worker.create_image(
            disk_info=disk_info,
            output_path=output_path,
            image_format=image_format,
            use_sparse=sparse,
            use_compress=compress,
            archive_after=archive,
            archive_type=archive_type,
            buffer_size_mb=buffer_size,
            cleanup_tools=cleanup,
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        print()  # New line after progress bar
        
        if success:
            print(f"✓ Image created successfully: {output_path}")
            if archive:
                archive_path = output_path_obj.with_suffix(f".{archive_type}")
                print(f"✓ Archive created: {archive_path}")
        else:
            print(f"✗ Error creating image: {message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during imaging")
        print(f"Error: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DiskImage - Create disk images and archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,        epilog="""
Examples:
  diskimage --list                           # List available disks
  diskimage --disk "\\\\.\\\\PHYSICALDRIVE1" --output disk1.img
  diskimage --disk "USB Drive" --output usb.qcow2 --format qcow2 --compress
  diskimage --disk "\\\\.\\\\PHYSICALDRIVE0" --output system.raw --archive --archive-type 7z
        """
    )
    
    # Action arguments
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available disks and exit"
    )
    
    # Disk selection
    parser.add_argument(
        "--disk", "-d",
        type=str,
        help="Disk ID or name to image (e.g., '\\\\.\\\\PHYSICALDRIVE1' or 'USB Drive')"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path"
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=SUPPORTED_IMAGE_FORMATS,
        default="raw",
        help="Image format (default: raw)"
    )
    
    # Image options
    parser.add_argument(
        "--no-sparse",
        action="store_true",
        help="Disable sparse file creation (creates full-size files)"
    )
    
    parser.add_argument(
        "--compress", "-c",
        action="store_true",
        help="Enable compression (format-dependent)"
    )
    
    # Archive options
    parser.add_argument(
        "--archive", "-a",
        action="store_true",
        help="Create archive after imaging"
    )
    
    parser.add_argument(
        "--archive-type",
        type=str,
        choices=["7z", "zip"],
        default="7z",
        help="Archive format (default: 7z)"
    )
    
    # Performance options
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=64,
        help="Buffer size in MB (default: 64)"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up temporary tool files"
    )
    
    # General options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Handle list action
    if args.list:
        list_available_disks()
        return
    
    # Validate required arguments for imaging
    if not args.disk:
        parser.error("--disk is required for imaging operations")
    
    if not args.output:
        parser.error("--output is required for imaging operations")
    
    # Create disk image
    create_disk_image(
        disk_id=args.disk,
        output_path=args.output,
        image_format=args.format,
        sparse=not args.no_sparse,
        compress=args.compress,
        archive=args.archive,
        archive_type=args.archive_type if args.archive else None,
        buffer_size=args.buffer_size,
        cleanup=not args.no_cleanup,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
