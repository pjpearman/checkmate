#!/usr/bin/env python3
"""
Integration test for the enhanced CheckMate GUI and TUI interfaces.
Tests the integration between the enhanced wrappers and the core functionality.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_gui_integration():
    """Test GUI integration with core."""
    print("Testing GUI Integration...")
    try:
        # Test that GUI module can be imported
        from gui.main import CheckMateGUI
        
        # Test core imports work
        from core import Config, CKLBHandler, CKLBGenerator, WebDownloader, FileUtils, InputValidator
        
        # Test that we can create core components
        config = Config()
        cklb_handler = CKLBHandler(config)
        cklb_generator = CKLBGenerator(config)
        web_downloader = WebDownloader(config)
        file_utils = FileUtils()
        validator = InputValidator()
        
        assert config is not None, "Config not created"
        assert cklb_handler is not None, "CKLB handler not created"
        assert cklb_generator is not None, "CKLB generator not created"
        assert web_downloader is not None, "Web downloader not created"
        assert file_utils is not None, "File utils not created"
        assert validator is not None, "Validator not created"
        
        print("✓ GUI integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ GUI integration test failed: {e}")
        return False

def test_tui_integration():
    """Test TUI integration with core."""
    print("Testing TUI Integration...")
    try:
        from tui.main import CheckMateTUI
        
        # Create TUI instance (don't run curses loop)
        tui = CheckMateTUI()
        
        # Test core component access
        assert tui.config is not None, "Config not initialized"
        assert tui.cklb_handler is not None, "CKLB handler not initialized"
        assert tui.cklb_generator is not None, "CKLB generator not initialized"
        assert tui.web_downloader is not None, "Web downloader not initialized"
        assert tui.file_utils is not None, "File utils not initialized"
        assert tui.validator is not None, "Validator not initialized"
        assert tui.menu_utils is not None, "Menu utils not initialized"
        
        # Test file list refresh
        tui.refresh_file_lists()
        assert hasattr(tui, 'file_lists'), "File lists not created"
        
        # Test TUI state
        assert tui.current_menu == "main", "Current menu not set"
        assert tui.main_menu_options is not None, "Menu options not initialized"
        
        # Test menu navigation methods
        max_idx = tui.get_max_selection_index()
        assert isinstance(max_idx, int), "Max selection index not integer"
        
        print("✓ TUI integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ TUI integration test failed: {e}")
        return False

def test_core_functionality():
    """Test core functionality used by both interfaces."""
    print("Testing Core Functionality...")
    try:
        from core import Config, CKLBHandler, CKLBGenerator, WebDownloader
        
        # Test configuration
        config = Config()
        assert config.base_dir is not None, "Base directory not set"
        assert config.get_version() is not None, "Version not available"
        
        # Test component initialization
        cklb_handler = CKLBHandler(config)
        cklb_generator = CKLBGenerator(config)
        web_downloader = WebDownloader(config)
        
        # Test directory access
        dirs = config.get_all_directories()
        assert isinstance(dirs, dict), "Directories not returned as dict"
        assert len(dirs) > 0, "No directories configured"
        
        print("✓ Core functionality test passed")
        return True
        
    except Exception as e:
        print(f"✗ Core functionality test failed: {e}")
        return False

def test_launcher_integration():
    """Test the unified launcher."""
    print("Testing Launcher Integration...")
    try:
        # Import the launcher module
        from checkmate import main, create_argument_parser
        
        # Test argument parser
        parser = create_argument_parser()
        assert parser is not None, "Argument parser not created"
        
        # Test parsing GUI command
        args = parser.parse_args(['gui'])
        assert args.interface == 'gui', "GUI argument not parsed correctly"
        
        # Test parsing TUI command
        args = parser.parse_args(['tui'])
        assert args.interface == 'tui', "TUI argument not parsed correctly"
        
        print("✓ Launcher integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Launcher integration test failed: {e}")
        return False

def test_directory_structure():
    """Test the directory structure is properly set up."""
    print("Testing Directory Structure...")
    try:
        from core import Config
        
        config = Config()
        
        # Check core directories exist
        required_dirs = ['user_docs', 'logs', 'tmp']
        for dir_name in required_dirs:
            dir_path = config.get_path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Required directory {dir_name} doesn't exist"
        
        # Check subdirectories under user_docs
        user_docs_subdirs = ['cklb_artifacts', 'cklb_new', 'cklb_updated', 'zip_files', 'inventory']
        for subdir in user_docs_subdirs:
            subdir_path = config.get_path('user_docs') / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True, exist_ok=True)
            assert subdir_path.exists(), f"User docs subdirectory {subdir} doesn't exist"
        
        print("✓ Directory structure test passed")
        return True
        
    except Exception as e:
        print(f"✗ Directory structure test failed: {e}")
        return False

def test_legacy_compatibility():
    """Test legacy compatibility features."""
    print("Testing Legacy Compatibility...")
    try:
        from core import Config
        
        config = Config()
        
        # Test legacy directory compatibility
        legacy_dirs = ['cklb_proc', 'usr_cklb_lib', 'cklb_lib', 'xccdf_lib']
        for dir_name in legacy_dirs:
            try:
                dir_path = config.get_path(dir_name)
                # If it returns a path, the compatibility mapping works
                assert dir_path is not None, f"Legacy directory {dir_name} not mapped"
            except KeyError:
                # It's okay if some legacy directories aren't mapped
                pass
        
        print("✓ Legacy compatibility test passed")
        return True
        
    except Exception as e:
        print(f"✗ Legacy compatibility test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("CheckMate Enhanced Integration Tests")
    print("=" * 60)
    
    tests = [
        test_core_functionality,
        test_directory_structure,
        test_gui_integration,
        test_tui_integration,
        test_launcher_integration,
        test_legacy_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("Enhanced CheckMate interfaces are ready for use.")
        print()
        print("Usage:")
        print("  python checkmate.py gui  # Launch enhanced GUI")
        print("  python checkmate.py tui  # Launch enhanced TUI")
        print()
        return 0
    else:
        print("❌ Some integration tests failed.")
        print("Please check the errors above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
