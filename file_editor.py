import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

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

def launch_file_editor(file_path, parent):
    if not file_path or not os.path.exists(file_path):
        # Inline error handling (no popups)
        return

    # Load file content as plain text
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        # Inline error handling (no popups)
        return

    # Configure styles for the editor window
    style = ttk.Style()
    style.configure("Accent.TButton",
        foreground="#ffffff",
        background="#3498db",
        borderwidth=0,
        focuscolor='none',
        padding=[10, 6])
    style.configure("Secondary.TButton",
        foreground="#2c3e50",
        background="#ffffff",
        borderwidth=1,
        relief="solid",
        focuscolor='none',
        padding=[10, 6])

    editor = tk.Toplevel(parent)
    center_window_on_parent(editor, parent, 700, 500)
    editor.title(f"Edit: {os.path.basename(file_path)}")
    editor.minsize(400, 300)
    editor.grab_set()

    # Track if changes have been made
    has_changes = tk.BooleanVar(value=False)
    original_content = content

    # Main frame with grid layout
    main_frame = ttk.Frame(editor)
    main_frame.pack(fill="both", expand=True)
    main_frame.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # Scrollable text area
    text_box = scrolledtext.ScrolledText(main_frame, wrap="word", font=("Consolas", 11))
    text_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,0))
    text_box.insert("1.0", content)

    # Track changes in the text widget
    def on_text_change(event=None):
        current_content = text_box.get("1.0", "end").rstrip()
        has_changes.set(current_content != original_content)
        # Update window title to show unsaved changes
        if has_changes.get():
            editor.title(f"Edit: {os.path.basename(file_path)} *")
        else:
            editor.title(f"Edit: {os.path.basename(file_path)}")

    # Bind text change events
    text_box.bind('<KeyPress>', on_text_change)
    text_box.bind('<KeyRelease>', on_text_change)
    text_box.bind('<Button-1>', on_text_change)
    text_box.bind('<ButtonRelease-1>', on_text_change)

    # Fixed button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(8, 12))
    button_frame.columnconfigure(0, weight=1)

    def save_file():
        try:
            new_content = text_box.get("1.0", "end").rstrip()
            with open(file_path, 'w') as f:
                f.write(new_content)
            # Reset change tracking
            has_changes.set(False)
            editor.title(f"Edit: {os.path.basename(file_path)}")
            editor.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}", parent=editor)

    def cancel_edit():
        if has_changes.get():
            # Ask user to confirm if there are unsaved changes
            result = messagebox.askyesnocancel(
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save before closing?",
                parent=editor
            )
            if result is True:  # Yes - save first
                save_file()
                return
            elif result is None:  # Cancel - don't close
                return
            # No - close without saving (result is False)
        editor.destroy()

    def on_window_close():
        cancel_edit()

    # Set up window close protocol
    editor.protocol("WM_DELETE_WINDOW", on_window_close)

    # Add both Save and Cancel buttons
    cancel_btn = ttk.Button(button_frame, text="Cancel", style="Secondary.TButton", command=cancel_edit)
    cancel_btn.pack(side="right", padx=(0, 10))
    
    save_btn = ttk.Button(button_frame, text="Save", style="Accent.TButton", command=save_file)
    save_btn.pack(side="right")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 file_editor.py <file_path>")
        return
    file_path = sys.argv[1]
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    launch_file_editor(file_path, root)
    root.mainloop()

if __name__ == "__main__":
    main()
