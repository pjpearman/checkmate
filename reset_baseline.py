import os
import yaml
import logging

def reset_baseline_fields(baseline_path, product_name):
    """
    Sets 'Release' and 'Version' to '0' for the selected product in the baseline YAML file.
    Args:
        baseline_path (str): Path to the baseline YAML file
        product_name (str): The product key to reset
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(baseline_path):
        logging.error(f"Baseline YAML not found: {baseline_path}")
        return False
    try:
        with open(baseline_path, 'r') as f:
            data = yaml.safe_load(f)
        if product_name not in data:
            logging.error(f"Product '{product_name}' not found in baseline.")
            return False
        data[product_name]['Release'] = '0'
        data[product_name]['Version'] = '0'
        with open(baseline_path, 'w') as f:
            yaml.dump(data, f, sort_keys=True)
        logging.info(f"Reset Release and Version for '{product_name}' in {baseline_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to reset baseline: {e}")
        return False
