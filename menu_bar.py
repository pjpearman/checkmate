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

    # Populate listbox with files and directories
    current_dir = [dir_path]  # Use a list to allow modification in nested functions
    def populate_listbox(path):
        listbox.delete(0, END)  # Clear current listbox content
        # Add parent directory navigation if not root
        if os.path.abspath(path) != os.path.abspath(os.sep):
            listbox.insert(END, "..")
        # Add directories (with trailing slash)
        try:
            entries = os.listdir(path)
            dirs = [d for d in entries if os.path.isdir(os.path.join(path, d))]
            files = [f for f in entries if os.path.isfile(os.path.join(path, f))]
            for d in sorted(dirs, key=lambda e: e.lower()):
                listbox.insert(END, d + "/")
            for f in sorted(files, key=lambda e: e.lower()):
                listbox.insert(END, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list directory {path}: {e}", parent=win)
        # Always keep the cursor visible
        if listbox.size() > 0:
            listbox.selection_clear(0, END)
            listbox.see(0)

    populate_listbox(current_dir[0])

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
                if fname == ".." or fname.endswith("/"):
                    continue  # Don't delete parent nav or directories here
                try:
                    path_to_remove = os.path.join(current_dir[0], fname)
                    os.remove(path_to_remove)  # Remove file
                    listbox.delete(idx)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {fname}: {e}", parent=win)

    def edit_selected():
        sel = list(listbox.curselection())
        if not sel:
            messagebox.showwarning("No selection", "Select a file to edit.", parent=win)
            return
        fname = listbox.get(sel[0])
        if fname == ".." or fname.endswith("/"):
            messagebox.showwarning("Invalid Selection", "Please select a file (not a directory) to edit.", parent=win)
            return
        file_path = os.path.join(current_dir[0], fname)
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

    def on_double_click(event):
        sel = list(listbox.curselection())
        if not sel:
            return
        fname = listbox.get(sel[0])
        if fname == "..":
            parent_dir = os.path.dirname(current_dir[0])
            current_dir[0] = parent_dir
            populate_listbox(current_dir[0])
            win.title(f"Files in {os.path.basename(current_dir[0])}")
        elif fname.endswith("/"):
            new_dir = os.path.join(current_dir[0], fname[:-1])
            current_dir[0] = new_dir
            populate_listbox(current_dir[0])
            win.title(f"Files in {os.path.basename(current_dir[0])}")
        # else: do nothing (file)

    def cancel():
        win.destroy()

    # Bind double-click event
    listbox.bind("<Double-Button-1>", on_double_click)

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
