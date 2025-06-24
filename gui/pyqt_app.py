"""
gui/pyqt_app.py - PyQt6 GUI entry point for DiskImage
"""
import sys
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QProgressBar, 
    QFileDialog, QCheckBox, QMessageBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Use new backend classes
from backend import (
    AppConfig, list_disks, is_admin, require_admin, ImagingWorker,
    DiskImageError, ValidationError, SUPPORTED_IMAGE_FORMATS
)

logger = logging.getLogger(__name__)


class ImagingThread(QThread):
    """Worker thread for disk imaging operations using the new backend."""
    
    progress = pyqtSignal(float)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)

    def __init__(self, disk_info: Dict[str, str], output_path: str, 
                 image_format: str, use_sparse: bool, use_compress: bool, 
                 archive_after: bool, archive_type: Optional[str], 
                 buffer_size: int, cleanup_tools: bool):
        super().__init__()
        self.disk_info = disk_info
        self.output_path = output_path
        self.image_format = image_format
        self.use_sparse = use_sparse
        self.use_compress = use_compress
        self.archive_after = archive_after
        self.archive_type = archive_type
        self.buffer_size = buffer_size
        self.cleanup_tools = cleanup_tools
        self.imaging_worker = ImagingWorker()

    def run(self):
        """Run the imaging operation in a separate thread."""
        try:
            def progress_callback(bytes_read: int) -> None:
                total_size = self._get_disk_size(self.disk_info)
                if total_size > 0:
                    percent = (bytes_read / total_size) * 100
                    self.progress.emit(min(percent, 100.0))

            success, message, log_output = self.imaging_worker.run_imaging_job(
                disk_info=self.disk_info,
                output_path=self.output_path,
                image_format=self.image_format,
                use_sparse=self.use_sparse,
                use_compress=self.use_compress,
                archive_after=self.archive_after,
                archive_type=self.archive_type,
                buffer_size=self.buffer_size,
                cleanup_tools=self.cleanup_tools,
                progress_callback=progress_callback
            )
            
            self.finished.emit(success, message)
            self.log.emit(log_output)
            
        except Exception as e:
            logger.exception("Imaging thread failed with exception")
            import traceback
            error_msg = f"Imaging failed with exception: {e}"
            self.finished.emit(False, error_msg)
            self.log.emit(traceback.format_exc())

    def _get_disk_size(self, disk_info: Dict[str, str]) -> float:
        """Extract disk size from disk info for progress calculation."""
        try:
            size_str = disk_info.get('size', '0 GB')
            # Extract numeric part (e.g., "500 GB" -> "500")
            size_parts = size_str.split()
            if size_parts:
                size_value = float(size_parts[0])
                # Convert to bytes (assuming GB)
                return size_value * (1024**3)
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse disk size '{disk_info.get('size')}': {e}")
        return 0.0


class DiskImagerWindow(QMainWindow):
    """Main GUI window for the DiskImage application."""
    
    def __init__(self):
        super().__init__()
        try:
            self.config = AppConfig.load()
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            self.config = AppConfig()
            
        self.setWindowTitle("DiskImage - Disk Imaging Tool")
        w, h = self.config.window_size
        self.setGeometry(100, 100, w, h)
        self.selected_disk: Optional[Dict[str, str]] = None
        self.imaging_thread: Optional[ImagingThread] = None
        
        self.init_ui()
        self.refresh_disks()
        self.restore_preferences()

    def init_ui(self):
        """Initialize the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        
        # Disk selection
        layout.addWidget(QLabel("Select Disk:"))
        self.disk_combo = QComboBox()
        self.disk_combo.currentIndexChanged.connect(self.on_disk_selected)
        layout.addWidget(self.disk_combo)
        
        # Output file
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output File:"))
        self.output_edit = QLineEdit()
        out_layout.addWidget(self.output_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        out_layout.addWidget(browse_btn)
        layout.addLayout(out_layout)
        
        # Format selection
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Image Format:"))
        self.format_combo = QComboBox()
        for label, format_code in SUPPORTED_IMAGE_FORMATS.items():
            self.format_combo.addItem(label, format_code)
        fmt_layout.addWidget(self.format_combo)
        layout.addLayout(fmt_layout)
        
        # Options
        self.sparse_cb = QCheckBox("Enable sparse imaging (faster for empty disks)")
        self.sparse_cb.setChecked(True)
        layout.addWidget(self.sparse_cb)
        
        self.compress_cb = QCheckBox("Enable compression (smaller output, slower)")
        layout.addWidget(self.compress_cb)
        
        self.archive_cb = QCheckBox("Archive image after creation")
        layout.addWidget(self.archive_cb)
        
        arch_layout = QHBoxLayout()
        arch_layout.addWidget(QLabel("Archive type:"))
        self.archive_type_combo = QComboBox()
        self.archive_type_combo.addItems(["zip", "7z"])
        arch_layout.addWidget(self.archive_type_combo)
        layout.addLayout(arch_layout)
        
        buf_layout = QHBoxLayout()
        buf_layout.addWidget(QLabel("Buffer size (MB):"))
        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(1, 1024)
        self.buffer_spin.setValue(self.config.buffer_size_mb)
        buf_layout.addWidget(self.buffer_spin)
        layout.addLayout(buf_layout)
        
        self.cleanup_cb = QCheckBox("Cleanup extracted tools after imaging")
        self.cleanup_cb.setChecked(self.config.cleanup_tools)
        layout.addWidget(self.cleanup_cb)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        
        # Status (use QTextEdit for copyable text)
        self.status_label = QTextEdit("Ready.")
        self.status_label.setReadOnly(True)
        self.status_label.setMaximumHeight(120)
        layout.addWidget(self.status_label)
        
        # Start button
        self.start_btn = QPushButton("Start Imaging")
        self.start_btn.clicked.connect(self.handle_start_imaging)
        layout.addWidget(self.start_btn)
        
        central.setLayout(layout)

    def restore_preferences(self):
        """Restore user preferences from configuration."""
        if self.config.last_output_dir:
            self.output_edit.setText(self.config.last_output_dir)

    def closeEvent(self, event):
        """Handle window close event - save preferences."""
        try:
            self.config.cleanup_tools = self.cleanup_cb.isChecked()
            self.config.last_output_dir = self.output_edit.text().strip()
            self.config.window_size = (self.width(), self.height())
            self.config.buffer_size_mb = self.buffer_spin.value()
            self.config.save()
            logger.info("Configuration saved on exit")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")        
        event.accept()

    def refresh_disks(self):
        """Refresh the list of available disks."""
        try:
            disks = list_disks()
            self.disks = disks
            self.disk_combo.clear()
            
            if not disks:
                self.disk_combo.addItem("No disks found")
                self.start_btn.setEnabled(False)
            else:
                for disk in disks:
                    # Include interface type in display name
                    interface = disk.get('interface', 'Unknown')
                    display_name = f"{disk['name']} ({disk['device_id']}) - {disk['size']} - {disk['model']} [{interface}]"
                    self.disk_combo.addItem(display_name)
                self.selected_disk = disks[0]
                self.start_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Failed to refresh disks: {e}")
            self.disk_combo.clear()
            self.disk_combo.addItem("Error loading disks")
            self.start_btn.setEnabled(False)

    def on_disk_selected(self, index: int):
        """Handle disk selection change."""
        if hasattr(self, 'disks') and 0 <= index < len(self.disks):
            self.selected_disk = self.disks[index]

    def browse_file(self):
        """Open file dialog to select output file."""
        try:
            if self.selected_disk:
                current_format = self.format_combo.currentData()
                default_name = f"{self.selected_disk['name']}_{datetime.datetime.now().strftime('%Y%m%d')}.{current_format}"
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Save Image File", 
                    default_name,
                    "All Supported (*.img *.vhd *.vmdk *.qcow2 *.iso);;All Files (*)"
                )
                
                if file_path:
                    self.output_edit.setText(file_path)
                    self.config.last_output_dir = file_path
                    self.config.save()
                    
        except Exception as e:
            logger.error(f"Error in file browser: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open file dialog: {e}")

    def handle_start_imaging(self):
        """Start the disk imaging process."""
        try:
            # Validate inputs
            if not self.selected_disk:
                QMessageBox.critical(self, "Error", "No disk selected.")
                return
                
            output_path = self.output_edit.text().strip()
            if not output_path:
                QMessageBox.critical(self, "Error", "Please specify an output file.")
                return
                
            # Check if file exists
            output_file = Path(output_path)
            if output_file.exists():
                reply = QMessageBox.question(
                    self, "Overwrite?", 
                    f"File '{output_path}' exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Get settings
            image_format = self.format_combo.currentData()
            use_sparse = self.sparse_cb.isChecked()
            use_compress = self.compress_cb.isChecked()
            archive_after = self.archive_cb.isChecked()
            archive_type = self.archive_type_combo.currentText() if archive_after else None
            buffer_size = self.buffer_spin.value() * 1024 * 1024  # Convert MB to bytes
            cleanup_tools = self.cleanup_cb.isChecked()
            
            # Reset UI for imaging
            self.progress.setValue(0)
            self.progress.setMaximum(100)
            self.status_label.setPlainText("Imaging in progress...")
            self.start_btn.setEnabled(False)
            
            # Start imaging thread
            self.imaging_thread = ImagingThread(
                self.selected_disk, output_path, image_format,
                use_sparse, use_compress, archive_after, archive_type,
                buffer_size, cleanup_tools
            )
            
            self.imaging_thread.progress.connect(self.update_progress)
            self.imaging_thread.finished.connect(self.on_imaging_finished)
            self.imaging_thread.log.connect(self.append_log)
            self.imaging_thread.start()
            
        except Exception as e:
            logger.exception("Failed to start imaging")
            QMessageBox.critical(self, "Error", f"Failed to start imaging: {e}")
            self.start_btn.setEnabled(True)

    def update_progress(self, percent: float):
        """Update the progress bar."""
        try:
            value = int(max(0, min(100, percent)))
            self.progress.setValue(value)
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    def append_log(self, text: str):
        """Append text to the log display."""
        if text:
            self.status_label.append(text)

    def on_imaging_finished(self, success: bool, message: str):
        """Handle completion of imaging operation."""
        self.status_label.setPlainText(message)
        self.start_btn.setEnabled(True)
        
        if not success and 'Could not open' in message and 'PhysicalDrive' in message:
            self.status_label.append(
                "\nHint: The selected physical drive may not exist, is in use, "
                "or requires administrator privileges. Make sure the drive is "
                "present and not locked by another process."
            )


def run_pyqt_gui():
    """Run the PyQt6 GUI application."""
    try:
        # Check admin privileges first
        require_admin()
        
        app = QApplication(sys.argv)
        app.setApplicationName("DiskImage")
        app.setApplicationVersion("2.0")
        
        window = DiskImagerWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Failed to start GUI: {e}")
        
        # Show error to user if possible
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None, "Error", 
                f"Failed to start DiskImage GUI: {e}\n\n"
                "Make sure you have administrator privileges and all dependencies are installed."
            )
        except Exception:
            print(f"Fatal error: {e}", file=sys.stderr)
        
        sys.exit(1)


if __name__ == "__main__":
    run_pyqt_gui()
