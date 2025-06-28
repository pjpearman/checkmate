"""
Input validation utilities for CheckMate applications.
Enhanced version with additional validation functions.
"""

import re
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path

from .log_config import get_operation_logger

logger = get_operation_logger("validation")


class InputValidator:
    """Input validation utilities for CheckMate."""
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate a filename is safe and follows conventions.
        
        Args:
            filename: The filename to validate
            
        Returns:
            bool: Whether the filename is valid
        """
        if not filename or not isinstance(filename, str):
            return False
        
        # Check for common unsafe characters
        unsafe_chars = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
        if unsafe_chars.search(filename):
            return False
            
        # Check it's not too long
        if len(filename) > 255:
            return False
            
        # Don't allow . or .. as filenames
        if filename in ('.', '..'):
            return False
            
        return True
    
    @staticmethod
    def validate_stig_id(stig_id: str) -> bool:
        """
        Validate a STIG ID follows the expected format.
        
        Args:
            stig_id: The STIG ID to validate
            
        Returns:
            bool: Whether the STIG ID is valid
        """
        if not stig_id or not isinstance(stig_id, str):
            return False
        
        # Basic STIG ID format validation - alphanumeric, underscore, hyphen
        stig_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        return bool(stig_pattern.match(stig_id))
    
    @staticmethod
    def validate_version_release(version: Union[str, int], release: Union[str, int]) -> bool:
        """
        Validate version and release numbers.
        Supports multiple formats:
        1. V#R# format - where version and release are numeric
        2. Y##M## format - where version starts with 'Y' and release starts with 'M'
        3. Plain integers
        
        Args:
            version: Version number string or int
            release: Release number string or int
            
        Returns:
            bool: Whether the version and release are valid
        """
        try:
            version_str = str(version)
            release_str = str(release)
            
            # Handle Y##M## format
            if version_str.startswith('Y') and release_str.startswith('M'):
                try:
                    year = int(version_str[1:])
                    month = int(release_str[1:])
                    return 0 <= year <= 99 and 1 <= month <= 12
                except (ValueError, IndexError):
                    return False
            
            # Handle V#R# format or plain integers
            try:
                v = int(version)
                r = int(release)
                return v > 0 and r > 0
            except (ValueError, TypeError):
                return False
                
        except Exception:
            return False
    
    @staticmethod
    def validate_cklb_basic(data: Dict[str, Any]) -> bool:
        """
        Basic validation of CKLB JSON structure.
        
        Args:
            data: The CKLB data dictionary
            
        Returns:
            bool: Whether the basic CKLB structure is valid
        """
        if not isinstance(data, dict):
            return False
        
        # Check for required top-level fields
        required_fields = {'stigs', 'title', 'id'}
        if not all(field in data for field in required_fields):
            return False
        
        # Validate stigs structure
        stigs = data.get('stigs')
        if not isinstance(stigs, list) or not stigs:
            return False
        
        # Check first STIG has required fields
        first_stig = stigs[0]
        stig_required_fields = {'stig_id', 'stig_name', 'rules'}
        if not all(field in first_stig for field in stig_required_fields):
            return False
        
        # Validate rules structure
        rules = first_stig.get('rules')
        if not isinstance(rules, list):
            return False
        
        return True
    
    @staticmethod
    def validate_cklb_rule(rule: Dict[str, Any]) -> bool:
        """
        Validate a CKLB rule structure.
        
        Args:
            rule: Rule dictionary
            
        Returns:
            bool: Whether the rule is valid
        """
        if not isinstance(rule, dict):
            return False
        
        # Required rule fields
        required_fields = {'rule_id', 'rule_title', 'group_id_src'}
        if not all(field in rule for field in required_fields):
            return False
        
        # Validate status if present
        status = rule.get('status')
        if status:
            valid_statuses = {'not_reviewed', 'not_applicable', 'open', 'not_a_finding'}
            if status not in valid_statuses:
                return False
        
        return True
    
    @staticmethod
    def get_safe_path(base_dir: Union[str, Path], filename: str) -> Optional[Path]:
        """
        Get a safe path joining base_dir and filename.
        Prevents directory traversal attacks.
        
        Args:
            base_dir: Base directory path
            filename: Filename to join
            
        Returns:
            Path object or None if unsafe
        """
        if not InputValidator.validate_filename(filename):
            return None
        
        base_path = Path(base_dir).resolve()
        file_path = (base_path / filename).resolve()
        
        # Ensure the resolved path is still within the base directory
        try:
            file_path.relative_to(base_path)
            return file_path
        except ValueError:
            # Path is outside base directory
            return None
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
        """
        Validate file has an allowed extension.
        
        Args:
            filename: Filename to check
            allowed_extensions: List of allowed extensions (with dots)
            
        Returns:
            bool: Whether extension is allowed
        """
        if not filename or not allowed_extensions:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def validate_json_content(content: str) -> bool:
        """
        Validate that content is valid JSON.
        
        Args:
            content: JSON content string
            
        Returns:
            bool: Whether content is valid JSON
        """
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def validate_rule_status(status: str) -> bool:
        """
        Validate CKLB rule status value.
        
        Args:
            status: Status string to validate
            
        Returns:
            bool: Whether status is valid
        """
        valid_statuses = {
            'not_reviewed',
            'not_applicable', 
            'open',
            'not_a_finding'
        }
        return status in valid_statuses
    
    @staticmethod
    def validate_severity(severity: str) -> bool:
        """
        Validate STIG rule severity value.
        
        Args:
            severity: Severity string to validate
            
        Returns:
            bool: Whether severity is valid
        """
        valid_severities = {'low', 'medium', 'high', 'critical'}
        return severity.lower() in valid_severities
    
    @staticmethod
    def sanitize_filename(filename: str, replacement: str = '_') -> str:
        """
        Sanitize a filename by replacing unsafe characters.
        
        Args:
            filename: Original filename
            replacement: Character to replace unsafe chars with
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Replace unsafe characters
        unsafe_chars = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
        sanitized = unsafe_chars.sub(replacement, filename)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = Path(sanitized).stem, Path(sanitized).suffix
            max_name_len = 255 - len(ext)
            sanitized = name[:max_name_len] + ext
        
        # Ensure it's not just dots
        if sanitized in ('.', '..'):
            sanitized = f"file{replacement}{sanitized}"
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: Whether email format is valid
        """
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Basic URL validation.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: Whether URL format is valid
        """
        if not url or not isinstance(url, str):
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))


# Convenience functions for backward compatibility
def validate_filename(filename: str) -> bool:
    """Validate filename using default validator."""
    return InputValidator.validate_filename(filename)

def validate_stig_id(stig_id: str) -> bool:
    """Validate STIG ID using default validator."""
    return InputValidator.validate_stig_id(stig_id)

def validate_version_release(version: Union[str, int], release: Union[str, int]) -> bool:
    """Validate version/release using default validator."""
    return InputValidator.validate_version_release(version, release)

def validate_cklb_basic(data: Dict[str, Any]) -> bool:
    """Validate CKLB structure using default validator."""
    return InputValidator.validate_cklb_basic(data)

def get_safe_path(base_dir: Union[str, Path], filename: str) -> Optional[Path]:
    """Get safe path using default validator."""
    return InputValidator.get_safe_path(base_dir, filename)
