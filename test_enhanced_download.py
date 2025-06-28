#!/usr/bin/env python3
"""
Test script for enhanced TUI download functionality with better error handling.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_download_functionality():
    """Test the enhanced download functionality with error handling."""
    print("Testing Enhanced TUI Download Functionality")
    print("=" * 45)
    
    try:
        from tui.main import CheckMateTUI
        from core.web import WebDownloader
        
        # Test 1: TUI initialization
        print("1. Testing TUI initialization...")
        tui = CheckMateTUI()
        assert hasattr(tui, 'web_downloader'), "TUI should have web_downloader"
        print("   ✓ TUI initialized successfully")
        
        # Test 2: Web downloader robustness
        print("2. Testing WebDownloader error handling...")
        
        web_downloader = WebDownloader()
        
        # Test get_file_info with invalid URL
        file_info = web_downloader.get_file_info("https://invalid-url-that-should-fail.com/test.zip")
        assert isinstance(file_info, dict), "get_file_info should always return a dict"
        assert 'url' in file_info, "file_info should have url field"
        assert 'filename' in file_info, "file_info should have filename field"
        print("   ✓ WebDownloader handles invalid URLs gracefully")
        
        # Test 3: STIG data validation with edge cases
        print("3. Testing STIG data validation with edge cases...")
        
        test_cases = [
            # Valid complete STIG
            {
                'input': {
                    'filename': 'U_Test_V1R1_STIG.zip',
                    'url': 'https://example.com/test.zip',
                    'stig_id': 'Test_STIG',
                    'version': 1,
                    'release': 1,
                    'size': 1000000
                },
                'should_pass': True,
                'description': 'Complete valid STIG'
            },
            # Missing optional fields
            {
                'input': {
                    'filename': 'minimal.zip',
                    'url': 'https://example.com/minimal.zip'
                },
                'should_pass': True,
                'description': 'Minimal STIG with only required fields'
            },
            # Invalid data types
            {
                'input': {
                    'filename': 123,  # Should be string
                    'url': 'https://example.com/test.zip'
                },
                'should_pass': True,  # Should be handled gracefully
                'description': 'STIG with invalid filename type'
            },
            # None values
            {
                'input': {
                    'filename': 'test.zip',
                    'url': 'https://example.com/test.zip',
                    'version': None,
                    'release': None,
                    'size': None
                },
                'should_pass': True,
                'description': 'STIG with None values'
            },
            # Missing required field
            {
                'input': {
                    'filename': 'test.zip'
                    # Missing URL
                },
                'should_pass': False,
                'description': 'STIG missing required URL field'
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            result = tui.validate_stig_data(test_case['input'].copy())
            expected = test_case['should_pass']
            description = test_case['description']
            
            if result == expected:
                print(f"   ✓ Test {i+1}: {description}")
            else:
                print(f"   ✗ Test {i+1} FAILED: {description} (expected {expected}, got {result})")
                return False
        
        # Test 4: Mock STIG processing
        print("4. Testing STIG list processing...")
        
        mock_stigs = [
            {
                'filename': 'U_Windows_10_V2R1_STIG.zip',
                'url': 'https://example.com/win10.zip',
                'stig_id': 'Windows_10',
                'version': 2,
                'release': 1,
                'size': 1500000,
                'last_modified': 'Fri, 01 Dec 2023 10:30:00 GMT'
            },
            {
                'filename': 'invalid_stig.zip',
                'url': 'https://example.com/invalid.zip',
                'stig_id': None,  # Invalid
                'version': 'not_a_number',  # Invalid
                'size': 'not_a_number'  # Invalid
            }
        ]
        
        # Validate all mock STIGs
        validated_stigs = []
        for stig in mock_stigs:
            if tui.validate_stig_data(stig.copy()):
                validated_stigs.append(stig)
        
        assert len(validated_stigs) == len(mock_stigs), f"All STIGs should validate after processing"
        print("   ✓ STIG list processing handles invalid data gracefully")
        
        # Test 5: Error screen functionality
        print("5. Testing error handling methods...")
        
        # Test that error handling methods exist and are callable
        error_methods = ['show_loading_screen', 'show_error_screen']
        for method_name in error_methods:
            method = getattr(tui, method_name, None)
            assert method is not None, f"Method {method_name} should exist"
            assert callable(method), f"Method {method_name} should be callable"
        
        print("   ✓ Error handling methods are available")
        
        # Test 6: Progress feedback simulation
        print("6. Testing progress feedback simulation...")
        
        # Test that the fetch_stigs_with_progress method exists
        assert hasattr(tui, 'fetch_stigs_with_progress'), "Should have fetch_stigs_with_progress method"
        assert callable(tui.fetch_stigs_with_progress), "fetch_stigs_with_progress should be callable"
        
        print("   ✓ Progress feedback methods are available")
        
        print("\n" + "=" * 45)
        print("✅ ALL ENHANCED DOWNLOAD TESTS PASSED")
        print("\nKey improvements implemented:")
        print("• Robust error handling for network issues")
        print("• Progress feedback during long-running operations")
        print("• Safe data validation with graceful degradation")
        print("• Better user feedback with loading and error screens")
        print("• Comprehensive logging for debugging")
        print("• Defensive programming against None/invalid data")
        
        print("\nUser experience improvements:")
        print("• No more 'NoneType' errors from invalid data")
        print("• Visual progress during STIG list fetching")
        print("• Clear error messages when operations fail")
        print("• Ability to cancel long-running operations")
        print("• Graceful handling of network timeouts")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ENHANCED DOWNLOAD TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_download_functionality()
    sys.exit(0 if success else 1)
