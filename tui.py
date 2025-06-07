#!/usr/bin/env python3
"""
tui.py: A lightweight, flexible terminal UI for web.py.
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
import zipfile
import glob
import tempfile
import subprocess

# Import existing functions
from web import fetch_page, parse_table_for_links, download_file, URL, HEADERS

# Setup a list of future functions for easy extension
FUNCTIONS = {
    "Create Inventory File": "create_inventory_file_tui",
    "Download Files": "download_files",
    "Download Selected Inventory": "download_selected_inventory_tui",
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
    Enhanced: supports multi-select, refresh, and status bar.
    """
    download_mode = prompt_download_mode_tui(stdscr)
    if not download_mode:
        return  # Cancelled

    while True:
        print("[TUI] Fetching webpage and parsing file links...")
        stdscr.clear()
        stdscr.addstr(0, 0, "Fetching webpage and parsing file links...")
        stdscr.refresh()
        try:
            html_content = fetch_page(URL)
            print("[TUI] Page fetched. Parsing links...")
            file_links = parse_table_for_links(html_content)
            print(f"[TUI] Found {len(file_links)} file links.")
        except Exception as e:
            stdscr.addstr(2, 0, f"Error: {e}. Press any key to return.")
            stdscr.refresh()
            print(f"[TUI] Error: {e}")
            stdscr.getch()
            return
        if not file_links:
            stdscr.addstr(2, 0, "No downloadable files found. Press any key to return.")
            stdscr.refresh()
            print("[TUI] No downloadable files found.")
            stdscr.getch()
            return
        selected = set()
        current_idx = 0
        scroll_offset = 0
        status = "SPACE: select, ENTER: download, r: refresh, b: back, q: quit"
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select files to download:")
            max_lines = curses.LINES - 3  # Reserve space for status and prompt
            # Adjust scroll_offset to keep current_idx visible
            if current_idx < scroll_offset:
                scroll_offset = current_idx
            elif current_idx >= scroll_offset + max_lines:
                scroll_offset = current_idx - max_lines + 1
            visible_links = file_links[scroll_offset:scroll_offset + max_lines]
            for vis_idx, (file_name, _) in enumerate(visible_links):
                idx = scroll_offset + vis_idx
                sel = "[x]" if idx in selected else "[ ]"
                line = f"{sel} {file_name}"
                # Truncate line to fit terminal width
                line = line[:curses.COLS - 4]
                if idx == current_idx:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(vis_idx + 1, 0, f"> {line}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(vis_idx + 1, 0, f"  {line}")
            stdscr.addstr(curses.LINES-2, 0, status[:curses.COLS-1])
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
                    print(f"[TUI] Downloading: {file_name} from {file_url}")
                    try:
                        download_file(file_url, file_name)
                        stdscr.addstr(2, 0, f"Downloaded: {file_name}")
                        print(f"[TUI] Downloaded: {file_name}")
                    except Exception as e:
                        stdscr.addstr(2, 0, f"Download error: {e}")
                        print(f"[TUI] Download error: {e}")
                    stdscr.refresh()
                stdscr.addstr(4, 0, "Press any key to continue.")
                stdscr.getch()
                selected.clear()
            elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
                return
            elif key in [ord('r'), ord('R')]:
                break  # Refresh file list

def prompt_download_mode_tui(stdscr):
    """
    Prompt user for download mode: Create CKLB or Download Zip Only.
    Returns 'cklb' or 'zip' or None if cancelled.
    """
    options = ["Create CKLB", "Download Zip Only", "Cancel"]
    selected_idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Choose download mode:")
        for idx, opt in enumerate(options):
            if idx == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 1, 0, f"> {opt}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"  {opt}")
        stdscr.addstr(len(options) + 2, 0, "UP/DOWN to select, ENTER to confirm, b/q to cancel")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(options)
        elif key in [10, 13]:
            if selected_idx == 0:
                return 'cklb'
            elif selected_idx == 1:
                return 'zip'
            else:
                return None
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return None

def create_inventory_file_tui(stdscr):
    """
    TUI option to create an inventory file from selected files (no download).
    Prompts the user for the output inventory filename (must end with .json) after selection.
    """
    import curses
    import curses.textpad
    stdscr.clear()
    stdscr.addstr(0, 0, "Fetching webpage and parsing file links...")
    stdscr.refresh()
    try:
        html_content = fetch_page(URL)
        file_links = parse_table_for_links(html_content)
    except Exception as e:
        stdscr.addstr(2, 0, f"Error: {e}. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return
    if not file_links:
        stdscr.addstr(2, 0, "No downloadable files found. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return
    selected = set()
    current_idx = 0
    scroll_offset = 0
    status = "SPACE: select, ENTER: save inventory, r: refresh, b: back, q: quit"
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select files for inventory:")
        max_lines = curses.LINES - 3
        if current_idx < scroll_offset:
            scroll_offset = current_idx
        elif current_idx >= scroll_offset + max_lines:
            scroll_offset = current_idx - max_lines + 1
        visible_links = file_links[scroll_offset:scroll_offset + max_lines]
        for vis_idx, (file_name, _) in enumerate(visible_links):
            idx = scroll_offset + vis_idx
            sel = "[x]" if idx in selected else "[ ]"
            line = f"{sel} {file_name}"
            line = line[:curses.COLS - 4]
            if idx == current_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(vis_idx + 1, 0, f"> {line}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(vis_idx + 1, 0, f"  {line}")
        stdscr.addstr(curses.LINES-2, 0, status[:curses.COLS-1])
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
            to_inventory = selected if selected else {current_idx}
            selected_files = [file_links[idx] for idx in to_inventory]
            # Prompt for filename after selection
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, "Enter inventory filename (must end with .json): ")
                curses.echo()
                filename = stdscr.getstr(1, 0, 100).decode("utf-8").strip()
                curses.noecho()
                output_dir = os.path.join("user_docs", "inventory")
                out_path = os.path.join(output_dir, filename)
                if filename.lower() in ['q', 'quit']:
                    return
                if not filename.endswith(".json"):
                    stdscr.addstr(2, 0, "Error: Filename must end with .json. Press any key to try again or 'q' to quit.")
                    stdscr.refresh()
                    key2 = stdscr.getch()
                    if key2 in [ord('q'), ord('Q')]:
                        return
                    continue
                if os.path.exists(out_path):
                    stdscr.addstr(2, 0, f"Error: {filename} already exists. Press any key to try again or 'q' to quit.")
                    stdscr.refresh()
                    key2 = stdscr.getch()
                    if key2 in [ord('q'), ord('Q')]:
                        return
                    continue
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, mode=0o700)
                import json
                with open(out_path, "w") as f:
                    json.dump(selected_files, f, indent=2)
                stdscr.clear()
                stdscr.addstr(0, 0, f"Inventory file created: {out_path}")
                stdscr.addstr(2, 0, "Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
                return
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return
        elif key in [ord('r'), ord('R')]:
            break  # Refresh file list

def download_selected_inventory_tui(stdscr):
    """
    TUI option to download the newest available file for each selected technology from an inventory file.
    Prompts for CKLB or Zip download mode.
    """
    import json
    import re
    import curses
    import curses.textpad
    import shutil
    user_docs_dir = os.path.join("user_docs", "inventory")
    zip_dir = os.path.join("user_docs", "zip_files")
    cklb_dir = os.path.join("user_docs", "cklb_new")
    # List inventory files
    inventory_files = [f for f in os.listdir(user_docs_dir) if f.endswith(".json") and os.path.isfile(os.path.join(user_docs_dir, f))]
    if not inventory_files:
        stdscr.clear()
        stdscr.addstr(0, 0, "No inventory files found in user_docs/inventory. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return
    selected_idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select an inventory file:")
        for idx, fname in enumerate(inventory_files):
            if idx == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 1, 0, f"> {fname}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"  {fname}")
        stdscr.addstr(len(inventory_files) + 2, 0, "UP/DOWN to select, ENTER to confirm, b/q to cancel")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(inventory_files)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(inventory_files)
        elif key in [10, 13]:  # ENTER
            break
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return
    inventory_path = os.path.join(user_docs_dir, inventory_files[selected_idx])
    with open(inventory_path, "r") as f:
        inventory = json.load(f)
    # Extract technologies
    tech_map = {}
    tech_list = []
    for file_name, file_url in inventory:
        m = re.match(r"U_([^_]+(?:_[^_]+)*)_V", file_name)
        if m:
            tech = m.group(1)
            if tech not in tech_map:
                tech_map[tech] = []
                tech_list.append(tech)
            tech_map[tech].append((file_name, file_url))
    if not tech_list:
        stdscr.clear()
        stdscr.addstr(0, 0, "No technologies found in inventory. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return
    # Select technologies
    selected = set()
    current_idx = 0
    scroll_offset = 0
    status = "SPACE: select, ENTER: download, b/q: back"
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Select technologies to download from {inventory_files[selected_idx]}:")
        max_lines = curses.LINES - 3
        if current_idx < scroll_offset:
            scroll_offset = current_idx
        elif current_idx >= scroll_offset + max_lines:
            scroll_offset = current_idx - max_lines + 1
        visible_techs = tech_list[scroll_offset:scroll_offset + max_lines]
        for vis_idx, tech in enumerate(visible_techs):
            idx = scroll_offset + vis_idx
            sel = "[x]" if idx in selected else "[ ]"
            line = f"{sel} {tech}"
            line = line[:curses.COLS - 4]
            if idx == current_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(vis_idx + 1, 0, f"> {line}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(vis_idx + 1, 0, f"  {line}")
        stdscr.addstr(curses.LINES-2, 0, status[:curses.COLS-1])
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(tech_list)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(tech_list)
        elif key == ord(' '):
            if current_idx in selected:
                selected.remove(current_idx)
            else:
                selected.add(current_idx)
        elif key in [10, 13]:  # ENTER
            to_download = selected if selected else {current_idx}
            # Prompt for download mode
            mode = prompt_download_mode_tui(stdscr)
            if mode is None:
                return
            from web import download_file
            if mode == 'zip':
                if not os.path.exists(zip_dir):
                    os.makedirs(zip_dir, mode=0o700)
                for idx in to_download:
                    tech = tech_list[idx]
                    files = sorted(tech_map[tech], key=lambda x: x[0], reverse=True)
                    file_name, file_url = files[0]
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"Downloading: {file_name} to zip_files...")
                    stdscr.refresh()
                    # Download to zip_files dir
                    dest_path = os.path.join(zip_dir, file_name)
                    if os.path.exists(dest_path):
                        stdscr.addstr(2, 0, f"File already exists: {file_name}")
                        stdscr.refresh()
                        continue
                    try:
                        # Download to tmp, then move
                        download_file(file_url, file_name)
                        shutil.move(os.path.join("tmp", file_name), dest_path)
                        stdscr.addstr(2, 0, f"Downloaded: {file_name}")
                    except Exception as e:
                        stdscr.addstr(2, 0, f"Download error: {e}")
                    stdscr.refresh()
                stdscr.addstr(4, 0, "Press any key to continue.")
                stdscr.getch()
                return
            elif mode == 'cklb':
                if not os.path.exists(cklb_dir):
                    os.makedirs(cklb_dir, mode=0o700)
                import tempfile
                import subprocess
                for idx in to_download:
                    tech = tech_list[idx]
                    files = sorted(tech_map[tech], key=lambda x: x[0], reverse=True)
                    file_name, file_url = files[0]
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"Downloading: {file_name} for CKLB conversion...")
                    stdscr.refresh()
                    try:
                        download_file(file_url, file_name)
                        tmp_path = os.path.join("tmp", file_name)
                        # Extract XML from zip
                        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                            with tempfile.TemporaryDirectory() as extract_dir:
                                zip_ref.extractall(extract_dir)
                                # Find XCCDF XML file recursively
                                xml_candidates = glob.glob(os.path.join(extract_dir, '**', '*xccdf*.xml'), recursive=True)
                                if not xml_candidates:
                                    xml_candidates = glob.glob(os.path.join(extract_dir, '**', '*.xml'), recursive=True)
                                if not xml_candidates:
                                    print(f"[CKLB ERROR] No XCCDF XML found in zip: {file_name}")
                                    continue  # Log error to terminal, skip to next file
                                xccdf_xml = xml_candidates[0]
                                cklb_name = os.path.splitext(file_name)[0] + ".cklb"
                                cklb_path = os.path.join(cklb_dir, cklb_name)
                                # Use subprocess to call create_cklb.py
                                result = subprocess.run([
                                    sys.executable, os.path.join(os.path.dirname(__file__), "create_cklb.py"),
                                    xccdf_xml, cklb_path
                                ], capture_output=True, text=True)
                                if result.returncode == 0:
                                    stdscr.addstr(2, 0, f"CKLB created: {cklb_name}")
                                else:
                                    stdscr.addstr(2, 0, f"CKLB error: {result.stderr.strip()}")
                    except Exception as e:
                        stdscr.addstr(2, 0, f"Download/CKLB error: {e}")
                    stdscr.refresh()
                stdscr.addstr(4, 0, "Press any key to continue.")
                stdscr.getch()
                return
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
            elif selected_func == "create_inventory_file_tui":
                create_inventory_file_tui(stdscr)
            elif selected_func == "download_selected_inventory_tui":
                download_selected_inventory_tui(stdscr)
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
