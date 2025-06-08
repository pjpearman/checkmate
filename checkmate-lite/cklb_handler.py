import os
import shutil

def import_cklbs(selected_files, dest_dir=None):
    """
    Import one or more CKLB files into the specified destination directory.
    If dest_dir is None, defaults to 'user_docs/cklb_artifacts'.
    Returns a list of (filename, status) tuples.
    """
    if dest_dir is None:
        dest_dir = os.path.join("user_docs", "cklb_artifacts")
    os.makedirs(dest_dir, exist_ok=True)
    results = []
    for file_path in selected_files:
        if not os.path.isfile(file_path):
            results.append((file_path, "File not found"))
            continue
        dest_path = os.path.join(dest_dir, os.path.basename(file_path))
        try:
            shutil.copy2(file_path, dest_path)
            results.append((file_path, "Imported"))
        except Exception as e:
            results.append((file_path, f"Error: {e}"))
    return results
