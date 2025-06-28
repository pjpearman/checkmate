# Enhanced CKLB Import Guide

## Overview

The CheckMate application now features enhanced CKLB import functionality for both GUI and TUI interfaces, providing users with intuitive file selection and import capabilities.

## TUI File Browser

When you select "Import CKLB Files" in the TUI:

### Navigation
- **↑/↓ Arrow Keys**: Navigate through directories and files
- **Enter**: Open directories or toggle file selection
- **Space**: Toggle individual file selection
- **A**: Select all CKLB files in current directory

### Visual Indicators
- **📁**: Directory
- **⬆**: Parent directory (..)
- **📄**: CKLB file
- **✓**: Selected file
- **►**: Currently highlighted item

### Actions
- **I**: Import all selected files
- **ESC**: Cancel and return to main menu
- **Q**: Quit file browser

### Features
- Real-time selection count display
- File type filtering (only CKLB files can be selected)
- Directory navigation starting from home directory
- Permission error handling

## GUI Enhanced Import

When you select "Import CKLB Files" in the GUI:

### File Selection Dialog
- Multiple file selection support
- File type filtering (CKLB, JSON, All files)
- Starts in user's home directory
- Preview of selected files

### Confirmation and Progress
- Confirmation dialog showing selected files
- Progress tracking during import
- Real-time status updates
- Error handling and reporting

### Duplicate File Handling
- Automatic detection of existing files
- User choice: Replace, Skip, or Cancel
- Preserves original files during import

### Features
- Background processing (non-blocking UI)
- Comprehensive error logging
- Success/failure notifications
- Automatic file list refresh after import

## Usage Examples

### TUI Usage
```bash
python checkmate.py tui
# Select "Import CKLB Files" from main menu
# Navigate to directory with CKLB files
# Use Space to select individual files or A to select all
# Press I to import selected files
```

### GUI Usage
```bash
python checkmate.py gui
# Go to "Manage" tab
# Click "Import CKLB Files" button
# Select files in the dialog
# Confirm import in the dialog
# Monitor progress in the status bar
```

## File Requirements

### Supported Formats
- `.cklb` files (primary format)
- `.json` files (if they contain CKLB data)

### File Validation
- Automatic file type checking
- Invalid files are skipped with warnings
- Import statistics show success/skip/error counts

## Import Destinations

Files are imported to the user CKLB directory:
- **New structure**: `user_docs/cklb_artifacts/`
- **Legacy structure**: `cklb_proc/usr_cklb_lib/` (for backward compatibility)

The system automatically uses the appropriate directory based on your installation.

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure you have read access to source files and write access to destination
2. **File Already Exists**: Choose Replace, Skip, or Cancel when prompted
3. **Invalid File Type**: Only CKLB and JSON files are accepted
4. **Empty Selection**: Make sure to select files before attempting import

### Error Messages
- Import errors are logged to the application log
- GUI shows error dialogs with specific error information
- TUI displays error messages in the status line

### Getting Help
- Check the application logs for detailed error information
- Use the test import functionality to verify setup:
  ```bash
  python test_import.py
  ```

## Advanced Features

### Batch Import
- Select multiple files at once
- Progress tracking for large imports
- Individual file error handling (continues on errors)

### Integration
- Imported files are automatically available in comparison and merge operations
- File lists are refreshed after successful import
- Preserves file metadata (timestamps, etc.)

This enhanced import functionality makes it easy to bring existing CKLB files into CheckMate for version tracking, comparison, and merging operations.
