# CheckMate Refactoring Plan

## Objective
Refactor the CheckMate application to leverage the modular functions from the ckl-lite directory, creating a shared core library that can be used by both:
1. GUI application (tkinter-based)
2. Terminal User Interface (TUI-based)

## Current Structure Analysis

### Main CheckMate Application
- `gui.py` - Tkinter GUI interface
- `handlers.py` - GUI task logic
- `cklb_generator.py` - XCCDF to CKLB conversion
- `selected_merger.py` - Checklist merging
- `cklb_importer.py` - CKLB file import
- Various utility modules

### CheckMate-Lite (docs/ckl-lite)
- `tui.py` - Terminal user interface
- `cklb_handler.py` - Core CKLB operations
- `create_cklb.py` - XCCDF to CKLB conversion
- `web.py` - Download functionality
- `config.py` - Configuration management
- `file_utils.py` - File operations
- Modular utilities

## Refactoring Strategy

### Phase 1: Create Shared Core Library
1. Move ckl-lite modules to a shared `core/` directory
2. Create abstracted interfaces for common operations
3. Standardize configuration and logging

### Phase 2: Refactor Main Application
1. Update GUI to use shared core functions
2. Remove duplicate functionality
3. Maintain GUI-specific presentation logic

### Phase 3: Create Unified Interface
1. Both GUI and TUI use same core functions
2. Shared configuration and data directories
3. Consistent behavior across interfaces

## Directory Structure (Target)

```
checkmate/
├── core/                    # Shared library (from ckl-lite)
│   ├── __init__.py
│   ├── cklb_handler.py      # Core CKLB operations
│   ├── create_cklb.py       # XCCDF to CKLB conversion
│   ├── web.py               # Download functionality
│   ├── config.py            # Shared configuration
│   ├── file_utils.py        # File operations
│   ├── input_validation.py  # Input validation
│   ├── log_config.py        # Logging configuration
│   └── menu_utils.py        # Menu utilities
├── gui/                     # GUI-specific code
│   ├── __init__.py
│   ├── main.py              # Main GUI application
│   ├── widgets.py           # GUI widgets and components
│   └── handlers.py          # GUI event handlers
├── tui/                     # TUI-specific code
│   ├── __init__.py
│   ├── main.py              # Main TUI application
│   └── menus.py             # TUI menu handlers
├── legacy/                  # Original files (for reference)
└── user_docs/               # Shared data directory
    ├── cklb_artifacts/      # User CKLB files
    ├── cklb_new/            # Generated CKLB files
    ├── cklb_updated/        # Updated CKLB files
    ├── zip_files/           # Downloaded ZIP files
    └── inventory/           # Inventory files
```

## Implementation Steps

1. **Create core module structure**
2. **Move and adapt ckl-lite functions to core/**
3. **Update main GUI to use core functions**
4. **Create unified configuration**
5. **Test both interfaces work with shared core**
6. **Clean up duplicate code**

## Benefits

- **Code Reuse**: Core functionality shared between GUI and TUI
- **Consistency**: Same behavior across interfaces
- **Maintainability**: Single source of truth for core operations
- **Flexibility**: Easy to add new interfaces (web, API, etc.)
- **Testing**: Core functions can be tested independently
