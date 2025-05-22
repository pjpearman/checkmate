import tkinter as tk
from tkinter import filedialog, messagebox
import yaml, json

def save_cklb_as(yaml_path_var):
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not path:
        return
    try:
        with open(yaml_path_var.get(), 'r') as f:
            data = yaml.safe_load(f)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Success", f"Saved baseline to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save: {e}")

def build_menu(root, yaml_path_var, on_closing):
    menu_bar = tk.Menu(root)

    # File Menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Open YAML...", command=lambda: yaml_path_var.set(
        filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
    ))
    file_menu.add_command(label="Save Baseline As...", command=lambda: save_cklb_as(yaml_path_var))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=on_closing)
    menu_bar.add_cascade(label="File", menu=file_menu)

    # Help Menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "CheckMate GUI\nVersion 2.0"))
    menu_bar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menu_bar)
