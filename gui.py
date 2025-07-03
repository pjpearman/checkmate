import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import logging
import os
import yaml
import sys
import threading
import json

# === GUI Setup and Variables (must be at the top) ===
def on_closing():
    try:
        root.destroy()
    except Exception:
        pass
    sys.exit(0)

root = tk.Tk()
root.lift()
root.attributes('-topmost', True)
root.title("CheckMate")
root.resizable(True, True)
root.configure(bg="#1e1e1e")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Responsive window with better defaults
root.geometry("1000x700")
root.minsize(800, 500)

# Variables
mode_var = tk.StringVar(value="Operating Systems")
yaml_path_var = tk.StringVar()
status_text = tk.StringVar(value="Ready")
download_var = tk.BooleanVar()
extract_var = tk.BooleanVar()

usr_dir  = os.path.join(os.getcwd(), 'cklb_proc', 'user_cklb_library')
cklb_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_lib')

# Ensure directories exist
os.makedirs(usr_dir, exist_ok=True)
os.makedirs(cklb_dir, exist_ok=True)

usr_files  = sorted([f for f in os.listdir(usr_dir) if f.lower().endswith('.cklb')])  if os.path.isdir(usr_dir)  else []
cklb_files = sorted([f for f in os.listdir(cklb_dir) if f.lower().endswith('.cklb')]) if os.path.isdir(cklb_dir) else []

usr_sel_var  = tk.StringVar()
cklb_sel_var = tk.StringVar()

from handlers import run_compare_task, run_merge_task
from selected_merger import load_cklb, save_cklb, check_stig_id_match
from file_editor import launch_file_editor
from menu_bar import build_menu

# === Professional Color Scheme ===
COLORS = {
    'bg_primary': '#f8f9fa',      # Light gray background
    'bg_secondary': '#ffffff',     # White for cards
    'bg_dark': '#2c3e50',         # Dark header/footer
    'accent': '#3498db',          # Professional blue
    'accent_hover': '#2980b9',    # Darker blue for hover
    'success': '#27ae60',         # Green
    'warning': '#f39c12',         # Orange
    'danger': '#e74c3c',          # Red
    'text_primary': '#2c3e50',    # Dark gray text
    'text_secondary': '#7f8c8d',  # Medium gray text
    'border': '#e0e0e0',          # Light border
    'input_bg': '#f5f6fa'         # Input background
}

# === Modern Font Configuration ===
FONTS = {
    'default': ('Inter', 9),
    'heading': ('Inter', 11, 'bold'),
    'small': ('Inter', 8),
    'mono': ('Consolas', 9)
}

# === Icon Dictionary (Unicode) ===
ICONS = {
    'play': '▶',
    'reset': '↺',
    'edit': '✎',
    'import': '📥',
    'run': '🚀',
    'update': '🔄',
    'folder': '📁',
    'download': '⬇',
    'check': '✓',
    'settings': '⚙',
    'info': 'ℹ',
    'log': '📋'
}

# === Logger ===
class GuiLogger(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Use after_idle to ensure thread safety
        self.text_widget.after_idle(self._update_log, msg)
    
    def _update_log(self, msg):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

# === Style Configuration ===
style = ttk.Style()
style.theme_use("clam")

# Configure ttk styles with professional theme
style.configure("TNotebook", background=COLORS['bg_primary'], borderwidth=0)
style.configure("TNotebook.Tab", 
    padding=[20, 10], 
    background=COLORS['bg_secondary'],
    foreground=COLORS['text_primary'],
    borderwidth=0,
    font=FONTS['default'])
style.map("TNotebook.Tab",
    background=[('selected', COLORS['accent']), ('active', COLORS['bg_primary'])],
    foreground=[('selected', '#ffffff'), ('active', COLORS['text_primary'])])

style.configure("Card.TFrame", background=COLORS['bg_secondary'], relief="flat", borderwidth=1)
style.configure("TLabelframe", 
    background=COLORS['bg_secondary'], 
    foreground=COLORS['text_primary'],
    borderwidth=1,
    relief="groove")
style.configure("TLabelframe.Label", 
    font=FONTS['heading'], 
    background=COLORS['bg_secondary'],
    foreground=COLORS['text_primary'],
    padding=[5, 2])

# Button styles
style.configure("Accent.TButton",
    font=FONTS['default'],
    foreground="#ffffff",
    background=COLORS['accent'],
    borderwidth=0,
    focuscolor='none',
    padding=[12, 8])
style.map("Accent.TButton",
    background=[('active', COLORS['accent_hover']), ('pressed', COLORS['accent_hover'])])

style.configure("Secondary.TButton",
    font=FONTS['default'],
    foreground=COLORS['text_primary'],
    background=COLORS['bg_secondary'],
    borderwidth=1,
    relief="solid",
    focuscolor='none',
    padding=[12, 8])

# Entry and Combobox styles
style.configure("Modern.TEntry",
    fieldbackground=COLORS['input_bg'],
    borderwidth=1,
    relief="solid",
    font=FONTS['default'])
style.configure("Modern.TCombobox",
    fieldbackground=COLORS['input_bg'],
    borderwidth=1,
    relief="solid",
    font=FONTS['default'])
style.configure("Modern.TCheckbutton",
    background=COLORS['bg_secondary'],
    foreground=COLORS['text_primary'],
    font=FONTS['default'])

# === Helper Functions ===
class ProgressPopup:
    """A popup window that shows progress for long-running background tasks."""
    
    def __init__(self, parent, title="Processing...", message="Please wait while the task completes."):
        self.parent = parent
        self.popup = None
        self.start_time = None
        self.timer_label = None
        self.progress_var = None
        self.is_running = False
        
        self.create_popup(title, message)
    
    def create_popup(self, title, message):
        """Create and display the progress popup."""
        self.popup = tk.Toplevel(self.parent)
        self.popup.title(title)
        center_window_on_parent(self.popup, self.parent, 400, 200)
        self.popup.configure(bg=COLORS['bg_primary'])
        self.popup.grab_set()  # Make modal
        self.popup.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
        
        # Main frame
        main_frame = ttk.Frame(self.popup, style="Card.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Spinning icon (using rotating characters)
        self.icon_label = ttk.Label(header_frame, text="⏳", font=('Inter', 16))
        self.icon_label.pack(side="left", padx=(0, 10))
        
        ttk.Label(header_frame, text=title, font=FONTS['heading']).pack(side="left")
        
        # Message
        ttk.Label(main_frame, text=message, font=FONTS['default'], 
                 wraplength=300, justify="center").pack(pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        progress_bar.pack(pady=(0, 15))
        progress_bar.start(10)  # Start animation
        
        # Timer display
        timer_frame = ttk.Frame(main_frame)
        timer_frame.pack(fill="x")
        
        ttk.Label(timer_frame, text="Elapsed time:", font=FONTS['small']).pack(side="left")
        self.timer_label = ttk.Label(timer_frame, text="00:00", font=FONTS['mono'], 
                                   foreground=COLORS['accent'])
        self.timer_label.pack(side="right")
        
        # Status text
        self.status_label = ttk.Label(main_frame, text="Initializing...", 
                                    font=FONTS['small'], foreground=COLORS['text_secondary'])
        self.status_label.pack(pady=(10, 0))
        
        # Start the timer
        self.start_time = threading.Lock()
        self.is_running = True
        self.start_timer()
        self.animate_icon()
    
    def start_timer(self):
        """Start the elapsed time timer."""
        import time
        self.start_time = time.time()
        self.update_timer()
    
    def update_timer(self):
        """Update the elapsed time display."""
        if not self.is_running or not self.popup.winfo_exists():
            return
            
        try:
            import time
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.configure(text=time_str)
            
            # Schedule next update
            self.popup.after(1000, self.update_timer)
        except:
            pass
    
    def animate_icon(self):
        """Animate the progress icon."""
        if not self.is_running or not self.popup.winfo_exists():
            return
            
        try:
            # Cycle through different clock icons
            icons = ["⏳", "⌛", "🕐", "🕑", "🕒", "🕓"]
            current_text = self.icon_label.cget("text")
            try:
                current_index = icons.index(current_text)
                next_index = (current_index + 1) % len(icons)
            except ValueError:
                next_index = 0
            
            self.icon_label.configure(text=icons[next_index])
            
            # Schedule next animation frame
            self.popup.after(500, self.animate_icon)
        except:
            pass
    
    def update_status(self, status_text):
        """Update the status message."""
        if self.popup and self.popup.winfo_exists():
            try:
                self.status_label.configure(text=status_text)
                self.popup.update_idletasks()
            except:
                pass
    
    def on_close_attempt(self):
        """Handle user attempting to close the popup."""
        # Don't allow closing while task is running
        pass
    
    def close(self):
        """Close the progress popup."""
        self.is_running = False
        if self.popup and self.popup.winfo_exists():
            try:
                self.popup.grab_release()
                self.popup.destroy()
            except:
                pass

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

def log_job_status(message):
    if hasattr(root, 'log_output'):
        root.log_output.configure(state="normal")
        root.log_output.insert(tk.END, message + '\n')
        root.log_output.see(tk.END)
        root.log_output.configure(state="disabled")
        # Update status in tab title
        update_log_tab_title()

def update_log_tab_title():
    if hasattr(root, 'notebook') and hasattr(root, 'log_frame'):
        current_tab = root.notebook.index("current")
        log_tab_index = root.notebook.index(root.log_frame)
        if current_tab != log_tab_index:
            # Add indicator that there are new logs
            root.notebook.tab(log_tab_index, text=f"{ICONS['log']} Logs & Status •")

def get_internal_mode(mode_label):
    mapping = {
        "SCAP Benchmarks": "benchmark",
        "Operating Systems": "checklist",
        "Applications": "application",
        "Network": "network",
        "ALL": "all"
    }
    return mapping.get(mode_label, "benchmark")

# === Button Commands with Feedback ===
def run_compare_with_feedback():
    log_job_status("[INFO] Job started: Running tasks...")
    
    # Show progress popup
    progress_popup = ProgressPopup(
        root, 
        "Running Tasks", 
        "Checking for updates and processing STIG files..."
    )
    
    def on_status_update(status):
        status_text.set(status)
        progress_popup.update_status(status)
        if status == "Done":
            log_job_status("[INFO] Job complete: Tasks finished.")
            progress_popup.close()
        elif status.startswith("Error"):
            log_job_status(f"[ERROR] {status}")
            progress_popup.close()
    
    threading.Thread(target=lambda: run_compare_task(
        mode=get_internal_mode(mode_var.get()),
        baseline_path=yaml_path_var.get(),
        download_updates_checked=download_var.get(),
        extract_checked=extract_var.get(),
        on_status_update=on_status_update,
        clear_log=lambda: root.log_output.delete(1.0, tk.END),
        on_cklb_refresh=refresh_cklb_combobox
    )).start()

def download_cklb_popup():
    popup = tk.Toplevel(root)
    popup.title("Download CKLB Files")
    center_window_on_parent(popup, root, 500, 400)
    popup.configure(bg=COLORS['bg_primary'])
    popup.grab_set()  # Make popup modal
    
    ttk.Label(popup, text="Select CKLB(s) to download:", font=FONTS['heading']).pack(pady=(20, 10))
    
    updated_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_updated')
    cklb_files = sorted(os.listdir(updated_dir)) if os.path.isdir(updated_dir) else []
    
    list_frame = ttk.Frame(popup, style="Card.TFrame")
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")
    
    listbox = tk.Listbox(list_frame, 
        selectmode=tk.MULTIPLE, 
        font=FONTS['default'],
        bg=COLORS['input_bg'],
        fg=COLORS['text_primary'],
        selectbackground=COLORS['accent'],
        yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    
    for f in cklb_files:
        listbox.insert(tk.END, f)
    
    def do_download():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if not selected:
            log_job_status("[ERROR] Please select at least one CKLB file.")
            return
        dest_dir = filedialog.askdirectory(title="Select Destination Directory")
        if not dest_dir:
            log_job_status("[INFO] Download cancelled.")
            return
        
        errors = []
        for fname in selected:
            src = os.path.join(updated_dir, fname)
            dst = os.path.join(dest_dir, fname)
            try:
                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                    fdst.write(fsrc.read())
            except Exception as e:
                errors.append(f"Failed to copy {fname}: {e}")
        
        if errors:
            for err in errors:
                log_job_status(f"[ERROR] {err}")
        log_job_status(f"[INFO] Copied {len(selected) - len(errors)} file(s) to {dest_dir}")
        popup.destroy()
    
    btn_frame = ttk.Frame(popup)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text=f"{ICONS['download']} Download Selected", 
               style="Accent.TButton", command=do_download).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", 
               style="Secondary.TButton", command=popup.destroy).pack(side="left", padx=5)

# Multi-rule input handler
def show_multi_rule_input(new_rules, checklist_files, on_submit, on_cancel):
    if hasattr(show_multi_rule_input, 'frame') and show_multi_rule_input.frame:
        show_multi_rule_input.frame.destroy()
    
    frame_mr = ttk.LabelFrame(checklist_frame, text="Input for New Rules", style="TLabelframe")
    frame_mr.pack(fill="both", expand=True, pady=10)
    show_multi_rule_input.frame = frame_mr
    
    # Checklist selection
    checklist_select = ttk.Frame(frame_mr)
    checklist_select.pack(fill="x", padx=10, pady=5)
    ttk.Label(checklist_select, text="Apply to checklists:", font=FONTS['default']).pack(side="left")
    
    cklb_vars = []
    for f in checklist_files:
        var = tk.BooleanVar(value=True)
        ttk.Checkbutton(checklist_select, text=f, variable=var).pack(side="left", padx=5)
        cklb_vars.append((f, var))
    
    # Bulk fill controls
    bulk_frame = ttk.Frame(frame_mr)
    bulk_frame.pack(fill="x", padx=10, pady=5)
    
    ttk.Label(bulk_frame, text="Bulk Fill:").pack(side="left", padx=(0, 5))
    status_bulk = tk.StringVar(value="not_reviewed")
    ttk.Combobox(bulk_frame, textvariable=status_bulk,
                 values=["not_reviewed", "not_applicable", "open", "not_a_finding"], 
                 state="readonly", width=15, style="Modern.TCombobox").pack(side="left", padx=5)
    
    ttk.Label(bulk_frame, text="Comment:").pack(side="left", padx=5)
    comment_bulk = tk.StringVar()
    ttk.Entry(bulk_frame, textvariable=comment_bulk, width=30, style="Modern.TEntry").pack(side="left", padx=5)
    
    def bulk_fill():
        for e in entries:
            if not e["ignore_var"].get():
                e["status_var"].set(status_bulk.get())
                e["comment_widget"].delete("1.0", "end")
                e["comment_widget"].insert("1.0", comment_bulk.get())
    
    ttk.Button(bulk_frame, text="Apply All", command=bulk_fill, style="Secondary.TButton").pack(side="left", padx=10)
    
    # Table
    table_frame = ttk.Frame(frame_mr)
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas = tk.Canvas(table_frame, height=200, bg=COLORS['bg_secondary'])
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Table headers
    headers = ["ID", "Rule Title", "Status", "Comment", "Ignore"]
    for i, header in enumerate(headers):
        ttk.Label(scrollable_frame, text=header, font=FONTS['heading']).grid(row=0, column=i, padx=5, pady=5)
    
    entries = []
    for i, rule in enumerate(new_rules, 1):
        row_id = rule["group_id_src"]
        rule_title = rule["rule_title"] or row_id
        
        ttk.Label(scrollable_frame, text=row_id, font=FONTS['small']).grid(row=i, column=0, padx=5, pady=2)
        ttk.Label(scrollable_frame, text=rule_title[:50] + "..." if len(rule_title) > 50 else rule_title,
                  font=FONTS['small']).grid(row=i, column=1, padx=5, pady=2, sticky="w")
        
        status_var = tk.StringVar(value="not_reviewed")
        ttk.Combobox(scrollable_frame, textvariable=status_var,
                     values=["not_reviewed", "not_applicable", "open", "not_a_finding"],
                     state="readonly", width=15, style="Modern.TCombobox").grid(row=i, column=2, padx=5, pady=2)
        
        comment_text = tk.Text(scrollable_frame, height=2, width=30, font=FONTS['small'])
        comment_text.grid(row=i, column=3, padx=5, pady=2)
        
        ignore_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(scrollable_frame, variable=ignore_var).grid(row=i, column=4, padx=5, pady=2)
        
        entries.append({
            "group_id_src": row_id,
            "status_var": status_var,
            "comment_widget": comment_text,
            "ignore_var": ignore_var
        })
    
    def do_ok():
        selected_cklbs = [fname for fname, var in cklb_vars if var.get()]
        results = []
        for entry in entries:
            if not entry["ignore_var"].get():
                results.append({
                    "group_id_src": entry["group_id_src"],
                    "status": entry["status_var"].get(),
                    "comments": entry["comment_widget"].get("1.0", "end").strip()
                })
        frame_mr.destroy()
        on_submit({"apply_cklbs": selected_cklbs, "rules": results})
    
    btn_frame = ttk.Frame(frame_mr)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text=f"{ICONS['check']} OK", style="Accent.TButton", 
               command=do_ok).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", 
               command=lambda: (frame_mr.destroy(), on_cancel())).pack(side="left", padx=5)

def update_now_handler():
    selected_old_files = [file_listbox.get(i) for i in file_listbox.curselection()]
    selected_new_indices = cklb_listbox.curselection()
    
    if not selected_old_files:
        log_job_status("[ERROR] Please select at least one CKLB to upgrade from the left panel.")
        return
    if not selected_new_indices:
        log_job_status("[ERROR] Please select at least one new CKLB version from the right panel.")
        return
    
    # Get the selected new CKLB files
    selected_new_files = []
    for i in selected_new_indices:
        item_text = cklb_listbox.get(i)
        if item_text.startswith("📁 "):  # Browsed file
            # Use the full path from browsed_files
            if hasattr(cklb_listbox, 'browsed_files') and i < len(cklb_listbox.browsed_files):
                selected_new_files.append(cklb_listbox.browsed_files[i])
        else:  # File from cklb_lib directory
            selected_new_files.append(os.path.join(cklb_dir, item_text))
    
    if not selected_new_files:
        log_job_status("[ERROR] Could not determine selected new CKLB files.")
        return
    
    # For now, use the first selected new file (maintain existing logic)
    new_file_path = selected_new_files[0]
    new_name = os.path.basename(new_file_path)
    
    # Check STIG ID mismatch
    old_path = os.path.join(usr_dir, selected_old_files[0])
    
    try:
        old_data = load_cklb(old_path)
        new_data = load_cklb(new_file_path)
        is_match, old_stig_id, new_stig_id, new_rules = check_stig_id_match(old_data, new_data)
        
        if not is_match:
            msg = (f"STIG ID mismatch detected:\n"
                   f"Old: {old_stig_id}\nNew: {new_stig_id}\n"
                   f"New rules: {len(new_rules)}\n\nProceed?")
            
            confirm_frame = ttk.Frame(checklist_frame)
            confirm_frame.pack(fill="x", pady=10)
            ttk.Label(confirm_frame, text=msg, foreground=COLORS['danger']).pack(side="left", padx=10)
            
            def proceed_merge(force_merge):
                confirm_frame.destroy()
                log_job_status("[INFO] Job started: Merging checklists...")
                
                merged_results = run_merge_task(
                    selected_old_files=selected_old_files,
                    new_name=new_name,
                    usr_dir=usr_dir,
                    cklb_dir=os.path.dirname(new_file_path),  # Use directory of selected file
                    on_status_update=status_text.set,
                    force=force_merge,
                    prefix=None
                )
                
                for result in merged_results:
                    if result["new_rules"]:
                        log_job_status(f"[INFO] {len(result['new_rules'])} new rules detected.")
                        show_multi_rule_input(
                            result["new_rules"], 
                            [result["merged_name"]], 
                            lambda user_input: handle_rule_updates(result, user_input),
                            lambda: log_job_status("[INFO] Rule input cancelled.")
                        )
                    else:
                        log_job_status("[INFO] Merge complete.")
            
            ttk.Button(confirm_frame, text="Proceed", style="Accent.TButton",
                      command=lambda: proceed_merge(True)).pack(side="left", padx=5)
            ttk.Button(confirm_frame, text="Cancel", style="Secondary.TButton",
                      command=lambda: (confirm_frame.destroy(), 
                                     log_job_status("[ERROR] Merge cancelled."))).pack(side="left", padx=5)
            return
        else:
            force_merge = False
    except Exception as e:
        log_job_status(f"[ERROR] Failed to check STIG IDs: {e}")
        return
    
    # Check for missing host_name
    needs_prefix = False
    for old_name in selected_old_files:
        old_path = os.path.join(usr_dir, old_name)
        try:
            with open(old_path, "r", encoding="utf-8") as f:
                old_json = json.load(f)
            if not old_json.get("target_data", {}).get("host_name"):
                needs_prefix = True
                break
        except Exception:
            needs_prefix = True
            break
    
    if needs_prefix:
        prefix_frame = ttk.Frame(checklist_frame)
        prefix_frame.pack(fill="x", pady=10)
        
        ttk.Label(prefix_frame, text="Enter host-name prefix:", 
                  foreground=COLORS['danger']).pack(side="left", padx=10)
        prefix_var = tk.StringVar()
        ttk.Entry(prefix_frame, textvariable=prefix_var, width=30, 
                  style="Modern.TEntry").pack(side="left", padx=10)
        
        def do_set_prefix():
            prefix = prefix_var.get().strip()
            if not prefix:
                log_job_status("[ERROR] Prefix cannot be blank.")
                return
            prefix_frame.destroy()
            run_merge_with_prefix(prefix, force_merge, new_file_path, new_name)
        
        ttk.Button(prefix_frame, text="OK", style="Accent.TButton",
                  command=do_set_prefix).pack(side="left", padx=5)
        ttk.Button(prefix_frame, text="Cancel", style="Secondary.TButton",
                  command=lambda: (prefix_frame.destroy(),
                                 log_job_status("[INFO] Cancelled."))).pack(side="left", padx=5)
    else:
        run_merge_with_prefix(None, force_merge, new_file_path, new_name)

def run_merge_with_prefix(prefix, force_merge, new_file_path, new_name):
    log_job_status("[INFO] Job started: Merging checklists...")
    
    # Show progress popup
    progress_popup = ProgressPopup(
        root, 
        "Merging Checklists", 
        "Updating checklists with new STIG versions..."
    )
    
    def on_merge_complete():
        progress_popup.close()
    
    def run_merge():
        try:
            merged_results = run_merge_task(
                selected_old_files=[file_listbox.get(i) for i in file_listbox.curselection()],
                new_name=new_name,
                usr_dir=usr_dir,
                cklb_dir=os.path.dirname(new_file_path),  # Use directory of selected file
                on_status_update=lambda status: (status_text.set(status), progress_popup.update_status(status)),
                force=force_merge,
                prefix=prefix
            )
            
            # Close progress popup before showing rule input
            progress_popup.close()
            
            for result in merged_results:
                if result["new_rules"]:
                    show_multi_rule_input(
                        result["new_rules"], 
                        [result["merged_name"]], 
                        lambda user_input: handle_rule_updates(result, user_input),
                        lambda: log_job_status("[INFO] Rule input cancelled.")
                    )
                else:
                    log_job_status("[INFO] Merge complete.")
        except Exception as e:
            progress_popup.close()
            log_job_status(f"[ERROR] Merge failed: {e}")
    
    threading.Thread(target=run_merge).start()

def handle_rule_updates(result, user_input):
    merged_cklb = load_cklb(result["merged_path"])
    for rule_entry in user_input["rules"]:
        for stig in merged_cklb.get("stigs", []):
            for rule in stig.get("rules", []):
                if rule.get("group_id_src") == rule_entry["group_id_src"]:
                    rule["status"] = rule_entry["status"]
                    rule["comments"] = rule_entry["comments"]
    save_cklb(result["merged_path"], merged_cklb)
    log_job_status(f"[INFO] Updated {len(user_input['rules'])} rules in {result['merged_name']}")

def refresh_usr_listbox():
    global usr_files
    usr_files = sorted(os.listdir(usr_dir)) if os.path.isdir(usr_dir) else []
    file_listbox.delete(0, tk.END)
    for f in usr_files:
        if f.lower().endswith('.cklb'):  # Only show CKLB files
            file_listbox.insert(tk.END, f)

def refresh_cklb_combobox():
    global cklb_files
    cklb_files = sorted([f for f in os.listdir(cklb_dir) if f.lower().endswith('.cklb')]) if os.path.isdir(cklb_dir) else []
    cklb_listbox.delete(0, tk.END)
    for f in cklb_files:
        cklb_listbox.insert(tk.END, f)
    if cklb_files and hasattr(root, 'cklb_combobox'):
        root.cklb_combobox['values'] = cklb_files
        cklb_sel_var.set(cklb_files[0] if cklb_files else "")

# === DISA Fetch Dialog ===
def show_disa_fetch_dialog():
    """Show dialog for selecting STIGs to fetch from DISA"""
    import threading
    popup = tk.Toplevel(root)
    popup.title("Fetch from DISA")
    popup.configure(bg="#ffffff")  # White background for better contrast
    popup.transient(root)
    popup.grab_set()
    
    # Center the popup on the main window
    center_window_on_parent(popup, root, 600, 500)

    # Header with white background
    header_frame = ttk.Frame(popup)
    header_frame.configure(style="Card.TFrame")
    header_frame.pack(fill="x", padx=20, pady=20)
    ttk.Label(header_frame, text="Select STIGs to Download", font=FONTS['heading']).pack()
    ttk.Label(header_frame, text="Fetching available STIGs from DISA...", 
              font=FONTS['default'], foreground=COLORS['text_secondary'], name="status_label").pack(pady=(5, 0))

    # List frame for STIGs with black border and white background
    list_frame = ttk.Frame(popup)
    list_frame.configure(relief="solid", borderwidth=2, style="Card.TFrame")
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    
    stig_scrollbar = ttk.Scrollbar(list_frame)
    stig_scrollbar.pack(side="right", fill="y")
    
    stig_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, font=FONTS['default'],
        bg="#ffffff", fg="#000000", selectbackground=COLORS['accent'],
        yscrollcommand=stig_scrollbar.set, width=80, height=15, relief="flat", borderwidth=0)
    stig_listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)
    stig_scrollbar.config(command=stig_listbox.yview)

    # Buttons with white background
    btn_frame = ttk.Frame(popup)
    btn_frame.configure(style="Card.TFrame")
    btn_frame.pack(fill="x", padx=20, pady=20)
    
    def start_fetch():
        selected_indices = stig_listbox.curselection()
        if not selected_indices:
            log_job_status("[ERROR] Please select at least one STIG item.")
            return
        
        # Filter out header and separator rows (indices 0 and 1)
        valid_indices = [i for i in selected_indices if i > 1]
        if not valid_indices:
            log_job_status("[ERROR] Please select at least one STIG item (not header rows).")
            return
            
        selected_dicts = [all_items[i-2] for i in valid_indices]  # -2 for header and separator rows
        popup.destroy()
        show_download_choice_dialog(selected_dicts)

    ttk.Button(btn_frame, text="Continue", 
               style="Accent.TButton", command=start_fetch).pack(side="right", padx=(10, 0))
    ttk.Button(btn_frame, text="Cancel", 
               style="Secondary.TButton", command=popup.destroy).pack(side="right")

    # Fetch STIGs in background
    def fetch_stigs():
        try:
            from scraper import scrape_stigs
            
            # Check if popup still exists before accessing widgets
            if not popup.winfo_exists():
                return
                
            status_label = header_frame.nametowidget("status_label")
            status_label.config(text="Fetching available STIGs from DISA...")
            
            items = scrape_stigs()
            
            # Check again before updating UI
            if not popup.winfo_exists():
                return
                
            if not items:
                if popup.winfo_exists():
                    status_label.config(text="No STIGs found.")
                return
                
            nonlocal all_items
            all_items = items
            
            # Check if listbox still exists before clearing
            if not popup.winfo_exists():
                return
                
            stig_listbox.delete(0, tk.END)
            
            # Add header row
            header = f"{'STIG Product':<70} | {'Ver':>6} | {'Rel':>6} | {'Updated':>15}"
            stig_listbox.insert(tk.END, header)
            stig_listbox.itemconfig(0, {'fg': COLORS['text_secondary']})
            
            # Add separator
            separator = "─" * len(header)
            stig_listbox.insert(tk.END, separator)
            stig_listbox.itemconfig(1, {'fg': COLORS['text_secondary']})
            
            for item in items:
                # Check if popup still exists during the loop
                if not popup.winfo_exists():
                    return
                    
                title = item.get('Product', 'Unknown')
                version = item.get('Version', 'Unknown')
                release = item.get('Release', 'Unknown')
                update_time = item.get('Updated', 'Unknown')
                
                # Truncate long titles
                title_disp = (title[:67] + '...') if len(title) > 70 else title.ljust(70)
                version_disp = str(version).rjust(6)
                release_disp = str(release).rjust(6)
                update_disp = str(update_time).rjust(15)
                
                display = f"{title_disp} | {version_disp} | {release_disp} | {update_disp}"
                stig_listbox.insert(tk.END, display)
                
            if popup.winfo_exists():
                status_label.config(text=f"Found {len(items)} STIGs. Select one or more to download and process.")
                
        except Exception as e:
            # Handle any errors gracefully
            if popup.winfo_exists():
                try:
                    status_label = header_frame.nametowidget("status_label")
                    status_label.config(text=f"Error fetching STIGs: {e}")
                except:
                    pass
            log_job_status(f"[ERROR] Failed to fetch STIGs: {e}")
    
    all_items = []
    threading.Thread(target=fetch_stigs, daemon=True).start()

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
    main_frame = ttk.Frame(choice_popup, style="Card.TFrame")
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
    
    # ZIP Download option with black border and better interactivity
    zip_frame = ttk.Frame(options_frame)
    zip_frame.configure(relief="solid", borderwidth=2)
    zip_frame.pack(fill="x", pady=(0, 10))
    
    # Make the frame clickable
    def on_zip_click(event=None):
        choose_zip()
    
    zip_frame.bind("<Button-1>", on_zip_click)
    
    zip_content = ttk.Frame(zip_frame)
    zip_content.pack(fill="x", padx=15, pady=15)
    zip_content.bind("<Button-1>", on_zip_click)
    
    zip_label1 = ttk.Label(zip_content, text=f"{ICONS['download']} Download ZIP Files Only", 
              font=FONTS['heading'])
    zip_label1.pack(anchor="w")
    zip_label1.bind("<Button-1>", on_zip_click)
    
    zip_label2 = ttk.Label(zip_content, text="Download the raw STIG ZIP files without processing", 
              font=FONTS['default'], foreground=COLORS['text_secondary'])
    zip_label2.pack(anchor="w", pady=(5, 0))
    zip_label2.bind("<Button-1>", on_zip_click)
    
    # CKLB option with black border and better interactivity
    cklb_frame = ttk.Frame(options_frame)
    cklb_frame.configure(relief="solid", borderwidth=2)
    cklb_frame.pack(fill="x")
    
    # Make the frame clickable
    def on_cklb_click(event=None):
        choose_cklb()
    
    cklb_frame.bind("<Button-1>", on_cklb_click)
    
    cklb_content = ttk.Frame(cklb_frame)
    cklb_content.pack(fill="x", padx=15, pady=15)
    cklb_content.bind("<Button-1>", on_cklb_click)
    
    cklb_label1 = ttk.Label(cklb_content, text=f"{ICONS['check']} Create CKLB Files", 
              font=FONTS['heading'])
    cklb_label1.pack(anchor="w")
    cklb_label1.bind("<Button-1>", on_cklb_click)
    
    cklb_label2 = ttk.Label(cklb_content, text="Download ZIPs, extract XCCDF files, and generate CKLB checklists", 
              font=FONTS['default'], foreground=COLORS['text_secondary'])
    cklb_label2.pack(anchor="w", pady=(5, 0))
    cklb_label2.bind("<Button-1>", on_cklb_click)
    
    # Buttons frame
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=(10, 0))
    
    def choose_zip():
        choice_popup.destroy()
        fetch_from_disa(selected_items, "zip_only")
    
    def choose_cklb():
        choice_popup.destroy()
        fetch_from_disa(selected_items, "cklb")
    
    ttk.Button(btn_frame, text="Cancel", 
               style="Secondary.TButton", command=choice_popup.destroy).pack(side="left")
    
    ttk.Button(btn_frame, text=f"{ICONS['download']} Download ZIPs", 
               style="Secondary.TButton", command=choose_zip).pack(side="right", padx=(10, 0))
    
    ttk.Button(btn_frame, text=f"{ICONS['check']} Create CKLBs", 
               style="Accent.TButton", command=choose_cklb).pack(side="right", padx=(10, 0))

def fetch_from_disa(selected_items, output_format):
    """Main function to fetch selected STIGs from DISA and process them"""
    log_job_status("[INFO] Starting DISA fetch process...")
    
    if output_format == "zip_only":
        action_text = "Downloading STIG ZIP files..."
    else:
        action_text = "Downloading and processing selected STIG files from DISA..."
    
    progress_popup = ProgressPopup(
        root, 
        "Fetching from DISA", 
        action_text
    )
    def on_status_update(status):
        status_text.set(status)
        progress_popup.update_status(status)
        if status == "Done":
            log_job_status("[INFO] DISA fetch complete.")
            progress_popup.close()
        elif status.startswith("Error"):
            log_job_status(f"[ERROR] {status}")
            progress_popup.close()
    threading.Thread(target=lambda: run_disa_fetch_task(
        selected_items=selected_items,
        output_format=output_format,
        on_status_update=on_status_update
    ), daemon=True).start()

# Update run_disa_fetch_task to accept selected_items

def run_disa_fetch_task(selected_items, output_format, on_status_update):
    """Background task to fetch and process selected STIGs from DISA"""
    try:
        from downloader import download_updates
        from xccdf_extractor import extract_xccdf_from_zip
        from cklb_generator import generate_cklb_json
        from datetime import datetime
        import os
        import json
        
        on_status_update("Downloading STIG ZIP files...")
        download_updates(selected_items, target_dir="cklb_proc/xccdf_lib")
        
        if output_format == "zip_only":
            log_job_status(f"[INFO] Downloaded {len(selected_items)} ZIP files to cklb_proc/xccdf_lib")
            on_status_update("Done")
            return
        
        # For CKLB creation (output_format == "cklb")
        on_status_update("Extracting XCCDF files and generating CKLB...")
        zip_dir = "cklb_proc/xccdf_lib"
        output_dir = "cklb_proc/cklb_lib"  # Use standard output directory
        os.makedirs(output_dir, exist_ok=True)
        
        generated_count = 0
        for item in selected_items:
            zip_filename = os.path.basename(item['URL'])
            zip_path = os.path.join(zip_dir, zip_filename)
            if os.path.exists(zip_path):
                xccdf_files = extract_xccdf_from_zip(zip_path, "cklb_proc/xccdf_extracted")
                if xccdf_files:
                    if not isinstance(xccdf_files, list):
                        xccdf_files = [xccdf_files]
                    for xccdf_file in xccdf_files:
                        try:
                            # Generate CKLB with proper filename
                            basename = os.path.basename(xccdf_file).replace('-xccdf.xml', '').replace('Manual', '').strip('_- ')
                            date_str = datetime.now().strftime("%Y%m%d")
                            cklb_filename = f"{basename}_{date_str}.cklb"
                            cklb_path = os.path.join(output_dir, cklb_filename)
                            
                            # Generate CKLB JSON - discussion text is preserved in cklb_generator.py
                            cklb_json = generate_cklb_json(xccdf_file)
                            with open(cklb_path, 'w') as f:
                                json.dump(cklb_json, f, indent=2)
                            generated_count += 1
                            log_job_status(f"[INFO] Generated CKLB: {cklb_filename}")
                        except Exception as e:
                            log_job_status(f"[ERROR] Failed to generate CKLB for {xccdf_file}: {e}")
                else:
                    log_job_status(f"[WARNING] No XCCDF files found in {zip_filename}")
            else:
                log_job_status(f"[WARNING] ZIP file not found: {zip_path}")
        
        log_job_status(f"[INFO] Generated {generated_count} CKLB files in {output_dir}")
        on_status_update("Done")
    except Exception as e:
        log_job_status(f"[ERROR] DISA fetch failed: {e}")
        on_status_update(f"Error: {e}")

def import_cklb_files():
    """Import CKLB files into the user library directory"""
    import shutil
    
    # Open file dialog to select CKLB files
    file_paths = filedialog.askopenfilenames(
        title="Select CKLB files to import",
        filetypes=[("CKLB files", "*.cklb"), ("All files", "*.*")],
        multiple=True
    )
    
    if not file_paths:
        log_job_status("[INFO] Import cancelled.")
        return
    
    # Ensure user directory exists
    os.makedirs(usr_dir, exist_ok=True)
    
    imported_count = 0
    errors = []
    
    for file_path in file_paths:
        try:
            filename = os.path.basename(file_path)
            
            # Validate file extension
            if not filename.lower().endswith('.cklb'):
                errors.append(f"Skipped {filename}: Not a CKLB file")
                continue
            
            dest_path = os.path.join(usr_dir, filename)
            
            # Check if file already exists
            if os.path.exists(dest_path):
                # Ask user if they want to overwrite
                from tkinter import messagebox
                overwrite = messagebox.askyesno(
                    "File Exists", 
                    f"File '{filename}' already exists in the user library.\n\nOverwrite?",
                    icon="question"
                )
                if not overwrite:
                    log_job_status(f"[INFO] Skipped {filename}: File exists")
                    continue
            
            # Copy the file
            shutil.copy2(file_path, dest_path)
            imported_count += 1
            log_job_status(f"[INFO] Imported: {filename}")
            
        except Exception as e:
            errors.append(f"Failed to import {os.path.basename(file_path)}: {e}")
    
    # Log results
    if errors:
        for error in errors:
            log_job_status(f"[ERROR] {error}")
    
    log_job_status(f"[INFO] Import complete: {imported_count} files imported to user library")
    
    # Refresh the user files listbox
    refresh_usr_listbox()

# === Create Notebook (Tabbed Interface) ===
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=0, pady=0)
root.notebook = notebook

# === Tab 1: Getting Started & Baseline ===
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text=f"{ICONS['settings']} Configuration")

# Create scrollable container for Tab 1
tab1_canvas = tk.Canvas(tab1, bg=COLORS['bg_primary'])
tab1_scrollbar = ttk.Scrollbar(tab1, orient="vertical", command=tab1_canvas.yview)
tab1_frame = ttk.Frame(tab1_canvas)
tab1_frame.bind("<Configure>", lambda e: tab1_canvas.configure(scrollregion=tab1_canvas.bbox("all")))
tab1_canvas.create_window((0, 0), window=tab1_frame, anchor="nw")
tab1_canvas.configure(yscrollcommand=tab1_scrollbar.set)
tab1_canvas.pack(side="left", fill="both", expand=True)
tab1_scrollbar.pack(side="right", fill="y")

# Getting Started Section
getting_started = ttk.LabelFrame(tab1_frame, text=f"{ICONS['info']} Getting Started Guide", style="TLabelframe")
getting_started.pack(fill="both", expand=True, padx=20, pady=(20, 10))

# Create a scrollable text widget for the detailed instructions
instructions_frame = ttk.Frame(getting_started)
instructions_frame.pack(fill="both", expand=True, padx=10, pady=10)

instructions_text = scrolledtext.ScrolledText(
    instructions_frame,
    wrap=tk.WORD,
    font=FONTS['default'],
    bg=COLORS['bg_secondary'],
    fg=COLORS['text_primary'],
    height=15,
    state="disabled"
)
instructions_text.pack(fill="both", expand=True, padx=20, pady=(20, 10))

# Detailed instructions content
detailed_instructions = """Welcome to CheckMate - Your STIG Compliance Management Tool!

CheckMate helps you manage STIG (Security Technical Implementation Guide) compliance by automating baseline generation, tracking updates, and managing checklist files. Follow these steps to get started:

═══════════════════════════════════════════════════════════════════════════════════

📋 STEP 1: UNDERSTANDING THE WORKFLOW

CheckMate follows a simple workflow:
• Generate or import a baseline YAML file that tracks your STIG products
• Monitor for updates to STIG releases
• Download and process updated checklists
• Merge your existing compliance data with new versions

═══════════════════════════════════════════════════════════════════════════════════

🚀 STEP 2: SETTING UP YOUR BASELINE

To get started, you'll need a baseline YAML file:
1. Click "📁 Browse" next to "Baseline YAML"
2. Select an existing baseline_*.yaml file from the baselines/ directory
3. If you don't have a baseline file, you can create one manually or obtain one from your system administrator

═══════════════════════════════════════════════════════════════════════════════════

⚙️ STEP 3: CONFIGURING OPTIONS

Before running tasks, configure these options:

• Download ZIPs for updated items:
  ☑ Check this to automatically download ZIP files for updated STIGs
  ☐ Leave unchecked to only check for updates without downloading

• Extract .xccdf and generate checklist:
  ☑ Check this to automatically extract XCCDF files and generate CKL checklists
  ☐ Leave unchecked if you only want to download ZIPs

═══════════════════════════════════════════════════════════════════════════════════

🔄 STEP 4: RUNNING UPDATE CHECKS

1. Ensure your baseline YAML file is selected
2. Configure your download/extract options
3. Use the "Checklist Management" tab to manage your checklists
4. Monitor progress in the "📋 Logs & Status" tab

What happens during update checks:
• CheckMate compares your baseline against current DISA releases
• New or updated STIGs are identified
• If enabled, ZIP files are downloaded to cklb_proc/cklb_lib/
• If enabled, XCCDF files are extracted and converted to CKL format
• Results are logged with detailed status information

═══════════════════════════════════════════════════════════════════════════════════

📦 STEP 5: MANAGING YOUR CHECKLIST LIBRARY

Use the "Checklist Management" tab to:
• Upgrade existing checklists with newer STIG versions
• Merge your compliance data while preserving finding statuses and comments
• Import and organize your checklist files

═══════════════════════════════════════════════════════════════════════════════════

🔧 STEP 6: UPGRADING EXISTING CHECKLISTS

Go to the "🔄 Checklist Management" tab:

1. Select CKLBs to upgrade:
   • Choose one or more checklist files from the left panel
   • These are your current checklists with compliance data

2. Select new CKLB version:
   • Choose the updated version from the right panel dropdown
   • This should be a newer version of the same STIG

3. Click "🔄 Update Now":
   • CheckMate will merge your existing data with the new version
   • Finding statuses, comments, and host information are preserved
   • New rules from the updated STIG will be highlighted for review
   • If STIG IDs don't match, you'll be prompted to confirm the merge

4. Handle new rules:
   • If new security rules are detected, a dialog will appear
   • Set the initial status for new rules (Not Reviewed, N/A, Open, etc.)
   • Add comments as needed
   • Apply changes to complete the upgrade

═══════════════════════════════════════════════════════════════════════════════════

📊 STEP 7: MONITORING AND TROUBLESHOOTING

Use the "📋 Logs & Status" tab to:
• Monitor real-time progress of long-running operations
• Review detailed logs of all activities
• Identify and troubleshoot any issues
• Clear logs when needed for a fresh start

Status indicators:
• [INFO] - Normal operation messages
• [ERROR] - Issues that need attention
• [WARN] - Warnings that may require review

═══════════════════════════════════════════════════════════════════════════════════

🗂️ STEP 8: FILE MANAGEMENT

Use the File menu to:
• Open baseline directory - View and manage your baseline files
• Open checklist libraries - Access your CKL files
• Open XCCDF library - View extracted XCCDF content

Directory structure:
• baselines/ - Contains your baseline YAML files
• cklb_proc/usr_cklb_lib/ - Your working checklist library
• cklb_proc/cklb_lib/ - Downloaded/generated checklists
• cklb_proc/xccdf_lib/ - Extracted XCCDF files

═══════════════════════════════════════════════════════════════════════════════════

💡 TIPS FOR SUCCESS

• Start with a specific scrape mode rather than "ALL" for faster initial setup
• Regularly update your baseline to track the latest STIG releases
• Keep backups of your usr_cklb_lib directory - it contains your compliance work
• Review the logs after each operation to ensure everything completed successfully

═══════════════════════════════════════════════════════════════════════════════════

Need help? Check the documentation or review the log files for detailed error messages."""

# Insert the instructions
instructions_text.configure(state="normal")
instructions_text.insert("1.0", detailed_instructions)
instructions_text.configure(state="disabled")

# Baseline Configuration Section
baseline_frame = ttk.LabelFrame(tab1_frame, text=f"{ICONS['settings']} Baseline Configuration", style="TLabelframe")
baseline_frame.pack(fill="x", padx=20, pady=(10, 20))

# Grid layout for baseline controls
baseline_controls = ttk.Frame(baseline_frame)
baseline_controls.pack(fill="x", padx=20, pady=15)

# Fetch from DISA button
ttk.Button(baseline_controls, text=f"{ICONS['download']} Fetch from DISA", 
           style="Accent.TButton", command=show_disa_fetch_dialog).pack(pady=10)

# Configure grid weights
baseline_controls.columnconfigure(1, weight=1)

# === Tab 2: Checklist Management ===
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text=f"{ICONS['update']} Checklist Management")

checklist_frame = ttk.Frame(tab2, style="Card.TFrame")
checklist_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Title
title_frame = ttk.Frame(checklist_frame)
title_frame.pack(fill="x", padx=20, pady=(20, 10))
ttk.Label(title_frame, text="Checklist Merge & Upgrade", font=FONTS['heading']).pack(side="left")

# Main content area with two panels
content_frame = ttk.Frame(checklist_frame)
content_frame.pack(fill="both", expand=True, padx=20, pady=10)
content_frame.columnconfigure(0, weight=1)
content_frame.columnconfigure(1, weight=1)
content_frame.rowconfigure(0, weight=1)

# Left panel: User CKLBs
left_panel = ttk.LabelFrame(content_frame, text="User CKLB Library (cklb_proc/user_cklb_library)", style="TLabelframe")
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
left_panel.columnconfigure(0, weight=1)
left_panel.rowconfigure(1, weight=1)

# Button frame for left panel - using grid for consistent layout
import_frame = ttk.Frame(left_panel)
import_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
import_frame.columnconfigure(0, weight=1)
import_frame.columnconfigure(1, weight=1)

ttk.Button(import_frame, text=f"{ICONS['import']} Import CKLB(s)", 
           style="Accent.TButton", command=import_cklb_files).grid(row=0, column=0, sticky="ew", padx=(0, 5))
ttk.Button(import_frame, text=f"{ICONS['reset']} Refresh", 
           style="Secondary.TButton", command=refresh_usr_listbox).grid(row=0, column=1, sticky="ew", padx=(5, 0))

file_listbox_frame = ttk.Frame(left_panel)
file_listbox_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
file_listbox_frame.columnconfigure(0, weight=1)
file_listbox_frame.rowconfigure(0, weight=1)

file_scrollbar = ttk.Scrollbar(file_listbox_frame)
file_scrollbar.grid(row=0, column=1, sticky="ns")

file_listbox = tk.Listbox(file_listbox_frame, 
                         selectmode=tk.MULTIPLE,
                         font=FONTS['default'],
                         bg=COLORS['input_bg'],
                         fg=COLORS['text_primary'],
                         selectbackground=COLORS['accent'],
                         selectforeground="#ffffff",
                         yscrollcommand=file_scrollbar.set)
file_listbox.grid(row=0, column=0, sticky="nsew")
file_scrollbar.config(command=file_listbox.yview)

# Populate listbox with only CKLB files
for f in usr_files:
    if f.lower().endswith('.cklb'):
        file_listbox.insert(tk.END, f)

# Right panel: CKLB Library
right_panel = ttk.LabelFrame(content_frame, text="CKLB Library (cklb_proc/cklb_lib)", style="TLabelframe")
right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
right_panel.columnconfigure(0, weight=1)
right_panel.rowconfigure(1, weight=1)

# Button frame for right panel - using grid for consistent layout
browse_frame = ttk.Frame(right_panel)
browse_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
browse_frame.columnconfigure(0, weight=1)
browse_frame.columnconfigure(1, weight=1)

def browse_cklb_directory():
    """Browse to select CKLB files from a different directory"""
    file_paths = filedialog.askopenfilenames(
        title="Select CKLB files",
        initialdir=cklb_dir,
        filetypes=[("CKLB files", "*.cklb"), ("All files", "*.*")],
        multiple=True
    )
    
    if file_paths:
        # Clear current selection and add selected files
        cklb_listbox.delete(0, tk.END)
        selected_files = []
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            if filename.lower().endswith('.cklb'):
                cklb_listbox.insert(tk.END, f"📁 {filename}")  # Add folder icon to distinguish browsed files
                selected_files.append(file_path)
        
        # Store the full paths for later use
        cklb_listbox.browsed_files = selected_files
        log_job_status(f"[INFO] Selected {len(selected_files)} CKLB files from browse")

ttk.Button(browse_frame, text=f"{ICONS['folder']} Browse...", 
           style="Accent.TButton", command=browse_cklb_directory).grid(row=0, column=0, sticky="ew", padx=(0, 5))
ttk.Button(browse_frame, text=f"{ICONS['reset']} Refresh Library", 
           style="Secondary.TButton", command=refresh_cklb_combobox).grid(row=0, column=1, sticky="ew", padx=(5, 0))

cklb_listbox_frame = ttk.Frame(right_panel)
cklb_listbox_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
cklb_listbox_frame.columnconfigure(0, weight=1)
cklb_listbox_frame.rowconfigure(0, weight=1)

cklb_scrollbar = ttk.Scrollbar(cklb_listbox_frame)
cklb_scrollbar.grid(row=0, column=1, sticky="ns")

cklb_listbox = tk.Listbox(cklb_listbox_frame, 
                         selectmode=tk.MULTIPLE,
                         font=FONTS['default'],
                         bg=COLORS['input_bg'],
                         fg=COLORS['text_primary'],
                         selectbackground=COLORS['accent'],
                         selectforeground="#ffffff",
                         yscrollcommand=cklb_scrollbar.set)
cklb_listbox.grid(row=0, column=0, sticky="nsew")
cklb_scrollbar.config(command=cklb_listbox.yview)

# Initialize browsed_files attribute
cklb_listbox.browsed_files = []

# Populate right listbox with CKLB files from cklb_lib
for f in cklb_files:
    if f.lower().endswith('.cklb'):
        cklb_listbox.insert(tk.END, f)

# Action buttons frame - centered below both panels
button_frame = ttk.Frame(checklist_frame)
button_frame.pack(pady=(20, 10))

ttk.Button(button_frame, text=f"{ICONS['update']} Check for Updates", 
           style="Accent.TButton", command=check_for_updates_handler).pack(side="left", padx=10)
ttk.Button(button_frame, text=f"{ICONS['folder']} Select Local File", 
           style="Secondary.TButton", command=select_local_file_handler).pack(side="left", padx=10)

# === Tab 3: Logs & Status ===
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text=f"{ICONS['log']} Logs & Status")
root.log_frame = tab3

log_container = ttk.Frame(tab3, style="Card.TFrame")
log_container.pack(fill="both", expand=True, padx=20, pady=20)

# Log output
log_output = scrolledtext.ScrolledText(
    log_container,
    wrap=tk.WORD,
    font=FONTS['mono'],
    bg=COLORS['bg_dark'],
    fg="#ffffff",
    insertbackground="#ffffff",
    state="disabled",
    height=20
)
log_output.pack(fill="both", expand=True, padx=20, pady=(20, 10))
root.log_output = log_output

# Status bar
status_frame = ttk.Frame(log_container)
status_frame.pack(fill="x", padx=20, pady=(0, 20))

ttk.Label(status_frame, text="Status:", font=FONTS['heading']).pack(side="left", padx=(0, 10))
status_label = ttk.Label(status_frame, textvariable=status_text, 
                        foreground=COLORS['accent'], font=FONTS['default'])
status_label.pack(side="left")

# Clear log button
ttk.Button(status_frame, text=f"{ICONS['reset']} Clear Log", 
           style="Secondary.TButton",
           command=lambda: log_output.delete(1.0, tk.END)).pack(side="right")

# When user clicks on log tab, remove the indicator
def on_tab_changed(event):
    current = notebook.index("current")
    if current == notebook.index(root.log_frame):
        notebook.tab(root.log_frame, text=f"{ICONS['log']} Logs & Status")

notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

# === Logging Setup ===
log_handler = GuiLogger(log_output)
log_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

# Initial log message
log_job_status("[INFO] CheckMate initialized successfully.")
log_job_status("[INFO] Ready to process checklists.")

# Build menu bar
build_menu(root, yaml_path_var, on_closing)

root.mainloop()