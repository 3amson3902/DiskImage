"""
gui/pyqt_app.py - PyQt6 GUI entry point for DiskImage
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QProgressBar, QFileDialog, QCheckBox, QMessageBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import logging
import datetime
from backend.disk_ops import create_disk_image
from backend.qemu_utils import create_disk_image_sparse
from backend.archive_utils import archive_image
from backend.admin_utils import is_admin
from backend.disk_list_utils import list_disks
from backend.config_utils import load_config, save_config, update_config

class ImagingThread(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)  # New signal for log/output

    def __init__(self, disk, out_path, image_format, use_sparse, use_compress, archive_after, archive_type, buffer_size, cleanup_tools):
        super().__init__()
        self.disk = disk
        self.out_path = out_path
        self.image_format = image_format
        self.use_sparse = use_sparse
        self.use_compress = use_compress
        self.archive_after = archive_after
        self.archive_type = archive_type
        self.buffer_size = buffer_size
        self.cleanup_tools = cleanup_tools

    def run(self):
        total_size = self.get_disk_size(self.disk)
        def progress_callback(bytes_read):
            if total_size > 0:
                percent = (bytes_read / total_size) * 100
                self.progress.emit(percent)
        try:
            import io
            import contextlib
            log_buffer = io.StringIO()
            with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
                if self.use_sparse and self.image_format in ("qcow2", "vhd", "vmdk"):
                    success, error = create_disk_image_sparse(self.disk, self.out_path, self.image_format, self.use_compress, cleanup_tools=self.cleanup_tools)
                else:
                    success, error = create_disk_image(self.disk, self.out_path, progress_callback, self.image_format, self.use_compress, self.buffer_size, cleanup_tools=self.cleanup_tools)
                if success and self.archive_after and self.archive_type:
                    arch_success, arch_error = archive_image(self.out_path, self.archive_type, cleanup_tools=self.cleanup_tools)
                    if arch_success:
                        self.finished.emit(True, f"Imaging and archiving complete: {arch_success}")
                    else:
                        self.finished.emit(False, f"Imaging complete, but archive failed: {arch_error}")
                elif success:
                    self.finished.emit(True, "Imaging complete.")
                else:
                    self.finished.emit(False, f"Error: {error}")
            # Emit all captured output to the log signal
            self.log.emit(log_buffer.getvalue())
        except Exception as e:
            import traceback
            self.log.emit(traceback.format_exc())
            self.finished.emit(False, f"Exception: {e}")

    def get_disk_size(self, disk):
        try:
            size_str = disk['size'].split()[0]
            return float(size_str) * (1024**3)
        except Exception:
            return 0

class DiskImagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setWindowTitle("Disk Imager (PyQt6)")
        w, h = self.config.get("window_size", [600, 350])
        self.setGeometry(100, 100, w, h)
        self.selected_disk = None
        self.init_ui()
        self.refresh_disks()
        # Restore preferences
        self.restore_preferences()

    def init_ui(self):
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
        # Format
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Image Format:"))
        self.format_combo = QComboBox()
        self.format_map = {"Raw (.img)": "img", "VHD (.vhd)": "vhd", "VMDK (.vmdk)": "vmdk", "QCOW2 (.qcow2)": "qcow2", "ISO (.iso)": "iso"}
        for label in self.format_map:
            self.format_combo.addItem(label)
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
        self.buffer_spin.setValue(64)
        buf_layout.addWidget(self.buffer_spin)
        layout.addLayout(buf_layout)
        self.cleanup_cb = QCheckBox("Cleanup extracted tools after imaging (QEMU/7-Zip)")
        self.cleanup_cb.setChecked(True)
        layout.addWidget(self.cleanup_cb)
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        # Status (replace QLabel with QTextEdit for copyable text)
        self.status_label = QTextEdit("Ready.")
        self.status_label.setReadOnly(True)
        self.status_label.setMaximumHeight(120)
        layout.addWidget(self.status_label)
        # Start
        self.start_btn = QPushButton("Start Imaging")
        self.start_btn.clicked.connect(self.start_imaging)
        layout.addWidget(self.start_btn)
        central.setLayout(layout)

    def restore_preferences(self):
        # Output dir
        if self.config.get("last_output_dir"):
            self.output_edit.setText(self.config["last_output_dir"])
        # Cleanup tools
        self.cleanup_cb.setChecked(self.config.get("cleanup_tools", True))
        # Window size
        if self.config.get("window_size"):
            w, h = self.config["window_size"]
            self.resize(w, h)
        # Theme and other prefs can be restored here

    def closeEvent(self, event):
        # Save preferences on close
        self.config["cleanup_tools"] = self.cleanup_cb.isChecked()
        self.config["last_output_dir"] = self.output_edit.text().strip()
        self.config["window_size"] = [self.width(), self.height()]
        save_config(self.config)
        event.accept()

    def refresh_disks(self):
        disks = list_disks()
        self.disks = disks
        self.disk_combo.clear()
        if not disks:
            self.disk_combo.addItem("No disks found")
            self.start_btn.setEnabled(False)
        else:
            for d in disks:
                self.disk_combo.addItem(f"{d['name']} ({d['device_id']}) - {d['size']} - {d['model']}")
            self.selected_disk = disks[0]
            self.start_btn.setEnabled(True)

    def on_disk_selected(self, idx):
        if 0 <= idx < len(self.disks):
            self.selected_disk = self.disks[idx]

    def browse_file(self):
        fmt = self.format_map[self.format_combo.currentText()]
        default = f"{self.selected_disk['name']}_{datetime.datetime.now().strftime('%Y%m%d')}.{fmt}"
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", default, "All Supported (*.img *.vhd *.vmdk *.qcow2 *.iso);;All Files (*)")
        if path:
            self.output_edit.setText(path)
            # Save last output dir
            self.config["last_output_dir"] = path
            save_config(self.config)

    def start_imaging(self):
        if not self.selected_disk:
            QMessageBox.critical(self, "Error", "No disk selected.")
            return
        out_path = self.output_edit.text().strip()
        if not out_path:
            QMessageBox.critical(self, "Error", "Please specify an output file.")
            return
        if os.path.exists(out_path):
            ret = QMessageBox.question(self, "Overwrite?", f"File '{out_path}' exists. Overwrite?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes:
                return
        image_format = self.format_map[self.format_combo.currentText()]
        use_sparse = self.sparse_cb.isChecked()
        use_compress = self.compress_cb.isChecked()
        archive_after = self.archive_cb.isChecked()
        archive_type = self.archive_type_combo.currentText() if archive_after else None
        buffer_size = self.buffer_spin.value() * 1024 * 1024
        cleanup_tools = self.cleanup_cb.isChecked()
        self.progress.setValue(0)
        self.status_label.setPlainText("Imaging in progress...")
        self.start_btn.setEnabled(False)
        self.thread = ImagingThread(self.selected_disk, out_path, image_format, use_sparse, use_compress, archive_after, archive_type, buffer_size, cleanup_tools)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_imaging_finished)
        self.thread.log.connect(self.append_log)  # Connect log signal
        self.thread.start()

    def append_log(self, text):
        if text:
            self.status_label.append(text)

    def on_imaging_finished(self, success, message):
        self.status_label.setPlainText(message)
        self.start_btn.setEnabled(True)
        # If error is about missing physical drive, show a user-friendly hint
        if not success and 'Could not open' in message and 'PhysicalDrive' in message:
            self.status_label.append("\nHint: The selected physical drive may not exist, is in use, or requires administrator privileges. Make sure the drive is present and not locked by another process.")


def run_pyqt_gui():
    if not is_admin():
        QMessageBox.critical(None, "Error", "This script requires administrator privileges. Run as administrator.")
        sys.exit(1)
    app = QApplication(sys.argv)
    win = DiskImagerWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_pyqt_gui()
