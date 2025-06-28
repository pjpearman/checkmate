"""
Enhanced CKLB Handler for CheckMate.
Combines functionality from both GUI and TUI applications.
"""

from pathlib import Path
import logging
import json
import re
import shutil
from typing import List, Dict, Tuple, Optional, Union, Any
from datetime import datetime

from .config import Config
from .file_utils import FileUtils
from .log_config import get_operation_logger

logger = get_operation_logger("cklb_handler")


class CKLBHandler:
    """Unified CKLB operations for CheckMate applications."""
    
    def __init__(self, config: Config = None):
        """Initialize CKLB handler with configuration."""
        self.config = config or Config()
        self.file_utils = FileUtils()
    
    @staticmethod
    def ensure_discussion_field(rules: List[Dict]) -> List[Dict]:
        """
        Ensure every rule in the list has a 'discussion' field.
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            Updated list of rules with discussion field
        """
        for rule in rules:
            if 'discussion' not in rule:
                rule['discussion'] = ''
        return rules
    
    def load_cklb(self, path: Union[str, Path]) -> Dict:
        """
        Load a CKLB file safely with validation.
        
        Args:
            path: Path to CKLB file
            
        Returns:
            CKLB data dictionary
            
        Raises:
            ValueError: If file is invalid
            FileNotFoundError: If file doesn't exist
        """
        try:
            data = self.file_utils.safe_json_load(path)
            
            # Ensure discussion fields in all rules
            if 'stigs' in data and isinstance(data['stigs'], list):
                for stig in data['stigs']:
                    if 'rules' in stig and isinstance(stig['rules'], list):
                        self.ensure_discussion_field(stig['rules'])
            
            return data
        except Exception as e:
            logger.error(f"Error loading CKLB {path}: {e}")
            raise
    
    def save_cklb(self, data: Dict, path: Union[str, Path]) -> Path:
        """
        Save CKLB data to file safely.
        
        Args:
            data: CKLB data dictionary
            path: Path to save file
            
        Returns:
            Path to saved file
        """
        try:
            return self.file_utils.safe_json_save(data, path)
        except Exception as e:
            logger.error(f"Error saving CKLB to {path}: {e}")
            raise
    
    def import_cklbs(
        self, 
        selected_files: List[Union[str, Path]], 
        dest_dir: Union[str, Path] = None
    ) -> List[Tuple[str, str]]:
        """
        Import one or more CKLB files into the specified destination directory.
        
        Args:
            selected_files: List of CKLB file paths to import
            dest_dir: Destination directory (defaults to cklb_artifacts)
            
        Returns:
            List of (filename, status) tuples
        """
        if dest_dir is None:
            dest_dir = self.config.get_user_cklb_dir()
        else:
            dest_dir = Path(dest_dir)
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        results = []
        
        for file_path in selected_files:
            file_path = Path(file_path)
            
            if not file_path.is_file():
                results.append((str(file_path), "File not found"))
                continue
            
            if not file_path.suffix.lower() == '.cklb':
                results.append((str(file_path), "Not a CKLB file"))
                continue
            
            try:
                # Load and validate CKLB
                data = self.load_cklb(file_path)
                
                # Save to destination with discussion fields ensured
                dest_path = dest_dir / file_path.name
                self.save_cklb(data, dest_path)
                
                results.append((str(file_path), "Imported"))
                logger.info(f"Imported CKLB: {dest_path}")
                
            except Exception as e:
                logger.error(f"Error importing {file_path}: {e}")
                results.append((str(file_path), f"Error: {e}"))
        
        return results
    
    def get_stig_info(self, cklb_data: Dict) -> Dict[str, str]:
        """
        Extract STIG information from CKLB data.
        
        Args:
            cklb_data: CKLB data dictionary
            
        Returns:
            Dictionary with STIG information
        """
        info = {
            'stig_id': None,
            'stig_name': None,
            'version': None,
            'release': None,
            'release_info': None
        }
        
        if 'stigs' in cklb_data and isinstance(cklb_data['stigs'], list) and cklb_data['stigs']:
            stig = cklb_data['stigs'][0]
            info['stig_id'] = stig.get('stig_id')
            info['stig_name'] = stig.get('stig_name')
            info['version'] = stig.get('version')
            info['release_info'] = stig.get('release_info')
            
            # Extract release number from release_info
            if info['release_info']:
                match = re.search(r'Release:\s*(\d+)', info['release_info'])
                if match:
                    info['release'] = match.group(1)
        
        return info
    
    def get_rules(self, cklb_data: Dict) -> List[Dict]:
        """
        Extract rules from CKLB data.
        
        Args:
            cklb_data: CKLB data dictionary
            
        Returns:
            List of rule dictionaries
        """
        # Try common locations for rules
        if 'stigs' in cklb_data and isinstance(cklb_data['stigs'], list) and cklb_data['stigs']:
            stig = cklb_data['stigs'][0]
            if 'rules' in stig:
                return stig['rules']
        
        # Try alternative locations
        for key in ['rules', 'Rules', 'stig_rules', 'stigRules']:
            if key in cklb_data:
                return cklb_data[key]
        
        # Try to find list of dictionaries with rule_id
        for value in cklb_data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict) and 'rule_id' in value[0]:
                return value
        
        return []
    
    def get_rule_key(self, rule: Dict) -> str:
        """
        Extract a unique key from a rule for comparison.
        
        Args:
            rule: Rule dictionary
            
        Returns:
            Rule identifier string
        """
        # Try various rule ID fields
        for field in ['rule_id', 'id', 'Rule_ID', 'group_id_src', 'group_id']:
            val = rule.get(field)
            if val:
                # Extract SV- pattern if present
                match = re.match(r'(SV-\d+)', val)
                if match:
                    return match.group(1)
                return val
        
        return str(rule.get('rule_id', ''))
    
    def compare_cklb_versions(
        self, 
        file_a_list: List[Union[str, Path]], 
        file_b: Union[str, Path]
    ) -> str:
        """
        Compare one or more CKLB files (A) to a second CKLB file (B).
        
        Args:
            file_a_list: List of CKLB files to compare from
            file_b: CKLB file to compare to
            
        Returns:
            Comparison report as string
        """
        file_b = Path(file_b)
        
        try:
            cklb_b = self.load_cklb(file_b)
        except Exception as e:
            return f"[ERROR] Could not load CKLB file: {file_b} - {e}"
        
        stig_b_info = self.get_stig_info(cklb_b)
        rules_b_list = self.get_rules(cklb_b)
        rules_b = {self.get_rule_key(r): r for r in rules_b_list}
        
        output = []
        
        for file_a in file_a_list:
            file_a = Path(file_a)
            
            if not file_a.suffix.lower() == '.cklb' or not file_b.suffix.lower() == '.cklb':
                output.append(f"[ERROR] Only .cklb files are supported: {file_a.name} or {file_b.name}")
                continue
            
            try:
                cklb_a = self.load_cklb(file_a)
            except Exception as e:
                output.append(f"[ERROR] Could not load CKLB file: {file_a} - {e}")
                continue
            
            stig_a_info = self.get_stig_info(cklb_a)
            
            # Check for STIG ID mismatch
            if (stig_a_info['stig_id'] and stig_b_info['stig_id'] and 
                stig_a_info['stig_id'] != stig_b_info['stig_id']):
                output.append(f"[WARNING] Mismatched STIG IDs: '{stig_a_info['stig_id']}' vs '{stig_b_info['stig_id']}'")
            
            rules_a = {self.get_rule_key(r): r for r in self.get_rules(cklb_a)}
            
            output.append(f"=== Comparing {file_a.name} to {file_b.name} ===\\n")
            
            # Find new rules in B
            new_in_b = [rid for rid in rules_b.keys() if rid not in rules_a]
            if new_in_b:
                output.append(f"New rules in {file_b.name} (not in {file_a.name}):")
                output.append(f"{'ID':<16} {'Rule Title'}")
                output.append(f"{'-'*16} {'-'*70}")
                
                for rid in new_in_b:
                    rule = rules_b[rid]
                    title = rule.get('rule_title') or rule.get('title') or rule.get('group_title') or ''
                    # Wrap long titles
                    if len(title) > 70:
                        title = title[:67] + "..."
                    output.append(f"{rid:<16} {title}")
                output.append("")
            
            # Find rules only in A
            only_in_a = [rid for rid in rules_a.keys() if rid not in rules_b]
            if only_in_a:
                output.append(f"Rules only in {file_a.name} (not in {file_b.name}):")
                output.append(f"{'ID':<16} {'Rule Title'}")
                output.append(f"{'-'*16} {'-'*70}")
                
                for rid in only_in_a:
                    rule = rules_a[rid]
                    title = rule.get('rule_title') or rule.get('title') or rule.get('group_title') or ''
                    if len(title) > 70:
                        title = title[:67] + "..."
                    output.append(f"{rid:<16} {title}")
                output.append("")
            
            # Count common rules
            common_rules = len(set(rules_a.keys()) & set(rules_b.keys()))
            output.append(f"Common rules: {common_rules}")
            output.append("")
        
        return '\\n'.join(output)
    
    def check_stig_id_match(self, old_data: Dict, new_data: Dict) -> Tuple[bool, str, str, List[Dict]]:
        """
        Check if STIG IDs match between old and new CKLB data and find new rules.
        
        Args:
            old_data: Old CKLB data
            new_data: New CKLB data
            
        Returns:
            Tuple of (is_match, old_stig_id, new_stig_id, new_rules)
        """
        old_info = self.get_stig_info(old_data)
        new_info = self.get_stig_info(new_data)
        
        old_stig_id = old_info['stig_id'] or "UNKNOWN"
        new_stig_id = new_info['stig_id'] or "UNKNOWN"
        
        # Find new rules
        old_rules = {self.get_rule_key(r): r for r in self.get_rules(old_data)}
        new_rules_list = self.get_rules(new_data)
        new_rules = []
        
        for rule in new_rules_list:
            rule_key = self.get_rule_key(rule)
            if rule_key not in old_rules:
                new_rules.append(rule)
        
        return old_stig_id == new_stig_id, old_stig_id, new_stig_id, new_rules
    
    def find_new_rules(self, old_data: Dict, new_data: Dict) -> List[Dict]:
        """
        Find rules that exist in new CKLB but not in old CKLB.
        
        Args:
            old_data: Old CKLB data
            new_data: New CKLB data
            
        Returns:
            List of new rules
        """
        _, _, _, new_rules = self.check_stig_id_match(old_data, new_data)
        return new_rules
    
    def merge_cklb_data(
        self, 
        old_data: Dict, 
        new_data: Dict, 
        new_rule_defaults: Dict = None
    ) -> Dict:
        """
        Merge old CKLB data into new CKLB structure.
        
        Args:
            old_data: Old CKLB data with user findings
            new_data: New CKLB structure
            new_rule_defaults: Default values for new rules
            
        Returns:
            Merged CKLB data
        """
        if new_rule_defaults is None:
            new_rule_defaults = {
                'status': 'not_reviewed',
                'comments': '',
                'finding_details': ''
            }
        
        # Get rules from both files
        old_rules = {self.get_rule_key(r): r for r in self.get_rules(old_data)}
        merged_data = json.loads(json.dumps(new_data))  # Deep copy
        
        # Update target data from old file if available
        if 'target_data' in old_data and 'target_data' in merged_data:
            merged_data['target_data'].update(old_data['target_data'])
        
        # Merge rules
        merged_rules = self.get_rules(merged_data)
        merged_count = 0
        
        for rule in merged_rules:
            rule_key = self.get_rule_key(rule)
            
            if rule_key in old_rules:
                old_rule = old_rules[rule_key]
                
                # Preserve user data from old rule
                for field in ['status', 'comments', 'finding_details', 'overrides']:
                    if field in old_rule:
                        rule[field] = old_rule[field]
                
                merged_count += 1
            else:
                # New rule - apply defaults
                for field, default_value in new_rule_defaults.items():
                    if field not in rule:
                        rule[field] = default_value
        
        logger.info(f"Merged {merged_count} rules from old checklist")
        return merged_data
    
    def upgrade_cklb_simple(
        self, 
        old_file: Union[str, Path], 
        new_file: Union[str, Path], 
        output_dir: Union[str, Path] = None
    ) -> Path:
        """
        Simple CKLB upgrade without user interaction.
        
        Args:
            old_file: Path to old CKLB with user data
            new_file: Path to new CKLB structure
            output_dir: Output directory (defaults to cklb_updated)
            
        Returns:
            Path to upgraded CKLB file
        """
        if output_dir is None:
            output_dir = self.config.directories["cklb_updated"]
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load files
        old_data = self.load_cklb(old_file)
        new_data = self.load_cklb(new_file)
        
        # Merge data
        merged_data = self.merge_cklb_data(old_data, new_data)
        
        # Generate output filename
        old_path = Path(old_file)
        timestamp = datetime.now().strftime("%Y%m%d")
        output_name = f"{old_path.stem}_upgraded_{timestamp}.cklb"
        output_path = output_dir / output_name
        
        # Save merged file
        self.save_cklb(merged_data, output_path)
        
        logger.info(f"Upgraded CKLB saved to: {output_path}")
        return output_path


# Convenience functions for backward compatibility
def load_cklb(path: Union[str, Path]) -> Dict:
    """Load CKLB file using default handler."""
    handler = CKLBHandler()
    return handler.load_cklb(path)

def save_cklb(data: Dict, path: Union[str, Path]) -> Path:
    """Save CKLB file using default handler."""
    handler = CKLBHandler()
    return handler.save_cklb(data, path)

def check_stig_id_match(old_data: Dict, new_data: Dict) -> Tuple[bool, str, str, List[Dict]]:
    """Check STIG ID match using default handler."""
    handler = CKLBHandler()
    return handler.check_stig_id_match(old_data, new_data)
