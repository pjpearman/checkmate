#!/usr/bin/env python3
"""
Test script to verify STIG filename parsing with both V#R# and Y##M## patterns.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.web import WebDownloader


def test_filename_parsing():
    """Test STIG filename parsing for both V#R# and Y##M## patterns."""
    downloader = WebDownloader()
    
    # Test cases with expected results
    test_cases = [
        # V#R# patterns (version/release)
        {
            'filename': 'U_Windows_10_V2R3_STIG.zip',
            'expected': {
                'stig_id': 'Windows_10',
                'version': 2,
                'release': 3,
                'format': 'version_release',
                'type': 'stig'
            }
        },
        {
            'filename': 'U_Microsoft_SQL_Server_2016_Instance_V2R8_20231201_STIG.zip',
            'expected': {
                'stig_id': 'Microsoft_SQL_Server_2016_Instance',
                'version': 2,
                'release': 8,
                'format': 'version_release',
                'type': 'stig',
                'date': '20231201'
            }
        },
        # Y##M## patterns (year/month)
        {
            'filename': 'U_IBM_zOS_Y25M04_STIG.zip',
            'expected': {
                'stig_id': 'IBM_zOS',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'stig'
            }
        },
        {
            'filename': 'U_VMW_vSphere_7-0_Y25M04_STIG.zip',
            'expected': {
                'stig_id': 'VMW_vSphere_7-0',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'stig'
            }
        },
        {
            'filename': 'U_zOS_ACF2_Y25M04_Products.zip',
            'expected': {
                'stig_id': 'zOS_ACF2',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'products'
            }
        },
        {
            'filename': 'U_Citrix_VAD_7-x_Y22M01_STIG.zip',
            'expected': {
                'stig_id': 'Citrix_VAD_7-x',
                'version': 'Y22',
                'release': 'M01',
                'format': 'year_month',
                'type': 'stig'
            }
        },
        {
            'filename': 'U_Apache_Server_2-4_Unix_Y25M04_STIG.zip',
            'expected': {
                'stig_id': 'Apache_Server_2-4_Unix',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'stig'
            }
        },
        {
            'filename': 'U_MS_Exchange_2019_Y25M01_STIG.zip',
            'expected': {
                'stig_id': 'MS_Exchange_2019',
                'version': 'Y25',
                'release': 'M01',
                'format': 'year_month',
                'type': 'stig'
            }
        },
        # Edge cases
        {
            'filename': 'U_zOS_Y25M04_SRR.zip',
            'expected': {
                'stig_id': 'zOS',
                'version': 'Y25',
                'release': 'M04',
                'format': 'year_month',
                'type': 'srr'
            }
        }
    ]
    
    print("Testing STIG filename parsing...")
    print("=" * 80)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        filename = test_case['filename']
        expected = test_case['expected']
        
        print(f"\nTest {i}: {filename}")
        
        # Parse the filename
        result = downloader.parse_stig_filename(filename)
        
        # Check each expected field
        test_passed = True
        for key, expected_value in expected.items():
            actual_value = result.get(key)
            if actual_value != expected_value:
                print(f"  ❌ {key}: expected '{expected_value}', got '{actual_value}'")
                test_passed = False
                all_passed = False
            else:
                print(f"  ✅ {key}: '{actual_value}'")
        
        if test_passed:
            print(f"  🎉 Test {i} PASSED")
        else:
            print(f"  💥 Test {i} FAILED")
            
        # Show full parsed result for debugging
        print(f"  Full result: {result}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 All tests PASSED! Both V#R# and Y##M## patterns are supported.")
        return True
    else:
        print("💥 Some tests FAILED. Please review the parsing logic.")
        return False


def test_display_formatting():
    """Test how the parsed data would be displayed in the TUI."""
    downloader = WebDownloader()
    
    filenames = [
        'U_Windows_10_V2R3_STIG.zip',
        'U_IBM_zOS_Y25M04_STIG.zip',
        'U_VMW_vSphere_7-0_Y25M04_STIG.zip',
        'U_MS_Exchange_2019_Y25M01_STIG.zip'
    ]
    
    print("\nTUI Display Format Test:")
    print("=" * 80)
    print(f"{'STIG ID':<30} {'Version':<10} {'Release':<10} {'Format':<15} {'Type':<10}")
    print("-" * 80)
    
    for filename in filenames:
        result = downloader.parse_stig_filename(filename)
        stig_id = result.get('stig_id', 'Unknown')[:29]  # Truncate for display
        version = str(result.get('version', 'N/A'))
        release = str(result.get('release', 'N/A'))
        format_type = result.get('format', 'unknown')
        file_type = result.get('type', 'unknown')
        
        print(f"{stig_id:<30} {version:<10} {release:<10} {format_type:<15} {file_type:<10}")


if __name__ == "__main__":
    success = test_filename_parsing()
    test_display_formatting()
    
    if success:
        print("\n✅ STIG filename parsing enhancement is working correctly!")
        print("Both V#R# (version/release) and Y##M## (year/month) patterns are now supported.")
    else:
        print("\n❌ There are issues with the STIG filename parsing logic.")
        sys.exit(1)
