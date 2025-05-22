import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yaml
import os

def launch_file_editor(baseline_path, parent):
    if not baseline_path or not os.path.exists(baseline_path):
        messagebox.showerror("File Error", "Please select a valid Baseline YAML file.", parent=parent)
        return

    # Load YAML content
    try:
        with open(baseline_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to read YAML file:\n{e}", parent=parent)
        return

    editor = tk.Toplevel(parent)
    editor.title("Edit Baseline")
    editor.geometry("700x500")
    editor.grab_set()

    text_box = scrolledtext.ScrolledText(editor, wrap="word", font=("Consolas", 11))
    text_box.pack(fill="both", expand=True, padx=10, pady=10)
    text_box.insert("1.0", yaml.dump(data, sort_keys=False))

    def save_baseline():
        try:
            new_data = yaml.safe_load(text_box.get("1.0", "end").strip())
            if not isinstance(new_data, dict):
                raise ValueError("YAML must be a dictionary at top-level.")
            # Optional: schema validation can go here
            with open(baseline_path, 'w') as f:
                yaml.dump(new_data, f, sort_keys=False)
            messagebox.showinfo("Success", "Baseline saved successfully.", parent=editor)
            editor.destroy()
        except Exception as e:
            messagebox.showerror("Validation Error", f"Invalid YAML or schema:\n{e}", parent=editor)

    ttk.Button(editor, text="Save", style="Accent.TButton", command=save_baseline).pack(pady=(0, 12))
