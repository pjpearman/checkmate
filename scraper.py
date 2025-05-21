import logging
from playwright.sync_api import sync_playwright
import re

# === Constants ===
SCAP_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=scap"
OS_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=operating-systems"
APP_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=app-security"
NET_URL = "https://public.cyber.mil/stigs/downloads/?_dl_facet_stigs=network-perimeter-wireless"

def scrape_stigs(mode: str, headful: bool = False) -> list:
    all_filtered_rows = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=not headful)
        page = browser.new_page()

        if mode in ['benchmark', 'all']:
            all_filtered_rows += scrape_page(page, SCAP_URL, mode_filter='benchmark' if mode != 'all' else None)

        if mode in ['checklist', 'all']:
            all_filtered_rows += scrape_page(page, OS_URL, mode_filter='checklist' if mode != 'all' else None)

        if mode in ['application', 'all']:
            all_filtered_rows += scrape_page(page, APP_URL, mode_filter='application' if mode != 'all' else None)

        if mode in ['network', 'all']:
            all_filtered_rows += scrape_page(page, NET_URL, mode_filter='network' if mode != 'all' else None)

        browser.close()

    parsed_items = parse_rows(all_filtered_rows)
    return parsed_items


def scrape_page(page, target_url, mode_filter=None) -> list:
    page.goto(target_url)
    logging.info(f"Page loaded: {target_url}")

    page.wait_for_selector("div.mfp-content", timeout=40000)
    logging.info("Consent popup detected.")
    page.evaluate("""
        document.querySelectorAll('.mfp-bg, .mfp-wrap, .mfp-content').forEach(el => el.remove());
    """)
    logging.info("Popup Handled.")

    page.evaluate("""
        document.body.style.overflow = 'auto';
        document.body.style.position = 'static';
    """)
    logging.info("Body styles reset.")

    try:
        page.wait_for_selector("select[name^='DataTables_Table_']", timeout=15000)
        dropdowns = page.query_selector_all("select[name^='DataTables_Table_']")
        if dropdowns:
            dropdowns[0].select_option("100")
            logging.info("Set table to show 100 entries.")
        else:
            logging.warning("No dropdowns found to adjust table length.")
    except Exception as e:
        logging.warning(f"Failed to set table length: {str(e)}")

    page.wait_for_timeout(3000)

    rows = page.query_selector_all("table.dataTable tbody tr")
    logging.info(f"Found {len(rows)} total rows.")

    parsed_items = []
    for row in rows:
        try:
            cells = row.query_selector_all("td")
            title_cell = cells[1]
            anchor = title_cell.query_selector("a")
            url = anchor.get_attribute("href") if anchor else "Unknown"
            title = anchor.inner_text().strip() if anchor else title_cell.inner_text().strip()
            updated = cells[3].inner_text().strip()
            parsed_items.append([url, title, updated])
        except Exception as e:
            logging.error(f"Failed to parse row: {row} ({str(e)})")
            continue

    filtered = []
    for item in parsed_items:
        title = item[1]
        if mode_filter == 'benchmark' and ("Benchmark" not in title):
            continue
        if mode_filter == 'checklist' and ("Benchmark" in title):
            continue
        filtered.append(item)

    logging.info(f"Found {len(filtered)} rows after {mode_filter or 'no'} filtering.")
    return filtered


def parse_rows(rows: list) -> list:
    parsed_items = []
    for row in rows:
        try:
            url, title, updated_date = row

            clean_title = title.replace('–', '-')
            version = "Unknown"
            release = "Unknown"

            # Try standard " - Ver X, Rel Y"
            if ' - Ver ' in clean_title:
                product_part, version_part = clean_title.split(' - Ver ')
                if ', Rel ' in version_part:
                    version_number, release_part = version_part.split(', Rel ')
                    version = version_number.strip()
                    release = release_part.strip()
                else:
                    version = version_part.strip()
                product_name = product_part.strip()
            else:
                product_name = clean_title.strip()
                # Try VxRy pattern in title or URL
                m = re.search(r'V(\d+)[Rr](\d+)', clean_title)
                if not m:
                    m = re.search(r'V(\d+)[Rr](\d+)', url)
                if m:
                    version, release = m.group(1), m.group(2)
                # Try YxxMxx (year/month) pattern
                m2 = re.search(r'Y(\d{2}M\d{2})', clean_title)
                if not m2:
                    m2 = re.search(r'Y(\d{2}M\d{2})', url)
                if m2:
                    version = f"Y{m2.group(1)}"

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
