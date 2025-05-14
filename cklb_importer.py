# cklb_importer.py

import os
import shutil
from tkinter import filedialog, Tk
import logging

def import_cklb_files(target_dir="cklb_proc/usr_cklb_lib", on_import_complete=None):
    os.makedirs(target_dir, exist_ok=True)

    # Suppress main tkinter window
    root = Tk()
    root.withdraw()

    # Ask for CKLB files
    file_paths = filedialog.askopenfilenames(
        title="Select CKLB Files",
        filetypes=[("CKLB Files", "*.cklb")]
    )

    if not file_paths:
        logging.info("No files selected.")
        return

    for path in file_paths:
        if not path.lower().endswith(".cklb"):
            logging.warning(f"Skipped invalid file: {path}")
            continue
        try:
            dest = os.path.join(target_dir, os.path.basename(path))
            shutil.copy2(path, dest)
            logging.info(f"Imported: {dest}")
        except Exception as e:
            logging.error(f"Failed to copy {path}: {e}")
    
    if on_import_complete:
        on_import_complete()