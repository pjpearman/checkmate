import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
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

usr_dir  = os.path.join(os.getcwd(), 'cklb_proc', 'usr_cklb_lib')
cklb_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_lib')
usr_files  = sorted(os.listdir(usr_dir))  if os.path.isdir(usr_dir)  else []
cklb_files = sorted(os.listdir(cklb_dir)) if os.path.isdir(cklb_dir) else []

usr_sel_var  = tk.StringVar()
cklb_sel_var = tk.StringVar()

from cklb_importer import import_cklb_files
from handlers import run_generate_baseline_task, run_compare_task, run_merge_task
from selected_merger import load_cklb, save_cklb, check_stig_id_match
from reset_baseline import reset_baseline_fields
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
    relief="flat")
style.configure("TLabelframe.Label", 
    font=FONTS['heading'], 
    background=COLORS['bg_secondary'],
    foreground=COLORS['text_primary'])

# Button styles
style.configure("Accent.TButton",
    font=FONTS['default'],
    foreground="#ffffff",
    background=COLORS['accent'],
    borderwidth=0,
    focuscolor='none',
    padding=[10, 6])
style.map("Accent.TButton",
    background=[('active', COLORS['accent_hover']), ('pressed', COLORS['accent_hover'])])

style.configure("Secondary.TButton",
    font=FONTS['default'],
    foreground=COLORS['text_primary'],
    background=COLORS['bg_secondary'],
    borderwidth=1,
    relief="solid",
    focuscolor='none',
    padding=[10, 6])

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

# === Helper Functions ===
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
def run_generate_baseline_with_feedback():
    log_job_status("[INFO] Job started: Generating new baseline...")
    def on_status_update(status):
        status_text.set(status)
        if status == "Done":
            log_job_status("[INFO] Job complete: Baseline generation finished.")
        elif status.startswith("Error"):
            log_job_status(f"[ERROR] {status}")
    threading.Thread(target=lambda: run_generate_baseline_task(
        mode=get_internal_mode(mode_var.get()),
        on_status_update=on_status_update,
        clear_log=lambda: root.log_output.delete(1.0, tk.END)
    )).start()

def import_cklb_with_feedback():
    log_job_status("[INFO] Job started: Importing CKLB library...")
    threading.Thread(target=lambda: import_cklb_files(on_import_complete=refresh_usr_listbox)).start()
    log_job_status("[INFO] Job complete: CKLB import finished.")

def run_compare_with_feedback():
    log_job_status("[INFO] Job started: Running tasks...")
    def on_status_update(status):
        status_text.set(status)
        if status == "Done":
            log_job_status("[INFO] Job complete: Tasks finished.")
        elif status.startswith("Error"):
            log_job_status(f"[ERROR] {status}")
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
    popup.geometry("500x400")
    popup.configure(bg=COLORS['bg_primary'])
    
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

def run_reset_baseline_with_feedback():
    baseline_path = yaml_path_var.get()
    if not baseline_path or not os.path.exists(baseline_path):
        log_job_status("[ERROR] Please select a valid Baseline YAML file.")
        return
    try:
        with open(baseline_path, 'r') as f:
            data = yaml.safe_load(f)
        products = list(data.keys())
    except Exception as e:
        log_job_status(f"[ERROR] Failed to load baseline: {e}")
        return
    
    # Create inline selection widget
    if hasattr(run_reset_baseline_with_feedback, 'sel_frame'):
        run_reset_baseline_with_feedback.sel_frame.destroy()
    
    sel_frame = ttk.LabelFrame(baseline_frame, text="Reset Baseline Products", style="TLabelframe")
    sel_frame.pack(fill="x", pady=10)
    run_reset_baseline_with_feedback.sel_frame = sel_frame
    
    select_all_var = tk.BooleanVar()
    prod_vars = []
    
    def on_select_all():
        for _, var in prod_vars:
            var.set(select_all_var.get())
    
    ttk.Checkbutton(sel_frame, text="Select All", variable=select_all_var, 
                    command=on_select_all).pack(anchor="w", padx=10, pady=5)
    
    for prod in products:
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(sel_frame, text=prod, variable=var)
        cb.pack(anchor="w", padx=30, pady=2)
        prod_vars.append((prod, var))
    
    def do_reset():
        selected = [prod for prod, var in prod_vars if var.get()]
        if not selected:
            log_job_status("[ERROR] Please select at least one product.")
            return
        
        if reset_baseline_fields(baseline_path, selected):
            log_job_status(f"[INFO] Reset Release and Version for {len(selected)} product(s).")
            sel_frame.destroy()
        else:
            log_job_status("[ERROR] Failed to reset baseline.")
    
    btn_frame = ttk.Frame(sel_frame)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text=f"{ICONS['reset']} Reset Selected", 
               style="Accent.TButton", command=do_reset).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", 
               style="Secondary.TButton", 
               command=lambda: sel_frame.destroy()).pack(side="left", padx=5)

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
    new_name = cklb_sel_var.get()
    
    if not selected_old_files:
        log_job_status("[ERROR] Please select at least one CKLB to upgrade.")
        return
    if not new_name:
        log_job_status("[ERROR] Please select a new CKLB version.")
        return
    
    # Check STIG ID mismatch
    old_path = os.path.join(usr_dir, selected_old_files[0])
    new_path = os.path.join(cklb_dir, new_name)
    
    try:
        old_data = load_cklb(old_path)
        new_data = load_cklb(new_path)
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
                    cklb_dir=cklb_dir,
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
            run_merge_with_prefix(prefix, force_merge)
        
        ttk.Button(prefix_frame, text="OK", style="Accent.TButton",
                  command=do_set_prefix).pack(side="left", padx=5)
        ttk.Button(prefix_frame, text="Cancel", style="Secondary.TButton",
                  command=lambda: (prefix_frame.destroy(),
                                 log_job_status("[INFO] Cancelled."))).pack(side="left", padx=5)
    else:
        run_merge_with_prefix(None, force_merge)

def run_merge_with_prefix(prefix, force_merge):
    log_job_status("[INFO] Job started: Merging checklists...")
    merged_results = run_merge_task(
        selected_old_files=[file_listbox.get(i) for i in file_listbox.curselection()],
        new_name=cklb_sel_var.get(),
        usr_dir=usr_dir,
        cklb_dir=cklb_dir,
        on_status_update=status_text.set,
        force=force_merge,
        prefix=prefix
    )
    
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
        file_listbox.insert(tk.END, f)

def refresh_cklb_combobox():
    global cklb_files
    cklb_files = sorted(os.listdir(cklb_dir)) if os.path.isdir(cklb_dir) else []
    cklb_combobox['values'] = cklb_files
    if cklb_files:
        cklb_sel_var.set(cklb_files[0])

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
getting_started = ttk.LabelFrame(tab1_frame, text=f"{ICONS['info']} Getting Started", style="TLabelframe")
getting_started.pack(fill="x", padx=20, pady=(20, 10))

info_text = """Welcome to CheckMate!

1. Generate or select a baseline YAML file
2. Configure scraping options
3. Run tasks to check for updates
4. Review logs in the Logs tab

For detailed help, check the documentation."""

ttk.Label(getting_started, text=info_text, font=FONTS['default'], 
          justify="left", wraplength=600).pack(padx=20, pady=20)

# Baseline Configuration Section
baseline_frame = ttk.LabelFrame(tab1_frame, text=f"{ICONS['settings']} Baseline Configuration", style="TLabelframe")
baseline_frame.pack(fill="x", padx=20, pady=10)

# Grid layout for baseline controls
baseline_controls = ttk.Frame(baseline_frame)
baseline_controls.pack(fill="x", padx=20, pady=20)

# Row 1: Scrape Mode
ttk.Label(baseline_controls, text="Scrape Mode:", font=FONTS['default']).grid(row=0, column=0, sticky="w", pady=5)
mode_combo = ttk.Combobox(baseline_controls, textvariable=mode_var, 
                          values=["SCAP Benchmarks", "Operating Systems", "Applications", "Network", "ALL"], 
                          state="readonly", width=25, style="Modern.TCombobox")
mode_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

# Row 2: Baseline YAML
ttk.Label(baseline_controls, text="Baseline YAML:", font=FONTS['default']).grid(row=1, column=0, sticky="w", pady=5)
yaml_entry = ttk.Entry(baseline_controls, textvariable=yaml_path_var, style="Modern.TEntry")
yaml_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
ttk.Button(baseline_controls, text=f"{ICONS['folder']} Browse", 
           command=lambda: yaml_path_var.set(filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])),
           style="Secondary.TButton").grid(row=1, column=2, pady=5, padx=(10, 0))

# Configure grid weights
baseline_controls.columnconfigure(1, weight=1)

# Checkboxes
options_frame = ttk.Frame(baseline_frame)
options_frame.pack(fill="x", padx=20, pady=(0, 10))

ttk.Checkbutton(options_frame, text="Download ZIPs for updated items", 
                variable=download_var).pack(side="left", padx=(0, 20))
ttk.Checkbutton(options_frame, text="Extract .xccdf and generate checklist", 
                variable=extract_var).pack(side="left")

# Action buttons
btn_frame = ttk.Frame(baseline_frame)
btn_frame.pack(fill="x", padx=20, pady=(10, 20))

ttk.Button(btn_frame, text=f"{ICONS['play']} Generate New Baseline", 
           style="Accent.TButton", command=run_generate_baseline_with_feedback).pack(side="left", padx=5)
ttk.Button(btn_frame, text=f"{ICONS['reset']} Reset Baseline", 
           style="Accent.TButton", command=run_reset_baseline_with_feedback).pack(side="left", padx=5)
ttk.Button(btn_frame, text=f"{ICONS['edit']} Edit Baseline", 
           style="Secondary.TButton", 
           command=lambda: launch_file_editor(yaml_path_var.get(), root)).pack(side="left", padx=5)
ttk.Button(btn_frame, text=f"{ICONS['import']} Import CKLB Library", 
           style="Secondary.TButton", command=import_cklb_with_feedback).pack(side="left", padx=5)
ttk.Button(btn_frame, text=f"{ICONS['run']} Run Tasks", 
           style="Accent.TButton", command=run_compare_with_feedback).pack(side="left", padx=5)

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

# Left panel: User CKLBs
left_panel = ttk.LabelFrame(content_frame, text="Select CKLBs to upgrade", style="TLabelframe")
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

file_listbox_frame = ttk.Frame(left_panel)
file_listbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

file_scrollbar = ttk.Scrollbar(file_listbox_frame)
file_scrollbar.pack(side="right", fill="y")

file_listbox = tk.Listbox(file_listbox_frame, 
                         selectmode=tk.MULTIPLE,
                         font=FONTS['default'],
                         bg=COLORS['input_bg'],
                         fg=COLORS['text_primary'],
                         selectbackground=COLORS['accent'],
                         selectforeground="#ffffff",
                         yscrollcommand=file_scrollbar.set)
file_listbox.pack(side="left", fill="both", expand=True)
file_scrollbar.config(command=file_listbox.yview)

# Populate listbox
for f in usr_files:
    file_listbox.insert(tk.END, f)

# Right panel: New version
right_panel = ttk.LabelFrame(content_frame, text="Select new CKLB version", style="TLabelframe")
right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

cklb_frame = ttk.Frame(right_panel)
cklb_frame.pack(fill="x", padx=10, pady=10)

cklb_combobox = ttk.Combobox(cklb_frame, textvariable=cklb_sel_var, 
                             values=cklb_files, state='readonly', 
                             font=FONTS['default'], style="Modern.TCombobox")
cklb_combobox.pack(fill="x")

# Buttons
button_frame = ttk.Frame(checklist_frame)
button_frame.pack(pady=20)

ttk.Button(button_frame, text=f"{ICONS['update']} Update Now", 
           style="Accent.TButton", command=update_now_handler).pack(side="left", padx=5)
ttk.Button(button_frame, text=f"{ICONS['folder']} Open CKLB Directory", 
           style="Secondary.TButton", command=download_cklb_popup).pack(side="left", padx=5)

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