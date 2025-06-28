import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Frame, Listbox, Scrollbar, Button, MULTIPLE, END
import yaml, json
import os
import subprocess

def center_window_on_parent(window, parent, width=700, height=500):
    """Center a window relative to its parent window instead of the screen."""
    window.update_idletasks()
    
    # Get parent window position and size
    parent.update_idletasks()
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    
    # Calculate position to center on parent
    x = parent_x + (parent_width // 2) - (width // 2)
    y = parent_y + (parent_height // 2) - (height // 2)
    
    # Ensure the window stays on screen
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))
    
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(400, 300)

def open_directory_frame(parent, dir_path, editor_cmd):
    # Create a new window
    win = Toplevel(parent)
    center_window_on_parent(win, parent, 700, 500)
    win.title(f"Files in {os.path.basename(dir_path)}")
    win.minsize(400, 300)
    win.grab_set()  # Make window modal
    frame = Frame(win)
    frame.pack(fill='both', expand=True)

    # Scrollable listbox
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side='right', fill='y')
    listbox = Listbox(frame, selectmode=MULTIPLE, yscrollcommand=scrollbar.set, width=60)
    listbox.pack(side='left', fill='both', expand=True)
    scrollbar.config(command=listbox.yview)

    # Populate listbox
    files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    for f in files:
        listbox.insert(END, f)

    # Button actions
    def delete_selected():
        sel = list(listbox.curselection())
        if not sel:
            messagebox.showwarning("No selection", "Select files to delete.", parent=win)
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(sel)} file(s)?", parent=win)
        if confirm:
            for idx in reversed(sel):
                fname = listbox.get(idx)
                try:
                    os.remove(os.path.join(dir_path, fname))
                    listbox.delete(idx)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {fname}: {e}", parent=win)

    def edit_selected():
        sel = list(listbox.curselection())
        if not sel:
            messagebox.showwarning("No selection", "Select a file to edit.", parent=win)
            return
        # Only allow editing one file at a time
        fname = listbox.get(sel[0])
        file_path = os.path.join(dir_path, fname)
        cmd = ["python3", editor_cmd, file_path]
        cwd = os.path.dirname(os.path.abspath(__file__))
        try:
            proc = subprocess.Popen(cmd, cwd=cwd)
            import time
            time.sleep(0.5)
            if proc.poll() is not None:
                messagebox.showerror("Error", f"Editor process exited immediately.\nCommand: {cmd}\nCheck if file_editor.py runs standalone.", parent=win)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open editor: {e}\nCommand: {cmd}", parent=win)
        win.destroy()

    def cancel():
        win.destroy()

    # Buttons
    btn_frame = Frame(win)
    btn_frame.pack(fill='x', pady=5)
    Button(btn_frame, text="Delete", command=delete_selected).pack(side='left', padx=5)
    Button(btn_frame, text="Edit", command=edit_selected).pack(side='left', padx=5)
    Button(btn_frame, text="Cancel", command=cancel).pack(side='right', padx=5)

def build_menu(root, yaml_path_var, on_closing):
    menu_bar = tk.Menu(root)

    # File Menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Open Baseline Directory", command=lambda: open_directory_frame(root, "baselines", "file_editor.py"))
    file_menu.add_command(label="Open My Checklist Library", command=lambda: open_directory_frame(root, "cklb_proc/usr_cklb_lib", "file_editor.py"))
    file_menu.add_command(label="Open New CKLB Version Directory", command=lambda: open_directory_frame(root, "cklb_proc/cklb_lib", "file_editor.py"))
    file_menu.add_command(label="Open XCCDF Library", command=lambda: open_directory_frame(root, "cklb_proc/xccdf_lib", "file_editor.py"))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=on_closing)
    menu_bar.add_cascade(label="File", menu=file_menu)

    # Help Menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "CheckMate GUI\nVersion 2.0", parent=root))
    menu_bar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menu_bar)
