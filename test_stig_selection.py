#!/usr/bin/env python3
"""
Test script for the enhanced STIG selection interface in TUI.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import WebDownloader, Config

def test_stig_selection():
    """Test the STIG selection interface components."""
    print("Testing STIG Selection Interface")
    print("=" * 40)
    
    # Initialize components
    config = Config()
    web_downloader = WebDownloader(config)
    
    print("1. Testing WebDownloader.get_available_stigs()...")
    try:
        stigs = web_downloader.get_available_stigs()
        print(f"   Found {len(stigs)} STIG files")
        
        if stigs:
            print("\n2. Sample STIG metadata:")
            sample_stig = stigs[0]
            for key, value in sample_stig.items():
                print(f"   {key}: {value}")
            
            print(f"\n3. Data structure validation:")
            required_fields = ['filename', 'url', 'stig_id', 'version', 'release']
            for field in required_fields:
                has_field = field in sample_stig
                print(f"   {field}: {'✓' if has_field else '✗'}")
                
        print("\n4. Testing size formatting...")
        test_sizes = [500, 1500, 1500000, 1500000000]
        for size in test_sizes:
            formatted = format_file_size(size)
            print(f"   {size} bytes -> {formatted}")
            
    except Exception as e:
        print(f"   Error: {e}")
        print("   This might be expected if not connected to internet")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes >= 1024*1024*1024:
        return f"{size_bytes/(1024*1024*1024):.1f}GB"
    elif size_bytes >= 1024*1024:
        return f"{size_bytes/(1024*1024):.1f}MB"
    elif size_bytes >= 1024:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes}B"

if __name__ == "__main__":
    test_stig_selection()
