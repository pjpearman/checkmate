#!/usr/bin/env python3
"""
Test script for the DISA fetch dialog improvements
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to path to import from gui.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock some required variables and functions from gui.py
COLORS = {
    'bg_primary': '#f8f9fa',
    'bg_secondary': '#ffffff',
    'accent': '#3498db',
    'text_secondary': '#7f8c8d',
}

FONTS = {
    'default': ('Inter', 9),
    'heading': ('Inter', 11, 'bold'),
}

ICONS = {
    'download': '⬇',
    'check': '✓',
}

def log_job_status(message):
    print(f"LOG: {message}")

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

def show_download_choice_dialog(selected_items):
    """Show a professional dialog to choose between ZIP download or CKLB creation"""
    choice_popup = tk.Toplevel(root)
    choice_popup.title("Choose Download Option")
    choice_popup.configure(bg=COLORS['bg_primary'])
    choice_popup.transient(root)
    choice_popup.grab_set()
    choice_popup.resizable(False, False)
    
    # Center the popup on the main window
    center_window_on_parent(choice_popup, root, 500, 300)
    
    # Main content frame
    main_frame = ttk.Frame(choice_popup)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    
    ttk.Label(header_frame, text="Select Download Format", 
              font=FONTS['heading']).pack()
    ttk.Label(header_frame, text=f"Processing {len(selected_items)} selected STIG(s)", 
              font=FONTS['default'], foreground=COLORS['text_secondary']).pack(pady=(5, 0))
    
    # Options frame
    options_frame = ttk.Frame(main_frame)
    options_frame.pack(fill="x", pady=(0, 20))
    
    # ZIP Download option
    zip_frame = ttk.Frame(options_frame, relief="raised", borderwidth=1)
    zip_frame.pack(fill="x", pady=(0, 10))
    
    zip_content = ttk.Frame(zip_frame)
    zip_content.pack(fill="x", padx=15, pady=15)
    
    ttk.Label(zip_content, text=f"{ICONS['download']} Download ZIP Files Only", 
              font=FONTS['heading']).pack(anchor="w")
    ttk.Label(zip_content, text="Download the raw STIG ZIP files without processing", 
              font=FONTS['default'], foreground=COLORS['text_secondary']).pack(anchor="w", pady=(5, 0))
    
    # CKLB option
    cklb_frame = ttk.Frame(options_frame, relief="raised", borderwidth=1)
    cklb_frame.pack(fill="x")
    
    cklb_content = ttk.Frame(cklb_frame)
    cklb_content.pack(fill="x", padx=15, pady=15)
    
    ttk.Label(cklb_content, text=f"{ICONS['check']} Create CKLB Files", 
              font=FONTS['heading']).pack(anchor="w")
    ttk.Label(cklb_content, text="Download ZIPs, extract XCCDF files, and generate CKLB checklists", 
              font=FONTS['default'], foreground=COLORS['text_secondary']).pack(anchor="w", pady=(5, 0))
    
    # Buttons frame
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=(10, 0))
    
    def choose_zip():
        choice_popup.destroy()
        log_job_status("User chose: Download ZIP files only")
    
    def choose_cklb():
        choice_popup.destroy()
        log_job_status("User chose: Create CKLB files")
    
    ttk.Button(btn_frame, text="Cancel", command=choice_popup.destroy).pack(side="left")
    
    ttk.Button(btn_frame, text=f"{ICONS['download']} Download ZIPs", 
               command=choose_zip).pack(side="right", padx=(10, 0))
    
    ttk.Button(btn_frame, text=f"{ICONS['check']} Create CKLBs", 
               command=choose_cklb).pack(side="right", padx=(10, 0))

# Test the dialog
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - CheckMate Dialog")
    root.geometry("800x600")
    root.configure(bg=COLORS['bg_primary'])
    
    # Test button
    def test_dialog():
        # Mock selected items
        mock_items = [
            {"Product": "Test STIG 1", "Version": "1", "Release": "1"},
            {"Product": "Test STIG 2", "Version": "2", "Release": "1"},
        ]
        show_download_choice_dialog(mock_items)
    
    test_btn = ttk.Button(root, text="Test Choice Dialog", command=test_dialog)
    test_btn.pack(pady=50)
    
    ttk.Label(root, text="Click the button above to test the new choice dialog", 
              font=FONTS['default']).pack()
    
    root.mainloop()
