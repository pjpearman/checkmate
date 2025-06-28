# Enhanced TUI Download Workflow Implementation

## Overview

This document describes the implementation of enhanced TUI download workflow features for CheckMate, including the addition of a "Type" column, download mode selection, CKLB creation functionality, and removal of the "Download all file types" option.

## Changes Implemented

### 1. Enhanced STIG Type Detection

**File:** `core/web.py`

Enhanced the `parse_stig_filename()` method to better detect file types:

- **stig**: Files containing "stig" in the name
- **benchmark**: Files containing "benchmark" in the name  
- **checklist**: Files containing "checklist" or "cklb" in the name
- **products**: Files containing "products" or "library" in the name
- **scap**: Files containing "scap" or "oval" in the name
- **srr**: Files containing "srr" or "readiness" in the name
- **other**: All other files

### 2. Enhanced Version Format Support

**File:** `core/web.py`

Added support for both versioning formats:

- **V#R# format**: Traditional version/release format (e.g., V2R1)
- **Y##M## format**: Year/month format (e.g., V25M04 for 2025, Month 04)

Updated pattern matching to handle:
- `U_STIGNAME_V25M04_20250401.zip`
- `STIGNAME_25M04.zip`
- Standard V#R# patterns

### 3. TUI Download Menu Updates

**File:** `tui/main.py`

#### Removed Options:
- **"Download all available files"** - This option has been completely removed from the download menu

#### Updated Download Menu Options:
```python
options = [
    "Fetch file list from URL",
    "Download specific file types", 
    "View downloaded files"
]
```

### 4. Enhanced STIG Selection Interface

**File:** `tui/main.py`

#### Added Type Column:
Updated the column headers to include a "Type" column:

```
Status | STIG ID              | Ver  | Rel  | Type      | Size     | Updated
```

#### Updated Display Logic:
- **STIG ID**: Reduced width to accommodate Type column (30 → 25 characters)
- **Type**: New column showing file type (10 characters)
- **Version/Release**: Enhanced to show both V#R# and Y##M## formats properly

#### Updated Instructions:
- Changed "ENTER=download selected" to "ENTER=choose download mode"
- Changed "D=download all" to "D=choose download mode for all"

### 5. Download Mode Selection

**File:** `tui/main.py`

#### New Method: `choose_download_mode()`

Provides three download options:
1. **"Download ZIP files only"** - Downloads files to zip_files directory
2. **"Create CKLB files only"** - Downloads temporarily and creates CKLB files
3. **"Download ZIP and create CKLB"** - Downloads files and creates CKLB files

#### Features:
- Scrollable selection interface with arrow key navigation
- File type summary display (e.g., "3 stig, 1 benchmark")
- ESC to cancel, ENTER to confirm selection
- Progress feedback during operations

### 6. CKLB Creation Integration

**File:** `tui/main.py`

#### New Method: `create_cklb_from_selected()`

Creates CKLB files from selected STIG ZIP files:
- Downloads ZIP files to temporary directory
- Extracts XCCDF content using `CKLBGenerator.convert_zip_to_cklb()`
- Saves CKLB files to user CKLB directory
- Shows progress and results summary

#### New Method: `download_and_create_cklb()`

Combined download and CKLB creation workflow:
- Downloads ZIP files to permanent zip_files directory
- Creates CKLB files in user CKLB directory
- Provides comprehensive results summary with counts for both operations

### 7. Enhanced User Experience

#### Progress Feedback:
- Step-by-step progress indication (e.g., "Step 1/2: Downloading ZIP files...")
- Real-time status updates during long operations
- Comprehensive results screens with success/failure counts

#### Error Handling:
- Graceful handling of download failures
- Individual file error reporting
- Continued processing when some files fail

#### File Management:
- Automatic directory creation
- Temporary file cleanup for CKLB-only operations
- File lists refresh after operations

## Usage Instructions

### 1. Accessing Enhanced Download Features

1. Start CheckMate TUI: `python checkmate.py tui`
2. Select "Download STIGs"
3. Choose "Fetch file list from URL"

### 2. Using the Enhanced Selection Interface

- **Navigation**: Use ↑/↓ arrow keys, PgUp/PgDn for page navigation
- **Selection**: Press SPACE to toggle individual files, A to select all, N to clear selection
- **Type Column**: View file types (stig, benchmark, other, etc.) in the Type column
- **Version Formats**: Both V#R# and Y##M## formats are supported and displayed properly

### 3. Download Mode Selection

After selecting files and pressing ENTER:

1. **Download ZIP files only**: 
   - Files are downloaded to the zip_files directory
   - No CKLB creation
   - Fastest option for archiving

2. **Create CKLB files only**:
   - ZIP files downloaded temporarily
   - XCCDF extracted and converted to CKLB
   - CKLB files saved to user CKLB directory
   - Temporary ZIP files cleaned up

3. **Download ZIP and create CKLB**:
   - ZIP files downloaded to permanent zip_files directory
   - CKLB files created from downloaded ZIPs
   - Both ZIP and CKLB files retained

## Technical Details

### Dependencies

The enhanced functionality relies on:
- `core.CKLBGenerator` for CKLB creation
- `core.WebDownloader` for file downloads and metadata parsing
- `core.Config` for directory management
- Standard Python libraries: `curses`, `pathlib`, `threading`

### File Structure

```
/workspaces/checkmate/
├── core/
│   ├── web.py              # Enhanced STIG type detection
│   ├── create_cklb.py      # CKLB generation functionality
│   └── cklb_handler.py     # CKLB file management
├── tui/
│   └── main.py             # Enhanced TUI with download modes
└── test_enhanced_tui_download.py  # Test script
```

### Configuration

The enhanced features use the following directories:
- **ZIP files**: `config.get_path('zip_files')` 
- **CKLB files**: `config.get_user_cklb_dir()`
- **Temporary files**: `config.get_path('tmp')`

## Testing

Run the test script to verify functionality:

```bash
cd /workspaces/checkmate
python test_enhanced_tui_download.py
```

The test verifies:
- STIG type detection with various filename patterns
- CKLB generation method availability
- TUI method integration
- Removal of deprecated functionality

## Migration Notes

### Removed Functionality
- **"Download all file types"** option has been completely removed
- **`download_all_files()`** method has been removed from TUI

### Enhanced Functionality
- All download operations now go through the download mode selection interface
- CKLB creation is now available as a primary workflow option
- File type information is prominently displayed in the selection interface

## Future Enhancements

Potential areas for future improvement:
1. **Filter by Type**: Add ability to filter files by type in the selection interface
2. **Bulk Operations**: Add options for bulk type-specific operations
3. **Download Resume**: Add support for resuming interrupted downloads
4. **Custom CKLB Settings**: Allow customization of CKLB generation parameters
