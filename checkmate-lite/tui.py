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

# Ensure user_docs and subdirectories exist at startup
USER_DOCS_DIR = "user_docs"
SUBDIRS = [
    "zip_files",
    "cklb_new",
    "cklb_artifacts",
    "inventory"
]
for sub in SUBDIRS:
    os.makedirs(os.path.join(USER_DOCS_DIR, sub), exist_ok=True)

# Import existing functions
from web import fetch_page, parse_table_for_links, download_file, URL, HEADERS

# Setup a list of future functions for easy extension
FUNCTIONS = {
    "Create Inventory File": "create_inventory_file_tui",
    "Download Options": "download_options_tui",
    "Manage Checklists": "manage_checklists_tui",
    # Example: "Set Download Directory": "set_download_dir",
    # Example: "Toggle File Types": "toggle_file_types",
}

def draw_menu(stdscr, selected_idx):
    """
    Display the main menu. Highlights the currently selected menu item.
    """
    stdscr.clear()
    stdscr.addstr(0, 0, "== CheckMate Lite TUI ==")
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
    If 'Create CKLB' is selected, convert downloaded zips to CKLBs.
    """
    download_mode = prompt_download_mode_tui(stdscr)
    if not download_mode:
        return  # Cancelled
    import shutil
    from web import download_file
    from create_cklb import convert_xccdf_zip_to_cklb
    zip_dir = os.path.join("user_docs", "zip_files")
    cklb_dir = os.path.join("user_docs", "cklb_new")
    tmp_dir = "tmp"
    while True:
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
                    try:
                        download_file(file_url, file_name)
                        stdscr.addstr(2, 0, f"Downloaded: {file_name}")
                        # If CKLB mode, convert zip to CKLB
                        if download_mode == 'cklb' and file_name.endswith('.zip'):
                            zip_path = os.path.join(tmp_dir, file_name)
                            if not os.path.exists(cklb_dir):
                                os.makedirs(cklb_dir, mode=0o700)
                            cklb_results = convert_xccdf_zip_to_cklb(zip_path, cklb_dir)
                            for cklb_path, error in cklb_results:
                                if cklb_path:
                                    stdscr.addstr(3, 0, f"CKLB created: {os.path.basename(cklb_path)}")
                                else:
                                    stdscr.addstr(3, 0, error or f"Unknown CKLB error for {file_name}")
                        elif download_mode == 'zip':
                            if not os.path.exists(zip_dir):
                                os.makedirs(zip_dir, mode=0o700)
                            shutil.move(os.path.join(tmp_dir, file_name), os.path.join(zip_dir, file_name))
                    except Exception as e:
                        stdscr.addstr(2, 0, f"Download error: {e}")
                    stdscr.refresh()
                stdscr.addstr(5, 0, "Press any key to continue.")
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
    from create_inventory import generate_inventory
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
            # Convert tuples to dicts for generate_inventory
            selected_dicts = [{'FileName': fn, 'URL': url} for fn, url in selected_files]
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
                # Use generate_inventory to write the file
                generate_inventory(selected_dicts, out_path)
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

def download_options_tui(stdscr):
    """
    Presents download options: Download All Files or Download from Inventory.
    """
    options = ["Select From All Files", "Download Using an Inventory File", "Back"]
    selected_idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Choose download option:")
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
                # Warn the user before downloading all files
                stdscr.clear()
                stdscr.addstr(0, 0, "This will download ALL selected files from the website.")
                stdscr.addstr(2, 0, "Are you sure you want to continue? (y/n)")
                stdscr.refresh()
                while True:
                    confirm_key = stdscr.getch()
                    if confirm_key in [ord('y'), ord('Y')]:
                        download_files(stdscr)
                        return
                    elif confirm_key in [ord('n'), ord('N'), ord('b'), ord('B'), ord('q'), ord('Q')]:
                        return
            elif selected_idx == 1:
                download_selected_inventory_tui(stdscr)
                return
            else:
                return
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return

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
    for entry in inventory:
        file_name = entry.get('file_name')
        file_url = entry.get('url')
        if not file_name or not file_url:
            continue
        # Match both _V#R# and _Y##M## patterns
        m = re.search(r"U_([^_]+(?:_[^_]+)*?)_(?:V\d+[Rr]\d+|Y\d{2}M\d{2})", file_name)
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
                from create_cklb import convert_xccdf_zip_to_cklb
                results = []
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
                        cklb_results = convert_xccdf_zip_to_cklb(tmp_path, cklb_dir)
                        for cklb_path, error in cklb_results:
                            if cklb_path:
                                results.append(f"CKLB created: {os.path.basename(cklb_path)}")
                            else:
                                results.append(error or f"Unknown CKLB error for {file_name}")
                    except Exception as e:
                        results.append(f"Download/CKLB error for {file_name}: {e}")
                        print(f"[CKLB ERROR] {e}")
                stdscr.clear()
                stdscr.addstr(0, 0, "CKLB creation results:")
                for i, msg in enumerate(results):
                    stdscr.addstr(i+1, 0, msg[:curses.COLS-1])
                stdscr.addstr(len(results)+2, 0, "Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
                return
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return
        elif key in [ord('r'), ord('R')]:
            break  # Refresh file list

def browse_and_select_cklb_files(stdscr, start_dir=None, file_label='.cklb'):
    """
    Terminal-based directory browser for selecting one or more files with a given extension.
    Returns a list of selected file paths or None if cancelled.
    Hidden files and directories (starting with '.') are not shown.
    ENTER: open directory, SPACE: select file, i: import/compare all selected files.
    """
    import os
    if start_dir is None:
        start_dir = os.path.expanduser("~")
    current_dir = os.path.abspath(start_dir)
    selected = set()
    current_idx = 0
    scroll_offset = 0
    while True:
        entries = [e for e in [".."] + sorted(os.listdir(current_dir)) if not e.startswith('.') or e == ".."]
        files_and_dirs = []
        for entry in entries:
            full_path = os.path.join(current_dir, entry)
            if os.path.isdir(full_path):
                files_and_dirs.append((entry + "/", full_path, True))
            elif entry.endswith(file_label):
                files_and_dirs.append((entry, full_path, False))
        stdscr.clear()
        stdscr.addstr(0, 0, f"Browsing: {current_dir}")
        stdscr.addstr(1, 0, f"UP/DOWN: move  ENTER: open dir  SPACE: select file  b/q: back/cancel  i: select {file_label} file(s)")
        max_lines = curses.LINES - 3
        if current_idx < scroll_offset:
            scroll_offset = current_idx
        elif current_idx >= scroll_offset + max_lines:
            scroll_offset = current_idx - max_lines + 1
        visible = files_and_dirs[scroll_offset:scroll_offset + max_lines]
        for vis_idx, (entry, full_path, is_dir) in enumerate(visible):
            idx = scroll_offset + vis_idx
            sel = "[x]" if (not is_dir and full_path in selected) else "[ ]"
            prefix = "> " if idx == current_idx else "  "
            display = f"{prefix}{sel if not is_dir else '   '} {entry}"
            display = display[:curses.COLS-1]
            if idx == current_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(vis_idx + 2, 0, display)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(vis_idx + 2, 0, display)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(files_and_dirs)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(files_and_dirs)
        elif key in [10, 13]:  # ENTER
            entry, full_path, is_dir = files_and_dirs[current_idx]
            if is_dir:
                current_dir = os.path.abspath(full_path)
                current_idx = 0
                scroll_offset = 0
        elif key == ord(' '):
            entry, full_path, is_dir = files_and_dirs[current_idx]
            if not is_dir:
                if full_path in selected:
                    selected.remove(full_path)
                else:
                    selected.add(full_path)
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return None
        elif key in [ord('i'), ord('I')]:
            if selected:
                return list(selected)
    return None

def manage_checklists_tui(stdscr):
    """
    Manage Checklists submenu with import and compare functionality and directory browsing.
    """
    from cklb_handler import import_cklbs, compare_cklb_versions
    options = [
        "Import CKLB(s)",
        "Compare CKLB Versions",
        "Upgrade CKLB(s) (future feature)",
        "Back"
    ]
    selected_idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Manage Checklists")
        for idx, opt in enumerate(options):
            if idx == selected_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx + 1, 0, f"> {opt}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"  {opt}")
        stdscr.addstr(len(options) + 2, 0, "UP/DOWN to select, ENTER to confirm, b/q to go back")
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(options)
        elif key in [10, 13]:
            if selected_idx == 0:
                # Import CKLB(s) with directory browser
                selected_files = browse_and_select_cklb_files(stdscr)
                if not selected_files:
                    continue
                results = import_cklbs(selected_files)
                stdscr.clear()
                stdscr.addstr(0, 0, "Import results:")
                for i, (fname, status) in enumerate(results):
                    stdscr.addstr(i+1, 0, f"{os.path.basename(fname)}: {status}"[:curses.COLS-1])
                stdscr.addstr(len(results)+2, 0, "Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
            elif selected_idx == 1:
                # Compare CKLB Versions
                stdscr.clear()
                stdscr.addstr(0, 0, "Select one or more CKLB files for comparison (A):")
                stdscr.refresh()
                files_a = browse_and_select_cklb_files(stdscr, start_dir=os.path.join("user_docs", "cklb_artifacts"), file_label='.cklb')
                if not files_a:
                    continue
                stdscr.clear()
                stdscr.addstr(0, 0, "Select a CKLB file to compare against (B):")
                stdscr.refresh()
                files_b = browse_and_select_cklb_files(stdscr, start_dir=os.path.join("user_docs", "cklb_new"), file_label='.cklb')
                if not files_b or len(files_b) != 1:
                    continue
                from cklb_handler import compare_cklb_versions
                diff_output = compare_cklb_versions(files_a, files_b[0])
                stdscr.clear()
                lines = diff_output.split('\n')
                show_paged_output(stdscr, lines)
                stdscr.addstr(curses.LINES-1, 0, "Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
            elif selected_idx == len(options) - 1:
                return  # Back
            else:
                stdscr.clear()
                stdscr.addstr(0, 0, f"{options[selected_idx]}\n\nThis feature will be available in a future release.")
                stdscr.addstr(3, 0, "Press any key to return.")
                stdscr.refresh()
                stdscr.getch()
        elif key in [ord('b'), ord('B'), ord('q'), ord('Q')]:
            return

def show_paged_output(stdscr, lines):
    import curses
    max_y, max_x = stdscr.getmaxyx()
    page_size = max_y - 2  # Leave room for prompt
    pos = 0
    while pos < len(lines):
        stdscr.clear()
        for i in range(page_size):
            if pos + i >= len(lines):
                break
            stdscr.addstr(i, 0, lines[pos + i][:max_x-1])
        prompt = "--More-- (SPACE: next, q: quit, ↑/↓: scroll)"
        stdscr.addstr(page_size, 0, prompt[:max_x-1])
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        elif key == ord(' '):
            pos += page_size
        elif key == curses.KEY_DOWN:
            pos += 1
        elif key == curses.KEY_UP:
            pos = max(0, pos - 1)
        else:
            pos += 1
    stdscr.clear()
    stdscr.refresh()

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
            if selected_func == "download_options_tui":
                download_options_tui(stdscr)
            elif selected_func == "create_inventory_file_tui":
                create_inventory_file_tui(stdscr)
            elif selected_func == "manage_checklists_tui":
                manage_checklists_tui(stdscr)
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
