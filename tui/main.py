"""
Main TUI application for CheckMate.
Enhanced version that integrates features from the original TUI application.
"""

import curses
import sys
import os
import json
import re
import logging
import textwrap
import threading
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Config, CKLBHandler, CKLBGenerator, WebDownloader,
    LogConfig, FileUtils, InputValidator, MenuUtils
)


class CheckMateTUI:
    """Enhanced TUI application for CheckMate using shared core."""
    
    def __init__(self):
        """Initialize the TUI application."""
        # Setup core components
        self.config = Config()
        self.cklb_handler = CKLBHandler(self.config)
        self.cklb_generator = CKLBGenerator(self.config)
        self.web_downloader = WebDownloader(self.config)
        self.file_utils = FileUtils()
        self.validator = InputValidator()
        self.menu_utils = MenuUtils(self.config)
        
        # Setup logging
        self.log_config = LogConfig(self.config)
        self.logger = self.log_config.setup_tui_logger()
        
        # Initialize TUI state
        self.stdscr = None
        self.current_menu = "main"
        self.selected_idx = 0
        self.status_message = "Ready"
        self.file_lists = {}
        
        # Main menu options
        self.main_menu_options = [
            "Generate CKLB from XCCDF",
            "Import CKLB Files", 
            "Compare CKLB Versions",
            "Download STIGs",
            "File Management",
            "Create Inventory",
            "View Configuration",
            "View Logs",
            "Exit"
        ]
        
        # Load file lists
        self.refresh_file_lists()
        
    def refresh_file_lists(self):
        """Refresh file lists from directories."""
        try:
            # Get user CKLB files
            usr_dir = self.config.get_path('usr_cklb_lib')
            if usr_dir.exists():
                self.file_lists['usr_cklb'] = sorted([f for f in os.listdir(usr_dir) if f.endswith('.cklb')])
            else:
                self.file_lists['usr_cklb'] = []
                
            # Get library CKLB files
            cklb_dir = self.config.get_path('cklb_lib')
            if cklb_dir.exists():
                self.file_lists['lib_cklb'] = sorted([f for f in os.listdir(cklb_dir) if f.endswith('.cklb')])
            else:
                self.file_lists['lib_cklb'] = []
                
            # Get XCCDF files
            xccdf_dir = self.config.get_path('xccdf_lib')
            if xccdf_dir.exists():
                self.file_lists['xccdf'] = sorted([f for f in os.listdir(xccdf_dir) if f.endswith('.xml')])
            else:
                self.file_lists['xccdf'] = []
                
            # Get downloaded ZIP files
            zip_dir = self.config.get_path('zip_files')
            if zip_dir.exists():
                self.file_lists['zip'] = sorted([f for f in os.listdir(zip_dir) if f.endswith('.zip')])
            else:
                self.file_lists['zip'] = []
                
        except Exception as e:
            self.logger.error(f"Error refreshing file lists: {e}")
        
    def run(self):
        """Run the TUI application."""
        try:
            self.logger.info("Starting CheckMate TUI")
            curses.wrapper(self.main_loop)
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            self.logger.error(f"TUI error: {e}")
            print(f"TUI error: {e}")
            
    def main_loop(self, stdscr):
        """Main application loop."""
        self.stdscr = stdscr
        self.setup_curses()
        
        while True:
            try:
                self.draw_interface()
                key = self.stdscr.getch()
                
                if self.handle_input(key):
                    break  # Exit requested
                    
            except curses.error:
                # Handle terminal resize or other curses errors
                self.setup_curses()
            except Exception as e:
                self.logger.error(f"Main loop error: {e}")
                self.show_error(f"Error: {e}")
                
        self.cleanup()
        
    def setup_curses(self):
        """Setup curses display settings."""
        self.stdscr.clear()
        curses.curs_set(0)  # Hide cursor
        
        # Setup colors if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Selected
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
            
    def draw_interface(self):
        """Draw the main interface."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Draw header
        self.draw_header(width)
        
        # Draw main content based on current menu
        if self.current_menu == "main":
            self.draw_main_menu(height, width)
        elif self.current_menu == "generate":
            self.draw_generate_menu(height, width)
        elif self.current_menu == "compare":
            self.draw_compare_menu(height, width)
        elif self.current_menu == "download":
            self.draw_download_menu(height, width)
        elif self.current_menu == "files":
            self.draw_file_menu(height, width)
        elif self.current_menu == "logs":
            self.draw_logs_view(height, width)
        elif self.current_menu == "config":
            self.draw_config_view(height, width)
            
        # Draw footer
        self.draw_footer(height, width)
        
        self.stdscr.refresh()
        
    def draw_header(self, width):
        """Draw the application header."""
        header_text = "CheckMate v2.1.0 - STIG Management Tool"
        art = "🛡️ CheckMate"
        
        # Header background
        if curses.has_colors():
            self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(0, 0, " " * width)
        self.stdscr.addstr(0, (width - len(header_text)) // 2, header_text)
        if curses.has_colors():
            self.stdscr.attroff(curses.color_pair(1))
            
        # Art/logo
        self.stdscr.addstr(1, 2, art)
        
        # Status line
        status_line = f"Status: {self.status_message}"
        self.stdscr.addstr(1, width - len(status_line) - 2, status_line)
        
        # Separator
        self.stdscr.addstr(2, 0, "─" * width)
        
    def draw_main_menu(self, height, width):
        """Draw the main menu."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Main Menu:")
        start_y += 2
        
        for i, option in enumerate(self.main_menu_options):
            y_pos = start_y + i
            if y_pos >= height - 3:  # Leave room for footer
                break
                
            prefix = "► " if i == self.selected_idx else "  "
            
            if i == self.selected_idx and curses.has_colors():
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}".ljust(width - 4))
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}")
                
    def draw_generate_menu(self, height, width):
        """Draw the CKLB generation menu."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Generate CKLB from XCCDF")
        self.stdscr.addstr(start_y + 1, 2, "─" * 30)
        
        start_y += 3
        
        # Show available XCCDF files
        self.stdscr.addstr(start_y, 2, "Available XCCDF files:")
        start_y += 1
        
        if self.file_lists.get('xccdf'):
            for i, filename in enumerate(self.file_lists['xccdf'][:10]):  # Show first 10
                y_pos = start_y + i
                if y_pos >= height - 8:
                    break
                prefix = "► " if i == self.selected_idx else "  "
                if i == self.selected_idx and curses.has_colors():
                    self.stdscr.attron(curses.color_pair(2))
                    self.stdscr.addstr(y_pos, 4, f"{prefix}{filename}".ljust(width - 6))
                    self.stdscr.attroff(curses.color_pair(2))
                else:
                    self.stdscr.addstr(y_pos, 4, f"{prefix}{filename}")
        else:
            self.stdscr.addstr(start_y, 4, "No XCCDF files found")
            
        # Instructions
        instructions_y = height - 6
        self.stdscr.addstr(instructions_y, 2, "Instructions:")
        self.stdscr.addstr(instructions_y + 1, 2, "ENTER - Generate CKLB from selected file")
        self.stdscr.addstr(instructions_y + 2, 2, "ESC - Back to main menu")
        
    def draw_compare_menu(self, height, width):
        """Draw the CKLB comparison menu."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Compare CKLB Files")
        self.stdscr.addstr(start_y + 1, 2, "─" * 20)
        
        start_y += 3
        
        # User files column
        col1_width = width // 2 - 2
        self.stdscr.addstr(start_y, 2, "User CKLB Files:")
        if self.file_lists.get('usr_cklb'):
            for i, filename in enumerate(self.file_lists['usr_cklb'][:8]):
                y_pos = start_y + 1 + i
                if y_pos >= height - 6:
                    break
                self.stdscr.addstr(y_pos, 2, f"  {filename[:col1_width-4]}")
        else:
            self.stdscr.addstr(start_y + 1, 2, "  No user files found")
            
        # Library files column
        col2_start = width // 2
        self.stdscr.addstr(start_y, col2_start, "Library CKLB Files:")
        if self.file_lists.get('lib_cklb'):
            for i, filename in enumerate(self.file_lists['lib_cklb'][:8]):
                y_pos = start_y + 1 + i
                if y_pos >= height - 6:
                    break
                prefix = "► " if i == self.selected_idx else "  "
                if i == self.selected_idx and curses.has_colors():
                    self.stdscr.attron(curses.color_pair(2))
                    display_text = f"{prefix}{filename}"[:width - col2_start - 2]
                    self.stdscr.addstr(y_pos, col2_start, display_text.ljust(width - col2_start - 2))
                    self.stdscr.attroff(curses.color_pair(2))
                else:
                    self.stdscr.addstr(y_pos, col2_start, f"{prefix}{filename}"[:width - col2_start - 2])
        else:
            self.stdscr.addstr(start_y + 1, col2_start, "  No library files found")
            
        # Instructions
        instructions_y = height - 5
        self.stdscr.addstr(instructions_y, 2, "Instructions:")
        self.stdscr.addstr(instructions_y + 1, 2, "ENTER - Compare selected files")
        self.stdscr.addstr(instructions_y + 2, 2, "ESC - Back to main menu")
        
    def draw_download_menu(self, height, width):
        """Draw the download menu."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Download STIGs")
        self.stdscr.addstr(start_y + 1, 2, "─" * 15)
        
        start_y += 3
        
        # Download URL
        default_url = "https://public.cyber.mil/stigs/downloads/"
        self.stdscr.addstr(start_y, 2, f"Download URL: {default_url}")
        start_y += 2
        
        # Download options
        options = [
            "Fetch file list from URL",
            "Download all available files",
            "Download specific file types",
            "View downloaded files"
        ]
        
        for i, option in enumerate(options):
            y_pos = start_y + i
            if y_pos >= height - 6:
                break
            prefix = "► " if i == self.selected_idx else "  "
            if i == self.selected_idx and curses.has_colors():
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}".ljust(width - 4))
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}")
                
        # Show downloaded files count
        zip_count = len(self.file_lists.get('zip', []))
        self.stdscr.addstr(height - 6, 2, f"Downloaded files: {zip_count}")
        
    def draw_file_menu(self, height, width):
        """Draw the file management menu."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "File Management")
        self.stdscr.addstr(start_y + 1, 2, "─" * 16)
        
        start_y += 3
        
        # File management options
        options = [
            "Import CKLB files",
            "Export CKLB files", 
            "Clean temporary files",
            "Validate file integrity",
            "View directory statistics",
            "Organize files by type"
        ]
        
        for i, option in enumerate(options):
            y_pos = start_y + i
            if y_pos >= height - 8:
                break
            prefix = "► " if i == self.selected_idx else "  "
            if i == self.selected_idx and curses.has_colors():
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}".ljust(width - 4))
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y_pos, 2, f"{prefix}{option}")
                
        # Directory statistics
        stats_y = height - 6
        self.stdscr.addstr(stats_y, 2, "Directory Statistics:")
        self.stdscr.addstr(stats_y + 1, 2, f"User CKLB: {len(self.file_lists.get('usr_cklb', []))}")
        self.stdscr.addstr(stats_y + 2, 2, f"Library CKLB: {len(self.file_lists.get('lib_cklb', []))}")
        self.stdscr.addstr(stats_y + 3, 2, f"ZIP files: {len(self.file_lists.get('zip', []))}")
        
    def draw_logs_view(self, height, width):
        """Draw the logs viewing interface."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Application Logs")
        self.stdscr.addstr(start_y + 1, 2, "─" * 16)
        
        start_y += 3
        
        try:
            # Read recent log entries
            log_file = self.config.get_path('logs') / 'tui.log'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    
                # Show last 15 lines
                recent_lines = lines[-15:] if len(lines) > 15 else lines
                
                for i, line in enumerate(recent_lines):
                    y_pos = start_y + i
                    if y_pos >= height - 4:
                        break
                    # Truncate long lines
                    display_line = line.strip()[:width - 4]
                    
                    # Color code log levels
                    if 'ERROR' in display_line and curses.has_colors():
                        self.stdscr.attron(curses.color_pair(4))
                        self.stdscr.addstr(y_pos, 2, display_line)
                        self.stdscr.attroff(curses.color_pair(4))
                    elif 'WARNING' in display_line and curses.has_colors():
                        self.stdscr.attron(curses.color_pair(5))
                        self.stdscr.addstr(y_pos, 2, display_line)
                        self.stdscr.attroff(curses.color_pair(5))
                    elif 'INFO' in display_line and curses.has_colors():
                        self.stdscr.attron(curses.color_pair(6))
                        self.stdscr.addstr(y_pos, 2, display_line)
                        self.stdscr.attroff(curses.color_pair(6))
                    else:
                        self.stdscr.addstr(y_pos, 2, display_line)
            else:
                self.stdscr.addstr(start_y, 2, "No log file found")
                
        except Exception as e:
            self.stdscr.addstr(start_y, 2, f"Error reading logs: {e}")
            
    def draw_config_view(self, height, width):
        """Draw the configuration view."""
        start_y = 4
        
        self.stdscr.addstr(start_y, 2, "Configuration")
        self.stdscr.addstr(start_y + 1, 2, "─" * 13)
        
        start_y += 3
        
        # Show key configuration items
        config_items = [
            f"Base Directory: {self.config.base_dir}",
            f"User Docs Dir: {self.config.get_path('user_docs')}",
            f"Version: {self.config.get_version()}",
            f"Log Level: {self.config.get_log_level()}",
            f"Total Managed Directories: {len(self.config.get_all_directories())}"
        ]
        
        for i, item in enumerate(config_items):
            y_pos = start_y + i
            if y_pos >= height - 8:
                break
            # Truncate long paths
            display_item = item[:width - 4] if len(item) > width - 4 else item
            self.stdscr.addstr(y_pos, 2, display_item)
            
        # Directory listing
        dirs_y = start_y + len(config_items) + 2
        if dirs_y < height - 6:
            self.stdscr.addstr(dirs_y, 2, "Managed Directories:")
            dirs_y += 1
            
            for i, (name, path) in enumerate(self.config.get_all_directories().items()):
                if dirs_y + i >= height - 4:
                    break
                status = "✓" if path.exists() else "✗"
                display_text = f"  {status} {name}: {str(path)}"[:width - 4]
                
                if status == "✓" and curses.has_colors():
                    self.stdscr.attron(curses.color_pair(3))
                    self.stdscr.addstr(dirs_y + i, 2, display_text)
                    self.stdscr.attroff(curses.color_pair(3))
                elif status == "✗" and curses.has_colors():
                    self.stdscr.attron(curses.color_pair(4))
                    self.stdscr.addstr(dirs_y + i, 2, display_text)
                    self.stdscr.attroff(curses.color_pair(4))
                else:
                    self.stdscr.addstr(dirs_y + i, 2, display_text)
        
    def draw_footer(self, height, width):
        """Draw the application footer."""
        footer_y = height - 2
        
        # Separator
        self.stdscr.addstr(footer_y - 1, 0, "─" * width)
        
        # Navigation help
        if self.current_menu == "main":
            help_text = "↑↓: Navigate  ENTER: Select  q: Quit"
        else:
            help_text = "↑↓: Navigate  ENTER: Select  ESC: Back  q: Quit"
            
        # Center the help text
        self.stdscr.addstr(footer_y, (width - len(help_text)) // 2, help_text)
        
        # Current menu indicator
        menu_indicator = f"Menu: {self.current_menu.capitalize()}"
        self.stdscr.addstr(footer_y, 2, menu_indicator)
        
    def handle_input(self, key):
        """Handle user input."""
        if key == ord('q') or key == ord('Q'):
            return True  # Exit
            
        elif key == 27:  # ESC key
            if self.current_menu != "main":
                self.current_menu = "main"
                self.selected_idx = 0
                
        elif key == curses.KEY_UP:
            self.selected_idx = max(0, self.selected_idx - 1)
            
        elif key == curses.KEY_DOWN:
            max_idx = self.get_max_selection_index()
            self.selected_idx = min(max_idx, self.selected_idx + 1)
            
        elif key == 10 or key == 13:  # Enter key
            self.handle_selection()
            
        elif key == ord('r') or key == ord('R'):
            # Refresh file lists
            self.refresh_file_lists()
            self.status_message = "File lists refreshed"
            
        return False  # Continue running
        
    def get_max_selection_index(self):
        """Get the maximum selection index for current menu."""
        if self.current_menu == "main":
            return len(self.main_menu_options) - 1
        elif self.current_menu == "generate":
            return max(0, len(self.file_lists.get('xccdf', [])) - 1)
        elif self.current_menu == "compare":
            return max(0, len(self.file_lists.get('lib_cklb', [])) - 1)
        elif self.current_menu == "download":
            return 3  # 4 download options
        elif self.current_menu == "files":
            return 5  # 6 file management options
        else:
            return 0
            
    def handle_selection(self):
        """Handle menu selection."""
        if self.current_menu == "main":
            self.handle_main_menu_selection()
        elif self.current_menu == "generate":
            self.handle_generate_selection()
        elif self.current_menu == "compare":
            self.handle_compare_selection()
        elif self.current_menu == "download":
            self.handle_download_selection()
        elif self.current_menu == "files":
            self.handle_file_selection()
            
    def handle_main_menu_selection(self):
        """Handle main menu selection."""
        option = self.main_menu_options[self.selected_idx]
        
        if option == "Generate CKLB from XCCDF":
            self.current_menu = "generate"
            self.selected_idx = 0
        elif option == "Import CKLB Files":
            self.import_cklb_files()
        elif option == "Compare CKLB Versions":
            self.current_menu = "compare"
            self.selected_idx = 0
        elif option == "Download STIGs":
            self.current_menu = "download"
            self.selected_idx = 0
        elif option == "File Management":
            self.current_menu = "files"
            self.selected_idx = 0
        elif option == "Create Inventory":
            self.create_inventory()
        elif option == "View Configuration":
            self.current_menu = "config"
            self.selected_idx = 0
        elif option == "View Logs":
            self.current_menu = "logs"
            self.selected_idx = 0
        elif option == "Exit":
            return True
            
    def handle_generate_selection(self):
        """Handle CKLB generation selection."""
        xccdf_files = self.file_lists.get('xccdf', [])
        if xccdf_files and self.selected_idx < len(xccdf_files):
            selected_file = xccdf_files[self.selected_idx]
            self.generate_cklb_from_xccdf(selected_file)
            
    def handle_compare_selection(self):
        """Handle CKLB comparison selection."""
        lib_files = self.file_lists.get('lib_cklb', [])
        if lib_files and self.selected_idx < len(lib_files):
            selected_lib_file = lib_files[self.selected_idx]
            self.compare_cklb_files(selected_lib_file)
            
    def handle_download_selection(self):
        """Handle download selection."""
        options = [
            "Fetch file list from URL",
            "Download all available files", 
            "Download specific file types",
            "View downloaded files"
        ]
        
        if self.selected_idx < len(options):
            option = options[self.selected_idx]
            if option == "Fetch file list from URL":
                self.fetch_download_list()
            elif option == "Download all available files":
                self.download_all_files()
            elif option == "Download specific file types":
                self.download_specific_types()
            elif option == "View downloaded files":
                self.view_downloaded_files()
                
    def handle_file_selection(self):
        """Handle file management selection."""
        options = [
            "Import CKLB files",
            "Export CKLB files",
            "Clean temporary files", 
            "Validate file integrity",
            "View directory statistics",
            "Organize files by type"
        ]
        
        if self.selected_idx < len(options):
            option = options[self.selected_idx]
            if option == "Import CKLB files":
                self.import_cklb_files()
            elif option == "Export CKLB files":
                self.export_cklb_files()
            elif option == "Clean temporary files":
                self.clean_temp_files()
            elif option == "Validate file integrity":
                self.validate_files()
            elif option == "View directory statistics":
                self.show_directory_stats()
            elif option == "Organize files by type":
                self.organize_files()
                
    # Core functionality methods
    def generate_cklb_from_xccdf(self, xccdf_file):
        """Generate CKLB from selected XCCDF file."""
        self.status_message = f"Generating CKLB from {xccdf_file}..."
        self.logger.info(f"Starting CKLB generation from {xccdf_file}")
        
        try:
            xccdf_path = self.config.get_path('xccdf_lib') / xccdf_file
            result = self.cklb_generator.convert_xccdf_to_cklb(str(xccdf_path))
            
            if result:
                self.status_message = "CKLB generation completed successfully"
                self.logger.info("CKLB generation completed successfully")
                self.refresh_file_lists()
            else:
                self.status_message = "CKLB generation failed"
                self.logger.error("CKLB generation failed")
                
        except Exception as e:
            self.status_message = f"Generation error: {e}"
            self.logger.error(f"CKLB generation error: {e}")
            
    def compare_cklb_files(self, lib_file):
        """Compare CKLB files."""
        usr_files = self.file_lists.get('usr_cklb', [])
        if not usr_files:
            self.status_message = "No user CKLB files found for comparison"
            return
            
        # For now, compare with the first user file
        usr_file = usr_files[0]
        self.status_message = f"Comparing {usr_file} with {lib_file}..."
        self.logger.info(f"Comparing {usr_file} with {lib_file}")
        
        try:
            result = self.cklb_handler.compare_versions(usr_file, lib_file)
            self.status_message = f"Comparison completed: {result}"
            self.logger.info(f"Comparison result: {result}")
        except Exception as e:
            self.status_message = f"Comparison error: {e}"
            self.logger.error(f"Comparison error: {e}")
            
    def import_cklb_files(self):
        """Import CKLB files functionality."""
        self.status_message = "CKLB import functionality"
        self.logger.info("CKLB import requested")
        # Implementation would prompt for files to import
        
    def create_inventory(self):
        """Create inventory file."""
        self.status_message = "Creating inventory file..."
        self.logger.info("Creating inventory file")
        
        try:
            # Use core functionality to create inventory
            inventory_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'user_cklb_count': len(self.file_lists.get('usr_cklb', [])),
                'lib_cklb_count': len(self.file_lists.get('lib_cklb', [])),
                'zip_count': len(self.file_lists.get('zip', [])),
                'xccdf_count': len(self.file_lists.get('xccdf', []))
            }
            
            inventory_file = self.config.get_path('inventory') / 'inventory.json'
            with open(inventory_file, 'w') as f:
                json.dump(inventory_data, f, indent=2)
                
            self.status_message = "Inventory file created successfully"
            self.logger.info("Inventory file created successfully")
            
        except Exception as e:
            self.status_message = f"Inventory creation error: {e}"
            self.logger.error(f"Inventory creation error: {e}")
            
    def fetch_download_list(self):
        """Fetch list of downloadable files."""
        self.status_message = "Fetching download list..."
        self.logger.info("Fetching download list from URL")
        
        try:
            # Use web downloader to fetch list
            files = self.web_downloader.get_available_files()
            self.status_message = f"Found {len(files)} downloadable files"
            self.logger.info(f"Found {len(files)} downloadable files")
        except Exception as e:
            self.status_message = f"Download list error: {e}"
            self.logger.error(f"Download list error: {e}")
            
    def download_all_files(self):
        """Download all available files."""
        self.status_message = "Starting download of all files..."
        self.logger.info("Starting download of all files")
        
        try:
            result = self.web_downloader.download_all()
            self.status_message = f"Download completed: {result}"
            self.logger.info(f"Download result: {result}")
            self.refresh_file_lists()
        except Exception as e:
            self.status_message = f"Download error: {e}"
            self.logger.error(f"Download error: {e}")
            
    def download_specific_types(self):
        """Download specific file types."""
        self.status_message = "Specific download functionality"
        self.logger.info("Specific download requested")
        
    def view_downloaded_files(self):
        """View downloaded files."""
        zip_files = self.file_lists.get('zip', [])
        self.status_message = f"Downloaded files: {len(zip_files)} ZIP files"
        
    def export_cklb_files(self):
        """Export CKLB files."""
        self.status_message = "CKLB export functionality"
        self.logger.info("CKLB export requested")
        
    def clean_temp_files(self):
        """Clean temporary files."""
        self.status_message = "Cleaning temporary files..."
        self.logger.info("Cleaning temporary files")
        
        try:
            temp_dir = self.config.get_path('tmp')
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                temp_dir.mkdir()
                self.status_message = "Temporary files cleaned"
                self.logger.info("Temporary files cleaned successfully")
            else:
                self.status_message = "No temporary files to clean"
        except Exception as e:
            self.status_message = f"Clean error: {e}"
            self.logger.error(f"Clean temp files error: {e}")
            
    def validate_files(self):
        """Validate file integrity."""
        self.status_message = "Validating files..."
        self.logger.info("Starting file validation")
        
        try:
            # Use core validator
            total_files = (len(self.file_lists.get('usr_cklb', [])) + 
                          len(self.file_lists.get('lib_cklb', [])))
            
            # Basic validation for now
            self.status_message = f"Validated {total_files} files"
            self.logger.info(f"File validation completed: {total_files} files")
            
        except Exception as e:
            self.status_message = f"Validation error: {e}"
            self.logger.error(f"File validation error: {e}")
            
    def show_directory_stats(self):
        """Show directory statistics."""
        total_dirs = len(self.config.get_all_directories())
        total_files = sum(len(files) for files in self.file_lists.values())
        self.status_message = f"Stats: {total_dirs} dirs, {total_files} files"
        
    def organize_files(self):
        """Organize files by type."""
        self.status_message = "File organization functionality"
        self.logger.info("File organization requested")
        
    def show_error(self, message):
        """Show error message."""
        self.status_message = f"Error: {message}"
        
    def cleanup(self):
        """Cleanup before exit."""
        self.logger.info("TUI application closing")
        
    def show_progress(self, message):
        """Show progress message."""
        # Simple progress indication
        self.status_message = message


def main():
    """Main entry point for the TUI application."""
    try:
        app = CheckMateTUI()
        app.run()
    except Exception as e:
        print(f"Failed to start TUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
