import threading
import subprocess
import sys
import os
import yaml
import json
from datetime import datetime
import logging

from scraper import scrape_stigs
from baseline_generator import generate_baseline
from comparator import compare_to_baseline
from downloader import download_updates
from xccdf_extractor import extract_xccdf_from_zip
from cklb_generator import generate_cklb_json
from selected_merger import find_new_rules, load_cklb, save_cklb

def run_generate_baseline_task(mode, headful, on_status_update, clear_log):
    clear_log()
    on_status_update("Working... please wait")

    def task():
        try:
            scraped = scrape_stigs(mode, headful)
            out_path = os.path.join("baselines", f"baseline_{mode}s.yaml")
            generate_baseline(scraped, out_path)
            on_status_update("Done")
        except Exception as e:
            logging.error(f"Error generating baseline: {e}")
            on_status_update("Error. Check log output.")
    threading.Thread(target=task).start()


def run_compare_task(mode, headful, baseline_path, download_updates_checked, extract_checked, on_status_update, clear_log, on_cklb_refresh=None):
    clear_log()
    on_status_update("Working... please wait")

    if not baseline_path or not os.path.exists(baseline_path):
        logging.error("Please select a valid YAML file to compare against.")
        on_status_update("Error. Invalid file.")
        return

    def task():
        try:
            scraped = scrape_stigs(mode, headful)
            with open(baseline_path, "r") as f:
                old_data = yaml.safe_load(f)

            changed_items = []
            for item in scraped:
                product = item.get("Product")
                if product not in old_data:
                    continue
                old = old_data[product]
                if old.get("Version") != item.get("Version") or old.get("Release") != item.get("Release"):
                    changed_items.append(item)

            compare_to_baseline(scraped, baseline_path)

            if download_updates_checked:
                logging.info(f"Found {len(changed_items)} new/changed items. Starting downloads...")
                download_updates(changed_items)

                if extract_checked:
                    zip_dir = os.path.join("cklb_proc", "xccdf_lib")
                    out_dir = os.path.join("cklb_proc", "cklb_lib")
                    os.makedirs(out_dir, exist_ok=True)

                    for item in changed_items:
                        zip_name = os.path.basename(item.get("URL", ""))
                        zip_path = os.path.join(zip_dir, zip_name)
                        xccdf_paths = extract_xccdf_from_zip(zip_path, zip_dir)

                        if xccdf_paths:
                            if not isinstance(xccdf_paths, list):
                                xccdf_paths = [xccdf_paths]
                            for xccdf_path in xccdf_paths:
                                try:
                                    cklb_json = generate_cklb_json(xccdf_path)
                                    basename = os.path.basename(xccdf_path).replace("-xccdf.xml", "").replace("Manual", "").strip("_- ")
                                    date_str = datetime.today().strftime("%Y%m%d")
                                    outfile_name = f"{basename}_{date_str}.cklb"
                                    outfile = os.path.join(out_dir, outfile_name)
                                    with open(outfile, 'w') as f:
                                        json.dump(cklb_json, f, indent=2)
                                    logging.info(f"Generated checklist: {outfile}")
                                except Exception as e:
                                    logging.error(f"Failed to generate checklist from {xccdf_path}: {e}")

            on_status_update("Done")
            if on_cklb_refresh:
              on_cklb_refresh()
        except Exception as e:
            logging.error(f"Error comparing to baseline: {e}")
            on_status_update("Error. Check log output.")
    threading.Thread(target=task).start()

def run_merge_task(selected_old_files, new_name, usr_dir, cklb_dir, on_status_update, force=False, prefix=None):
    if not selected_old_files or not new_name:
        on_status_update("Select at least one old and one new CKLB file.")
        return []

    merged_results = []

    for old_name in selected_old_files:
        old_path = os.path.join(usr_dir, old_name)
        new_path = os.path.join(cklb_dir, new_name)
        out_dir = os.path.join(os.getcwd(), 'cklb_proc', 'cklb_updated')
        os.makedirs(out_dir, exist_ok=True)

        with open(old_path, "r", encoding="utf-8") as f:
            old_json = json.load(f)
        # Determine host_prefix: only use prefix if this file lacks host_name
        host_name = old_json.get("target_data", {}).get("host_name")
        if not host_name:
            if prefix is None or not prefix.strip():
                on_status_update(f"[ERROR] Prefix required for checklist '{old_name}' (missing host_name). Aborting batch.")
                return []
            host_prefix = prefix
        else:
            host_prefix = host_name
        # Guarantee uniqueness
        base = f"{host_prefix}_{new_name}"
        out_name = base
        counter = 1
        while os.path.exists(os.path.join(out_dir, out_name)):
            out_name = f"{base}_{counter}"
            counter += 1
        merged_name = out_name
        out_path = os.path.join(out_dir, merged_name)

        cmd = [sys.executable, os.path.join(os.getcwd(), 'selected_merger.py'), old_path, new_path, '-o', out_path]
        if not host_name and prefix:
            cmd.extend(['--prefix', prefix])
        if force:
            cmd.append('--force')
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logging.info(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            logging.error(e.stderr.strip())
            continue

        from selected_merger import find_new_rules
        old_cklb = load_cklb(old_path)
        merged_cklb = load_cklb(out_path)
        new_rules = find_new_rules(old_cklb, merged_cklb)
        merged_results.append({"merged_path": out_path, "merged_name": merged_name, "new_rules": new_rules})

    on_status_update("Merge complete.")
    return merged_results