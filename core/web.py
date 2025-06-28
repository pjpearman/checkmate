"""
Enhanced web downloader for CheckMate.
Fetches STIG files from DISA website with improved error handling and features.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union
from datetime import datetime
import json

from .config import Config
from .file_utils import FileUtils
from .log_config import get_operation_logger

logger = get_operation_logger("web_downloader")


class WebDownloader:
    """Enhanced web downloader for CheckMate applications."""
    
    # Default DISA STIG downloads URL
    DEFAULT_URL = "https://public.cyber.mil/stigs/downloads/"
    
    # User-Agent header to mimic a browser request
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; CheckMate/2.1.0; +https://github.com/pjpearman/checkmate)"
    }
    
    def __init__(self, config: Config = None):
        """Initialize web downloader with configuration."""
        self.config = config or Config()
        self.file_utils = FileUtils()
        self.download_dir = self.config.directories["tmp"]
        self.headers = self.DEFAULT_HEADERS.copy()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def set_download_directory(self, download_dir: Union[str, Path]) -> None:
        """
        Set the download directory.
        
        Args:
            download_dir: Directory path for downloads
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_page(self, url: str = None, timeout: int = 30) -> str:
        """
        Fetch webpage content.
        
        Args:
            url: URL to fetch (defaults to DISA STIG downloads)
            timeout: Request timeout in seconds
            
        Returns:
            HTML content as string
            
        Raises:
            requests.RequestException: If request fails
        """
        if url is None:
            url = self.DEFAULT_URL
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Fetched page: {url}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            raise
    
    def parse_table_for_links(
        self, 
        html_content: str, 
        file_extensions: List[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Parse HTML content and extract file download links.
        
        Args:
            html_content: HTML content to parse
            file_extensions: List of file extensions to include (defaults to .zip)
            
        Returns:
            List of (filename, url) tuples
        """
        if file_extensions is None:
            file_extensions = ['.zip']
        
        soup = BeautifulSoup(html_content, "html.parser")
        file_links = []
        
        # Look for all <a> tags with download links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # Check if href ends with any of the allowed extensions
            if any(href.lower().endswith(ext.lower()) for ext in file_extensions):
                file_url = urljoin(self.DEFAULT_URL, href)
                file_name = os.path.basename(href)
                file_links.append((file_name, file_url))
                logger.debug(f"Found file link: {file_name} -> {file_url}")
        
        if not file_links:
            logger.warning("No downloadable file links found on the page")
        else:
            logger.info(f"Found {len(file_links)} downloadable files")
        
        return file_links
    
    def get_file_info(self, file_url: str) -> Dict:
        """
        Get file information without downloading.
        
        Args:
            file_url: URL of the file
            
        Returns:
            Dictionary with file information (never None)
        """
        # Default info structure
        default_info = {
            'url': file_url,
            'filename': os.path.basename(urlparse(file_url).path) or 'unknown',
            'size': None,
            'content_type': 'application/zip',
            'last_modified': '',
            'etag': ''
        }
        
        try:
            response = self.session.head(file_url, timeout=10)
            response.raise_for_status()
            
            info = {
                'url': file_url,
                'filename': os.path.basename(urlparse(file_url).path) or 'unknown',
                'size': response.headers.get('content-length'),
                'content_type': response.headers.get('content-type', 'application/zip'),
                'last_modified': response.headers.get('last-modified', ''),
                'etag': response.headers.get('etag', '')
            }
            
            # Convert size to integer if available
            if info['size']:
                try:
                    info['size'] = int(info['size'])
                except (ValueError, TypeError):
                    info['size'] = None
            
            return info
            
        except requests.RequestException as e:
            logger.warning(f"Failed to get file info for {file_url}: {e}")
            return default_info
        except Exception as e:
            logger.error(f"Unexpected error getting file info for {file_url}: {e}")
            return default_info
    
    def download_file(
        self, 
        file_url: str, 
        file_name: str = None, 
        output_dir: Union[str, Path] = None,
        overwrite: bool = False,
        progress_callback: callable = None
    ) -> Optional[Path]:
        """
        Download a file with progress tracking and error handling.
        
        Args:
            file_url: URL of the file to download
            file_name: Custom filename (defaults to URL basename)
            output_dir: Output directory (defaults to configured download dir)
            overwrite: Whether to overwrite existing files
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded file, or None if failed
        """
        if file_name is None:
            file_name = os.path.basename(urlparse(file_url).path)
        
        if output_dir is None:
            output_dir = self.download_dir
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        dest_path = output_dir / file_name
        
        # Check if file already exists
        if dest_path.exists() and not overwrite:
            logger.info(f"File already exists: {file_name}")
            return dest_path
        
        try:
            logger.info(f"Downloading: {file_name}")
            
            with self.session.get(file_url, stream=True, timeout=30) as response:
                response.raise_for_status()
                
                # Get file size for progress tracking
                total_size = response.headers.get('content-length')
                if total_size:
                    total_size = int(total_size)
                
                downloaded = 0
                chunk_size = 8192
                
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Call progress callback if provided
                            if progress_callback and total_size:
                                progress_callback(downloaded, total_size, file_name)
            
            logger.info(f"Downloaded: {file_name} ({downloaded} bytes)")
            return dest_path
            
        except requests.RequestException as e:
            logger.error(f"Failed to download {file_name} from {file_url}: {e}")
            # Clean up partial download
            if dest_path.exists():
                try:
                    dest_path.unlink()
                except Exception:
                    pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {file_name}: {e}")
            return None
    
    def download_multiple_files(
        self, 
        file_links: List[Tuple[str, str]], 
        output_dir: Union[str, Path] = None,
        progress_callback: callable = None
    ) -> List[Tuple[str, Optional[Path], Optional[str]]]:
        """
        Download multiple files with progress tracking.
        
        Args:
            file_links: List of (filename, url) tuples
            output_dir: Output directory
            progress_callback: Optional callback for overall progress
            
        Returns:
            List of (filename, path, error) tuples
        """
        if output_dir is None:
            output_dir = self.download_dir
        
        results = []
        total_files = len(file_links)
        
        for i, (file_name, file_url) in enumerate(file_links, 1):
            if progress_callback:
                progress_callback(i, total_files, f"Downloading {file_name}")
            
            try:
                path = self.download_file(file_url, file_name, output_dir)
                if path:
                    results.append((file_name, path, None))
                else:
                    results.append((file_name, None, "Download failed"))
            except Exception as e:
                error_msg = f"Error downloading {file_name}: {e}"
                logger.error(error_msg)
                results.append((file_name, None, error_msg))
        
        return results
    
    def get_available_stigs(self) -> List[Dict]:
        """
        Get list of available STIG files with metadata.
        
        Returns:
            List of STIG file information dictionaries
        """
        try:
            logger.info("Fetching STIG page content...")
            html_content = self.fetch_page()
            
            logger.info("Parsing file links from page...")
            file_links = self.parse_table_for_links(html_content)
            
            if not file_links:
                logger.warning("No file links found on page")
                return []
            
            logger.info(f"Found {len(file_links)} file links, processing metadata...")
            stigs = []
            
            for i, (file_name, file_url) in enumerate(file_links):
                try:
                    # Parse STIG information from filename
                    stig_info = self.parse_stig_filename(file_name)
                    stig_info['filename'] = file_name
                    stig_info['url'] = file_url
                    
                    # Get additional file info (with error handling)
                    try:
                        file_info = self.get_file_info(file_url)
                        if file_info and isinstance(file_info, dict):
                            # Only update if we got valid file info
                            stig_info.update(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to get file info for {file_name}: {e}")
                        # Set default values for missing file info
                        stig_info.setdefault('size', None)
                        stig_info.setdefault('content_type', 'application/zip')
                        stig_info.setdefault('last_modified', '')
                        stig_info.setdefault('etag', '')
                    
                    stigs.append(stig_info)
                    
                    # Log progress for large lists
                    if i > 0 and i % 50 == 0:
                        logger.info(f"Processed {i}/{len(file_links)} files...")
                        
                except Exception as e:
                    logger.error(f"Error processing STIG file {file_name}: {e}")
                    # Continue with next file rather than failing completely
                    continue
            
            logger.info(f"Successfully processed {len(stigs)} STIG files")
            return stigs
            
        except Exception as e:
            logger.error(f"Error getting available STIGs: {e}")
            return []
    
    def parse_stig_filename(self, filename: str) -> Dict:
        """
        Parse STIG information from filename.
        Supports both V#R# (version/release) and Y##M## (year/month) patterns.
        
        Args:
            filename: STIG filename
            
        Returns:
            Dictionary with parsed STIG information
        """
        info = {
            'stig_id': None,
            'version': None,
            'release': None,
            'date': None,
            'type': 'unknown',
            'format': None  # 'version_release' or 'year_month'
        }
        
        # Common STIG filename patterns
        patterns = [
            # V#R# patterns (version/release)
            (r'U_([^_]+(?:_[^_]+)*)_V(\d+)[Rr](\d+)_(\d{8})', 'version_release'),  # U_STIGNAME_V1R2_20231201
            (r'U_([^_]+(?:_[^_]+)*)_V(\d+)[Rr](\d+)', 'version_release'),          # U_STIGNAME_V1R2
            (r'([^_]+(?:_[^_]+)*)_V(\d+)R(\d+)', 'version_release'),               # STIGNAME_V1R2
            
            # Y##M## patterns (year/month)
            (r'U_([^_]+(?:_[^_]+)*)_Y(\d{2})M(\d{2})_(\d{8})', 'year_month'),      # U_STIGNAME_Y25M04_20250401
            (r'U_([^_]+(?:_[^_]+)*)_Y(\d{2})M(\d{2})', 'year_month'),              # U_STIGNAME_Y25M04
            (r'([^_]+(?:_[^_]+)*)_Y(\d{2})M(\d{2})', 'year_month'),                # STIGNAME_Y25M04
        ]
        
        for pattern, format_type in patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                info['stig_id'] = groups[0]
                info['format'] = format_type
                
                if format_type == 'version_release':
                    info['version'] = int(groups[1]) if groups[1] else None
                    info['release'] = int(groups[2]) if groups[2] else None
                    if len(groups) > 3:
                        info['date'] = groups[3]
                elif format_type == 'year_month':
                    # For Y##M## format, store as version/release for display compatibility
                    info['version'] = f"Y{groups[1]}" if groups[1] else None
                    info['release'] = f"M{groups[2]}" if groups[2] else None
                    if len(groups) > 3:
                        info['date'] = groups[3]
                
                break
        
        # Determine STIG type
        if any(keyword in filename.lower() for keyword in ['stig', 'benchmark']):
            info['type'] = 'stig'
        elif 'checklist' in filename.lower():
            info['type'] = 'checklist'
        elif 'products' in filename.lower():
            info['type'] = 'products'
        elif 'srr' in filename.lower():
            info['type'] = 'srr'
        
        return info
    
    def filter_stigs_by_criteria(
        self, 
        stigs: List[Dict], 
        stig_ids: List[str] = None,
        min_version: int = None,
        max_age_days: int = None
    ) -> List[Dict]:
        """
        Filter STIGs by various criteria.
        
        Args:
            stigs: List of STIG dictionaries
            stig_ids: List of STIG IDs to include
            min_version: Minimum version number
            max_age_days: Maximum age in days
            
        Returns:
            Filtered list of STIGs
        """
        filtered = stigs
        
        if stig_ids:
            filtered = [s for s in filtered if s.get('stig_id') in stig_ids]
        
        if min_version:
            filtered = [s for s in filtered 
                       if s.get('version') and s['version'] >= min_version]
        
        if max_age_days:
            # Filter by file date if available
            cutoff_date = datetime.now().strftime('%Y%m%d')
            filtered = [s for s in filtered
                       if not s.get('date') or s['date'] >= cutoff_date]
        
        return filtered


# Convenience functions for backward compatibility
def fetch_page(url: str) -> str:
    """Fetch page using default downloader."""
    downloader = WebDownloader()
    return downloader.fetch_page(url)

def parse_table_for_links(html_content: str) -> List[Tuple[str, str]]:
    """Parse table links using default downloader."""
    downloader = WebDownloader()
    return downloader.parse_table_for_links(html_content)

def download_file(file_url: str, file_name: str) -> None:
    """Download file using default downloader."""
    downloader = WebDownloader()
    downloader.download_file(file_url, file_name)
