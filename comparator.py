import os
import yaml
import logging

def compare_to_baseline(scraped_items: list, baseline_path: str):
    """
    Compare scraped STIG items against a baseline YAML file.

    Args:
        scraped_items (list): List of dicts from scraper
        baseline_path (str): Path to baseline YAML file
    """
    if not os.path.isfile(baseline_path):
        logging.error(f"Baseline YAML not found: {baseline_path}")
        return

    try:
        with open(baseline_path, "r") as f:
            baseline_data = yaml.safe_load(f)
        logging.info("Loaded baseline successfully.")
    except Exception as e:
        logging.error(f"Failed to load baseline YAML: {str(e)}")
        return

    scraped_products = {entry['Product'] for entry in scraped_items}
    differences_found = False  # Track if any differences are found

    for parsed in scraped_items:
        product = parsed['Product']
        version = parsed['Version']
        release = parsed['Release']

        expected = baseline_data.get(product)
        if not expected:
            logging.info(f"[NEW] Not in baseline: {product}")
            differences_found = True
        else:
            if expected['Version'] != version or expected['Release'] != release:
                logging.info(f"[CHANGE] Version mismatch for {product}: Expected Ver {expected['Version']} Rel {expected['Release']}, Found Ver {version} Rel {release}")
                differences_found = True

    for product in baseline_data.keys():
        if product not in scraped_products:
            logging.info(f"[MISSING] Missing from scrape: {product}")
            differences_found = True

    if not differences_found:
        logging.info("[INFO] Comparison completed — no differences found.")