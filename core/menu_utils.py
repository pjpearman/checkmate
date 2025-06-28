"""
Menu utilities for CheckMate applications.
Contains reusable menu rendering and handling functions for TUI.
"""

import curses
from typing import List, Tuple, Optional, Callable, Any

from .config import Config
from .log_config import get_operation_logger

logger = get_operation_logger("menu_utils")


class MenuUtils:
    """Menu utilities for CheckMate TUI applications."""
    
    def __init__(self, config: Config = None):
        """Initialize menu utilities."""
        self.config = config or Config()
    
    @staticmethod
    def init_colors():
        """Initialize curses color pairs."""
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Error
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning
            curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Info
    
    @staticmethod
    def clean_screen(stdscr):
        """Clear screen and refresh."""
        stdscr.clear()
        stdscr.refresh()
    
    @staticmethod
    def render_menu(
        stdscr, 
        title: str, 
        options: List[str], 
        selected_idx: int, 
        start_y: int = 0, 
        pear_art: str = ""
    ):
        """
        Generic menu rendering function.
        
        Args:
            stdscr: Curses window object
            title: Menu title string
            options: List of menu options
            selected_idx: Currently selected option index
            start_y: Starting Y coordinate for the menu
            pear_art: Optional art to prepend to menu items
        """
        MenuUtils.clean_screen(stdscr)
        
        # Title
        title_line = f"== {title} =="
        stdscr.addstr(start_y, 0, title_line[:curses.COLS-1])
        
        # Menu options
        for idx, opt in enumerate(options):
            y_pos = idx + start_y + 2
            if y_pos >= curses.LINES - 1:  # Prevent writing past screen
                break
            
            menu_line = f"{pear_art}{opt}" if pear_art else opt
            if idx == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y_pos, 0, f"> {menu_line}"[:curses.COLS-1])
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y_pos, 0, f"  {menu_line}"[:curses.COLS-1])
        
        stdscr.refresh()
    
    @staticmethod
    def handle_menu_input(key: int, selected_idx: int, num_options: int) -> Tuple[int, bool, bool]:
        """
        Handle standard menu navigation input.
        
        Args:
            key: Input key code
            selected_idx: Current selection index
            num_options: Total number of menu options
            
        Returns:
            Tuple of (new_idx, should_return, should_select)
        """
        if key == curses.KEY_UP:
            return (selected_idx - 1) % num_options, False, False
        elif key == curses.KEY_DOWN:
            return (selected_idx + 1) % num_options, False, False
        elif key in [10, 13]:  # Enter
            return selected_idx, False, True
        elif key in [ord('q'), ord('Q'), 27]:  # q or ESC
            return selected_idx, True, False
        elif key in [ord('b'), ord('B')]:  # Back
            return selected_idx, True, False
        else:
            return selected_idx, False, False
    
    @staticmethod
    def show_message(
        stdscr, 
        message: str, 
        title: str = "Message", 
        color_pair: int = 0,
        wait_for_key: bool = True
    ):
        """
        Show a message dialog.
        
        Args:
            stdscr: Curses window object
            message: Message to display
            title: Dialog title
            color_pair: Color pair for message
            wait_for_key: Whether to wait for keypress
        """
        MenuUtils.clean_screen(stdscr)
        
        # Title
        stdscr.addstr(0, 0, f"== {title} ==")
        
        # Message (handle multi-line)
        lines = message.split('\\n')
        for i, line in enumerate(lines):
            y_pos = i + 2
            if y_pos >= curses.LINES - 2:
                break
            
            if color_pair > 0:
                stdscr.attron(curses.color_pair(color_pair))
            stdscr.addstr(y_pos, 0, line[:curses.COLS-1])
            if color_pair > 0:
                stdscr.attroff(curses.color_pair(color_pair))
        
        if wait_for_key:
            prompt_y = min(len(lines) + 4, curses.LINES - 1)
            stdscr.addstr(prompt_y, 0, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()
        else:
            stdscr.refresh()
    
    @staticmethod
    def show_error(stdscr, error_message: str, title: str = "Error"):
        """Show error message in red."""
        MenuUtils.show_message(stdscr, error_message, title, color_pair=3)
    
    @staticmethod
    def show_success(stdscr, success_message: str, title: str = "Success"):
        """Show success message in green."""
        MenuUtils.show_message(stdscr, success_message, title, color_pair=2)
    
    @staticmethod
    def show_warning(stdscr, warning_message: str, title: str = "Warning"):
        """Show warning message in yellow."""
        MenuUtils.show_message(stdscr, warning_message, title, color_pair=4)
    
    @staticmethod
    def prompt_yes_no(stdscr, question: str, title: str = "Confirm") -> bool:
        """
        Show yes/no prompt.
        
        Args:
            stdscr: Curses window object
            question: Question to ask
            title: Dialog title
            
        Returns:
            True for yes, False for no
        """
        options = ["Yes", "No"]
        selected_idx = 1  # Default to No
        
        while True:
            MenuUtils.clean_screen(stdscr)
            stdscr.addstr(0, 0, f"== {title} ==")
            stdscr.addstr(2, 0, question)
            
            for idx, opt in enumerate(options):
                y_pos = idx + 4
                if idx == selected_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y_pos, 0, f"> {opt}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(y_pos, 0, f"  {opt}")
            
            stdscr.addstr(7, 0, "Use UP/DOWN to select, ENTER to confirm")
            stdscr.refresh()
            
            key = stdscr.getch()
            new_idx, should_return, should_select = MenuUtils.handle_menu_input(
                key, selected_idx, len(options)
            )
            
            if should_return:
                return False  # Cancelled
            elif should_select:
                return selected_idx == 0  # Yes is index 0
            else:
                selected_idx = new_idx
    
    @staticmethod
    def prompt_string(
        stdscr, 
        prompt: str, 
        title: str = "Input", 
        default: str = "",
        max_length: int = 255
    ) -> Optional[str]:
        """
        Prompt for string input.
        
        Args:
            stdscr: Curses window object
            prompt: Input prompt
            title: Dialog title
            default: Default value
            max_length: Maximum input length
            
        Returns:
            Input string or None if cancelled
        """
        MenuUtils.clean_screen(stdscr)
        stdscr.addstr(0, 0, f"== {title} ==")
        stdscr.addstr(2, 0, prompt)
        stdscr.addstr(4, 0, f"Default: {default}")
        stdscr.addstr(5, 0, "Input: ")
        stdscr.addstr(7, 0, "Press ENTER when done, ESC to cancel")
        
        # Enable cursor and echo
        curses.curs_set(1)
        curses.echo()
        
        try:
            # Get input
            stdscr.move(5, 7)
            input_str = stdscr.getstr(5, 7, max_length).decode('utf-8')
            
            # Use default if empty
            if not input_str.strip() and default:
                input_str = default
            
            return input_str.strip() if input_str.strip() else None
            
        except KeyboardInterrupt:
            return None
        finally:
            # Disable cursor and echo
            curses.curs_set(0)
            curses.noecho()
    
    @staticmethod
    def show_scrollable_text(
        stdscr, 
        text: str, 
        title: str = "Text Viewer"
    ):
        """
        Show scrollable text content.
        
        Args:
            stdscr: Curses window object
            text: Text to display
            title: Window title
        """
        lines = text.split('\\n')
        scroll_offset = 0
        max_lines = curses.LINES - 4  # Reserve space for title and instructions
        
        while True:
            MenuUtils.clean_screen(stdscr)
            stdscr.addstr(0, 0, f"== {title} ==")
            
            # Show visible lines
            visible_lines = lines[scroll_offset:scroll_offset + max_lines]
            for i, line in enumerate(visible_lines):
                stdscr.addstr(i + 1, 0, line[:curses.COLS-1])
            
            # Show scroll info and instructions
            total_lines = len(lines)
            if total_lines > max_lines:
                progress = f"Line {scroll_offset + 1}-{min(scroll_offset + max_lines, total_lines)} of {total_lines}"
                stdscr.addstr(curses.LINES - 2, 0, progress)
            
            stdscr.addstr(curses.LINES - 1, 0, "UP/DOWN/PGUP/PGDN to scroll, 'q' to quit")
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key in [ord('q'), ord('Q'), 27]:  # Quit
                break
            elif key == curses.KEY_UP and scroll_offset > 0:
                scroll_offset -= 1
            elif key == curses.KEY_DOWN and scroll_offset < total_lines - max_lines:
                scroll_offset += 1
            elif key == curses.KEY_PPAGE:  # Page Up
                scroll_offset = max(0, scroll_offset - max_lines)
            elif key == curses.KEY_NPAGE:  # Page Down
                scroll_offset = min(total_lines - max_lines, scroll_offset + max_lines)


# Convenience functions for backward compatibility
def render_menu(stdscr, title: str, options: List[str], selected_idx: int, start_y: int = 0, pear_art: str = ""):
    """Render menu using default utils."""
    MenuUtils.render_menu(stdscr, title, options, selected_idx, start_y, pear_art)

def handle_menu_input(key: int, selected_idx: int, num_options: int) -> Tuple[int, bool, bool]:
    """Handle menu input using default utils."""
    return MenuUtils.handle_menu_input(key, selected_idx, num_options)
