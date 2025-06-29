# cklb_importer.py

import os
import shutil
from tkinter import filedialog, Tk
import logging

def import_cklb_files(target_dir="cklb_proc/usr_cklb_lib", on_import_complete=None, parent=None):
    os.makedirs(target_dir, exist_ok=True)

    # Use parent window if provided, otherwise create a temporary one
    if parent is None:
        root = Tk()
        root.withdraw()
        dialog_parent = root
    else:
        dialog_parent = parent

    # Start in user's home directory or current working directory
    initial_dir = os.path.expanduser("~")
    if not os.path.exists(initial_dir):
        initial_dir = os.getcwd()

    # Ask for CKLB files with better positioning
    file_paths = filedialog.askopenfilenames(
        parent=dialog_parent,
        title="Select CKLB Files to Import",
        filetypes=[("CKLB Files", "*.cklb"), ("All Files", "*.*")],
        initialdir=initial_dir
    )

    # Clean up temporary root if we created one
    if parent is None:
        root.destroy()

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