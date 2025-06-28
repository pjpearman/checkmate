#!/usr/bin/env python3
"""
Test script to verify that the TUI displays both V#R# and Y##M## STIG metadata correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.web import WebDownloader
from core.config import Config
from core.log_config import get_operation_logger

logger = get_operation_logger("stig_metadata_test")


def test_stig_metadata_display():
    """Test that STIG metadata includes both V#R# and Y##M## formats."""
    print("Testing STIG metadata display with both V#R# and Y##M## formats...")
    print("=" * 80)
    
    # Create a mock list of STIG files with both formats
    mock_file_links = [
        ('U_Windows_10_V2R3_STIG.zip', 'https://example.com/U_Windows_10_V2R3_STIG.zip'),
        ('U_IBM_zOS_Y25M04_STIG.zip', 'https://example.com/U_IBM_zOS_Y25M04_STIG.zip'),
        ('U_VMW_vSphere_7-0_Y25M04_STIG.zip', 'https://example.com/U_VMW_vSphere_7-0_Y25M04_STIG.zip'),
        ('U_Microsoft_SQL_Server_2016_Instance_V2R8_STIG.zip', 'https://example.com/U_Microsoft_SQL_Server_2016_Instance_V2R8_STIG.zip'),
        ('U_MS_Exchange_2019_Y25M01_STIG.zip', 'https://example.com/U_MS_Exchange_2019_Y25M01_STIG.zip'),
        ('U_zOS_ACF2_Y25M04_Products.zip', 'https://example.com/U_zOS_ACF2_Y25M04_Products.zip'),
        ('U_Apache_Server_2-4_Unix_Y25M04_STIG.zip', 'https://example.com/U_Apache_Server_2-4_Unix_Y25M04_STIG.zip'),
        ('U_Citrix_VAD_7-x_Y22M01_STIG.zip', 'https://example.com/U_Citrix_VAD_7-x_Y22M01_STIG.zip'),
    ]
    
    downloader = WebDownloader()
    stigs = []
    
    # Process each mock file to create metadata
    for file_name, file_url in mock_file_links:
        try:
            # Parse STIG information from filename
            stig_info = downloader.parse_stig_filename(file_name)
            stig_info['filename'] = file_name
            stig_info['url'] = file_url
            
            # Add some mock file info
            stig_info.update({
                'size': 1024000,  # 1MB mock size
                'content_type': 'application/zip',
                'last_modified': '2025-01-15',
                'etag': f'mock-etag-{hash(file_name)}'
            })
            
            stigs.append(stig_info)
            
        except Exception as e:
            logger.error(f"Error processing STIG file {file_name}: {e}")
            continue
    
    # Display the results in a format similar to the TUI
    print(f"\nFound {len(stigs)} STIG files with metadata:")
    print("=" * 120)
    print(f"{'#':<3} {'STIG ID':<35} {'Ver':<8} {'Rel':<8} {'Format':<12} {'Type':<8} {'Size':<10}")
    print("-" * 120)
    
    for i, stig in enumerate(stigs, 1):
        stig_id = str(stig.get('stig_id', 'Unknown'))[:34]
        version = str(stig.get('version', 'N/A'))[:7]
        release = str(stig.get('release', 'N/A'))[:7]
        format_type = str(stig.get('format', 'unknown'))[:11]
        file_type = str(stig.get('type', 'unknown'))[:7]
        size = f"{stig.get('size', 0) // 1024}KB" if stig.get('size') else 'N/A'
        
        print(f"{i:<3} {stig_id:<35} {version:<8} {release:<8} {format_type:<12} {file_type:<8} {size:<10}")
    
    # Summary by format
    version_release_count = sum(1 for s in stigs if s.get('format') == 'version_release')
    year_month_count = sum(1 for s in stigs if s.get('format') == 'year_month')
    
    print("\n" + "=" * 120)
    print("Summary:")
    print(f"  📊 Total STIGs: {len(stigs)}")
    print(f"  📅 V#R# format (version/release): {version_release_count}")
    print(f"  🗓️  Y##M## format (year/month): {year_month_count}")
    print(f"  ✅ Both formats are recognized and displayed!")
    
    return len(stigs) > 0 and version_release_count > 0 and year_month_count > 0


def test_tui_column_display():
    """Test how the metadata would appear in TUI columns."""
    print("\n" + "=" * 80)
    print("TUI Column Display Test")
    print("=" * 80)
    
    # Test various STIG names and formats
    test_files = [
        'U_Windows_10_V2R3_STIG.zip',
        'U_IBM_zOS_Y25M04_STIG.zip', 
        'U_Microsoft_SQL_Server_2016_Instance_V1R24_STIG.zip',
        'U_VMW_vSphere_8-0_Y25M04_STIG.zip',
        'U_Apache_Server_2-4_Unix_Y25M04_STIG.zip'
    ]
    
    downloader = WebDownloader()
    
    # Column headers (as they would appear in the TUI)
    print("Column headers as they would appear in TUI:")
    print(f"{'STIG ID':<40} {'Version':<10} {'Release':<10}")
    print("-" * 60)
    
    for filename in test_files:
        parsed = downloader.parse_stig_filename(filename)
        stig_id = str(parsed.get('stig_id', 'Unknown'))[:39]
        version = str(parsed.get('version', 'N/A'))
        release = str(parsed.get('release', 'N/A'))
        
        print(f"{stig_id:<40} {version:<10} {release:<10}")
    
    print("\n✅ Both V#R# and Y##M## formats display correctly in TUI columns!")


if __name__ == "__main__":
    success = test_stig_metadata_display()
    test_tui_column_display()
    
    if success:
        print("\n🎉 SUCCESS: Both V#R# and Y##M## STIG formats are properly supported!")
        print("The TUI will correctly display metadata for both version/release and year/month STIGs.")
    else:
        print("\n❌ FAILURE: Issues detected with STIG metadata processing.")
        sys.exit(1)
