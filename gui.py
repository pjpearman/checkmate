import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import logging
import os

from cklb_importer import import_cklb_files
from handlers import run_generate_baseline_task, run_compare_task, run_merge_task
from selected_merger import load_cklb, save_cklb

# === Logger ===
class GuiLogger(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)

# === New Rule Input Dialog ===
class MultiRuleInputDialog(tk.Toplevel):
    def __init__(self, parent, new_rules, checklist_files):
        super().__init__(parent)
        self.title("Input for New Rules")
        self.result = None
        self.configure(bg="#f5f5f5")

        # Checklist Selection
        checklist_frame = ttk.Frame(self)
        checklist_frame.pack(fill="x", pady=(12, 8), padx=12)
        ttk.Label(checklist_frame, text="Apply to selected checklists:").pack(side="left")
        self.cklb_vars = []
        for f in checklist_files:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(checklist_frame, text=f, variable=var).pack(side="left", padx=6)
            self.cklb_vars.append((f, var))

        # Bulk Fill
        bulk_frame = ttk.Frame(self)
        bulk_frame.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(bulk_frame, text="Bulk Fill Status:").pack(side="left")
        self.status_bulk = tk.StringVar(value="not_reviewed")
        status_bulk_cb = ttk.Combobox(bulk_frame, textvariable=self.status_bulk,
            values=["not_reviewed", "not_applicable", "open", "not_a_finding"], state="readonly", width=18)
        status_bulk_cb.pack(side="left", padx=5)
        ttk.Label(bulk_frame, text="Comment:").pack(side="left")
        self.comment_bulk = tk.StringVar()
        comment_bulk_entry = ttk.Entry(bulk_frame, textvariable=self.comment_bulk, width=40)
        comment_bulk_entry.pack(side="left", padx=5)
        ttk.Button(bulk_frame, text="Apply to all", command=self.bulk_fill).pack(side="left", padx=10)

        # Scrollable Table
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True, padx=12)
        canvas = tk.Canvas(canvas_frame, height=300, bg="#f5f5f5", highlightthickness=0)
        scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.table_frame = ttk.Frame(canvas)
        self.table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        canvas.config(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Table Headers
        headers = ["ID", "Rule Title", "Status", "Comment", "Ignore"]
        col_weights = [0, 1, 0, 2, 0]
        for c, col in enumerate(headers):
            ttk.Label(self.table_frame, text=col, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=c, padx=5, pady=3, sticky="nsew")
            self.table_frame.columnconfigure(c, weight=col_weights[c])

        # Rows
        self.entries = []
        for i, rule in enumerate(new_rules, 1):
            bg = "#f0f4fc" if i % 2 == 0 else "#ffffff"
            row_id = rule["group_id_src"]
            rule_title = rule["rule_title"] or row_id

            # ID
            ttk.Label(self.table_frame, text=row_id, background=bg, anchor="w").grid(row=i, column=0, sticky="nsew", padx=5, pady=2)

            # Rule Title (wrapped)
            title_lbl = ttk.Label(self.table_frame, text=rule_title, background=bg, anchor="w", wraplength=300, justify="left")
            title_lbl.grid(row=i, column=1, sticky="nsew", padx=5, pady=2)

            # Status
            status_var = tk.StringVar(value="not_reviewed")
            status_cb = ttk.Combobox(self.table_frame, textvariable=status_var,
                values=["not_reviewed", "not_applicable", "open", "not_a_finding"], state="readonly", width=18)
            status_cb.grid(row=i, column=2, padx=5, pady=2)
            status_cb.configure(background=bg)

            # Comment (wrapped to 3 lines)
            comment_var = tk.StringVar()
            comment_entry = tk.Text(self.table_frame, height=3, width=40, wrap="word", background=bg)
            comment_entry.grid(row=i, column=3, sticky="nsew", padx=5, pady=2)

            # Ignore
            ignore_var = tk.BooleanVar(value=False)
            ignore_cb = ttk.Checkbutton(self.table_frame, variable=ignore_var)
            ignore_cb.grid(row=i, column=4, padx=5, pady=2)
            ignore_cb.configure(style="Toolbutton")

            self.entries.append({
                "group_id_src": row_id,
                "status_var": status_var,
                "comment_widget": comment_entry,
                "ignore_var": ignore_var
            })

        # Buttons
        btns = ttk.Frame(self)
        btns.pack(pady=(12, 8))
        ttk.Button(btns, text="OK", command=self.on_apply, width=10).pack(side="left", padx=12)
        ttk.Button(btns, text="Cancel", command=self.on_cancel, width=10).pack(side="left", padx=12)

    def bulk_fill(self):
        value = self.status_bulk.get()
        comment = self.comment_bulk.get()
        for e in self.entries:
            if not e["ignore_var"].get():
                e["status_var"].set(value)
                e["comment_widget"].delete("1.0", "end")
                e["comment_widget"].insert("1.0", comment)

    def on_apply(self):
        selected_cklbs = [fname for fname, var in self.cklb_vars if var.get()]
        results = []
        for entry in self.entries:
            if entry["ignore_var"].get():
                continue
            results.append({
                "group_id_src": entry["group_id_src"],
                "status": entry["status_var"].get(),
                "comments": entry["comment_widget"].get("1.0", "end").strip()
            })
        self.result = {
            "apply_cklbs": selected_cklbs,
            "rules": results
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

# === GUI Setup ===
root = tk.Tk()
root.title("StigFlow")
root.geometry("1100x800")
root.configure(bg="#f7fafd")

# === Variables (must be defined before layout) ===
mode_var = tk.StringVar(value="benchmark")
headful_var = tk.BooleanVar()
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

# === Refresh Combo Logic ===
def refresh_cklb_combobox():
    new_cklb_files = sorted(os.listdir(cklb_dir)) if os.path.isdir(cklb_dir) else []
    cklb_combobox['values'] = new_cklb_files

# === Refresh User CKLB Library ===
def refresh_usr_listbox():
    usr_files = sorted(os.listdir(usr_dir)) if os.path.isdir(usr_dir) else []
    file_listbox.delete(0, tk.END)
    for f in usr_files:
        file_listbox.insert(tk.END, f)

# === Handler must come after widgets ===
def update_now_handler():
    selected_old_files = [file_listbox.get(i) for i in file_listbox.curselection()]
    new_name = cklb_sel_var.get()
    merged_results = run_merge_task(
        selected_old_files=selected_old_files,
        new_name=new_name,
        usr_dir=usr_dir,
        cklb_dir=cklb_dir,
        on_status_update=status_text.set
    )
    for result in merged_results:
        if result["new_rules"]:
            dialog = MultiRuleInputDialog(root, result["new_rules"], [result["merged_name"]])
            root.wait_window(dialog)
            user_input = dialog.result
            if user_input:
                merged_cklb = load_cklb(result["merged_path"])
                for rule_entry in user_input["rules"]:
                    for stig in merged_cklb.get("stigs", []):
                        for rule in stig.get("rules", []):
                            if rule.get("group_id_src") == rule_entry["group_id_src"]:
                                rule["status"] = rule_entry["status"]
                                rule["comments"] = rule_entry["comments"]
                save_cklb(result["merged_path"], merged_cklb)
                status_text.set(f"Updated {len(user_input['rules'])} new rules in {result['merged_name']}")

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

# === Top Controls Group ===
top_controls = ttk.Labelframe(frame, text="Scrape and Baseline Options", padding=18, style="TLabelframe")
top_controls.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 18), padx=0)

# Use a single grid for all controls in top_controls for perfect alignment
scrape_label = ttk.Label(top_controls, text="Scrape Mode:", font=LABEL_FONT)
scrape_label.grid(row=0, column=0, padx=(0, 10), pady=4, sticky="w")
scrape_combo = ttk.Combobox(top_controls, textvariable=mode_var, values=["benchmark", "checklist", "application", "network", "all"], state="readonly", width=15)
scrape_combo.grid(row=0, column=1, padx=(0, 10), pady=4, sticky="ew")
headful_cb = ttk.Checkbutton(top_controls, text="Headful Browser", variable=headful_var)
headful_cb.grid(row=0, column=2, padx=(0, 10), pady=4, sticky="w")

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
ttk.Button(btn_col, text="Generate New Baseline", style="Accent.TButton", command=lambda: run_generate_baseline_task(
    mode=mode_var.get(),
    headful=headful_var.get(),
    on_status_update=status_text.set,
    clear_log=lambda: log_output.delete(1.0, tk.END)
)).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Import CKLB Library", style="Accent.TButton", command=lambda: import_cklb_files(on_import_complete=refresh_usr_listbox)).pack(fill="x", pady=(0, 10))
ttk.Button(btn_col, text="Run Tasks", style="Accent.TButton", command=lambda: run_compare_task(
    mode=mode_var.get(),
    headful=headful_var.get(),
    baseline_path=yaml_path_var.get(),
    download_updates_checked=download_var.get(),
    extract_checked=extract_var.get(),
    on_status_update=status_text.set,
    clear_log=lambda: log_output.delete(1.0, tk.END),
    on_cklb_refresh=refresh_cklb_combobox
)).pack(fill="x")

for i in range(3):
    top_controls.columnconfigure(i, weight=1)
top_controls.columnconfigure(3, weight=0)

# === Separator ===
sep1 = ttk.Separator(frame, orient="horizontal")
sep1.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 18))

# === Merge Area ===
merge_area = ttk.Labelframe(frame, text="Checklist Merge & Upgrade", padding=18, style="TLabelframe")
merge_area.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 18))
frame.rowconfigure(2, weight=2)

left_panel = ttk.Frame(merge_area, style="TLabelframe")
left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 18), pady=4)
merge_area.columnconfigure(0, weight=2)
merge_area.rowconfigure(0, weight=1)
ttk.Label(left_panel, text="Select one or more CKLBs to upgrade", font=HEADER_FONT, background=SECTION_BG, foreground=ACCENT, anchor="w").pack(fill="x", pady=(0, 8))
left_scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL)
file_listbox = tk.Listbox(left_panel, selectmode=tk.MULTIPLE, exportselection=False, yscrollcommand=left_scrollbar.set, font=LABEL_FONT, bg="#f0f4fc", relief="flat", borderwidth=1, highlightthickness=0)
left_scrollbar.config(command=file_listbox.yview)
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

center_panel = ttk.Frame(merge_area, style="TLabelframe")
center_panel.grid(row=0, column=1, sticky='nsew', padx=(0, 18), pady=4)
merge_area.columnconfigure(1, weight=1)
ttk.Button(center_panel, text="Update Now", style="Accent.TButton", command=update_now_handler).pack(pady=40, fill="x")

right_panel = ttk.Frame(merge_area, style="TLabelframe")
right_panel.grid(row=0, column=2, sticky='nsew', pady=4)
merge_area.columnconfigure(2, weight=2)
ttk.Label(right_panel, text="Select new cklb version", font=HEADER_FONT, background=SECTION_BG, foreground=ACCENT, anchor="w").pack(fill="x", pady=(0, 8))
cklb_combobox = ttk.Combobox(right_panel, textvariable=cklb_sel_var, values=cklb_files, state='readonly', font=LABEL_FONT)
cklb_combobox.pack(fill="x", padx=(0, 10))

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

log_output = scrolledtext.ScrolledText(log_area, height=8, wrap=tk.WORD, font=("Consolas", 10), bg="#f0f4fc", relief="flat", borderwidth=1)
log_output.pack(fill="both", expand=True, pady=(0, 8))

ttk.Label(log_area, textvariable=status_text, foreground=ACCENT, font=LABEL_FONT, background=SECTION_BG).pack(anchor="w", pady=(0, 2))

# === Logging Setup ===
log_handler = GuiLogger(log_output)
log_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

root.mainloop()