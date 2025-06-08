# CheckMate-Lite

CheckMate-Lite is a lightweight toolkit for working with Security Technical Implementation Guide (STIG) content, focusing on the creation, management, and review of checklist bundles (CKLB files). It provides a simple menu driven terminal user interface for interacting with STIG checklists.

## Features

- **Convert STIG XCCDF XML to CKLB**: Easily generate `.cklb` files from official DISA STIG XMLs using `create_cklb.py`.
- **Inventory Management**: Create and manage inventories of available checklists with `create_inventory.py`.
- **Terminal User Interface (TUI)**: Review and update checklists in a terminal environment via `tui.py`.

## Directory Structure

```
create_cklb.py         # Convert XCCDF XML to .cklb JSON
create_inventory.py    # Create/manage inventory of checklists
tui.py                 # Terminal user interface for checklist interaction
user_docs/
  cklb_new/            # Generated .cklb files
  zip_files/           # (Optional) Zipped checklist bundles
```

## Terminal Menu Structure
```
Create Inventory File                 # Generate a list of technologies.
  | 
Download Options                      # Top-level menu item
  |- Download All FIles               # Download All .zips available.
  |- Download Using Inventory File    # Download .zips listed in inv file.
    |- Create CKLB                    # Creates CKLB. Discards .zip
    |- Download Zip Only              # Downloads zip to user_docs/zip_files
Manage Checklists                     # Top-level menu item
  |- Import CKLB(s)                   # Import user's completed cklbs
  |- Compare CKLB Versions            # Compares diff between version A & B
  |- Upgrade CKLB(s)                  # Select cklb(s) for version upgrade
```
## Usage

### 1. Generate a CKLB File

Convert a STIG XCCDF XML file to a `.cklb` file:

```bash
python create_cklb.py /path/to/STIG-xccdf.xml
```

The output `.cklb` file will be placed in `user_docs/cklb_new/`.

### 2. Create an Inventory

Generate an inventory of available checklists:

```bash
python create_inventory.py
```

### 3. Terminal User Interface

Launch the TUI to interact with checklists:

```bash
python tui.py
```

### 4. Web Interface

Start the web server to browse checklists:

```bash
python web.py
```

Then open your browser to the provided URL (typically `http://localhost:5000`).

## File Formats

- **CKLB (.cklb)**: JSON-based format containing parsed STIG rules, metadata, and evaluation status.
- **XCCDF XML**: Official DISA STIG XML input files.

## Example

A generated `.cklb` file contains all rules, metadata, and evaluation status for a given STIG, making it easier to track compliance and findings.

## Requirements

- Python 3.7+
- Standard Python libraries (no external dependencies required for core scripts)

## License

This project is released under the MIT License.

---

For more information, see the user documentation in `user_docs/`.
