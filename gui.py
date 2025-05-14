import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import logging
import os

from cklb_importer import import_cklb_files
from handlers import run_generate_baseline_task, run_compare_task, run_merge_task

# === Logger ===
class GuiLogger(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)

# === GUI Setup ===
root = tk.Tk()
root.title("StigFlow")
root.geometry("1024x768")
style = ttk.Style()
style.theme_use("clam")

style.configure("TButton", padding=6)
style.configure("TLabel", padding=4)
style.configure("TCheckbutton", padding=4)
style.configure("TEntry", padding=4)
style.configure("TCombobox", padding=4)

frame = ttk.Frame(root, padding=10)
frame.pack(fill=tk.BOTH, expand=True)

mode_var = tk.StringVar(value="benchmark")
headful_var = tk.BooleanVar()
yaml_path_var = tk.StringVar()
status_text = tk.StringVar(value="Ready")
download_var = tk.BooleanVar()
extract_var = tk.BooleanVar()

# === Directory Setup ===
usr_sel_var  = tk.StringVar()
cklb_sel_var = tk.StringVar()
usr_dir  = os.path.join(os.getcwd(), 'cklb_proc', 'usr_cklb_lib')
cklb_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_lib')
usr_files  = sorted(os.listdir(usr_dir))  if os.path.isdir(usr_dir)  else []
cklb_files = sorted(os.listdir(cklb_dir)) if os.path.isdir(cklb_dir) else []

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

# === Top Controls Group ===
top_controls = ttk.LabelFrame(frame, text="Scrape and Baseline Options", padding=10)
top_controls.grid(row=0, column=0, columnspan=3, sticky="ew", pady=5)

ttk.Label(top_controls, text="Scrape Mode:").grid(row=0, column=0, sticky=tk.W)
ttk.Combobox(top_controls, textvariable=mode_var, values=["benchmark", "checklist", "application", "network", "all"], state="readonly", width=15).grid(row=0, column=1, sticky=tk.W)
ttk.Checkbutton(top_controls, text="Headful Browser", variable=headful_var).grid(row=0, column=2, sticky=tk.W)

ttk.Label(top_controls, text="Baseline YAML:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
ttk.Entry(top_controls, textvariable=yaml_path_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=(5,0))
ttk.Button(top_controls, text="Browse", command=lambda: yaml_path_var.set(
    filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
)).grid(row=1, column=2, sticky=tk.W, pady=(5,0))

ttk.Checkbutton(top_controls, text="Download ZIPs for updated items", variable=download_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)
ttk.Checkbutton(top_controls, text="Extract .xccdf and generate checklist", variable=extract_var).grid(row=3, column=0, columnspan=2, sticky=tk.W)

ttk.Button(top_controls, text="Run StigFlow Task Sequence", command=lambda: run_compare_task(
    mode=mode_var.get(),
    headful=headful_var.get(),
    baseline_path=yaml_path_var.get(),
    download_updates_checked=download_var.get(),
    extract_checked=extract_var.get(),
    on_status_update=status_text.set,
    clear_log=lambda: log_output.delete(1.0, tk.END),
    on_cklb_refresh=refresh_cklb_combobox
)).grid(row=4, column=0, pady=10)

ttk.Button(top_controls, text="Generate New Baseline", command=lambda: run_generate_baseline_task(
    mode=mode_var.get(),
    headful=headful_var.get(),
    on_status_update=status_text.set,
    clear_log=lambda: log_output.delete(1.0, tk.END)
)).grid(row=4, column=1, pady=10)

ttk.Button(top_controls, text="Import CKLB Library", command=lambda: import_cklb_files(on_import_complete=refresh_usr_listbox)).grid(row=4, column=2, pady=10)

# === Merge Area ===
ttk.Label(frame, text="Select new cklb version").grid(row=6, column=2, sticky='w', padx=5)
cklb_combobox = ttk.Combobox(frame, textvariable=cklb_sel_var, values=cklb_files, state='readonly')
cklb_combobox.grid(row=7, column=2, sticky='n', padx=5)

ttk.Label(frame, text="Select one or more CKLBs to upgrade").grid(row=6, column=0, sticky='w', padx=5)
left_frame = ttk.Frame(frame)
left_frame.grid(row=7, column=0, sticky='nsew', padx=(5,2), pady=5)
frame.rowconfigure(7, weight=1)
frame.columnconfigure(0, weight=1)

left_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
file_listbox = tk.Listbox(left_frame, selectmode=tk.MULTIPLE, exportselection=False, yscrollcommand=left_scrollbar.set)
left_scrollbar.config(command=file_listbox.yview)
left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Populate the listbox with files
for f in usr_files:
    file_listbox.insert(tk.END, f)

ttk.Button(frame, text="Update Now", command=lambda: run_merge_task(
    selected_old_files=[file_listbox.get(i) for i in file_listbox.curselection()],
    new_name=cklb_sel_var.get(),
    usr_dir=usr_dir,
    cklb_dir=cklb_dir,
    on_status_update=status_text.set
)).grid(row=7, column=1, padx=2, pady=5)

# === Logs and Status ===
log_output = scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD)
log_output.grid(row=8, column=0, columnspan=3, sticky="nsew")
frame.rowconfigure(8, weight=1)

ttk.Label(frame, textvariable=status_text, foreground="blue").grid(row=9, column=0, columnspan=3, sticky=tk.W, pady=5)

# === Logging Setup ===
log_handler = GuiLogger(log_output)
log_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

root.mainloop()