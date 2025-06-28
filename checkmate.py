#!/usr/bin/env python3
"""
CheckMate Unified Launcher
Launch either GUI or TUI interface using shared core functionality.
"""

import sys
import argparse
from pathlib import Path

def create_argument_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="CheckMate - STIG Management Tool",
        epilog="Use 'checkmate gui' for graphical interface or 'checkmate tui' for terminal interface"
    )
    
    parser.add_argument(
        'interface',
        choices=['gui', 'tui'],
        help='Interface to launch (gui or tui)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='CheckMate v2.1.0 (Refactored)'
    )
    
    return parser

def main():
    """Main entry point for CheckMate applications."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        if args.interface == 'gui':
            # Launch GUI
            print("Starting CheckMate GUI...")
            from gui.main import main as gui_main
            gui_main()
            
        elif args.interface == 'tui':
            # Launch TUI
            print("Starting CheckMate TUI...")
            from tui.main import CheckMateTUI
            import curses
            def tui_main():
                app = CheckMateTUI()
                curses.wrapper(app.main_loop)
            tui_main()
            
    except ImportError as e:
        print(f"Error importing {args.interface} module: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting {args.interface}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
