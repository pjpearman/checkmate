# Changelog

## [v2.0.2] - 2025-05-22
### Changed
- The baseline/file editor is now a general-purpose raw text editor. Users can open and edit any file type (YAML, XML, CKLB, etc.) from the GUI, not just YAML. All schema validation and YAML-specific logic have been removed for broader compatibility.
- Improved error handling and user feedback for launching the file editor from the GUI.

## [v2.0.1] - 2025-05-22
### Added
- Error handling for STIG ID mismatches during checklist upgrade: user is now warned if the old and new STIG IDs do not match, with a detailed message and the option to proceed or cancel.
- GUI now displays a confirmation dialog for STIG ID mismatches instead of freezing or failing silently.
- CLI supports a `--force` flag to override STIG ID mismatches without prompting.
- Prefix override in batch checklist upgrades now only renames checklists that are missing host_name data. All other checklists retain their original host_name as the prefix. This prevents unintended renaming of all files in a batch when only some lack host metadata.
- Baseline editor: Users can now open and edit the selected baseline YAML file directly from the GUI, with schema validation before saving. An "Edit Baseline" button is available in the main interface.

### Fixed
- Prevented GUI freeze when merging checklists with mismatched STIG IDs.
- Improved merge workflow to ensure checklists are created or updated only after user confirmation on mismatches.

### Changed
- Refactored merge logic to allow both CLI and GUI to handle user confirmation appropriately.

## [v2.0.0] - 2025-05-20
### Added
- Major GUI redesign: modern, aligned, and user-friendly layout for checklist merging and downloads
- "Download New CKLB" button and popup for exporting updated checklists
- Immediate log/status feedback in the GUI for all long-running jobs
- Multi-rule editing pop-up for new rules during checklist upgrades
- Improved batch checklist upgrade workflow
- Enhanced error/status reporting in the GUI
- More robust file selection and directory prompts
- Improved alignment and spacing for all controls in the merge area
- All buttons now match modern style and are consistently sized

### Improved
- UI layout and button styling for consistency and accessibility
- Table formatting for wrapped Rule Title and Comments
- Tooltips and layout refinements for modern UX
- Status and log pane feedback is now instant and accurate
- Merge and download actions are now more discoverable and user-friendly

### Fixed
- Button alignment and stacking issues in the merge area
- Spacing between panes and controls for a cleaner look
- All known issues from previous release candidates

### Notes
- This is a major release focused on usability, workflow, and visual polish for real-world checklist management.

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
