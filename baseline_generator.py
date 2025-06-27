import os
import yaml
import logging
from scraper import scrape_stigs

# === Baseline Generator ===

def generate_baseline(scraped_items: list, output_path: str):
    """
    Generates a baseline YAML file from scraped items.

    Args:
        scraped_items (list): List of dicts from scraper
        output_path (str): Path to save the generated YAML
    """
    baseline_data = {}

    for item in scraped_items:
        product = item['Product']
        version = item['Version']
        release = item['Release']
        url = item.get('URL', 'N/A')
        error = item.get('Error', None)

        baseline_data[product] = {
            'Version': version,
            'Release': release,
            'URL': url
        }

        if error:
            baseline_data[product]['Error'] = error
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            yaml.dump(baseline_data, f, sort_keys=True)
        logging.info(f"Baseline successfully written to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write baseline YAML: {str(e)}")

# === CLI Interface (optional) ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['benchmark', 'checklist', 'all'], required=True, help='Scrape mode for baseline generation')
    args = parser.parse_args()

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Scrape the data
    scraped_items = scrape_stigs(mode=args.mode)

    # Pick output filename
    output_filename = {
        'benchmark': 'baseline_benchmarks.yaml',
        'checklist': 'baseline_checklists.yaml',
        'application': 'baseline_applications.yaml',
        'network': 'baseline_networks.yaml',
        'all': 'baseline_all.yaml'
    }[args.mode]

    output_path = os.path.join(os.path.dirname(__file__), 'baselines', output_filename)

    # Generate baseline
    generate_baseline(scraped_items, output_path)
