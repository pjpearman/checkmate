#!/usr/bin/env python3
"""
Demonstration script for TUI STIG selection enhancement.
Shows the new interface capabilities with mock data.
"""

import sys
import curses
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_stig_selection_interface(stdscr):
    """Demonstrate the STIG selection interface with mock data."""
    
    # Mock STIG data for demonstration
    mock_stigs = [
        {
            'filename': 'U_Windows_10_V2R1_20231201_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/windows10.zip',
            'stig_id': 'Windows_10',
            'version': 2,
            'release': 1,
            'date': '20231201',
            'type': 'stig',
            'size': 1456789,
            'last_modified': 'Fri, 01 Dec 2023 10:30:00 GMT'
        },
        {
            'filename': 'U_RHEL_8_V1R12_20231115_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/rhel8.zip',
            'stig_id': 'RHEL_8',
            'version': 1,
            'release': 12,
            'date': '20231115',
            'type': 'stig',
            'size': 2387456,
            'last_modified': 'Wed, 15 Nov 2023 14:45:00 GMT'
        },
        {
            'filename': 'U_MS_SQL_Server_2019_V2R3_20231010_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/mssql2019.zip',
            'stig_id': 'MS_SQL_Server_2019',
            'version': 2,
            'release': 3,
            'date': '20231010',
            'type': 'stig',
            'size': 856234,
            'last_modified': 'Tue, 10 Oct 2023 09:15:00 GMT'
        },
        {
            'filename': 'U_Apache_Server_2_4_V2R4_20231120_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/apache24.zip',
            'stig_id': 'Apache_Server_2_4',
            'version': 2,
            'release': 4,
            'date': '20231120',
            'type': 'stig',
            'size': 1123567,
            'last_modified': 'Mon, 20 Nov 2023 16:20:00 GMT'
        },
        {
            'filename': 'U_Oracle_Database_19c_V1R8_20231025_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/oracle19c.zip',
            'stig_id': 'Oracle_Database_19c',
            'version': 1,
            'release': 8,
            'date': '20231025',
            'type': 'stig',
            'size': 3245678,
            'last_modified': 'Wed, 25 Oct 2023 11:30:00 GMT'
        },
        {
            'filename': 'U_Cisco_IOS_XE_V2R7_20231205_STIG.zip',
            'url': 'https://public.cyber.mil/stigs/downloads/ciscoiosxe.zip',
            'stig_id': 'Cisco_IOS_XE',
            'version': 2,
            'release': 7,
            'date': '20231205',
            'type': 'stig',
            'size': 987654,
            'last_modified': 'Tue, 05 Dec 2023 13:45:00 GMT'
        }
    ]
    
    # Initialize display
    stdscr.clear()
    curses.curs_set(0)
    
    # Setup colors if available
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Selected
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
    
    # Demo state
    current_idx = 0
    selected_files = {0, 2, 4}  # Pre-select some files for demo
    
    def format_file_size(size_bytes):
        """Format file size in human readable format."""
        if size_bytes >= 1024*1024:
            return f"{size_bytes/(1024*1024):.1f}MB"
        elif size_bytes >= 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes}B"
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = "CheckMate TUI - Enhanced STIG Selection Demo"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Subtitle
        subtitle = f"Mock Data: {len(mock_stigs)} files ({len(selected_files)} selected)"
        stdscr.addstr(1, (width - len(subtitle)) // 2, subtitle)
        
        # Instructions
        instructions = [
            "Navigation: ↑/↓ arrows  |  Selection: SPACE to toggle, A=all, N=none",
            "Demo Actions: ENTER=show selection, D=show download info, Q=quit demo"
        ]
        
        for i, instruction in enumerate(instructions):
            if 3 + i < height:
                stdscr.addstr(3 + i, 0, instruction[:width-1])
        
        # Column headers
        header_line = 6
        if header_line < height:
            header = f"{'Status':<8} {'STIG ID':<30} {'Ver':<6} {'Rel':<6} {'Size':<10} {'Updated':<12}"
            stdscr.addstr(header_line, 0, header[:width-1], curses.A_REVERSE)
        
        # Display files
        content_start = header_line + 1
        
        for i, stig in enumerate(mock_stigs):
            line_y = content_start + i
            if line_y >= height - 2:
                break
                
            # Format file information
            status = "[✓]" if i in selected_files else "[ ]"
            stig_id = stig.get('stig_id', 'Unknown')[:29]
            version = f"V{stig.get('version', '?')}" if stig.get('version') else "V?"
            release = f"R{stig.get('release', '?')}" if stig.get('release') else "R?"
            size_str = format_file_size(stig.get('size', 0))
            
            # Format date
            date_str = "2023-12-01" if i == 0 else f"2023-{11 + (i % 2):02d}-{15 - i:02d}"
            
            line_text = f"{status:<8} {stig_id:<30} {version:<6} {release:<6} {size_str:<10} {date_str:<12}"
            
            # Highlight current selection
            if i == current_idx and curses.has_colors():
                stdscr.addstr(line_y, 0, line_text[:width-1], curses.color_pair(2))
            else:
                stdscr.addstr(line_y, 0, line_text[:width-1])
        
        # Status line
        status_y = height - 1
        status_text = f"File {current_idx + 1}/{len(mock_stigs)} | Selected: {len(selected_files)} | DEMO MODE - Press Q to quit"
        stdscr.addstr(status_y, 0, status_text[:width-1], curses.A_REVERSE)
        
        stdscr.refresh()
        
        # Handle input
        key = stdscr.getch()
        
        if key == ord('q') or key == ord('Q'):
            break
        elif key == curses.KEY_UP:
            current_idx = max(0, current_idx - 1)
        elif key == curses.KEY_DOWN:
            current_idx = min(len(mock_stigs) - 1, current_idx + 1)
        elif key == ord(' '):  # Space to toggle selection
            if current_idx in selected_files:
                selected_files.remove(current_idx)
            else:
                selected_files.add(current_idx)
        elif key == ord('a') or key == ord('A'):  # Select all
            selected_files = set(range(len(mock_stigs)))
        elif key == ord('n') or key == ord('N'):  # Select none
            selected_files.clear()
        elif key == 10 or key == 13:  # Enter - show selection
            show_selection_info(stdscr, mock_stigs, selected_files)
        elif key == ord('d') or key == ord('D'):  # Show download info
            show_download_info(stdscr, mock_stigs)

def show_selection_info(stdscr, stigs, selected_files):
    """Show information about selected files."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    title = "Selected Files Information"
    stdscr.addstr(0, 0, title, curses.A_BOLD)
    stdscr.addstr(1, 0, "=" * len(title))
    
    if not selected_files:
        stdscr.addstr(3, 0, "No files selected.")
    else:
        total_size = 0
        for i, idx in enumerate(sorted(selected_files)):
            if i + 3 >= height - 3:
                stdscr.addstr(i + 3, 0, f"... and {len(selected_files) - i} more files")
                break
                
            stig = stigs[idx]
            size = stig.get('size', 0)
            total_size += size
            
            size_str = format_file_size(size) if size > 0 else "Unknown"
            stdscr.addstr(i + 3, 0, f"{i+1}. {stig['stig_id']} ({size_str})")
        
        # Show totals
        stdscr.addstr(len(selected_files) + 5, 0, f"Total selected: {len(selected_files)} files")
        if total_size > 0:
            stdscr.addstr(len(selected_files) + 6, 0, f"Total size: {format_file_size(total_size)}")
    
    stdscr.addstr(height - 2, 0, "Press any key to return...")
    stdscr.refresh()
    stdscr.getch()

def show_download_info(stdscr, stigs):
    """Show download information."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    title = "Download Information (Demo Mode)"
    stdscr.addstr(0, 0, title, curses.A_BOLD)
    stdscr.addstr(1, 0, "=" * len(title))
    
    info_lines = [
        "",
        "In the real application, this would:",
        "• Download selected STIG files from DISA website",
        "• Show real-time progress for each file",
        "• Display download speeds and time remaining",
        "• Handle network errors gracefully",
        "• Save files to the configured zip_files directory",
        "• Provide success/failure summary",
        "",
        f"Available files: {len(stigs)}",
        f"Total size: {format_file_size(sum(s.get('size', 0) for s in stigs))}",
        "",
        "Key benefits of this enhancement:",
        "• No more terminal flooding with 400+ files",
        "• Intuitive navigation and selection",
        "• Rich metadata for informed decisions",
        "• Batch operations support",
        "• Progress feedback and error handling",
    ]
    
    for i, line in enumerate(info_lines):
        if i + 3 < height - 2:
            stdscr.addstr(i + 3, 0, line[:width-1])
    
    stdscr.addstr(height - 2, 0, "Press any key to return...")
    stdscr.refresh()
    stdscr.getch()

def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes >= 1024*1024:
        return f"{size_bytes/(1024*1024):.1f}MB"
    elif size_bytes >= 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes}B"

def main():
    """Main demo function."""
    print("CheckMate TUI STIG Selection Enhancement Demo")
    print("=" * 45)
    print()
    print("This demo shows the enhanced STIG file selection interface")
    print("that solves the problem of terminal flooding with 400+ files.")
    print()
    print("Key features you'll see:")
    print("• Scrollable table view with metadata")
    print("• Multi-file selection capabilities") 
    print("• Intuitive keyboard navigation")
    print("• File size formatting")
    print("• Selection status indicators")
    print()
    print("Controls in demo:")
    print("• ↑/↓: Navigate files")
    print("• SPACE: Toggle selection")
    print("• A: Select all, N: Select none")
    print("• ENTER: Show selection info")
    print("• D: Show download info")
    print("• Q: Quit demo")
    print()
    print("Press ENTER to start demo (or Ctrl+C to cancel)...")
    
    try:
        input()
        print("Starting demo...")
        curses.wrapper(demo_stig_selection_interface)
        print("\nDemo completed! The enhanced TUI interface provides:")
        print("✓ No terminal flooding with large file lists")
        print("✓ Intuitive navigation and selection")
        print("✓ Rich metadata display")
        print("✓ Progress feedback and error handling")
        print("\nTry it out: python checkmate.py --tui")
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
    except Exception as e:
        print(f"\nDemo error: {e}")
        print("Note: This demo requires a terminal with curses support.")

if __name__ == "__main__":
    main()
