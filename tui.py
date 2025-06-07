#!/usr/bin/env python3
"""
tui.py: A lightweight, flexible terminal UI for beautifulsoup_scraper.py.

- Uses curses for a clean UI.
- Allows selecting and downloading files.
- Modular structure for future expansion.
- Secure by design: no sensitive input storage, logs to local log file.

Add more features as needed: toggles, input fields, etc.
"""

import curses
import os
import sys
import requests

# Import existing functions
from web import fetch_page, parse_table_for_links, download_file, URL, HEADERS

# Setup a list of future functions for easy extension
FUNCTIONS = {
    "Download Files": "download_files",
    # Example: "Set Download Directory": "set_download_dir",
    # Example: "Toggle File Types": "toggle_file_types",
}

def draw_menu(stdscr, selected_idx):
    """
    Display the main menu. Highlights the currently selected menu item.
    """
    stdscr.clear()
    stdscr.addstr(0, 0, "== BeautifulSoup Scraper TUI ==")
    stdscr.addstr(1, 0, "Use UP/DOWN to navigate, ENTER to select, 'q' to quit.")

    for idx, option in enumerate(FUNCTIONS.keys()):
        if idx == selected_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(idx + 3, 0, f"> {option}")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(idx + 3, 0, f"  {option}")

    stdscr.refresh()

def download_files(stdscr):
    """
    Downloads files by fetching the page and displaying the list.
    Enhanced: supports multi-select, file size display, refresh, and status bar.
    """
    def get_file_size(url):
        try:
            resp = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            size = int(resp.headers.get('Content-Length', 0))
            return size if size > 0 else None
        except Exception:
            return None

    def human_size(size):
        for unit in ['B','KB','MB','GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Fetching webpage and parsing file links...")
        stdscr.refresh()
        try:
            html_content = fetch_page(URL)
            file_links = parse_table_for_links(html_content)
        except Exception as e:
            stdscr.addstr(2, 0, f"Error: {e}. Press any key to return.")
            stdscr.getch()
            return
        if not file_links:
            stdscr.addstr(2, 0, "No downloadable files found. Press any key to return.")
            stdscr.getch()
            return
        # Get file sizes (head requests, but only for visible files)
        sizes = [get_file_size(url) for _, url in file_links]
        selected = set()
        current_idx = 0
        status = "SPACE: select, ENTER: download, r: refresh, b: back, q: quit"
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select files to download:")
            for idx, (file_name, _) in enumerate(file_links):
                sel = "[x]" if idx in selected else "[ ]"
                size_str = f" ({human_size(sizes[idx])})" if sizes[idx] else ""
                line = f"{sel} {file_name}{size_str}"
                if idx == current_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(idx + 1, 0, f"> {line}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(idx + 1, 0, f"  {line}")
            stdscr.addstr(curses.LINES-2, 0, status)
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP:
                current_idx = (current_idx - 1) % len(file_links)
            elif key == curses.KEY_DOWN:
                current_idx = (current_idx + 1) % len(file_links)
            elif key == ord(' '):
                if current_idx in selected:
                    selected.remove(current_idx)
                else:
                    selected.add(current_idx)
            elif key in [10, 13]:  # ENTER
                to_download = selected if selected else {current_idx}
                for idx in to_download:
                    file_name, file_url = file_links[idx]
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"Downloading: {file_name}...")
                    stdscr.refresh()
                    try:
                        download_file(file_url, file_name)
                        stdscr.addstr(2, 0, f"Downloaded: {file_name}")
                    except Exception as e:
                        stdscr.addstr(2, 0, f"Download error: {e}")
                    stdscr.refresh()
                stdscr.addstr(4, 0, "Press any key to continue.")
                stdscr.getch()
                selected.clear()
            elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
                return
            elif key in [ord('r'), ord('R')]:
                break  # Refresh file list

def main(stdscr):
    """
    Main loop for the TUI.
    """
    # Setup color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

    selected_idx = 0
    while True:
        draw_menu(stdscr, selected_idx)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(FUNCTIONS)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(FUNCTIONS)
        elif key in [10, 13]:  # ENTER key
            selected_func = list(FUNCTIONS.values())[selected_idx]
            if selected_func == "download_files":
                download_files(stdscr)
            # elif selected_func == "set_download_dir":
            #     set_download_dir(stdscr)
            # elif selected_func == "toggle_file_types":
            #     toggle_file_types(stdscr)
        elif key in [ord('q'), ord('Q')]:
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
