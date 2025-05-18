# Changelog

## [v1.0.0] - 2025-05-13
### Added
- CLI for converting XCCDF to CKLB format
- GUI for batch checklist upgrades
- JSON schema validation for .cklb generation
- Support for extracting host metadata
- Patch to preserve classification and version

### Fixed
- Bug in selected_merger.py not reading old hostname
- Validation errors in CKLB output

### Notes
- This is the first stable release

## [v1.0.1] - 2025-05-14
### Added

### Fixed 
- Refresh pane after ckl imported added to gui.py and importer.py

## [v1.1.1] - 2025-05-14
### Added 
- Added Support for "Application" STIG Mode
- Included baseline output as baseline_applications.yaml
- Supports download, XCCDF extraction, and .cklb generation workflows

## [v1.2.1] - 2025-05-14
### Added 
- Added Support for "Network-Perimeter" STIG Mode
- Included baseline output as baseline_applications.yaml

## CheckMate v2.0.0-rc1
- Added: Multi-rule editing pop-up with new rule handling logic
- Improved: UI layout and button styling for consistency
- Adjusted: Table formatting for wrapped Rule Title and Comments
- Added: Tooltips and layout refinements for modern UX
- Ready for early adopter feedback and real-world checklist testing

- Supports download, XCCDF extraction, and .cklb generation workflows
