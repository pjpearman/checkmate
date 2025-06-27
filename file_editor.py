import tkinter as tk
from tkinter import ttk, scrolledtext
import os

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

    editor = tk.Toplevel(parent)
    center_window(editor, 700, 500)
    editor.title(f"Edit: {os.path.basename(file_path)}")
    editor.minsize(400, 300)
    editor.grab_set()

    # Main frame with grid layout
    main_frame = ttk.Frame(editor)
    main_frame.pack(fill="both", expand=True)
    main_frame.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # Scrollable text area
    text_box = scrolledtext.ScrolledText(main_frame, wrap="word", font=("Consolas", 11))
    text_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,0))
    text_box.insert("1.0", content)

    # Fixed button frame at the bottom
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(8, 12))
    button_frame.columnconfigure(0, weight=1)

    def save_file():
        try:
            new_content = text_box.get("1.0", "end").rstrip()
            with open(file_path, 'w') as f:
                f.write(new_content)
            # Inline success message (no popups)
            editor.destroy()
        except Exception as e:
            # Inline error handling (no popups)
            pass

    save_btn = ttk.Button(button_frame, text="Save", style="Accent.TButton", command=save_file)
    save_btn.pack(side="right")

def center_window(win, width=700, height=500):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = max((screen_width // 2) - (width // 2), 0)
    y = max((screen_height // 2) - (height // 2), 0)
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.minsize(400, 300)

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
