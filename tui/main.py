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
import shutil
from datetime import datetime
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
            usr_dir = self.config.get_path('cklb_artifacts')
            if usr_dir.exists():
                self.file_lists['usr_cklb'] = sorted([f for f in os.listdir(usr_dir) if f.endswith('.cklb')])
            else:
                self.file_lists['usr_cklb'] = []
                
            # Get library CKLB files
            cklb_dir = self.config.get_path('cklb_new')
            if cklb_dir.exists():
                self.file_lists['lib_cklb'] = sorted([f for f in os.listdir(cklb_dir) if f.endswith('.cklb')])
            else:
                self.file_lists['lib_cklb'] = []
                
            # Get XCCDF files - for now we'll keep looking in the legacy location
            # since XCCDF files are typically extracted temporarily
            xccdf_dir = self.config.get_path('tmp')
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
                self.show_error_screen(f"Error: {e}")
                
        self.cleanup()
        
    def cleanup(self):
        """Clean up resources and restore terminal state."""
        try:
            if self.stdscr:
                self.stdscr.clear()
                self.stdscr.refresh()
            self.logger.info("CheckMate TUI cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
        
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
            "Download specific file types",
            "View downloaded files"
        ]
        
        if self.selected_idx < len(options):
            option = options[self.selected_idx]
            if option == "Fetch file list from URL":
                self.fetch_download_list()
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
        """Generate CKLB from selected XCCDF file and save to cklb_new."""
        self.status_message = f"Generating CKLB from {xccdf_file}..."
        self.logger.info(f"Starting CKLB generation from {xccdf_file}")
        try:
            xccdf_path = self.config.get_path('tmp') / xccdf_file
            cklb_dir = self.config.get_path('cklb_new')
            cklb_name = Path(xccdf_file).stem + ".cklb"
            output_cklb = cklb_dir / cklb_name
            result = self.cklb_generator.convert_xml_to_cklb(str(xccdf_path), str(output_cklb))
            if result:
                self.status_message = f"CKLB generated: {output_cklb.name}"
                self.logger.info(f"CKLB generation completed: {output_cklb}")
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
        """Import CKLB files with TUI file browser."""
        self.status_message = "Select CKLB files to import..."
        self.logger.info("CKLB import requested")
        
        try:
            # Launch TUI file browser
            selected_files = self.file_browser_dialog()
            
            if not selected_files:
                self.status_message = "Import cancelled - no files selected"
                return
                
            # Import selected files
            target_dir = self.config.get_path('cklb_artifacts')
            imported_count = 0
            
            for file_path in selected_files:
                try:
                    if file_path.suffix.lower() == '.cklb':
                        dest_path = target_dir / file_path.name
                        
                        # Copy file to target directory
                        import shutil
                        shutil.copy2(file_path, dest_path)
                        imported_count += 1
                        self.logger.info(f"Imported: {dest_path}")
                    else:
                        self.logger.warning(f"Skipped non-CKLB file: {file_path}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to import {file_path}: {e}")
                    
            # Update status and refresh file lists
            self.status_message = f"Imported {imported_count} CKLB files successfully"
            self.refresh_file_lists()
            
        except Exception as e:
            self.status_message = f"Import error: {e}"
            self.logger.error(f"CKLB import error: {e}")
            
    def file_browser_dialog(self):
        """TUI file browser for selecting files."""
        current_dir = Path.home()  # Start from home directory
        selected_files = []
        
        while True:
            # Clear screen and show file browser
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Header
            self.stdscr.addstr(0, 0, "File Browser - Select CKLB Files")
            self.stdscr.addstr(1, 0, f"Current Directory: {current_dir}")
            self.stdscr.addstr(2, 0, "─" * width)
            
            # Get directory contents
            try:
                items = []
                if current_dir.parent != current_dir:  # Not root
                    items.append(("..", True, current_dir.parent))
                    
                # Add directories first
                dirs = [d for d in current_dir.iterdir() if d.is_dir()]
                dirs.sort()
                for d in dirs:
                    items.append((d.name + "/", True, d))
                    
                # Add files
                files = [f for f in current_dir.iterdir() if f.is_file()]
                files.sort()
                for f in files:
                    items.append((f.name, False, f))
                    
            except PermissionError:
                self.stdscr.addstr(4, 0, "Permission denied accessing this directory")
                self.stdscr.addstr(5, 0, "Press any key to go back...")
                self.stdscr.refresh()
                self.stdscr.getch()
                current_dir = current_dir.parent
                continue
                
            # Display items with selection and scrolling
            start_y = 4
            max_items = height - 10  # Leave room for instructions
            
            if hasattr(self, 'browser_selected_idx'):
                browser_selected_idx = self.browser_selected_idx
            else:
                browser_selected_idx = 0
                
            if hasattr(self, 'browser_scroll_offset'):
                scroll_offset = self.browser_scroll_offset
            else:
                scroll_offset = 0
                
            # Ensure selection is within bounds
            browser_selected_idx = min(browser_selected_idx, len(items) - 1)
            browser_selected_idx = max(0, browser_selected_idx)
            
            # Adjust scroll offset to keep selected item visible
            if browser_selected_idx < scroll_offset:
                scroll_offset = browser_selected_idx
            elif browser_selected_idx >= scroll_offset + max_items:
                scroll_offset = browser_selected_idx - max_items + 1
                
            # Ensure scroll offset is within bounds
            scroll_offset = max(0, min(scroll_offset, len(items) - max_items))
            if len(items) <= max_items:
                scroll_offset = 0
                
            # Display visible items
            visible_items = items[scroll_offset:scroll_offset + max_items]
            for i, (name, is_dir, path) in enumerate(visible_items):
                y_pos = start_y + i
                if y_pos >= height - 6:
                    break
                    
                actual_idx = scroll_offset + i
                actual_idx = scroll_offset + i
                    
                # Mark selected files
                marker = ""
                if not is_dir and path in selected_files:
                    marker = "✓ "
                elif is_dir and name != "../":
                    marker = "📁 "
                elif name == "../":
                    marker = "⬆ "
                else:
                    # Check if it's a CKLB file
                    if path.suffix.lower() == '.cklb':
                        marker = "📄 "
                    else:
                        marker = "   "
                
                prefix = "► " if actual_idx == browser_selected_idx else "  "
                display_name = f"{marker}{name}"
                
                if actual_idx == browser_selected_idx and curses.has_colors():
                    self.stdscr.attron(curses.color_pair(2))
                    self.stdscr.addstr(y_pos, 0, f"{prefix}{display_name}".ljust(width))
                    self.stdscr.attroff(curses.color_pair(2))
                else:
                    self.stdscr.addstr(y_pos, 0, f"{prefix}{display_name}"[:width-1])
                    
            # Show scroll indicator if there are more items
            if len(items) > max_items:
                total_items = len(items)
                scroll_indicator = f"[{scroll_offset + 1}-{min(scroll_offset + max_items, total_items)} of {total_items}]"
                self.stdscr.addstr(height - 7, 0, scroll_indicator)
                    
            # Show selected files count
            selected_count = len(selected_files)
            self.stdscr.addstr(height - 6, 0, f"Selected files: {selected_count}")
            
            # Instructions
            self.stdscr.addstr(height - 5, 0, "Instructions:")
            self.stdscr.addstr(height - 4, 0, "↑↓: Navigate  ENTER: Open dir/Toggle file selection")
            self.stdscr.addstr(height - 3, 0, "SPACE: Toggle file selection  A: Select all CKLB files")
            self.stdscr.addstr(height - 2, 0, "I: Import selected files  ESC: Cancel  Q: Quit browser")
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == 27:  # ESC - cancel
                return []
            elif key == ord('q') or key == ord('Q'):  # Quit browser
                return []
            elif key == ord('i') or key == ord('I'):  # Import selected files
                return selected_files
            elif key == curses.KEY_UP:
                browser_selected_idx = max(0, browser_selected_idx - 1)
            elif key == curses.KEY_DOWN:
                browser_selected_idx = min(len(items) - 1, browser_selected_idx + 1)
            elif key == 10 or key == 13:  # Enter
                if browser_selected_idx < len(items):
                    name, is_dir, path = items[browser_selected_idx]
                    if is_dir:
                        current_dir = path
                        browser_selected_idx = 0
                        scroll_offset = 0  # Reset scroll when changing directories
                    else:
                        # Toggle file selection
                        if path in selected_files:
                            selected_files.remove(path)
                        else:
                            if path.suffix.lower() == '.cklb':
                                selected_files.append(path)
            elif key == ord(' '):  # Space - toggle selection
                if browser_selected_idx < len(items):
                    name, is_dir, path = items[browser_selected_idx]
                    if not is_dir and path.suffix.lower() == '.cklb':
                        if path in selected_files:
                            selected_files.remove(path)
                        else:
                            selected_files.append(path)
            elif key == ord('a') or key == ord('A'):  # Select all CKLB files
                cklb_files = [path for name, is_dir, path in items 
                             if not is_dir and path.suffix.lower() == '.cklb']
                for f in cklb_files:
                    if f not in selected_files:
                        selected_files.append(f)
                        
            # Store selection index and scroll offset
            self.browser_selected_idx = browser_selected_idx
            self.browser_scroll_offset = scroll_offset
        
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
        """Fetch and display list of downloadable files with selection interface."""
        self.status_message = "Fetching download list..."
        self.logger.info("Fetching download list from URL")
        
        # Show progress screen
        self.show_loading_screen("Fetching STIG file list from DISA website...")
        
        try:
            # Use web downloader to fetch available STIGs with timeout handling
            stigs = self.fetch_stigs_with_progress()
            
            if not stigs:
                self.show_error_screen("No STIG files found or unable to fetch from website")
                return
                
            self.status_message = f"Found {len(stigs)} downloadable STIG files"
            self.logger.info(f"Found {len(stigs)} downloadable STIG files")
            
            # Display the STIG selection interface
            self.display_stig_selection(stigs)
            
        except Exception as e:
            error_msg = f"Download list error: {e}"
            self.status_message = error_msg
            self.logger.error(error_msg)
            self.show_error_screen(f"Failed to fetch STIG files:\n{str(e)}\n\nPlease check your internet connection.")
            
    def fetch_stigs_with_progress(self) -> List[Dict]:
        """
        Fetch STIGs with progress feedback and error handling.
        
        Returns:
            List of STIG dictionaries, empty list if failed
        """
        import threading
        import time
        
        # Shared variables for threading
        result = {'stigs': None, 'error': None, 'done': False}
        
        def fetch_worker():
            """Worker thread to fetch STIGs."""
            try:
                result['stigs'] = self.web_downloader.get_available_stigs(fetch_file_info=False)
                result['done'] = True
            except Exception as e:
                result['error'] = str(e)
                result['done'] = True
        
        # Start fetch in background thread
        fetch_thread = threading.Thread(target=fetch_worker, daemon=True)
        fetch_thread.start()
        
        # Show progress while waiting
        start_time = time.time()
        dots = 0
        
        while not result['done']:
            elapsed = int(time.time() - start_time)
            dot_animation = "." * (dots % 4)
            
            progress_msg = f"Fetching STIG list from DISA website{dot_animation}\nElapsed time: {elapsed}s\n\nPress 'q' to cancel"
            self.show_loading_screen(progress_msg)
            
            # Check for user cancellation
            self.stdscr.timeout(500)  # 0.5 second timeout
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.status_message = "Download cancelled by user"
                return []
            
            dots += 1
            time.sleep(0.5)
        
        # Reset timeout
        self.stdscr.timeout(-1)
        
        # Check results
        if result['error']:
            raise Exception(result['error'])
        
        stigs = result['stigs'] or []
        
        # Validate STIG data structure
        validated_stigs = []
        for stig in stigs:
            if self.validate_stig_data(stig):
                validated_stigs.append(stig)
            else:
                self.logger.warning(f"Invalid STIG data structure: {stig}")
        
        return validated_stigs
    
    def validate_stig_data(self, stig: Dict) -> bool:
        """
        Validate STIG data structure.
        
        Args:
            stig: STIG dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(stig, dict):
            return False
        
        # Required fields
        required_fields = ['filename', 'url']
        for field in required_fields:
            if field not in stig or not stig[field]:
                return False
        
        # Ensure optional fields have default values
        stig.setdefault('stig_id', 'Unknown')
        stig.setdefault('version', None)
        stig.setdefault('release', None)
        stig.setdefault('size', None)
        stig.setdefault('last_modified', '')
        stig.setdefault('type', 'unknown')
        
        return True
    
    def show_loading_screen(self, message: str):
        """
        Show a loading screen with message.
        
        Args:
            message: Loading message to display
        """
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Title
        title = "CheckMate - Loading"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Draw a simple border
        border_y = 3
        border_height = 8
        border_width = min(60, width - 4)
        border_x = (width - border_width) // 2
        
        # Top border
        self.stdscr.addstr(border_y, border_x, "┌" + "─" * (border_width - 2) + "┐")
        
        # Side borders and content
        message_lines = message.split('\n')
        for i in range(border_height - 2):
            line_y = border_y + 1 + i
            self.stdscr.addstr(line_y, border_x, "│")
            self.stdscr.addstr(line_y, border_x + border_width - 1, "│")
            
            # Add message content
            if i < len(message_lines):
                line_content = message_lines[i][:border_width - 4]
                content_x = border_x + 2
                self.stdscr.addstr(line_y, content_x, line_content)
        
        # Bottom border
        self.stdscr.addstr(border_y + border_height - 1, border_x, "└" + "─" * (border_width - 2) + "┘")
        
        self.stdscr.refresh()
    
    def show_error_screen(self, error_message: str):
        """
        Show an error screen with message.
        
        Args:
            error_message: Error message to display
        """
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Title
        title = "CheckMate - Error"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Error content
        content_start = 3
        error_lines = error_message.split('\n')
        
        for i, line in enumerate(error_lines):
            if content_start + i < height - 3:
                # Center short lines, left-align long lines
                if len(line) < width - 4:
                    x_pos = (width - len(line)) // 2
                else:
                    x_pos = 2
                    line = line[:width - 4]
                
                # Use error color if available
                if curses.has_colors():
                    self.stdscr.attron(curses.color_pair(4))  # Red
                    self.stdscr.addstr(content_start + i, x_pos, line)
                    self.stdscr.attroff(curses.color_pair(4))
                else:
                    self.stdscr.addstr(content_start + i, x_pos, line)
        
        # Instructions
        instruction_y = height - 3
        instruction = "Press any key to return to menu..."
        self.stdscr.addstr(instruction_y, (width - len(instruction)) // 2, instruction)
        
        self.stdscr.refresh()
        self.stdscr.getch()  # Wait for keypress
            
    def display_stig_selection(self, stigs: List[Dict]):
        """
        Display STIG files in a scrollable, selectable interface.
        
        Args:
            stigs: List of STIG file dictionaries with metadata
        """
        if not stigs:
            self.show_error_screen("No STIG files available to display")
            return
            
        # Initialize selection state
        scroll_pos = 0
        selected_files = set()
        current_idx = 0
        
        while True:
            try:
                self.stdscr.clear()
                height, width = self.stdscr.getmaxyx()
                
                # Header
                title = f"STIG Files ({len(stigs)} available, {len(selected_files)} selected)"
                self.stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)
                
                # Instructions
                instructions = [
                    "Navigation: ↑/↓ arrows, PgUp/PgDn  |  Selection: SPACE to toggle, A=all, N=none",
                    "Actions: ENTER=choose download mode, D=download all, ESC=back to menu, Q=quit"
                ]
                
                for i, instruction in enumerate(instructions):
                    if 2 + i < height:
                        self.stdscr.addstr(2 + i, 0, instruction[:width-1])
                
                # Column headers
                header_line = 4
                if header_line < height:
                    header = f"{'Status':<8} {'STIG ID':<25} {'Ver':<6} {'Rel':<6} {'Type':<10} {'Size':<10} {'Updated':<12}"
                    self.stdscr.addstr(header_line, 0, header[:width-1], curses.A_REVERSE)
                
                # Calculate visible area
                content_start = header_line + 1
                visible_lines = height - content_start - 2  # Leave space for status
                
                # Adjust scroll position to keep current selection visible
                if current_idx < scroll_pos:
                    scroll_pos = current_idx
                elif current_idx >= scroll_pos + visible_lines:
                    scroll_pos = current_idx - visible_lines + 1
                    
                # Display STIG files
                for i in range(visible_lines):
                    file_idx = scroll_pos + i
                    if file_idx >= len(stigs):
                        break
                        
                    line_y = content_start + i
                    if line_y >= height - 1:
                        break
                    
                    try:
                        stig = stigs[file_idx]
                        
                        # Format file information with safe data access
                        status = "[✓]" if file_idx in selected_files else "[ ]"
                        stig_id = str(stig.get('stig_id', 'Unknown'))[:24]
                        
                        # Safe version formatting
                        version = stig.get('version')
                        if version is not None:
                            if isinstance(version, str) and version.startswith('Y'):
                                version_str = version[:5]  # Y##M##
                            else:
                                version_str = f"V{version}"
                        else:
                            version_str = "V?"
                        
                        # Safe release formatting
                        release = stig.get('release')
                        if release is not None:
                            if isinstance(release, str) and release.startswith('M'):
                                release_str = release[:3]  # M##
                            else:
                                release_str = f"R{release}"
                        else:
                            release_str = "R?"
                        
                        # File type
                        file_type = str(stig.get('type', 'other'))[:9]
                        
                        # Format file size safely
                        size = stig.get('size')
                        if isinstance(size, (int, float)) and size > 0:
                            if size > 1024*1024:
                                size_str = f"{size/(1024*1024):.1f}MB"
                            elif size > 1024:
                                size_str = f"{size/1024:.1f}KB"
                            else:
                                size_str = f"{int(size)}B"
                        else:
                            size_str = "Unknown"
                        
                        # Format last modified date safely
                        last_mod = stig.get('last_modified', '')
                        date_str = "Unknown"
                        if last_mod:
                            try:
                                from datetime import datetime
                                # Parse common date formats from HTTP headers
                                date_formats = [
                                    '%a, %d %b %Y %H:%M:%S %Z',
                                    '%a, %d %b %Y %H:%M:%S GMT',
                                    '%d %b %Y',
                                    '%Y-%m-%d'
                                ]
                                for fmt in date_formats:
                                    try:
                                        dt = datetime.strptime(last_mod, fmt)
                                        date_str = dt.strftime('%Y-%m-%d');
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    # If no format matches, use first 12 characters
                                    date_str = str(last_mod)[:12] if last_mod else "Unknown"
                            except Exception:
                                date_str = str(last_mod)[:12] if last_mod else "Unknown"
                        
                        line_text = f"{status:<8} {stig_id:<25} {version_str:<6} {release_str:<6} {file_type:<10} {size_str:<10} {date_str:<12}"
                        
                        # Highlight current selection
                        attr = curses.A_REVERSE if file_idx == current_idx else curses.A_NORMAL
                        
                        self.stdscr.addstr(line_y, 0, line_text[:width-1], attr)
                        
                    except Exception as e:
                        # Handle individual STIG display errors
                        error_line = f"[ ]      Error displaying STIG {file_idx}: {str(e)[:50]}"
                        self.stdscr.addstr(line_y, 0, error_line[:width-1])
                        self.logger.warning(f"Error displaying STIG {file_idx}: {e}")
                
                # Status line
                status_y = height - 1
                status_text = f"File {current_idx + 1}/{len(stigs)} | Selected: {len(selected_files)} | Press 'h' for help"
                self.stdscr.addstr(status_y, 0, status_text[:width-1], curses.A_REVERSE)
                
                self.stdscr.refresh()
                
                # Handle input
                key = self.stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    return  # Quit
                elif key == 27:  # ESC
                    return  # Back to menu
                elif key == curses.KEY_UP:
                    current_idx = max(0, current_idx - 1)
                elif key == curses.KEY_DOWN:
                    current_idx = min(len(stigs) - 1, current_idx + 1)
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_idx = max(0, current_idx - visible_lines)
                elif key == curses.KEY_NPAGE:  # Page Down
                    current_idx = min(len(stigs) - 1, current_idx + visible_lines)
                elif key == curses.KEY_HOME:
                    current_idx = 0
                elif key == curses.KEY_END:
                    current_idx = len(stigs) - 1
                elif key == ord(' '):  # Space to toggle selection
                    if current_idx in selected_files:
                        selected_files.remove(current_idx)
                    else:
                        selected_files.add(current_idx)
                elif key == ord('a') or key == ord('A'):  # Select all
                    selected_files = set(range(len(stigs)))
                elif key == ord('n') or key == ord('N'):  # Select none
                    selected_files.clear()
                elif key == 10 or key == 13:  # Enter - choose download mode for selected files
                    if selected_files:
                        selected_stigs = []
                        for i in sorted(selected_files):
                            if i < len(stigs):
                                selected_stigs.append(stigs[i])
                        if selected_stigs:
                            self.choose_download_mode(selected_stigs)
                            return
                    else:
                        # Flash message about no selection
                        try:
                            self.stdscr.addstr(status_y, 0, "No files selected! Press SPACE to select files.", curses.A_BLINK)
                            self.stdscr.refresh()
                            curses.napms(1500)
                        except curses.error:
                            pass
                elif key == ord('d') or key == ord('D'):  # Download all
                    self.choose_download_mode(stigs)
                    return
                elif key == ord('h') or key == ord('H'):  # Help
                    self.show_stig_selection_help()
                    
            except curses.error as e:
                # Handle curses display errors
                self.logger.error(f"Curses display error: {e}")
                # Try to recover by clearing and continuing
                try:
                    self.stdscr.clear()
                    self.stdscr.refresh()
                except curses.error:
                    break
            except Exception as e:
                # Handle other unexpected errors
                self.logger.error(f"Unexpected error in STIG selection: {e}")
                self.show_error_screen(f"Unexpected error:\n{str(e)}")
                break
                
    def show_stig_selection_help(self):
        """Show help for STIG selection interface."""
        help_text = [
            "STIG File Selection Help",
            "",
            "Navigation:",
            "  ↑/↓ arrows    - Move up/down one item",
            "  PgUp/PgDn     - Move up/down one page", 
            "  Home/End      - Go to first/last item",
            "",
            "Selection:",
            "  SPACE         - Toggle selection of current item",
            "  A             - Select all files",
            "  N             - Clear all selections",
            "",
            "Actions:",
            "  ENTER         - Choose download mode for selected files",
            "  D             - Choose download mode for all files", 
            "  ESC           - Return to previous menu",
            "  Q             - Quit application",
            "  H             - Show this help",
            "",
            "File Information:",
            "  Status        - [✓] selected, [ ] not selected",
            "  STIG ID       - Security Technical Implementation Guide identifier",
            "  Ver/Rel       - Version and Release numbers (V#R# or Y##M##)",
            "  Type          - File type (stig, benchmark, other, etc.)",
            "  Size          - File size in MB/KB/bytes",
            "  Updated       - Last modification date",
            "",
            "Press any key to continue..."
        ]
        
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx();
        
        for i, line in enumerate(help_text):
            if i < height - 1:
                self.stdscr.addstr(i, 0, line[:width-1])
        
        self.stdscr.refresh()
        self.stdscr.getch()  # Wait for any key
        
    def choose_download_mode(self, selected_stigs: List[Dict]):
        """
        Allow user to choose download mode for selected STIG files.
        
        Args:
            selected_stigs: List of selected STIG dictionaries
        """
        if not selected_stigs:
            return
            
        download_modes = [
            ("Download ZIP only", "Downloads ZIP files to local storage"),
            ("Create CKLB only", "Downloads ZIPs, creates CKLB files, then removes ZIPs"),
            ("Both", "Downloads ZIPs and creates CKLB files, keeps both")
        ]
        
        selected_mode = 0
        
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Title
            title = f"Download Mode Selection ({len(selected_stigs)} files)"
            self.stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)
            
            # Instructions
            instructions = "Choose how you want to process the selected STIG files:"
            self.stdscr.addstr(2, 0, instructions[:width-1])
            
            # Show download options
            for i, (mode_name, description) in enumerate(download_modes):
                y_pos = 4 + i * 2
                if y_pos < height - 3:
                    # Mode number and name
                    prefix = f"{i + 1}. {mode_name}"
                    if i == selected_mode:
                        self.stdscr.addstr(y_pos, 0, f"► {prefix}"[:width-1], curses.A_REVERSE)
                    else:
                        self.stdscr.addstr(y_pos, 0, f"  {prefix}"[:width-1])
                    
                    # Description
                    if y_pos + 1 < height - 3:
                        desc_text = f"    {description}"
                        self.stdscr.addstr(y_pos + 1, 0, desc_text[:width-1], curses.A_DIM)
            
            # Navigation help
            help_y = height - 3
            help_text = "Use ↑/↓ arrows to select, ENTER to confirm, ESC to cancel"
            if help_y > 0:
                self.stdscr.addstr(help_y, 0, help_text[:width-1], curses.A_DIM)
            
            self.stdscr.refresh()
            
            # Handle input
            try:
                key = self.stdscr.getch()
                
                if key == curses.KEY_UP:
                    selected_mode = (selected_mode - 1) % len(download_modes)
                elif key == curses.KEY_DOWN:
                    selected_mode = (selected_mode + 1) % len(download_modes)
                elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                    # Execute selected download mode
                    if selected_mode == 0:  # Download ZIP only
                        self.download_selected_stigs(selected_stigs)
                    elif selected_mode == 1:  # Create CKLB only
                        self.download_and_create_cklb(selected_stigs, keep_zip=False)
                    elif selected_mode == 2:  # Both
                        self.download_and_create_cklb(selected_stigs, keep_zip=True)
                    break
                elif key == 27:  # ESC key
                    break
                elif key in [ord('q'), ord('Q')]:
                    sys.exit(0)
                elif key in [ord('1'), ord('2'), ord('3')]:
                    # Allow direct number selection
                    num_selected = key - ord('0') - 1
                    if 0 <= num_selected < len(download_modes):
                        selected_mode = num_selected
                        
            except curses.error:
                break
    
    def download_selected_stigs(self, selected_stigs: List[Dict]):
        """
        Download selected STIG files with progress feedback.
        
        Args:
            selected_stigs: List of selected STIG dictionaries
        """
        if not selected_stigs:
            return
            
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Show download progress
        title = f"Downloading {len(selected_stigs)} STIG files..."
        self.stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)
        self.stdscr.addstr(2, 0, "Progress will be shown below. Press 'q' to cancel.", curses.A_DIM)
        self.stdscr.refresh()
        
        try:
            # Convert to file links format
            file_links = [(stig.get('filename', 'unknown'), stig.get('url', '')) for stig in selected_stigs]
            
            # Download multiple files
            output_dir = self.config.get_path('zip_files')
            results = self.web_downloader.download_multiple_files(file_links, output_dir)
            
            # Count successes and failures
            successful = len([r for r in results if r[2] is None])
            failed = len(results) - successful
            
            # Calculate total size
            total_size = 0
            for stig in selected_stigs:
                size = stig.get('size')
                if isinstance(size, int):
                    total_size += size
            
            # Show results
            self.stdscr.clear()
            result_lines = [
                "Download Complete!",
                "",
                f"Files processed: {len(results)}",
                f"Successfully downloaded: {successful}",
                f"Failed downloads: {failed}",
                f"Total size: {self.format_file_size(total_size)}" if total_size > 0 else "Total size: Unknown",
                f"Download directory: {output_dir}",
                "",
                "Press any key to continue..."
            ]
            
            for i, line in enumerate(result_lines):
                if i < height - 1:
                    attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
                    self.stdscr.addstr(i, 0, line[:width-1], attr)
            
            self.stdscr.refresh()
            self.stdscr.getch()  # Wait for key press
            
            # Update status and refresh file lists
            self.status_message = f"Downloaded {successful}/{len(results)} files successfully"
            self.logger.info(f"Download result: {successful}/{len(results)} files downloaded")
            self.refresh_file_lists()
            
        except Exception as e:
            # Show error
            self.stdscr.clear()
            error_lines = [
                "Download Error!",
                "",
                f"Error: {str(e)}",
                "",
                "Press any key to continue..."
            ]
            
            for i, line in enumerate(error_lines):
                if i < height - 1:
                    attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
                    self.stdscr.addstr(i, 0, line[:width-1], attr)
            
            self.stdscr.refresh()
            self.stdscr.getch()
            
            self.status_message = f"Download error: {e}"
            self.logger.error(f"Download error: {e}")
            
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes >= 1024*1024*1024:
            return f"{size_bytes/(1024*1024*1024):.1f}GB"
        elif size_bytes >= 1024*1024:
            return f"{size_bytes/(1024*1024):.1f}MB"
        elif size_bytes >= 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes}B"
            
    def download_all_files(self):
        """Download all available files."""
        self.status_message = "Starting download of all files..."
        self.logger.info("Starting download of all files")
        
        try:
            # First get available STIGs
            stigs = self.web_downloader.get_available_stigs(fetch_file_info=False)
            if not stigs:
                self.status_message = "No STIG files found to download"
                return
            
            # Convert to file links format
            file_links = [(stig.get('filename', 'unknown'), stig.get('url', '')) for stig in stigs]
            
            # Download multiple files
            output_dir = self.config.get_path('zip_files')
            results = self.web_downloader.download_multiple_files(file_links, output_dir)
            
            # Count successes and failures
            successful = len([r for r in results if r[2] is None])
            failed = len(results) - successful
            
            self.status_message = f"Download completed: {successful} successful, {failed} failed"
            self.logger.info(f"Download result: {successful}/{len(results)} files downloaded")
            self.refresh_file_lists()
            
        except Exception as e:
            self.status_message = f"Download error: {e}"
            self.logger.error(f"Download error: {e}")
            
    def download_specific_types(self):
        """Download specific file types based on user selection."""
        # This method can be implemented later if needed
        self.status_message = "Specific type download not yet implemented"
        pass
    
    def download_and_create_cklb(self, selected_stigs: List[Dict], keep_zip: bool = True):
        """
        Download STIG files and create CKLB files from them.
        
        Args:
            selected_stigs: List of selected STIG dictionaries
            keep_zip: Whether to keep ZIP files after CKLB creation
        """
        if not selected_stigs:
            return
            
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Show progress
        mode_text = "with ZIP cleanup" if not keep_zip else "keeping ZIPs"
        title = f"Downloading and creating CKLB files ({mode_text})..."
        self.stdscr.addstr(0, 0, title[:width-1], curses.A_BOLD)
        self.stdscr.addstr(2, 0, "Progress will be shown below. Press 'q' to cancel.", curses.A_DIM)
        self.stdscr.refresh()
        
        try:
            # Step 1: Download ZIP files
            file_links = [(stig.get('filename', 'unknown'), stig.get('url', '')) for stig in selected_stigs]
            zip_dir = self.config.get_path('zip_files')
            results = self.web_downloader.download_multiple_files(file_links, zip_dir)
            
            successful_downloads = [r for r in results if r[2] is None]
            
            if not successful_downloads:
                self.show_error_screen("No files were successfully downloaded.")
                return
            
            # Step 2: Create CKLB files from downloaded ZIPs
            cklb_created = 0
            cklb_failed = 0
            
            for filename, url, error in successful_downloads:
                try:
                    zip_path = zip_dir / filename
                    if zip_path.exists():
                        # Use CKLB generator to create CKLB from ZIP
                        output_dir = self.config.get_path('cklb_new')
                        results = self.cklb_generator.convert_zip_to_cklb(zip_path, output_dir)
                        
                        # Check if CKLB was created successfully
                        success = any(result[0] is not None for result in results)
                        if success:
                            cklb_created += 1
                            # Remove ZIP if requested
                            if not keep_zip:
                                zip_path.unlink()
                        else:
                            cklb_failed += 1
                            # Log any errors
                            for result in results:
                                if result[1]:  # Error message exists
                                    self.logger.error(f"CKLB creation error: {result[1]}")
                    else:
                        cklb_failed += 1
                        
                except Exception as e:
                    self.logger.error(f"Error creating CKLB from {filename}: {e}")
                    cklb_failed += 1
            
            # Show results
            self.stdscr.clear()
            result_lines = [
                "Download and CKLB Creation Complete!",
                "",
                f"Files downloaded: {len(successful_downloads)}",
                f"CKLB files created: {cklb_created}",
                f"CKLB creation failed: {cklb_failed}",
                f"ZIP files {'removed' if not keep_zip else 'kept'}: {len(successful_downloads)}",
                f"CKLB directory: {self.config.get_path('cklb_new')}",
                "",
                "Press any key to continue..."
            ]
            
            for i, line in enumerate(result_lines):
                if i < height - 1:
                    attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
                    self.stdscr.addstr(i, 0, line[:width-1], attr)
            
            self.stdscr.refresh()
            self.stdscr.getch()  # Wait for key press
            
            # Update status and refresh file lists
            self.status_message = f"Created {cklb_created} CKLB files from {len(successful_downloads)} downloads"
            self.logger.info(f"CKLB creation result: {cklb_created}/{len(successful_downloads)} files processed")
            self.refresh_file_lists()
            
        except Exception as e:
            # Show error
            self.stdscr.clear()
            error_lines = [
                "Download and CKLB Creation Error!",
                "",
                f"Error: {str(e)}",
                "",
                "Press any key to continue..."
            ]
            
            for i, line in enumerate(error_lines):
                if i < height - 1:
                    attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
                    self.stdscr.addstr(i, 0, line[:width-1], attr)
            
            self.stdscr.refresh()
            self.stdscr.getch()
            
            self.status_message = f"Download/CKLB creation error: {e}"
            self.logger.error(f"Download/CKLB creation error: {e}")
    
    def view_downloaded_files(self):
        """View and manage downloaded files."""
        self.status_message = "Viewing downloaded files..."
        self.logger.info("Viewing downloaded files")
        
        try:
            zip_dir = self.config.get_path('zip_files')
            if not zip_dir.exists():
                self.status_message = "No download directory found"
                return
                
            zip_files = list(zip_dir.glob('*.zip'))
            if not zip_files:
                self.status_message = "No downloaded files found"
                return
                
            # Simple file listing for now
            file_info = []
            for zip_file in zip_files[:10]:  # Limit to first 10 files
                size = zip_file.stat().st_size
                size_str = self.format_file_size(size)
                file_info.append(f"{zip_file.name} ({size_str})")
            
            self.status_message = f"Found {len(zip_files)} downloaded files"
            
        except Exception as e:
            self.status_message = f"Error viewing downloaded files: {e}"
            self.logger.error(f"Error viewing downloaded files: {e}")
            
    def export_cklb_files(self):
        """Export CKLB files to a target directory."""
        self.status_message = "Export functionality not yet implemented"
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
                temp_dir.mkdir(exist_ok=True)
                cleaned = True
            else:
                cleaned = False
                
            if cleaned:
                self.status_message = "Temporary files cleaned successfully"
            else:
                self.status_message = "No temporary files to clean"
                
        except Exception as e:
            self.status_message = f"Error cleaning temp files: {e}"
            self.logger.error(f"Error cleaning temp files: {e}")
            
    def validate_files(self):
        """Validate file integrity."""
        self.status_message = "File validation not yet implemented"
        self.logger.info("File validation requested")
        
    def show_directory_stats(self):
        """Show directory statistics."""
        self.status_message = "Gathering directory statistics..."
        self.logger.info("Directory statistics requested")
        
        try:
            stats = {}
            for name, path in self.config.get_all_directories().items():
                if path.exists():
                    file_count = len(list(path.glob('*')))
                    stats[name] = file_count
                else:
                    stats[name] = 0
                    
            self.status_message = f"Statistics gathered for {len(stats)} directories"
            
        except Exception as e:
            self.status_message = f"Error gathering statistics: {e}"
            self.logger.error(f"Error gathering statistics: {e}")
            
    def organize_files(self):
        """Organize files by type."""
        self.status_message = "File organization not yet implemented"
        self.logger.info("File organization requested")
