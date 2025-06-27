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
root.resizable(True, True)  # Allow resizing
root.configure(bg="#f7fafd")
root.protocol("WM_DELETE_WINDOW", on_closing)

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

# === Logger ===
class GuiLogger(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

# === Job Status Feedback Helper ===
def log_job_status(message):
    log_output.configure(state="normal")
    log_output.insert(tk.END, message + '\n')
    log_output.see(tk.END)
    log_output.configure(state="disabled")

# === Modified Button Commands with Feedback ===
def get_internal_mode(mode_label):
    mapping = {
        "SCAP Benchmarks": "benchmark",
        "Operating Systems": "checklist",
        "Applications": "application",
        "Network": "network",
        "ALL": "all"
    }
    return mapping.get(mode_label, "benchmark")

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
        clear_log=lambda: log_output.delete(1.0, tk.END)
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
        clear_log=lambda: log_output.delete(1.0, tk.END),
        on_cklb_refresh=refresh_cklb_combobox
    )).start()

def download_cklb_popup():
    popup = tk.Toplevel(root)
    popup.title("Open New CKLB Directory")
    popup.geometry("500x400")
    popup.grab_set()
    popup.configure(bg="#f5f5f5")

    ttk.Label(popup, text="Select CKLB(s) to download:", font=HEADER_FONT).pack(pady=(18, 8))
    updated_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_updated')
    cklb_files = sorted(os.listdir(updated_dir)) if os.path.isdir(updated_dir) else []

    listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE, font=LABEL_FONT, bg="#f0f4fc", width=60, height=12)
    for f in cklb_files:
        listbox.insert(tk.END, f)
    listbox.pack(padx=18, pady=(0, 18), fill="both", expand=True)

    def do_download():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if not selected:
            log_job_status("[ERROR] Please select at least one CKLB file.")
            return
        try:
            dest_dir = filedialog.askdirectory(title="Select Destination Directory")
        except Exception as e:
            log_job_status(f"[ERROR] File dialog failed: {e}")
            return
        if not dest_dir:
            log_job_status("[INFO] Download cancelled (no directory selected).")
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
        popup.grab_release()
        popup.destroy()

    ttk.Button(popup, text="Download Selected", style="Accent.TButton", command=do_download).pack(pady=(0, 18))
    ttk.Button(popup, text="Cancel", command=lambda: [popup.grab_release(), popup.destroy()]).pack()

def run_reset_baseline_with_feedback():
    baseline_path = yaml_path_var.get()
    if not baseline_path or not os.path.exists(baseline_path):
        log_job_status("[ERROR] Please select a valid Baseline YAML file.")
        return
    # Load YAML and get product list
    try:
        with open(baseline_path, 'r') as f:
            data = yaml.safe_load(f)
        products = list(data.keys())
    except Exception as e:
        log_job_status(f"[ERROR] Failed to load baseline: {e}")
        return
    # Inline product selection UI
    if hasattr(run_reset_baseline_with_feedback, 'sel_frame') and run_reset_baseline_with_feedback.sel_frame:
        run_reset_baseline_with_feedback.sel_frame.destroy()
    sel_frame = ttk.Frame(frame)
    sel_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)
    run_reset_baseline_with_feedback.sel_frame = sel_frame
    ttk.Label(sel_frame, text="Select baseline products to reset:", font=HEADER_FONT).pack(anchor="w", padx=18, pady=(8, 8))
    select_all_var = tk.BooleanVar()
    prod_vars = []
    def on_select_all():
        for _, var in prod_vars:
            var.set(select_all_var.get())
    select_all_cb = ttk.Checkbutton(sel_frame, text="Select All", variable=select_all_var, command=on_select_all)
    select_all_cb.pack(anchor="w", padx=18)
    # Product checkboxes
    for prod in products:
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(sel_frame, text=prod, variable=var)
        cb.pack(anchor="w", padx=36)
        prod_vars.append((prod, var))
    # Reset and Cancel buttons
    btn_frame = ttk.Frame(sel_frame)
    btn_frame.pack(pady=(8, 10))
    def do_reset():
        selected = [prod for prod, var in prod_vars if var.get()]
        if not selected:
            log_job_status("[ERROR] Please select at least one product.")
            return
        msg = "This will set 'Release' and 'Version' to '0' for: " + ", ".join(selected) + ". Proceed?"
        def do_confirm():
            ok = reset_baseline_fields(baseline_path, selected)
            if ok:
                log_job_status(f"[INFO] Reset Release and Version for {len(selected)} product(s).")
                sel_frame.destroy()
                run_reset_baseline_with_feedback.sel_frame = None
            else:
                log_job_status("[ERROR] Failed to reset one or more products. See log for details.")
        def do_cancel():
            log_job_status("[INFO] Reset cancelled.")
            sel_frame.destroy()
            run_reset_baseline_with_feedback.sel_frame = None
        confirm_frame = ttk.Frame(sel_frame)
        confirm_frame.pack(pady=(8, 0))
        ttk.Label(confirm_frame, text=msg, foreground="red").pack(side="left", padx=10)
        ttk.Button(confirm_frame, text="Yes", style="Accent.TButton", command=do_confirm).pack(side="left", padx=10)
        ttk.Button(confirm_frame, text="No", command=do_cancel).pack(side="left", padx=10)
    ttk.Button(btn_frame, text="Reset Baseline", style="Accent.TButton", command=do_reset).pack(side="left", padx=12)
    def on_cancel():
        sel_frame.destroy()
        run_reset_baseline_with_feedback.sel_frame = None
        log_job_status("[INFO] Reset cancelled.")
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=12)

# === New Rule Input Dialog ===
# Replaces MultiRuleInputDialog pop-up with inline widget

def show_multi_rule_input(new_rules, checklist_files, on_submit, on_cancel):
    if hasattr(show_multi_rule_input, 'frame') and show_multi_rule_input.frame:
        show_multi_rule_input.frame.destroy()
    frame_mr = ttk.Frame(frame)
    frame_mr.grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)
    show_multi_rule_input.frame = frame_mr
    ttk.Label(frame_mr, text="Input for New Rules", font=HEADER_FONT).pack(anchor="w", padx=12, pady=(8, 8))
    # Checklist selection
    checklist_frame = ttk.Frame(frame_mr)
    checklist_frame.pack(fill="x", padx=12, pady=(0, 8))
    ttk.Label(checklist_frame, text="Apply to selected checklists:").pack(side="left")
    cklb_vars = []
    for f in checklist_files:
        var = tk.BooleanVar(value=True)
        ttk.Checkbutton(checklist_frame, text=f, variable=var).pack(side="left", padx=6)
        cklb_vars.append((f, var))
    # Bulk fill
    bulk_frame = ttk.Frame(frame_mr)
    bulk_frame.pack(fill="x", padx=12, pady=(0, 10))
    ttk.Label(bulk_frame, text="Bulk Fill Status:").pack(side="left")
    status_bulk = tk.StringVar(value="not_reviewed")
    status_bulk_cb = ttk.Combobox(bulk_frame, textvariable=status_bulk,
        values=["not_reviewed", "not_applicable", "open", "not_a_finding"], state="readonly", width=18)
    status_bulk_cb.pack(side="left", padx=5)
    ttk.Label(bulk_frame, text="Comment:").pack(side="left")
    comment_bulk = tk.StringVar()
    comment_bulk_entry = ttk.Entry(bulk_frame, textvariable=comment_bulk, width=40)
    comment_bulk_entry.pack(side="left", padx=5)
    # Table
    canvas_frame = ttk.Frame(frame_mr)
    canvas_frame.pack(fill="both", expand=True, padx=12)
    canvas = tk.Canvas(canvas_frame, height=300, bg="#f5f5f5", highlightthickness=0)
    scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    table_frame = ttk.Frame(canvas)
    table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=table_frame, anchor="nw")
    canvas.config(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    headers = ["ID", "Rule Title", "Status", "Comment", "Ignore"]
    col_weights = [0, 1, 0, 2, 0]
    for c, col in enumerate(headers):
        ttk.Label(table_frame, text=col, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=c, padx=5, pady=3, sticky="nsew")
        table_frame.columnconfigure(c, weight=col_weights[c])
    entries = []
    for i, rule in enumerate(new_rules, 1):
        bg = "#f0f4fc" if i % 2 == 0 else "#ffffff"
        row_id = rule["group_id_src"]
        rule_title = rule["rule_title"] or row_id
        ttk.Label(table_frame, text=row_id, background=bg, anchor="w").grid(row=i, column=0, sticky="nsew", padx=5, pady=2)
        title_lbl = ttk.Label(table_frame, text=rule_title, background=bg, anchor="w", wraplength=300, justify="left")
        title_lbl.grid(row=i, column=1, sticky="nsew", padx=5, pady=2)
        status_var = tk.StringVar(value="not_reviewed")
        status_cb = ttk.Combobox(table_frame, textvariable=status_var,
            values=["not_reviewed", "not_applicable", "open", "not_a_finding"], state="readonly", width=18)
        status_cb.grid(row=i, column=2, padx=5, pady=2)
        status_cb.configure(background=bg)
        comment_entry = tk.Text(table_frame, height=3, width=40, wrap="word", background=bg)
        comment_entry.grid(row=i, column=3, sticky="nsew", padx=5, pady=2)
        ignore_var = tk.BooleanVar(value=False)
        ignore_cb = ttk.Checkbutton(table_frame, variable=ignore_var)
        ignore_cb.grid(row=i, column=4, padx=5, pady=2)
        ignore_cb.configure(style="Toolbutton")
        entries.append({
            "group_id_src": row_id,
            "status_var": status_var,
            "comment_widget": comment_entry,
            "ignore_var": ignore_var
        })
    # Bulk fill logic
    def bulk_fill():
        value = status_bulk.get()
        comment = comment_bulk.get()
        for e in entries:
            if not e["ignore_var"].get():
                e["status_var"].set(value)
                e["comment_widget"].delete("1.0", "end")
                e["comment_widget"].insert("1.0", comment)
    ttk.Button(bulk_frame, text="Apply to all", command=bulk_fill).pack(side="left", padx=10)
    # OK/Cancel
    btns = ttk.Frame(frame_mr)
    btns.pack(pady=(12, 8))
    def do_ok():
        selected_cklbs = [fname for fname, var in cklb_vars if var.get()]
        results = []
        for entry in entries:
            if entry["ignore_var"].get():
                continue
            results.append({
                "group_id_src": entry["group_id_src"],
                "status": entry["status_var"].get(),
                "comments": entry["comment_widget"].get("1.0", "end").strip()
            })
        frame_mr.destroy()
        show_multi_rule_input.frame = None
        on_submit({"apply_cklbs": selected_cklbs, "rules": results})
    def do_cancel():
        frame_mr.destroy()
        show_multi_rule_input.frame = None
        on_cancel()
    ttk.Button(btns, text="OK", command=do_ok, width=10).pack(side="left", padx=12)
    ttk.Button(btns, text="Cancel", command=do_cancel, width=10).pack(side="left", padx=12)

# Patch update_now_handler to use inline multi-rule input
# === Handler must come after widgets ===
def update_now_handler():
    # Check for selection errors
    selected_old_files = [file_listbox.get(i) for i in file_listbox.curselection()]
    new_name = cklb_sel_var.get()
    if not selected_old_files:
        log_job_status("[ERROR] Please select at least one CKLB to upgrade.")
        return
    if not new_name:
        log_job_status("[ERROR] Please select a new CKLB version to upgrade to.")
        return

    # --- STIG ID mismatch check before merge ---
    old_path = os.path.join(usr_dir, selected_old_files[0])
    new_path = os.path.join(cklb_dir, new_name)
    try:
        old_data = load_cklb(old_path)
        new_data = load_cklb(new_path)
        is_match, old_stig_id, new_stig_id, new_rules = check_stig_id_match(old_data, new_data)
        if not is_match:
            msg = (f"The STIG ID of the old checklist does not match the new checklist.\n"
                   f"Old STIG ID: {old_stig_id}\nNew STIG ID: {new_stig_id}\n"
                   f"Number of new rules in the new checklist: {len(new_rules)}\n\n"
                   "Proceed with merge?")
            # Inline confirmation widget
            def do_confirm_merge():
                confirm_frame.destroy()
                proceed_merge(True)
            def do_cancel_merge():
                confirm_frame.destroy()
                log_job_status("[ERROR] Merge cancelled by user due to STIG ID mismatch.")
            confirm_frame = ttk.Frame(frame)
            confirm_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)
            ttk.Label(confirm_frame, text=msg, foreground="red").pack(side="left", padx=10)
            ttk.Button(confirm_frame, text="Proceed", style="Accent.TButton", command=do_confirm_merge).pack(side="left", padx=10)
            ttk.Button(confirm_frame, text="Cancel", command=do_cancel_merge).pack(side="left", padx=10)
            def proceed_merge(force_merge):
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
                        log_job_status(f"[INFO] {len(result['new_rules'])} new rules detected. Please review in the main window.")
                        # TODO: Inline rule review UI
                log_job_status("[INFO] Job complete: Merge/update finished.")
            return
        else:
            force_merge = False
    except Exception as e:
        log_job_status(f"[ERROR] Failed to check STIG IDs: {e}")
        return

    # Check if any selected old files lack host_name
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
    prefix = None
    if needs_prefix:
        # Inline prefix entry UI
        if hasattr(update_now_handler, 'prefix_frame') and update_now_handler.prefix_frame:
            update_now_handler.prefix_frame.destroy()
        prefix_frame = ttk.Frame(frame)
        prefix_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=10)
        update_now_handler.prefix_frame = prefix_frame
        ttk.Label(prefix_frame, text="Enter host-name prefix (required):", foreground="red").pack(side="left", padx=10)
        prefix_var = tk.StringVar()
        prefix_entry = ttk.Entry(prefix_frame, textvariable=prefix_var, width=30)
        prefix_entry.pack(side="left", padx=10)
        def do_set_prefix():
            val = prefix_var.get().strip()
            if not val:
                log_job_status("[ERROR] Prefix cannot be blank. Please enter a valid prefix.")
                return
            nonlocal prefix
            prefix = val
            prefix_frame.destroy()
            update_now_handler.prefix_frame = None
            proceed_merge(force_merge)
        def do_cancel_prefix():
            log_job_status("[INFO] Prefix entry cancelled.")
            prefix_frame.destroy()
            update_now_handler.prefix_frame = None
        ttk.Button(prefix_frame, text="OK", style="Accent.TButton", command=do_set_prefix).pack(side="left", padx=10)
        ttk.Button(prefix_frame, text="Cancel", command=do_cancel_prefix).pack(side="left", padx=10)
        return

    log_job_status("[INFO] Job started: Merging/updating checklists...")
    merged_results = run_merge_task(
        selected_old_files=selected_old_files,
        new_name=new_name,
        usr_dir=usr_dir,
        cklb_dir=cklb_dir,
        on_status_update=status_text.set,
        force=force_merge,
        prefix=prefix
    )
    for result in merged_results:
        if result["new_rules"]:
            def handle_submit(user_input):
                merged_cklb = load_cklb(result["merged_path"])
                for rule_entry in user_input["rules"]:
                    for stig in merged_cklb.get("stigs", []):
                        for rule in stig.get("rules", []):
                            if rule.get("group_id_src") == rule_entry["group_id_src"]:
                                rule["status"] = rule_entry["status"]
                                rule["comments"] = rule_entry["comments"]
                save_cklb(result["merged_path"], merged_cklb)
                status_text.set(f"Updated {len(user_input['rules'])} new rules in {result['merged_name']}")
            def handle_cancel():
                log_job_status("[INFO] Multi-rule input cancelled.")
            show_multi_rule_input(result["new_rules"], [result["merged_name"]], handle_submit, handle_cancel)
        else:
            log_job_status("[INFO] Job complete: Merge/update finished.")

style = ttk.Style()
style.theme_use("clam")

# Modern color palette
PRIMARY_BG = "#f7fafd"
SECTION_BG = "#ffffff"
ACCENT = "#2563eb"
HEADER_FONT = ("Segoe UI", 13, "bold")
LABEL_FONT = ("Segoe UI", 10)
BUTTON_FONT = ("Segoe UI", 11, "bold")

style.configure("TButton", padding=10, font=BUTTON_FONT, background=ACCENT, foreground="#fff", borderwidth=0)
style.map("TButton", background=[("active", "#1d4ed8")])
style.configure("TLabel", padding=6, font=LABEL_FONT, background=SECTION_BG)
style.configure("TCheckbutton", padding=6, font=LABEL_FONT, background=SECTION_BG)
style.configure("TEntry", padding=6, font=LABEL_FONT, fieldbackground="#f0f4fc", borderwidth=1)
style.configure("TCombobox", padding=6, font=LABEL_FONT, fieldbackground="#f0f4fc", borderwidth=1)
style.configure("TLabelframe", background=SECTION_BG, borderwidth=2, relief="groove")
style.configure("TLabelframe.Label", font=HEADER_FONT, background=SECTION_BG, foreground=ACCENT)

frame = ttk.Frame(root, padding=18, style="TLabelframe", relief="flat")
frame.pack(fill=tk.BOTH, expand=True)

# === Getting Started Panel ===
getting_started = ttk.Labelframe(frame, text="Getting Started", padding=18, style="TLabelframe")
getting_started.grid(row=0, column=0, sticky="nsew", pady=(0, 18), padx=(0, 18))
getting_started.columnconfigure(0, weight=1)
getting_started.rowconfigure(0, weight=1)

# Example content for Getting Started (customize as needed)
ttks = ttk.Label(getting_started, text="1. Create & Customize Baseline.\n2. Set Custom Baseline. (Used to compare your version against published versions.)\n3. Import completed cklb.\n4. Select task options and Run Tasks. (Ensure correct mode selected for selected baseline.) \n\nIMPORTANT:\nWhen creating your first baseline, CheckMate uses the current release and version info \nfrom the DISA website. This may not align with your current cklbs. Edit the baseline \nto match that of your version release, ex:RHEL8_v1r2.\nBaselines and Scrape Mode misuse are the most common cause of download failures.", font=LABEL_FONT, background=SECTION_BG, justify="left", anchor="nw")
ttks.grid(row=0, column=0, sticky="nw", padx=0, pady=0)

# === Top Controls Group ===
top_controls = ttk.Labelframe(frame, text="Scrape and Baseline Options", padding=18, style="TLabelframe")
top_controls.grid(row=0, column=1, columnspan=2, sticky="nsew", pady=(0, 18), padx=0)

# Use a single grid for all controls in top_controls for perfect alignment
scrape_label = ttk.Label(top_controls, text="Scrape Mode:", font=LABEL_FONT)
scrape_label.grid(row=0, column=0, padx=(0, 10), pady=4, sticky="w")
scrape_combo = ttk.Combobox(top_controls, textvariable=mode_var, values=["SCAP Benchmarks", "Operating Systems", "Applications", "Network", "ALL"], state="readonly", width=15)
scrape_combo.grid(row=0, column=1, padx=(0, 10), pady=4, sticky="ew")

yaml_label = ttk.Label(top_controls, text="Baseline YAML:", font=LABEL_FONT)
yaml_label.grid(row=1, column=0, padx=(0, 10), pady=4, sticky="w")
yaml_entry = ttk.Entry(top_controls, textvariable=yaml_path_var, width=50)
yaml_entry.grid(row=1, column=1, padx=(0, 10), pady=4, sticky="ew")
yaml_browse = ttk.Button(top_controls, text="Browse", command=lambda: yaml_path_var.set(
    filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
))
yaml_browse.grid(row=1, column=2, padx=(0, 10), pady=4, sticky="w")

download_cb = ttk.Checkbutton(top_controls, text="Download ZIPs for updated items", variable=download_var)
download_cb.grid(row=2, column=0, padx=(0, 10), pady=4, sticky="w")
extract_cb = ttk.Checkbutton(top_controls, text="Extract .xccdf and generate checklist", variable=extract_var)
extract_cb.grid(row=2, column=1, padx=(0, 10), pady=4, sticky="w")

btn_col = ttk.Frame(top_controls, style="TLabelframe")
btn_col.grid(row=0, column=3, rowspan=3, padx=(30,0), pady=4, sticky="nsew")
ttk.Button(btn_col, text="Generate New Baseline", style="Accent.TButton", command=run_generate_baseline_with_feedback).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Reset Baseline", style="Accent.TButton", command=run_reset_baseline_with_feedback).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Edit Baseline", style="Accent.TButton", command=lambda: launch_file_editor(yaml_path_var.get(), root)).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Import CKLB Library", style="Accent.TButton", command=import_cklb_with_feedback).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Run Tasks", style="Accent.TButton", command=run_compare_with_feedback).pack(fill="x")

for i in range(3):
    top_controls.columnconfigure(i, weight=1)
top_controls.columnconfigure(3, weight=0)

# Adjust frame column weights for new layout
frame.columnconfigure(0, weight=1)  # Getting Started (left 1/4)
frame.columnconfigure(1, weight=3)  # Top Controls (right 3/4, spans 2 columns)
frame.columnconfigure(2, weight=3)

# === Separator ===
sep1 = ttk.Separator(frame, orient="horizontal")
sep1.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 18))

# === Merge Area ===
merge_area = ttk.Labelframe(frame, text="Checklist Merge & Upgrade", padding=18, style="TLabelframe")
merge_area.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 18))
frame.rowconfigure(2, weight=2)

# Use a single grid for all controls in merge_area for perfect alignment
# Clear any previous widgets
for widget in merge_area.winfo_children():
    widget.destroy()

# Left: User CKLBs
left_label = ttk.Label(merge_area, text="Select one or more CKLBs to upgrade", font=HEADER_FONT, background=SECTION_BG, foreground=ACCENT, anchor="w")
left_label.grid(row=0, column=0, padx=(0, 10), pady=(0, 6), sticky="w")
left_scrollbar = ttk.Scrollbar(merge_area, orient=tk.VERTICAL)
file_listbox = tk.Listbox(merge_area, selectmode=tk.MULTIPLE, exportselection=False, yscrollcommand=left_scrollbar.set, font=LABEL_FONT, bg="#f0f4fc", relief="flat", borderwidth=1, highlightthickness=0)
left_scrollbar.config(command=file_listbox.yview)
file_listbox.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 8))
left_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 8))
merge_area.rowconfigure(1, weight=1)
merge_area.columnconfigure(0, weight=2)

# Right: New CKLB Version (move to immediate right of left panel)
right_label = ttk.Label(merge_area, text="Select new cklb version", font=HEADER_FONT, background=SECTION_BG, foreground=ACCENT, anchor="w")
right_label.grid(row=0, column=2, padx=(30, 10), pady=(0, 6), sticky="w")  # Increased left padding
right_panel = ttk.Frame(merge_area, style="TLabelframe")
right_panel.grid(row=1, column=2, sticky='nsew', pady=(0, 8), padx=(30, 0))  # Increased left padding
merge_area.columnconfigure(2, weight=2)
cklb_combobox = ttk.Combobox(right_panel, textvariable=cklb_sel_var, values=cklb_files, state='readonly', font=LABEL_FONT)
cklb_combobox.pack(fill="x", padx=(0, 10))

# Center: Buttons (move to right margin, align and size like Scrape/Baseline buttons)
button_col = ttk.Frame(merge_area, style="TLabelframe")
button_col.grid(row=1, column=3, sticky="nsew", padx=(0, 18), pady=(0, 8))
merge_area.columnconfigure(3, weight=1)

update_btn = ttk.Button(button_col, text="Update Now", style="Accent.TButton", command=update_now_handler)
update_btn.pack(fill="x", pady=(0, 10))
cklb_download_btn = ttk.Button(button_col, text="Open New CKLB Directory", style="Accent.TButton", command=download_cklb_popup)
cklb_download_btn.pack(fill="x")

# Populate the listbox with files
file_listbox.delete(0, tk.END)
for f in usr_files:
    file_listbox.insert(tk.END, f)

# === Separator ===
sep2 = ttk.Separator(frame, orient="horizontal")
sep2.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))

# === Logs and Status ===
log_area = ttk.Labelframe(frame, text="Logs & Status", padding=12, style="TLabelframe")
log_area.grid(row=4, column=0, columnspan=3, sticky="nsew")
frame.rowconfigure(4, weight=1)

log_output = scrolledtext.ScrolledText(log_area, height=8, wrap=tk.WORD, font=("Consolas", 10), bg="#f0f4fc", relief="flat", borderwidth=1, state="disabled")
log_output.pack(fill="both", expand=True, pady=(0, 8))

ttk.Label(log_area, textvariable=status_text, foreground=ACCENT, font=LABEL_FONT, background=SECTION_BG).pack(anchor="w", pady=(0, 2))

# === Logging Setup ===
log_handler = GuiLogger(log_output)
log_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

root.mainloop()