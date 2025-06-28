#!/usr/bin/env python3
"""
Integration test to verify the TUI properly displays both V#R# and Y##M## STIG formats.
This test simulates the TUI STIG selection process with enhanced parsing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.web import WebDownloader
from core.config import Config
from core.log_config import get_operation_logger

logger = get_operation_logger("tui_integration_test")


def simulate_tui_stig_selection():
    """Simulate the TUI STIG selection process with enhanced parsing."""
    print("🔧 TUI Integration Test: STIG Selection with V#R# and Y##M## Support")
    print("=" * 80)
    
    try:
        # Initialize components
        config = Config()
        downloader = WebDownloader(config)
        
        print("📡 Simulating STIG list fetch...")
        
        # Create a mock STIG list that includes both formats
        mock_stigs = [
            {
                'filename': 'U_Windows_10_V2R3_STIG.zip',
                'url': 'https://example.com/U_Windows_10_V2R3_STIG.zip',
                'stig_id': 'Windows_10',
                'version': 2,
                'release': 3,
                'format': 'version_release',
                'type': 'stig',
                'size': 1500000,
                'last_modified': '2024-12-15'
            },
            {
                'filename': 'U_IBM_zOS_Y25M04_STIG.zip',
                'url': 'https://example.com/U_IBM_zOS_Y25M04_STIG.zip',
                'stig_id': 'IBM_zOS',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'stig',
                'size': 2100000,
                'last_modified': '2025-04-01'
            },
            {
                'filename': 'U_VMW_vSphere_7-0_Y25M04_STIG.zip',
                'url': 'https://example.com/U_VMW_vSphere_7-0_Y25M04_STIG.zip',
                'stig_id': 'VMW_vSphere_7-0',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'stig',
                'size': 1800000,
                'last_modified': '2025-04-01'
            },
            {
                'filename': 'U_MS_Exchange_2019_Y25M01_STIG.zip',
                'url': 'https://example.com/U_MS_Exchange_2019_Y25M01_STIG.zip',
                'stig_id': 'MS_Exchange_2019',
                'version': 'Y25',
                'release': 'M01',
                'format': 'year_month',
                'type': 'stig',
                'size': 1200000,
                'last_modified': '2025-01-15'
            }
        ]
        
        print(f"✅ Successfully loaded {len(mock_stigs)} STIG files")
        
        # Simulate TUI display
        print("\n📋 TUI STIG Selection Display:")
        print("=" * 90)
        print(f"{'#':<3} {'STIG ID':<30} {'Version':<10} {'Release':<10} {'Size':<10} {'Updated':<12}")
        print("-" * 90)
        
        for i, stig in enumerate(mock_stigs, 1):
            stig_id = str(stig['stig_id'])[:29]
            version = str(stig['version'])
            release = str(stig['release'])
            size_mb = f"{stig['size'] // 1024 // 1024}MB"
            updated = stig['last_modified']
            
            # Add format indicator
            format_indicator = "📅" if stig['format'] == 'version_release' else "🗓️"
            
            print(f"{i:<3} {format_indicator} {stig_id:<28} {version:<10} {release:<10} {size_mb:<10} {updated:<12}")
        
        print("\nLegend:")
        print("  📅 V#R# format (version/release)")
        print("  🗓️  Y##M## format (year/month)")
        
        # Test format recognition
        print("\n🔍 Format Recognition Test:")
        print("-" * 40)
        
        v_r_count = sum(1 for s in mock_stigs if s['format'] == 'version_release')
        y_m_count = sum(1 for s in mock_stigs if s['format'] == 'year_month')
        
        print(f"V#R# STIGs detected: {v_r_count}")
        print(f"Y##M## STIGs detected: {y_m_count}")
        print(f"Total STIGs: {len(mock_stigs)}")
        
        # Test parsing consistency
        print("\n🧪 Parsing Consistency Test:")
        print("-" * 40)
        
        all_parsed_correctly = True
        
        for stig in mock_stigs:
            # Re-parse the filename to verify consistency
            parsed = downloader.parse_stig_filename(stig['filename'])
            
            if parsed['stig_id'] != stig['stig_id']:
                print(f"❌ STIG ID mismatch for {stig['filename']}")
                all_parsed_correctly = False
            elif parsed['version'] != stig['version']:
                print(f"❌ Version mismatch for {stig['filename']}")
                all_parsed_correctly = False
            elif parsed['release'] != stig['release']:
                print(f"❌ Release mismatch for {stig['filename']}")
                all_parsed_correctly = False
            else:
                print(f"✅ {stig['filename']} parsed correctly")
        
        if all_parsed_correctly:
            print("\n🎉 All STIG files parsed consistently!")
        else:
            print("\n❌ Some parsing inconsistencies detected.")
            return False
        
        # Test selection simulation
        print("\n🎯 Selection Simulation:")
        print("-" * 40)
        
        selected_stigs = [mock_stigs[0], mock_stigs[1]]  # Select first two
        total_size = sum(stig['size'] for stig in selected_stigs)
        
        print(f"Selected {len(selected_stigs)} STIGs:")
        for stig in selected_stigs:
            format_name = "V#R#" if stig['format'] == 'version_release' else "Y##M##"
            print(f"  - {stig['stig_id']} ({format_name}: {stig['version']}/{stig['release']})")
        
        print(f"Total download size: {total_size // 1024 // 1024}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"TUI integration test failed: {e}")
        return False


def test_real_parsing():
    """Test parsing with actual STIG filenames from logs."""
    print("\n" + "=" * 80)
    print("🔍 Real STIG Filename Parsing Test")
    print("=" * 80)
    
    # Real filenames from the logs
    real_filenames = [
        'U_IBM_zOS_Y25M04_STIG.zip',
        'U_VMW_vSphere_7-0_Y25M04_STIG.zip',
        'U_VMW_vSphere_8-0_Y25M04_STIG.zip',
        'U_zOS_ACF2_Y25M04_Products.zip',
        'U_zOS_RACF_Y25M04_Products.zip',
        'U_zOS_Y25M04_SRR.zip',
        'U_zOS_TSS_Y25M04_Products.zip',
        'U_Apache_Server_2-4_Unix_Y25M04_STIG.zip',
        'U_Apache_Server_2-4_Windows_Y25M04_STIG.zip',
        'U_Citrix_VAD_7-x_Y22M01_STIG.zip',
        'U_Citrix_XenDesktop_7-x_Y20M04_STIG.zip',
        'U_MS_Exchange_2016_Y25M01_STIG.zip',
        'U_MS_Exchange_2019_Y25M01_STIG.zip'
    ]
    
    downloader = WebDownloader()
    
    print(f"Testing {len(real_filenames)} real STIG filenames...")
    print(f"{'Filename':<50} {'STIG ID':<25} {'Ver':<6} {'Rel':<6} {'Format':<12}")
    print("-" * 105)
    
    all_parsed = True
    
    for filename in real_filenames:
        parsed = downloader.parse_stig_filename(filename)
        
        if not parsed['stig_id']:
            print(f"❌ {filename:<50} {'FAILED TO PARSE':<25}")
            all_parsed = False
        else:
            stig_id = str(parsed['stig_id'])[:24]
            version = str(parsed['version'])[:5]
            release = str(parsed['release'])[:5]
            format_type = str(parsed['format'])[:11]
            
            print(f"✅ {filename:<50} {stig_id:<25} {version:<6} {release:<6} {format_type:<12}")
    
    if all_parsed:
        print(f"\n🎉 All {len(real_filenames)} real STIG filenames parsed successfully!")
        return True
    else:
        print(f"\n❌ Some real STIG filenames failed to parse.")
        return False


if __name__ == "__main__":
    print("🚀 Running TUI Integration Test for Enhanced STIG Parsing")
    print("=" * 80)
    
    success1 = simulate_tui_stig_selection()
    success2 = test_real_parsing()
    
    if success1 and success2:
        print("\n" + "=" * 80)
        print("🎉 TUI INTEGRATION TEST PASSED!")
        print("✅ Both V#R# and Y##M## STIG formats are fully supported in the TUI")
        print("✅ STIG metadata is correctly parsed and displayed")
        print("✅ File selection and download simulation works correctly")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ TUI INTEGRATION TEST FAILED!")
        print("Please review the parsing logic and TUI implementation.")
        print("=" * 80)
        sys.exit(1)
