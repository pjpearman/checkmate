# CheckMate: DISA STIG Collection Manager

## Overview

**CheckMate** automates version tracking, checklist generation, and upgrade merging for DISA STIGs.

Runs on Windows or Linux!

Can be used in air-gapped environments (without downloading features)

## What's New in v2.0.0

- 🚀 **Major GUI Redesign:** Modern, aligned, and user-friendly layout for checklist merging and downloads.
- 📥 **Download New CKLB:** Export updated checklists with a dedicated button and popup.
- ⚡ **Instant Feedback:** Immediate log/status feedback in the GUI for all long-running jobs.
- 📝 **Multi-rule Editing:** Pop-up for new rules during checklist upgrades, with batch-edit support.
- 🛠️ **Improved Batch Upgrade:** Enhanced workflow for merging and upgrading checklists.
- 🧰 **Better Error/Status Reporting:** More robust file selection, directory prompts, and error handling.
- 🎨 **Consistent Modern Styling:** All controls and buttons now match a modern style and are consistently sized.

---

### Core Features:

- ✅ **Comparison Mode:** Compares downloaded STIG metadata to a YAML baseline.
- ✅ **Baseline Generation:** Creates new baseline files for future comparisons.
- ✅ **ZIP Downloading:** Fetches updated STIG ZIP files when changes are detected.
- ✅ **Checklist Generator:** Extracts `-xccdf.xml` files and creates `.cklb` checklist files.
- ✅ **Merge & Upgrade:** Merges older `.cklb` checklists with newer versions, preserving history and handling new rules.
- ✅ **GUI Support:** Tkinter-based interface with instant status feedback, logging, and export/download features.

> ⚠️ This is not an assessment tool. It complements tools like SCAP, OpenSCAP, and Evaluate-STIG to easily upgrade existing checklists to newer versions.

**Supports:**
- STIG Benchmarks (SCAP/XCCDF)
- STIG Checklists (ZIP/PDF) for OS, Applications, and Network
- `.cklb` JSON format (compatible with DISA STIG Viewer 3)

Planned:
- Containerization is being examined.

---

## License

This project is licensed under the **MIT License**.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the conditions of the MIT License.

See the full license text in [LICENSE.txt](LICENSE.txt).

## Install Instructions

**Tested on Ubuntu, Windows with WSL, and Windows.**

### Windows Users: Install Python First

1. Download Python from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer. **IMPORTANT:** On the first screen, check the box that says **"Add Python to PATH"** before clicking Install.
3. Complete the installation, then open a new Command Prompt to continue with the steps below.

---

1. **Clone the repo**
    ```bash
    git clone https://github.com/pjpearman/checkmate.git
    cd checkmate
    ```
    - No git? Download Checkmate's {current_release}.zip

2. **Create a Python venv**
    ```bash
    python3 -m venv stigvenv
    source stigvenv/bin/activate
    ```
    - On Windows, activate with:
      ```cmd
      python -m venv stigvenv
      .\stigvenv\Scripts\activate
      ```

3. **Install Python packages**
    ```bash
    pip install -r requirements.txt
    ```

---

## GUI Mode

To launch the enhanced GUI:

```bash
python checkmate.py gui
```

## TUI Mode  

To launch the enhanced Terminal User Interface:

```bash
python checkmate.py tui
```

## Legacy GUI (if needed)

To launch the original GUI:

```bash
python gui.py
```

Features:
- Modern, aligned layout for merging, upgrading, and exporting checklists
- Drop-downs for mode and files
- Multi-rule editing pop-up for new rules
- Download/export updated checklists
- Background thread processing with instant status/log updates
- Robust error/status reporting

**Workflow:**
1. Create and edit a checklist baseline to match your environment.
2. Import completed checklists.
3. Bulk upgrade: select older completed checklists and transfer the data into the latest version.
4. Download/export updated checklists as needed.

NOTE: checklist storage is currently in `workdir/cklb_proc/`...

---

## Usage (CLI) (WARNING. The CLI us currently behind in features and may not be stable.)

### Compare to Baseline
```bash
python runner.py --mode checklist --yaml baselines/baseline_checklists.yaml
```

### Generate a New Baseline
```bash
python runner.py --mode benchmark --generate-baseline
```

### Compare + Download Updates
```bash
python runner.py --mode checklist --yaml baselines/baseline_checklists.yaml --download-updates
```

### Generate Checklists
```bash
python runner.py --mode checklist --yaml baselines/baseline_checklists.yaml --download-updates --extract-xccdf
```

### Merge Updated Checklists
```bash
python runner.py --mode checklist --merge usr_cklb_lib/old1.cklb usr_cklb_lib/old2.cklb new_checklist.cklb
```

### Other CLI Options:
| Option | Description |
|--------|-------------|
| `--mode [benchmark|checklist|all]` | Type of STIGs to scrape |
| `--yaml` | Path to baseline YAML |
| `--generate-baseline` | Generate instead of compare |
| `--download-updates` | Fetch ZIPs for new/changed STIGs |
| `--extract-xccdf` | Generate `.cklb` from updated ZIPs |
| `--import-cklb` | Import `.cklb` files to local library |
| `--merge` | Merge old `.cklb`s with a new one |
| `--print-urls` | Dump scraped URLs and exit |
| `--headful` | Run Playwright in non-headless mode |
| `--log [terminal|file]` | Logging destination |

---

## Project Structure

```
stigflow/
├── runner.py             # CLI entry point
├── gui_launcher.py       # Tkinter GUI frontend
├── handlers.py           # GUI task logic (imported by GUI)
├── scraper.py            # Scrapes DISA STIG pages
├── comparator.py         # Compares current vs baseline
├── downloader.py         # Downloads updated ZIPs
├── baseline_generator.py # Creates baseline YAMLs
├── xccdf_extractor.py    # Extracts XCCDFs from ZIPs
├── cklb_generator.py     # Generates .cklb JSON from XCCDF
├── selected_merger.py    # Merges old and new .cklb files
├── cklb_importer.py      # Imports .cklb files into local library
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── baselines/            # YAML baselines
├── cklb_proc/            # Checklist processing directories
├── logs/                 # Log output (optional)
```

---

## Version

**v2.1.0**
- Removed the playwright dependency. 


**v2.0.0**
- Major GUI redesign, instant feedback, multi-rule editing, and robust export/download support
- Full GUI + CLI support
- ZIP, XCCDF, CKLB generation
- Merging and batch upgrade support
- Cleaner modular layout

---

**Built to automate boring, repeatable STIG maintenance tasks.**

## Contributions

This project is currently maintained by a single author:

**ppear**  
🔧 Developer, architect, and maintainer of all features  
📬 Reach out via GitHub Issues for feedback or bug reports

Contributions are welcome in the future once the architecture stabilizes.

