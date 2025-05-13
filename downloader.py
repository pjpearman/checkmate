import os
import logging
import requests
import time

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def download_updates(changed_items: list, target_dir: str = "cklb_proc/xccdf_lib"):
    os.makedirs(target_dir, exist_ok=True)
    for item in changed_items:
        product = item.get("Product")
        url = item.get("URL")

        if not url or not url.endswith(".zip"):
            logging.warning(f"Skipping {product} — invalid or missing URL.")
            continue

        filename = os.path.basename(url)
        dest_path = os.path.join(target_dir, filename)

        if os.path.exists(dest_path):
            logging.info(f"{filename} already exists. Skipping.")
            continue

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logging.info(f"Downloading {product} from {url} (attempt {attempt})...")
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logging.info(f"Saved to {dest_path}")
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt} failed for {product}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    logging.error(f"Failed to download {url} after {MAX_RETRIES} attempts. This error is usually due to a network/dns issue. Try again.")
