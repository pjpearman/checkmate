import os
import argparse
import logging
import yaml
import json
from datetime import datetime
from scraper import scrape_stigs
from comparator import compare_to_baseline
from baseline_generator import generate_baseline
from downloader import download_updates
from xccdf_extractor import extract_xccdf_from_zip
from cklb_generator import generate_cklb_json

# === Setup paths ===
script_dir = os.path.dirname(os.path.abspath(__file__))

# === Setup argument parser ===
parser = argparse.ArgumentParser(description="DISA STIG Scraper and Baseline Manager")
parser.add_argument('--mode', choices=['benchmark', 'checklist', 'application', 'network', 'all'], required=True, help='Which type of STIGs to scrape')
parser.add_argument('--yaml', required=False, help='Baseline YAML file to compare against (optional)')
parser.add_argument('--log', choices=['terminal', 'file'], default='terminal', help='Log to terminal or file')
parser.add_argument('--generate-baseline', action='store_true', help='Generate a new baseline YAML instead of comparing')
parser.add_argument('--print-urls', action='store_true', help='Print download URLs and exit')
parser.add_argument('--download-updates', action='store_true', help='Download ZIPs for new or changed items')
parser.add_argument('--extract-xccdf', action='store_true', help='Extract .xccdf.xml from downloaded ZIPs and generate checklists')
parser.add_argument('--import-cklb', action='store_true', help='Import .cklb files into user checklist library')

args = parser.parse_args()

# === Setup logging ===
if args.log == 'file':
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "stig_scrape.log")
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# === Main Logic ===
def main():
    scraped_items = scrape_stigs(mode=args.mode)

    if args.import_cklb:
        from cklb_importer import import_cklb_files
        import_cklb_files()
        return

    if args.print_urls:
        for item in scraped_items:
            print(item['URL'])
        return

    if args.generate_baseline:
        # Generate a new baseline file
        baseline_folder = os.path.join(script_dir, "baselines")
        os.makedirs(baseline_folder, exist_ok=True)

        if args.mode == 'benchmark':
            output_path = os.path.join(baseline_folder, "baseline_benchmarks.yaml")
        elif args.mode == 'checklist':
            output_path = os.path.join(baseline_folder, "baseline_checklists.yaml")
        elif args.mode == 'application':
            output_path = os.path.join(baseline_folder, "baseline_applications.yaml")
        elif args.mode == 'network':
            output_path = os.path.join(baseline_folder, "baseline_networks.yaml")
        else:
            output_path = os.path.join(baseline_folder, "baseline_all.yaml")

        generate_baseline(scraped_items, output_path)
        logging.info(f"Generated new baseline at {output_path}")

    else:
        # Compare to existing baseline
        if not args.yaml:
            logging.error("You must provide a --yaml baseline to compare against.")
            return
        baseline_path = os.path.join(script_dir, args.yaml)

        # Load baseline
        try:
            with open(baseline_path, "r") as f:
                old_data = yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Could not load baseline file: {e}")
            return

        # Collect changed items
        changed_items = []
        for item in scraped_items:
            product = item["Product"]
            if product not in old_data:
                continue
            old = old_data[product]
            if old.get("Version") != item.get("Version") or old.get("Release") != item.get("Release"):
                changed_items.append(item)

        # Perform comparison and optionally download
        compare_to_baseline(scraped_items, baseline_path)

        if args.download_updates:
            logging.info(f"Found {len(changed_items)} new/changed items. Starting downloads...")
            download_updates(changed_items)

            if args.extract_xccdf:
                zip_dir = os.path.join(script_dir, "cklb_proc", "xccdf_lib")
                cklb_out_dir = os.path.join(script_dir, "cklb_proc", "cklb_lib")
                os.makedirs(cklb_out_dir, exist_ok=True)

                for item in changed_items:
                    url = item.get("URL")
                    if not url:
                        continue
                    zip_name = os.path.basename(url)
                    zip_path = os.path.join(zip_dir, zip_name)
                    xccdf_path = extract_xccdf_from_zip(zip_path, zip_dir)

                    if xccdf_path:
                        try:
                            cklb_json = generate_cklb_json(xccdf_path)
                            basename = os.path.basename(xccdf_path).replace("-xccdf.xml", "").replace("Manual", "").strip("_-")
                            date_str = datetime.today().strftime("%Y%m%d")
                            outfile_name = f"{basename}_{date_str}.cklb"
                            outfile = os.path.join(cklb_out_dir, outfile_name)
                            with open(outfile, 'w') as f:
                                json.dump(cklb_json, f, indent=2)
                            logging.info(f"Generated checklist: {outfile}")
                        except Exception as e:
                            logging.error(f"Failed to generate checklist from {xccdf_path}: {e}")

if __name__ == "__main__":
    main()