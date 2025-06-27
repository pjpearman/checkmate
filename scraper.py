import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === Constants ===
SCAP_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=scap"
OS_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=operating-systems"
APP_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=app-security"
NET_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=network-perimeter-wireless"

# User-Agent header to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; STIGCheckerBot/1.0; +https://example.com/bot)"
}

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, mode=0o700)
LOG_FILE = os.path.join(LOG_DIR, "scraper.logs")
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

def fetch_page(url):
    """Fetch the webpage content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        logging.info(f"Fetched page: {url}")
        return response.text
    except Exception as e:
        logging.error(f"Failed to fetch page {url}: {e}")
        raise

def scrape_page(url: str, mode_filter: str = None) -> list:
    """Scrape a single page and return filtered rows using robust link search."""
    html_content = fetch_page(url)
    soup = BeautifulSoup(html_content, "html.parser")
    rows = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".zip"):
            file_url = urljoin(url, href)
            title = link.text.strip() or os.path.basename(href)
            # Try to find a nearby date (if available)
            updated = "Unknown"
            parent = link.find_parent()
            if parent:
                # Look for a sibling or parent with a date string
                text = parent.get_text(" ", strip=True)
                m = re.search(r'(\d{1,2} [A-Za-z]{3,9} \d{4})', text)
                if m:
                    updated = m.group(1)
            rows.append([file_url, title, updated])
            logging.info(f"Found file link: {title} -> {file_url} (updated: {updated})")
    if not rows:
        logging.warning(f"No downloadable .zip file links found on page: {url}")
        print(f"[DEBUG] No downloadable .zip file links found on page: {url}")
    else:
        print(f"[DEBUG] Found {len(rows)} .zip file links on page: {url}")
    return rows

def scrape_stigs(mode: str, headful: bool = False) -> list:
    """Main scraping function that processes all relevant pages."""
    all_filtered_rows = []

    # Determine which URLs to scrape based on mode
    urls_to_scrape = []
    if mode in ['benchmark', 'all']:
        urls_to_scrape.append((SCAP_URL, 'benchmark' if mode != 'all' else None))
    if mode in ['checklist', 'all']:
        urls_to_scrape.append((OS_URL, 'checklist' if mode != 'all' else None))
    if mode in ['application', 'all']:
        urls_to_scrape.append((APP_URL, 'application' if mode != 'all' else None))
    if mode in ['network', 'all']:
        urls_to_scrape.append((NET_URL, 'network' if mode != 'all' else None))

    # Scrape each URL
    for url, mode_filter in urls_to_scrape:
        try:
            filtered_rows = scrape_page(url, mode_filter)
            all_filtered_rows.extend(filtered_rows)
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")
            continue

    return parse_rows(all_filtered_rows)

def extract_version_release_from_filename(file_name):
    # Try V#R# pattern (e.g., V2R1)
    m = re.search(r'_V(\d+)[Rr](\d+)', file_name)
    if m:
        return m.group(1), m.group(2)
    # Try Y##M## pattern (e.g., Y25M04)
    m = re.search(r'_Y(\d{2})M(\d{2})', file_name)
    if m:
        return f"Y{m.group(1)}", f"M{m.group(2)}"
    # Try Version Y## Release M##
    m = re.search(r'Version[\s_]?Y(\d{2})[\s_]?Release[\s_]?M(\d{2})', file_name, re.IGNORECASE)
    if m:
        return f"Y{m.group(1)}", f"M{m.group(2)}"
    return None, None

def parse_rows(rows: list) -> list:
    """Parse the raw row data into structured items."""
    parsed_items = []
    for row in rows:
        try:
            url, title, updated_date = row
            clean_title = title.replace('–', '-')
            version = "Unknown"
            release = "Unknown"
            product_name = clean_title.strip()
            # Try to extract from title
            if ' - Ver ' in clean_title:
                product_part, version_part = clean_title.split(' - Ver ', 1)
                if ', Rel ' in version_part:
                    version_number, release_part = version_part.split(', Rel ', 1)
                    version = version_number.strip()
                    release = release_part.strip()
                else:
                    version = version_part.strip()
                product_name = product_part.strip()
            else:
                # Try V#R# or Y##M## or Version Y## Release M## from title
                v, r = extract_version_release_from_filename(clean_title)
                if v:
                    version = v
                if r:
                    release = r
            # If still unknown, try to extract from file name in URL
            if (version == "Unknown" or release == "Unknown") and url:
                file_name = os.path.basename(url)
                v, r = extract_version_release_from_filename(file_name)
                if v:
                    version = v
                if r:
                    release = r
            parsed_items.append({
                'Product': product_name,
                'Version': version,
                'Release': release,
                'Updated': updated_date,
                'URL': url
            })
        except Exception as e:
            logging.error(f"Failed to parse row: {row} ({str(e)})")
            continue
    return parsed_items
