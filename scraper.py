import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === Constants ===
MAIN_URL = "https://public.cyber.mil/stigs/downloads/"

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
    """Scrape the DISA downloads page and return structured data."""
    html_content = fetch_page(url)
    soup = BeautifulSoup(html_content, "html.parser")
    items = []
    
    # Look for the downloads table or list structure
    # The DISA site typically has a table or structured list with download links
    download_links = soup.find_all("a", href=True)
    
    for link in download_links:
        href = link.get("href", "")
        
        # Only process ZIP files
        if not href.lower().endswith(".zip"):
            continue
            
        # Get the full URL
        file_url = urljoin(url, href)
        
        # Get the link text (title)
        title = link.get_text(strip=True)
        if not title:
            title = os.path.basename(href)
        
        # Try to find metadata in the surrounding context
        updated_date = "Unknown"
        version = "Unknown"
        release = "Unknown"
        
        # Look for parent elements that might contain version/date info
        parent = link.find_parent()
        grandparent = parent.find_parent() if parent else None
        
        # Check various parent elements for date information
        for element in [link, parent, grandparent]:
            if not element:
                continue
                
            text = element.get_text(" ", strip=True)
            
            # Look for date patterns
            date_match = re.search(r'(\d{1,2}[\s/\-]\w{3,9}[\s/\-]\d{4})', text)
            if date_match and updated_date == "Unknown":
                updated_date = date_match.group(1)
            
            # Look for version patterns in the context
            version_match = re.search(r'[Vv]ersion\s+(\d+(?:\.\d+)*)', text)
            if version_match and version == "Unknown":
                version = version_match.group(1)
                
            # Look for release patterns
            release_match = re.search(r'[Rr]elease\s+(\d+(?:\.\d+)*)', text)
            if release_match and release == "Unknown":
                release = release_match.group(1)
        
        # Try to extract version/release from filename if not found
        if version == "Unknown" or release == "Unknown":
            v, r = extract_version_release_from_filename(title)
            if v and version == "Unknown":
                version = v
            if r and release == "Unknown":
                release = r
                
        # Try to extract version/release from URL filename
        if version == "Unknown" or release == "Unknown":
            url_filename = os.path.basename(file_url)
            v, r = extract_version_release_from_filename(url_filename)
            if v and version == "Unknown":
                version = v
            if r and release == "Unknown":
                release = r
        
        # Clean up the title
        title = title.replace('–', '-').strip()
        
        items.append({
            'Product': title,
            'Version': version,
            'Release': release,
            'Updated': updated_date,
            'URL': file_url
        })
        
        logging.info(f"Found: {title} (V{version} R{release}) - {updated_date}")
    
    if not items:
        logging.warning(f"No downloadable .zip files found on page: {url}")
        print(f"[DEBUG] No downloadable .zip files found on page: {url}")
    else:
        print(f"[DEBUG] Found {len(items)} .zip files on page: {url}")
    
    return items

def scrape_stigs(mode: str = "all", headful: bool = False) -> list:
    """Main scraping function that fetches all STIGs from the DISA downloads page."""
    try:
        logging.info(f"Starting STIG scraping from {MAIN_URL}")
        items = scrape_page(MAIN_URL)
        
        # Sort items by Product name for better presentation
        items.sort(key=lambda x: x.get('Product', '').lower())
        
        logging.info(f"Successfully scraped {len(items)} STIG items")
        return items
        
    except Exception as e:
        logging.error(f"Failed to scrape STIGs: {e}")
        raise

def extract_version_release_from_filename(file_name):
    """Extract version and release information from filename."""
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
    
    # Try standard version patterns
    m = re.search(r'[Vv](\d+)[Rr](\d+)', file_name)
    if m:
        return m.group(1), m.group(2)
        
    return None, None
