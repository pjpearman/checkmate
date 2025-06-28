#!/usr/bin/env python3
"""
CheckMate Refactoring Demonstration
Shows how the shared core library works with both GUI and TUI interfaces.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_core_functionality():
    """Demonstrate core functionality."""
    print("=" * 60)
    print("CheckMate Refactoring Demonstration")
    print("=" * 60)
    
    # Import core modules
    try:
        from core import (
            Config, CKLBHandler, CKLBGenerator, WebDownloader,
            FileUtils, InputValidator, LogConfig
        )
        print("✓ Successfully imported all core modules")
    except ImportError as e:
        print(f"✗ Error importing core modules: {e}")
        return False
    
    print()
    
    # 1. Configuration Demo
    print("1. Configuration Management")
    print("-" * 30)
    config = Config()
    print(f"✓ Created configuration instance")
    print(f"  Base directory: {config.base_dir}")
    print(f"  User docs dir: {config.user_docs_dir}")
    print(f"  Version: {config.VERSION}")
    print(f"  Total directories managed: {len(config.directories)}")
    print()
    
    # 2. Logging Demo
    print("2. Logging Setup")
    print("-" * 30)
    log_config = LogConfig(config)
    logger = log_config.setup_logging("demo", enable_console=True)
    logger.info("✓ Logging system initialized")
    print()
    
    # 3. File Utils Demo
    print("3. File Utilities")
    print("-" * 30)
    file_utils = FileUtils()
    
    # Check if any CKLB files exist
    cklb_files = file_utils.find_cklb_files(config.user_docs_dir)
    logger.info(f"Found {len(cklb_files)} CKLB files in user directory")
    
    if cklb_files:
        for cklb_file in cklb_files[:3]:  # Show first 3
            info = file_utils.get_file_info(cklb_file)
            logger.info(f"  - {info['name']}: {info['size']} bytes")
    print()
    
    # 4. CKLB Handler Demo
    print("4. CKLB Handler")
    print("-" * 30)
    cklb_handler = CKLBHandler(config)
    logger.info("✓ CKLB handler initialized")
    
    if cklb_files:
        try:
            # Try to load a CKLB file
            sample_cklb = cklb_handler.load_cklb(cklb_files[0])
            stig_info = cklb_handler.get_stig_info(sample_cklb)
            logger.info(f"  Sample CKLB - STIG ID: {stig_info.get('stig_id', 'Unknown')}")
            logger.info(f"  Version: {stig_info.get('version', 'Unknown')}")
            
            rules = cklb_handler.get_rules(sample_cklb)
            logger.info(f"  Rules count: {len(rules)}")
        except Exception as e:
            logger.warning(f"  Could not load sample CKLB: {e}")
    print()
    
    # 5. Input Validation Demo
    print("5. Input Validation")
    print("-" * 30)
    validator = InputValidator()
    
    test_cases = [
        ("valid_filename.cklb", "filename"),
        ("RHEL_8_STIG", "stig_id"),
        ("invalid<>filename.cklb", "filename"),
        ("", "filename")
    ]
    
    for test_value, test_type in test_cases:
        if test_type == "filename":
            result = validator.validate_filename(test_value)
        elif test_type == "stig_id":
            result = validator.validate_stig_id(test_value)
        
        status = "✓" if result else "✗"
        logger.info(f"  {status} {test_type} validation: '{test_value}' -> {result}")
    print()
    
    # 6. Web Downloader Demo (without actually downloading)
    print("6. Web Downloader")
    print("-" * 30)
    web_downloader = WebDownloader(config)
    logger.info("✓ Web downloader initialized")
    logger.info(f"  Default URL: {web_downloader.DEFAULT_URL}")
    logger.info("  (Demo mode - not actually fetching)")
    print()
    
    # 7. CKLB Generator Demo
    print("7. CKLB Generator")
    print("-" * 30)
    cklb_generator = CKLBGenerator(config)
    logger.info("✓ CKLB generator initialized")
    logger.info("  Ready to convert XCCDF files to CKLB format")
    print()
    
    return True

def demo_interface_compatibility():
    """Demonstrate interface compatibility."""
    print("8. Interface Compatibility")
    print("-" * 30)
    
    # Check GUI compatibility
    try:
        from gui import CheckMateGUI
        print("✓ GUI interface available")
    except ImportError as e:
        print(f"✗ GUI interface not available: {e}")
    
    # Check TUI compatibility
    try:
        from tui import CheckMateTUI
        print("✓ TUI interface available")
    except ImportError as e:
        print(f"✗ TUI interface not available: {e}")
    
    print()

def show_directory_structure():
    """Show the new directory structure."""
    print("9. Directory Structure")
    print("-" * 30)
    
    from core import Config
    config = Config()
    
    print("Managed directories:")
    for name, path in config.directories.items():
        exists = "✓" if path.exists() else "✗"
        try:
            file_count = len(list(path.iterdir())) if path.exists() else 0
            print(f"  {exists} {name}: {path} ({file_count} items)")
        except PermissionError:
            print(f"  {exists} {name}: {path} (permission denied)")
    
    print()

def show_migration_info():
    """Show legacy migration information."""
    print("10. Legacy Migration")
    print("-" * 30)
    
    from core import Config
    config = Config()
    
    legacy_paths = [
        config.directories["usr_cklb_lib"],
        config.directories["cklb_lib"]
    ]
    
    has_legacy_data = False
    for path in legacy_paths:
        if path.exists() and any(path.iterdir()):
            has_legacy_data = True
            print(f"  ⚠ Legacy data found in: {path}")
    
    if has_legacy_data:
        print("  💡 Run config.migrate_legacy_data() to migrate to new structure")
    else:
        print("  ✓ No legacy data found - using new structure")
    
    print()

def main():
    """Main demonstration function."""
    print("CheckMate Core Functionality Demonstration")
    print("This shows how the refactored core library works.")
    print()
    
    # Run demonstrations
    if not demo_core_functionality():
        print("❌ Core functionality demo failed")
        return 1
    
    demo_interface_compatibility()
    show_directory_structure()
    show_migration_info()
    
    print("=" * 60)
    print("Refactoring Summary:")
    print("✓ Shared core library created")
    print("✓ Both GUI and TUI can use same functions") 
    print("✓ Configuration unified")
    print("✓ Logging centralized")
    print("✓ File operations standardized")
    print("✓ Legacy compatibility maintained")
    print()
    print("Next steps:")
    print("- Run 'python checkmate.py gui' for GUI interface")
    print("- Run 'python checkmate.py tui' for TUI interface")
    print("- Both use the same core functionality!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
