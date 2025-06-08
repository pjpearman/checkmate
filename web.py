#!/usr/bin/env python3
"""
This script fetches a webpage, parses its table to find new file links, 
and downloads them securely using requests. 
It uses BeautifulSoup for HTML parsing.

Make sure to:
- Adapt the URL and table/element selectors for your specific webpage.
- Run `pip install requests beautifulsoup4` before executing this script.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import logging
import json
from datetime import datetime

# URL of the page containing the table
URL = "https://public.cyber.mil/stigs/downloads/"  # Change this to your target URL
# Directory to save downloaded files
DOWNLOAD_DIR = "tmp"

# User-Agent header to mimic a browser request (some servers block default python-requests User-Agent)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FileDownloaderBot/1.0; +https://example.com/bot)"
}

# Set up logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "downloader.logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, mode=0o700)
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

def fetch_page(url):
    """Fetch the webpage content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        logging.info(f"Fetched page: {url}")
        return response.text
    except Exception as e:
        logging.error(f"Failed to fetch page {url}: {e}")
        raise

def parse_table_for_links(html_content):
    """Parse the page and extract file links (only .zip files)."""
    soup = BeautifulSoup(html_content, "html.parser")
    file_links = []
    # Look for all <a> tags with hrefs that look like downloadable files
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Only consider links to .zip files
        if href.lower().endswith(".zip"):
            file_url = urljoin(URL, href)
            file_name = os.path.basename(href)
            file_links.append((file_name, file_url))
            logging.info(f"Found file link: {file_name} -> {file_url}")
    if not file_links:
        msg = "Warning: No downloadable file links found on the page."
        print(msg)
        logging.warning(msg)
    return file_links

def download_file(file_url, file_name):
    """Download the file and save it to DOWNLOAD_DIR."""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR, mode=0o700)  # Restrict permissions for security
        logging.info(f"Created download directory: {DOWNLOAD_DIR}")

    # Prevent overwriting existing files
    dest_path = os.path.join(DOWNLOAD_DIR, file_name)
    if os.path.exists(dest_path):
        msg = f"File already exists: {file_name}"
        print(msg)
        logging.info(msg)
        return

    try:
        with requests.get(file_url, headers=HEADERS, stream=True, timeout=10) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        msg = f"Downloaded: {file_name}"
        print(msg)
        logging.info(msg)
    except Exception as e:
        msg = f"Failed to download {file_name} from {file_url}: {e}"
        print(msg)
        logging.error(msg)

def main():
    logging.info("Downloader script started.")
    try:
        html_content = fetch_page(URL)
        file_links = parse_table_for_links(html_content)
        
        for file_name, file_url in file_links:
            # TODO: Add logic to determine if this file is "new" (e.g., by timestamp or tracking a database)
            # For now, download every file found:
            download_file(file_url, file_name)
        
        logging.info("Downloader script finished.")
    except Exception as e:
        logging.error(f"Script terminated with error: {e}")
        raise

if __name__ == "__main__":
    main()
