import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os

def launch_file_editor(file_path, parent):
    if not file_path or not os.path.exists(file_path):
        messagebox.showerror("File Error", "Please select a valid file.", parent=parent)
        return

    # Load file content as plain text
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        messagebox.showerror("Load Error", f"Failed to read file:\n{e}", parent=parent)
        return

    editor = tk.Toplevel(parent)
    editor.title(f"Edit: {os.path.basename(file_path)}")
    editor.geometry("700x500")
    editor.grab_set()

    text_box = scrolledtext.ScrolledText(editor, wrap="word", font=("Consolas", 11))
    text_box.pack(fill="both", expand=True, padx=10, pady=10)
    text_box.insert("1.0", content)

    def save_file():
        try:
            new_content = text_box.get("1.0", "end").rstrip()
            with open(file_path, 'w') as f:
                f.write(new_content)
            messagebox.showinfo("Success", "File saved successfully.", parent=editor)
            editor.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file:\n{e}", parent=editor)

    ttk.Button(editor, text="Save", style="Accent.TButton", command=save_file).pack(pady=(0, 12))

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
