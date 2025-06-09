import os
import json
import logging
import re

# === Inventory Generator ===

def extract_version_release(file_name):
    # Try V#R# pattern (e.g., V2R1)
    m = re.search(r'_V(\d+)[Rr](\d+)', file_name)
    if m:
        return m.group(1), m.group(2)
    # Try Y##M## pattern (e.g., Y25M04)
    m = re.search(r'_Y(\d{2})M(\d{2})', file_name)
    if m:
        return f"Y{m.group(1)}", f"M{m.group(2)}"
    return None, None

def generate_inventory(scraped_items: list, output_path: str):
    """
    Generates a JSON inventory file from scraped items, extracting version and release from file_name if not present.

    Args:
        scraped_items (list): List of dicts from scraper
        output_path (str): Path to save the generated JSON
    """
    inventory = []
    for item in scraped_items:
        file_name = item.get('FileName') or item.get('Product')
        url = item.get('URL')
        version = item.get('Version')
        release = item.get('Release')
        error = item.get('Error', None)
        # If version/release missing, try to extract from file_name
        if file_name and (version is None or release is None):
            v, r = extract_version_release(file_name)
            if version is None:
                version = v
            if release is None:
                release = r
        if file_name and url:
            entry = {
                'file_name': file_name,
                'url': url,
                'version': version,
                'release': release
            }
            if error:
                entry['error'] = error
            inventory.append(entry)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        with open(output_path, 'w') as f:
            json.dump(inventory, f, indent=2)
        logging.info(f"Inventory successfully written to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write inventory JSON: {str(e)}")

# === CLI Interface (optional) ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['benchmark', 'checklist', 'all'], required=True, help='Scrape mode for inventory generation')
    parser.add_argument('--headful', action='store_true', help='Run browser headful (optional)')
    parser.add_argument('--output', type=str, default=None, help='Output filename (optional, default: user_docs/inventory/inventory_<date>.json)')
    args = parser.parse_args()

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Scrape the data
    scraped_items = scrape_stigs(mode=args.mode, headful=args.headful)

    from datetime import datetime
    if args.output:
        output_path = args.output
    else:
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join('user_docs', 'inventory', f'inventory_{date_str}.json')

    # Generate inventory
    generate_inventory(scraped_items, output_path)
