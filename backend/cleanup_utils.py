import os
import shutil

def cleanup_qemu_files():
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools', 'qemu')
    if os.path.exists(tools_dir):
        for fname in os.listdir(tools_dir):
            fpath = os.path.join(tools_dir, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception:
                pass
