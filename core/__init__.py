"""
CheckMate Core Library
Shared functionality for both GUI and TUI interfaces.
"""

__version__ = "2.1.0"
__author__ = "ppear"

# Core exports
from .config import Config, default_config
from .cklb_handler import CKLBHandler, load_cklb, save_cklb, check_stig_id_match
from .create_cklb import CKLBGenerator, generate_cklb_json, convert_xccdf_zip_to_cklb
from .web import WebDownloader, fetch_page, parse_table_for_links, download_file
from .file_utils import FileUtils, ensure_dir, validate_file_ext, safe_json_load, safe_file_move, list_files_with_ext
from .input_validation import InputValidator, validate_filename, validate_stig_id, validate_version_release, validate_cklb_basic, get_safe_path
from .log_config import LogConfig, default_log_config, setup_logging, get_operation_logger
from .menu_utils import MenuUtils, render_menu, handle_menu_input

__all__ = [
    # Main classes
    'Config', 'default_config',
    'CKLBHandler', 'CKLBGenerator', 'WebDownloader', 'FileUtils', 
    'InputValidator', 'LogConfig', 'MenuUtils',
    
    # CKLB functions
    'load_cklb', 'save_cklb', 'check_stig_id_match',
    'generate_cklb_json', 'convert_xccdf_zip_to_cklb',
    
    # Web functions
    'fetch_page', 'parse_table_for_links', 'download_file',
    
    # File functions
    'ensure_dir', 'validate_file_ext', 'safe_json_load', 'safe_file_move', 'list_files_with_ext',
    
    # Validation functions
    'validate_filename', 'validate_stig_id', 'validate_version_release', 'validate_cklb_basic', 'get_safe_path',
    
    # Logging functions
    'default_log_config', 'setup_logging', 'get_operation_logger',
    
    # Menu functions
    'render_menu', 'handle_menu_input'
]
