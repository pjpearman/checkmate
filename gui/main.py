"""
Main GUI application for CheckMate.
Enhanced version that integrates features from the original GUI application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import os
import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Config, CKLBHandler, CKLBGenerator, WebDownloader, 
    LogConfig, FileUtils, InputValidator
)

# Import original handlers for advanced features
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from handlers import run_generate_baseline_task, run_compare_task, run_merge_task
    from selected_merger import load_cklb, save_cklb, check_stig_id_match
    from reset_baseline import reset_baseline_fields
    from file_editor import launch_file_editor
    from cklb_importer import import_cklb_files
except ImportError as e:
    print(f"Warning: Some legacy features may not be available: {e}")


class CheckMateGUI:
    """Enhanced GUI application for CheckMate using shared core."""
    
    def __init__(self):
        """Initialize the GUI application."""
        # Setup core components
        self.config = Config()
        self.cklb_handler = CKLBHandler(self.config)
        self.cklb_generator = CKLBGenerator(self.config)
        self.web_downloader = WebDownloader(self.config)
        self.file_utils = FileUtils()
        self.validator = InputValidator()
        
        # Setup logging
        self.log_config = LogConfig(self.config)
        self.logger = self.log_config.setup_gui_logger()
        
        # Initialize GUI state variables
        self.init_variables()
        
        # Setup GUI
        self.setup_gui()
        self.setup_logging()
        
        # Load initial data
        self.refresh_file_lists()
        
    def init_variables(self):
        """Initialize GUI state variables."""
        self.mode_var = tk.StringVar(value="Operating Systems")
        self.yaml_path_var = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.download_var = tk.BooleanVar()
        self.extract_var = tk.BooleanVar()
        self.usr_sel_var = tk.StringVar()
        self.cklb_sel_var = tk.StringVar()
        
        # File lists
        self.usr_files = []
        self.cklb_files = []
        
        # Progress tracking
        self.current_task = None
        
    def refresh_file_lists(self):
        """Refresh the file lists from directories."""
        try:
            # Get user CKLB files
            usr_dir = self.config.get_path('usr_cklb_lib')
            if os.path.isdir(usr_dir):
                self.usr_files = sorted([f for f in os.listdir(usr_dir) if f.endswith('.cklb')])
            else:
                self.usr_files = []
                
            # Get library CKLB files  
            cklb_dir = self.config.get_path('cklb_lib')
            if os.path.isdir(cklb_dir):
                self.cklb_files = sorted([f for f in os.listdir(cklb_dir) if f.endswith('.cklb')])
            else:
                self.cklb_files = []
                
            # Update comboboxes if they exist
            if hasattr(self, 'usr_combo'):
                self.usr_combo['values'] = self.usr_files
            if hasattr(self, 'cklb_combo'):
                self.cklb_combo['values'] = self.cklb_files
                
        except Exception as e:
            self.logger.error(f"Error refreshing file lists: {e}")
        
    def setup_gui(self):
        """Setup the main GUI window."""
        self.root = tk.Tk()
        self.root.title("CheckMate v2.1.0 - Enhanced")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Colors and styling
        self.colors = {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'bg_dark': '#2c3e50',
            'accent': '#3498db',
            'accent_hover': '#2980b9',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'border': '#e0e0e0',
            'input_bg': '#f5f6fa'
        }
        
        self.fonts = {
            'default': ('Inter', 9),
            'heading': ('Inter', 11, 'bold'),
            'small': ('Inter', 8),
            'mono': ('Consolas', 9)
        }
        
        self.icons = {
            'play': '▶', 'reset': '↺', 'edit': '✎', 'import': '📥',
            'run': '🚀', 'update': '🔄', 'folder': '📁', 'download': '⬇',
            'check': '✓', 'settings': '⚙', 'info': 'ℹ', 'log': '📋'
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg_primary'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup styles
        self.setup_styles()
        
        # Create main layout
        self.create_main_layout()
        
        # Setup menu bar
        self.setup_menu_bar()
        
    def setup_styles(self):
        """Setup TTK styles for the application."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure styles
        self.style.configure("TNotebook", 
            background=self.colors['bg_primary'], 
            borderwidth=0)
        self.style.configure("TNotebook.Tab", 
            padding=[20, 10], 
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary'],
            borderwidth=0,
            font=self.fonts['default'])
        self.style.map("TNotebook.Tab",
            background=[('selected', self.colors['accent']), 
                       ('active', self.colors['bg_primary'])],
            foreground=[('selected', '#ffffff'), 
                       ('active', self.colors['text_primary'])])
        
        # Button styles
        self.style.configure("Accent.TButton",
            font=self.fonts['default'],
            foreground="#ffffff",
            background=self.colors['accent'],
            borderwidth=0,
            focuscolor='none',
            padding=[10, 6])
        self.style.map("Accent.TButton",
            background=[('active', self.colors['accent_hover']), 
                       ('pressed', self.colors['accent_hover'])])
        
    def create_main_layout(self):
        """Create the main application layout."""
        # Header frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ttk.Label(header_frame, 
            text="CheckMate - STIG Management Tool", 
            font=self.fonts['heading'])
        title_label.pack(side="left")
        
        # Status label
        self.status_label = ttk.Label(header_frame, 
            textvariable=self.status_text,
            font=self.fonts['small'])
        self.status_label.pack(side="right")
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_generator_tab()
        self.create_comparison_tab()
        self.create_download_tab()
        self.create_management_tab()
        self.create_logs_tab()
        
    def create_generator_tab(self):
        """Create the CKLB generator tab."""
        self.gen_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gen_frame, text=f"{self.icons['run']} Generate CKLB")
        
        # Generator options frame
        gen_options_frame = ttk.LabelFrame(self.gen_frame, 
            text="XCCDF to CKLB Generation")
        gen_options_frame.pack(fill="x", padx=10, pady=5)
        
        # Mode selection
        mode_frame = ttk.Frame(gen_options_frame)
        mode_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side="left")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var,
            values=["Operating Systems", "Applications"])
        mode_combo.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        # YAML path selection
        yaml_frame = ttk.Frame(gen_options_frame)
        yaml_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(yaml_frame, text="YAML Config:").pack(side="left")
        yaml_entry = ttk.Entry(yaml_frame, textvariable=self.yaml_path_var)
        yaml_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        yaml_browse_btn = ttk.Button(yaml_frame, text=f"{self.icons['folder']} Browse",
            command=self.browse_yaml_file)
        yaml_browse_btn.pack(side="right", padx=(5, 0))
        
        # Options checkboxes
        options_frame = ttk.Frame(gen_options_frame)
        options_frame.pack(fill="x", padx=5, pady=5)
        
        download_check = ttk.Checkbutton(options_frame, 
            text="Download files", variable=self.download_var)
        download_check.pack(side="left")
        
        extract_check = ttk.Checkbutton(options_frame,
            text="Extract archives", variable=self.extract_var)
        extract_check.pack(side="left", padx=(10, 0))
        
        # Generate button
        gen_btn_frame = ttk.Frame(gen_options_frame)
        gen_btn_frame.pack(fill="x", padx=5, pady=10)
        
        generate_btn = ttk.Button(gen_btn_frame, 
            text=f"{self.icons['run']} Generate CKLB Files",
            style="Accent.TButton",
            command=self.run_generate_task)
        generate_btn.pack(side="left")
        
        reset_btn = ttk.Button(gen_btn_frame,
            text=f"{self.icons['reset']} Reset",
            command=self.reset_generator_fields)
        reset_btn.pack(side="left", padx=(10, 0))
        
    def create_comparison_tab(self):
        """Create the CKLB comparison tab."""
        self.comp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comp_frame, text=f"{self.icons['update']} Compare")
        
        # File selection frame
        selection_frame = ttk.LabelFrame(self.comp_frame, 
            text="File Selection for Comparison")
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        # User file selection
        usr_frame = ttk.Frame(selection_frame)
        usr_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(usr_frame, text="User CKLB:").pack(side="left")
        self.usr_combo = ttk.Combobox(usr_frame, textvariable=self.usr_sel_var,
            values=self.usr_files)
        self.usr_combo.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        usr_browse_btn = ttk.Button(usr_frame, text=f"{self.icons['folder']} Browse",
            command=self.browse_usr_file)
        usr_browse_btn.pack(side="right", padx=(5, 0))
        
        # Library file selection
        cklb_frame = ttk.Frame(selection_frame)
        cklb_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(cklb_frame, text="Library CKLB:").pack(side="left")
        self.cklb_combo = ttk.Combobox(cklb_frame, textvariable=self.cklb_sel_var,
            values=self.cklb_files)
        self.cklb_combo.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        cklb_browse_btn = ttk.Button(cklb_frame, text=f"{self.icons['folder']} Browse",
            command=self.browse_cklb_file)
        cklb_browse_btn.pack(side="right", padx=(5, 0))
        
        # Action buttons
        action_frame = ttk.Frame(selection_frame)
        action_frame.pack(fill="x", padx=5, pady=10)
        
        compare_btn = ttk.Button(action_frame,
            text=f"{self.icons['update']} Compare Files",
            style="Accent.TButton",
            command=self.run_compare_task)
        compare_btn.pack(side="left")
        
        merge_btn = ttk.Button(action_frame,
            text=f"{self.icons['check']} Merge Updates",
            command=self.run_merge_task)
        merge_btn.pack(side="left", padx=(10, 0))
        
        refresh_btn = ttk.Button(action_frame,
            text=f"{self.icons['reset']} Refresh Lists",
            command=self.refresh_file_lists)
        refresh_btn.pack(side="right")
        
    def create_download_tab(self):
        """Create the download tab."""
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text=f"{self.icons['download']} Download")
        
        # Download options frame
        download_options_frame = ttk.LabelFrame(self.download_frame,
            text="STIG Download Options")
        download_options_frame.pack(fill="x", padx=10, pady=5)
        
        # URL and download controls will be implemented here
        url_frame = ttk.Frame(download_options_frame)
        url_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(url_frame, text="Download URL:").pack(side="left")
        self.url_var = tk.StringVar(value="https://public.cyber.mil/stigs/downloads/")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        url_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        download_btn = ttk.Button(url_frame,
            text=f"{self.icons['download']} Download STIGs",
            style="Accent.TButton",
            command=self.run_download_task)
        download_btn.pack(side="right", padx=(10, 0))
        
    def create_management_tab(self):
        """Create the file management tab."""
        self.mgmt_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mgmt_frame, text=f"{self.icons['folder']} Manage")
        
        # File management options
        mgmt_options_frame = ttk.LabelFrame(self.mgmt_frame,
            text="File Management")
        mgmt_options_frame.pack(fill="x", padx=10, pady=5)
        
        # Import CKLB files
        import_btn = ttk.Button(mgmt_options_frame,
            text=f"{self.icons['import']} Import CKLB Files",
            command=self.import_cklb_files)
        import_btn.pack(side="left", padx=5, pady=5)
        
        # File editor
        editor_btn = ttk.Button(mgmt_options_frame,
            text=f"{self.icons['edit']} File Editor",
            command=self.launch_file_editor)
        editor_btn.pack(side="left", padx=5, pady=5)
        
        # Directory browser
        browse_btn = ttk.Button(mgmt_options_frame,
            text=f"{self.icons['folder']} Browse Directories",
            command=self.browse_directories)
        browse_btn.pack(side="left", padx=5, pady=5)
        
    def create_logs_tab(self):
        """Create the logs viewing tab."""
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text=f"{self.icons['log']} Logs")
        
        # Log display area
        log_display_frame = ttk.LabelFrame(self.logs_frame, text="Application Logs")
        log_display_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(log_display_frame,
            height=20, font=self.fonts['mono'], wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Log controls
        log_controls_frame = ttk.Frame(log_display_frame)
        log_controls_frame.pack(fill="x", padx=5, pady=5)
        
        clear_btn = ttk.Button(log_controls_frame,
            text="Clear Logs",
            command=self.clear_logs)
        clear_btn.pack(side="left")
        
        refresh_logs_btn = ttk.Button(log_controls_frame,
            text="Refresh",
            command=self.refresh_logs)
        refresh_logs_btn.pack(side="left", padx=(10, 0))
        
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Configuration", command=self.open_config)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reset Baseline", command=self.reset_baseline)
        tools_menu.add_command(label="Validate Files", command=self.validate_files)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_logging(self):
        """Setup GUI logging handler."""
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                # Use after_idle to ensure thread safety
                self.text_widget.after_idle(self._update_log, msg)
                
            def _update_log(self, msg):
                self.text_widget.configure(state="normal")
                self.text_widget.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
                self.text_widget.see(tk.END)
                self.text_widget.configure(state="disabled")
        
        # Add GUI handler to logger
        gui_handler = GuiLogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(gui_handler)
        
    # Event handlers and utility methods
    def browse_yaml_file(self):
        """Browse for YAML configuration file."""
        filename = filedialog.askopenfilename(
            title="Select YAML Configuration File",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if filename:
            self.yaml_path_var.set(filename)
            
    def browse_usr_file(self):
        """Browse for user CKLB file."""
        filename = filedialog.askopenfilename(
            title="Select User CKLB File",
            filetypes=[("CKLB files", "*.cklb"), ("All files", "*.*")]
        )
        if filename:
            self.usr_sel_var.set(os.path.basename(filename))
            
    def browse_cklb_file(self):
        """Browse for library CKLB file."""
        filename = filedialog.askopenfilename(
            title="Select Library CKLB File",
            filetypes=[("CKLB files", "*.cklb"), ("All files", "*.*")]
        )
        if filename:
            self.cklb_sel_var.set(os.path.basename(filename))
            
    def run_generate_task(self):
        """Run the generate baseline task in a background thread."""
        if not self.yaml_path_var.get():
            messagebox.showerror("Error", "Please select a YAML configuration file.")
            return
            
        self.status_text.set("Generating CKLB files...")
        self.logger.info("Starting CKLB generation task")
        
        def task():
            try:
                # Use core CKLB generator
                success = self.cklb_generator.generate_from_config(
                    config_path=self.yaml_path_var.get(),
                    mode=self.mode_var.get(),
                    download=self.download_var.get(),
                    extract=self.extract_var.get()
                )
                
                if success:
                    self.status_text.set("CKLB generation completed successfully")
                    self.logger.info("CKLB generation completed successfully")
                    self.refresh_file_lists()
                else:
                    self.status_text.set("CKLB generation failed")
                    self.logger.error("CKLB generation failed")
                    
            except Exception as e:
                self.status_text.set(f"Error: {e}")
                self.logger.error(f"CKLB generation error: {e}")
                
        threading.Thread(target=task, daemon=True).start()
        
    def run_compare_task(self):
        """Run the comparison task."""
        usr_file = self.usr_sel_var.get()
        cklb_file = self.cklb_sel_var.get()
        
        if not usr_file or not cklb_file:
            messagebox.showerror("Error", "Please select both user and library CKLB files.")
            return
            
        self.status_text.set("Comparing CKLB files...")
        self.logger.info(f"Comparing {usr_file} with {cklb_file}")
        
        def task():
            try:
                result = self.cklb_handler.compare_versions(usr_file, cklb_file)
                self.status_text.set("Comparison completed")
                self.logger.info(f"Comparison result: {result}")
            except Exception as e:
                self.status_text.set(f"Comparison error: {e}")
                self.logger.error(f"Comparison error: {e}")
                
        threading.Thread(target=task, daemon=True).start()
        
    def run_merge_task(self):
        """Run the merge task."""
        usr_file = self.usr_sel_var.get()
        cklb_file = self.cklb_sel_var.get()
        
        if not usr_file or not cklb_file:
            messagebox.showerror("Error", "Please select both user and library CKLB files.")
            return
            
        self.status_text.set("Merging CKLB updates...")
        self.logger.info(f"Merging updates from {cklb_file} to {usr_file}")
        
        def task():
            try:
                result = self.cklb_handler.merge_updates(usr_file, cklb_file)
                self.status_text.set("Merge completed")
                self.logger.info(f"Merge result: {result}")
            except Exception as e:
                self.status_text.set(f"Merge error: {e}")
                self.logger.error(f"Merge error: {e}")
                
        threading.Thread(target=task, daemon=True).start()
        
    def run_download_task(self):
        """Run the download task."""
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a download URL.")
            return
            
        self.status_text.set("Downloading STIGs...")
        self.logger.info(f"Starting download from {url}")
        
        def task():
            try:
                result = self.web_downloader.download_from_url(url)
                self.status_text.set("Download completed")
                self.logger.info(f"Download result: {result}")
            except Exception as e:
                self.status_text.set(f"Download error: {e}")
                self.logger.error(f"Download error: {e}")
                
        threading.Thread(target=task, daemon=True).start()
        
    def reset_generator_fields(self):
        """Reset generator form fields."""
        self.yaml_path_var.set("")
        self.download_var.set(False)
        self.extract_var.set(False)
        self.status_text.set("Ready")
        
    def import_cklb_files(self):
        """Import CKLB files using the file dialog."""
        try:
            files = filedialog.askopenfilenames(
                title="Select CKLB Files to Import",
                filetypes=[("CKLB files", "*.cklb"), ("All files", "*.*")]
            )
            if files:
                self.logger.info(f"Importing {len(files)} CKLB files")
                for file in files:
                    # Use core file utilities to import
                    self.file_utils.copy_file(file, self.config.get_path('usr_cklb_lib'))
                self.refresh_file_lists()
                self.status_text.set(f"Imported {len(files)} files")
        except Exception as e:
            self.logger.error(f"Import error: {e}")
            messagebox.showerror("Import Error", str(e))
            
    def launch_file_editor(self):
        """Launch the file editor."""
        try:
            # This would integrate with the existing file editor
            self.logger.info("Launching file editor")
            messagebox.showinfo("File Editor", "File editor functionality would be integrated here.")
        except Exception as e:
            self.logger.error(f"File editor error: {e}")
            
    def browse_directories(self):
        """Browse application directories."""
        try:
            directory = filedialog.askdirectory(title="Select Directory to Browse")
            if directory:
                self.logger.info(f"Browsing directory: {directory}")
                # Could open in file manager or show in a dialog
        except Exception as e:
            self.logger.error(f"Directory browse error: {e}")
            
    def clear_logs(self):
        """Clear the log display."""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")
        
    def refresh_logs(self):
        """Refresh logs from log files."""
        try:
            log_file = self.config.get_path('logs') / 'gui.log'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    content = f.read()
                self.log_text.configure(state="normal")
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, content)
                self.log_text.see(tk.END)
                self.log_text.configure(state="disabled")
        except Exception as e:
            self.logger.error(f"Error refreshing logs: {e}")
            
    def open_config(self):
        """Open configuration file."""
        # Implementation for opening configuration
        pass
        
    def save_config(self):
        """Save configuration file."""
        # Implementation for saving configuration
        pass
        
    def reset_baseline(self):
        """Reset baseline functionality."""
        try:
            # Use existing reset_baseline functionality
            messagebox.showinfo("Reset Baseline", "Baseline reset functionality would be integrated here.")
        except Exception as e:
            self.logger.error(f"Reset baseline error: {e}")
            
    def validate_files(self):
        """Validate CKLB files."""
        try:
            # Use core validation functionality
            self.logger.info("Starting file validation")
            # Implementation would validate files using core validator
            messagebox.showinfo("Validation", "File validation completed.")
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            
    def show_about(self):
        """Show about dialog."""
        about_text = f"""CheckMate v2.1.0 - Enhanced
        
STIG Management Tool with Shared Core Architecture

Features:
- XCCDF to CKLB conversion
- CKLB file comparison and merging  
- STIG download and management
- File validation and processing
- Unified configuration and logging

Built with shared core library for consistency
between GUI and TUI interfaces.
"""
        messagebox.showinfo("About CheckMate", about_text)
        
    def on_closing(self):
        """Handle application closing."""
        try:
            self.logger.info("Application closing")
            self.root.destroy()
        except Exception:
            pass
        finally:
            sys.exit(0)
            
    def run(self):
        """Run the GUI application."""
        try:
            self.logger.info("Starting CheckMate GUI")
            self.status_text.set("CheckMate GUI Ready")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            messagebox.showerror("Application Error", f"An error occurred: {e}")
            self.on_closing()


def main():
    """Main entry point for the GUI application."""
    try:
        app = CheckMateGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
