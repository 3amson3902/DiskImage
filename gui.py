import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from main import is_admin, list_disks, create_disk_image, create_disk_image_sparse, archive_image
import sys
import os
import logging
import datetime

class DiskImagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Disk Imager GUI")
        self.geometry("600x400")
        self.resizable(False, False)
        self.selected_disk = None
        self.output_path = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready.")
        logging.basicConfig(filename='diskimager_gui.log', level=logging.DEBUG, 
                            format='%(asctime)s %(levelname)s %(message)s')
        logging.debug('DiskImagerApp initialized')
        self.create_widgets()
        self.refresh_disks()

    def create_widgets(self):
        # Disk selection
        tk.Label(self, text="Select Disk:").pack(pady=(20, 0))
        self.disk_combo = ttk.Combobox(self, state="readonly", width=70)
        self.disk_combo.pack(pady=5)
        self.disk_combo.bind("<<ComboboxSelected>>", self.on_disk_selected)

        # Output file selection
        frame = tk.Frame(self)
        frame.pack(pady=10)
        tk.Label(frame, text="Output File:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.output_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)

        # Output format selection
        format_frame = tk.Frame(self)
        format_frame.pack(pady=5)
        tk.Label(format_frame, text="Image Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="img")
        format_options = [
            ("Raw (.img)", "img"),
            ("VHD (.vhd)", "vhd"),
            ("VMDK (.vmdk)", "vmdk"),
            ("QCOW2 (.qcow2)", "qcow2"),
            ("ISO (.iso)", "iso")
        ]
        self.format_menu = ttk.Combobox(format_frame, state="readonly", width=10, textvariable=self.format_var)
        self.format_menu['values'] = [opt[0] for opt in format_options]
        self.format_menu.current(0)
        self.format_menu.pack(side=tk.LEFT, padx=5)
        self.format_map = {opt[0]: opt[1] for opt in format_options}

        # Sparse imaging option
        self.sparse_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="Enable sparse imaging (faster for empty disks)", variable=self.sparse_var).pack(pady=2)

        # Compression option
        # If enabled, the backend will compress the output image:
        # - For raw (.img) and ISO (.iso), gzip is used (output is .img or .iso, but internally compressed)
        # - For qcow2/vmdk, qemu-img's -c option is used for built-in format compression
        # - If 'zip' or '7z' is selected, the final image will be archived after creation
        # Compression reduces file size but may slow down the imaging process
        self.compress_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Enable compression (smaller output, slower)", variable=self.compress_var).pack(pady=2)

        # Archive option
        self.archive_after_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Archive image after creation", variable=self.archive_after_var).pack(pady=2)
        self.archive_type_var = tk.StringVar(value="7z")  # Default to 7z
        archive_type_frame = tk.Frame(self)
        archive_type_frame.pack(pady=2)
        tk.Label(archive_type_frame, text="Archive type:").pack(side=tk.LEFT)
        archive_type_menu = ttk.Combobox(archive_type_frame, state="readonly", width=6, textvariable=self.archive_type_var)
        archive_type_menu['values'] = ["zip", "7z"]
        archive_type_menu.current(1)  # Set default to 7z
        archive_type_menu.pack(side=tk.LEFT, padx=5)

        # Buffer size option
        self.buffer_size_mb = tk.IntVar(value=64)
        buffer_frame = tk.Frame(self)
        buffer_frame.pack(pady=2)
        tk.Label(buffer_frame, text="Buffer size (MB):").pack(side=tk.LEFT)
        tk.Spinbox(buffer_frame, from_=1, to=1024, textvariable=self.buffer_size_mb, width=5).pack(side=tk.LEFT, padx=5)

        # Progress bar (modern style)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("custom.Horizontal.TProgressbar", troughcolor='#e0e0e0', bordercolor='#e0e0e0', background='#4caf50', lightcolor='#4caf50', darkcolor='#388e3c')
        self.progress = ttk.Progressbar(self, variable=self.progress_var, maximum=100, length=500, style="custom.Horizontal.TProgressbar")
        self.progress.pack(pady=10)

        # Status (modern label)
        status_frame = tk.Frame(self)
        status_frame.pack(pady=5)
        tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold"), fg="#333").pack()

        # Start button (modern style)
        self.start_btn = tk.Button(self, text="Start Imaging", command=self.start_imaging, bg="#1976d2", fg="white", font=("Segoe UI", 11, "bold"), activebackground="#1565c0", activeforeground="white", relief=tk.FLAT, padx=20, pady=5)
        self.start_btn.pack(pady=10)

        # Install/Update Python Packages button
        self.pip_btn = tk.Button(self, text="Install/Update Python Packages", command=self.install_packages, bg="#388e3c", fg="white", font=("Segoe UI", 10, "bold"), activebackground="#2e7d32", activeforeground="white", relief=tk.FLAT, padx=10, pady=3)
        self.pip_btn.pack(pady=5)

    def refresh_disks(self):
        logging.debug('Refreshing disk list')
        disks = list_disks()
        self.disks = disks
        if not disks:
            logging.warning('No disks found')
            self.disk_combo['values'] = ["No disks found"]
            self.disk_combo.current(0)
            self.start_btn.config(state=tk.DISABLED)
        else:
            self.disk_combo['values'] = [f"{d['name']} ({d['device_id']}) - {d['size']} - {d['model']}" for d in disks]
            self.disk_combo.current(0)
            self.selected_disk = disks[0]
            self.start_btn.config(state=tk.NORMAL)
        logging.debug(f'Disks found: {self.disks}')

    def on_disk_selected(self, event):
        idx = self.disk_combo.current()
        logging.debug(f'Disk selected index: {idx}')
        if 0 <= idx < len(self.disks):
            self.selected_disk = self.disks[idx]
            logging.info(f'Selected disk: {self.selected_disk}')

    def browse_file(self):
        ext_map = {"img": ".img", "vhd": ".vhd", "vmdk": ".vmdk", "qcow2": ".qcow2", "iso": ".iso"}
        fmt = self.format_map[self.format_menu.get()]
        default = f"{self.selected_disk['name']}_{datetime.datetime.now().strftime('%Y%m%d')}{ext_map.get(fmt, '.img')}" if self.selected_disk else "disk_image.img"
        path = filedialog.asksaveasfilename(defaultextension=ext_map.get(fmt, '.img'), initialfile=default, filetypes=[("All Supported", "*.img *.vhd *.vmdk *.qcow2 *.iso"), ("Raw Images", "*.img"), ("VHD", "*.vhd"), ("VMDK", "*.vmdk"), ("QCOW2", "*.qcow2"), ("ISO", "*.iso"), ("All Files", "*.*")])
        if path:
            logging.info(f'Output file selected: {path}')
            self.output_path.set(path)

    def start_imaging(self):
        logging.info('Start imaging button pressed')
        if not self.selected_disk:
            logging.error('No disk selected')
            messagebox.showerror("Error", "No disk selected.")
            return
        out_path = self.output_path.get().strip()
        if not out_path:
            logging.error('No output file specified')
            messagebox.showerror("Error", "Please specify an output file.")
            return
        if os.path.exists(out_path):
            if not messagebox.askyesno("Overwrite?", f"File '{out_path}' exists. Overwrite?"):
                logging.info('User declined to overwrite existing file')
                return
        image_format = self.format_map[self.format_menu.get()]
        use_sparse = self.sparse_var.get()
        use_compress = self.compress_var.get()
        archive_after = self.archive_after_var.get()
        archive_type = self.archive_type_var.get() if archive_after else None
        buffer_size = self.buffer_size_mb.get() * 1024 * 1024
        logging.debug(f'Imaging params: out_path={out_path}, format={image_format}, sparse={use_sparse}, compress={use_compress}, archive={archive_type}, buffer={buffer_size}')
        self.progress_var.set(0)
        self.status_var.set("Imaging in progress...")
        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.run_imaging, args=(out_path, image_format, use_sparse, use_compress, archive_after, archive_type, buffer_size), daemon=True).start()

    def run_imaging(self, out_path, image_format, use_sparse, use_compress, archive_after, archive_type, buffer_size):
        logging.info(f'Imaging started: {out_path}')
        total_size = self.get_disk_size(self.selected_disk)
        def progress_callback(bytes_read):
            if total_size > 0:
                percent = (bytes_read / total_size) * 100
                self.progress_var.set(percent)
                if int(percent) % 10 == 0:
                    logging.debug(f'Progress: {percent:.2f}%')
        try:
            if use_sparse and image_format in ("qcow2", "vhd", "vmdk"):
                success, error = create_disk_image_sparse(self.selected_disk, out_path, image_format, use_compress)
            else:
                success, error = create_disk_image(self.selected_disk, out_path, progress_callback, image_format, use_compress, buffer_size)
            if success and archive_after and archive_type:
                self.status_var.set("Archiving...")
                logging.info('Archiving image')
                arch_success, arch_error = archive_image(out_path, archive_type)
                if arch_success:
                    self.status_var.set(f"Imaging and archiving complete: {arch_success}")
                    logging.info(f'Archiving complete: {arch_success}')
                else:
                    self.status_var.set(f"Imaging complete, but archive failed: {arch_error}")
                    logging.error(f'Archive failed: {arch_error}')
            elif success:
                self.status_var.set("Imaging complete.")
                logging.info('Imaging complete')
            else:
                self.status_var.set(f"Error: {error}")
                logging.error(f'Imaging failed: {error}')
        except Exception as e:
            self.status_var.set(f"Exception: {e}")
            logging.exception('Exception during imaging')
        self.start_btn.config(state=tk.NORMAL)

    def get_disk_size(self, disk):
        try:
            size_str = disk['size'].split()[0]
            return float(size_str) * (1024**3)
        except Exception as e:
            logging.error(f'Failed to get disk size: {e}')
            return 0

    def install_packages(self):
        """Install or update Python packages using pip and requirements.txt."""
        import subprocess
        import sys
        req_path = os.path.join(os.path.dirname(sys.executable), '..', 'requirements.txt')
        req_path = os.path.abspath(req_path)
        python_exe = sys.executable
        pip_cmd = [python_exe, '-m', 'pip', 'install', '--upgrade', '-r', req_path]
        try:
            result = subprocess.run(pip_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Success", f"Packages installed/updated successfully.\n\n{result.stdout}")
            else:
                messagebox.showerror("Error", f"pip failed:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Exception running pip:\n{e}")

def run_gui():
    if not is_admin():
        tk.Tk().withdraw()
        messagebox.showerror("Error", "This script requires administrator privileges. Run as administrator.")
        sys.exit(1)
    app = DiskImagerApp()
    app.mainloop()

if __name__ == "__main__":
    run_gui()
