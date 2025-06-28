"""
Enhanced CKLB Generator for CheckMate.
Converts XCCDF STIG XML files into CKLB JSON format.
Combines functionality from both GUI and TUI applications.
"""

import argparse
import os
import uuid
import json
import zipfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional
import xml.etree.ElementTree as ET

from .config import Config
from .file_utils import FileUtils
from .log_config import get_operation_logger

logger = get_operation_logger("cklb_generator")

# Namespace mapping for XCCDF 1.1
NS = {'xccdf': 'http://checklists.nist.gov/xccdf/1.1'}


class CKLBGenerator:
    """Enhanced CKLB generator for CheckMate applications."""
    
    def __init__(self, config: Config = None):
        """Initialize CKLB generator with configuration."""
        self.config = config or Config()
        self.file_utils = FileUtils()
    
    def parse_benchmark(self, tree: ET.ElementTree) -> Tuple[str, str, str, str]:
        """
        Parse benchmark metadata from XCCDF XML.
        
        Args:
            tree: Parsed XML tree
            
        Returns:
            Tuple of (stig_name, stig_id, release_info, stig_version)
        """
        root = tree.getroot()
        stig_name = root.find('xccdf:title', NS).text or ""
        stig_id = root.get('id') or ""
        release_info = root.find("xccdf:plain-text[@id='release-info']", NS).text or ""
        stig_version = root.find('xccdf:version', NS).text or ""
        return stig_name, stig_id, release_info, stig_version
    
    def parse_rules(self, tree: ET.ElementTree, input_file: str, stig_uuid: str) -> List[Dict]:
        """
        Parse rules from XCCDF XML.
        
        Args:
            tree: Parsed XML tree
            input_file: Input XML file path
            stig_uuid: STIG UUID
            
        Returns:
            List of parsed rules
        """
        root = tree.getroot()
        rules = []
        mtime = datetime.fromtimestamp(os.path.getmtime(input_file), timezone.utc).isoformat()
        
        for grp in root.findall('xccdf:Group', NS):
            rule_elem = grp.find('xccdf:Rule', NS)
            if rule_elem is None:
                continue
                
            gid_src = grp.get('id') or ""
            rid_src = rule_elem.get('id') or ""
            pretty_rid = rid_src.replace('_rule', '')

            # Group metadata
            group_title = grp.find('xccdf:title', NS).text or ""
            group_desc = grp.find('xccdf:description', NS).text or ""

            # Description sections
            desc_elem = rule_elem.find('xccdf:description', NS)
            desc_data = {}
            for sec in ['VulnDiscussion','FalsePositives','FalseNegatives','Documentable',
                        'SeverityOverrideGuidance','PotentialImpacts','ThirdPartyTools',
                        'Mitigations','MitigationControl','Responsibility','IAControls']:
                node = desc_elem.find(f'xccdf:{sec}', NS) if desc_elem is not None else None
                desc_data[sec.lower()] = node.text.strip() if node is not None and node.text else ""

            # Robustly extract VulnDiscussion
            discussion = ""
            vuln_discussion_elem = rule_elem.find('xccdf:VulnDiscussion', NS)
            if vuln_discussion_elem is not None and vuln_discussion_elem.text:
                discussion = vuln_discussion_elem.text.strip()
            else:
                discussion = desc_data.get('vulndiscussion', '')
                # Try to parse as HTML-escaped text if still empty
                if not discussion and desc_elem is not None and desc_elem.text:
                    import re
                    desc_text = desc_elem.text
                    match = re.search(r'<VulnDiscussion>(.*?)</VulnDiscussion>', desc_text, re.DOTALL)
                    if match:
                        discussion = match.group(1).strip()

            # Extract fix text
            fix_text = ""
            fix_elem = rule_elem.find('xccdf:fix/xccdf:fixtext', NS)
            if fix_elem is None:
                fix_elem = rule_elem.find('xccdf:fixtext', NS)
            if fix_elem is not None and fix_elem.text:
                fix_text = fix_elem.text.strip()

            # Check content
            check = rule_elem.find('xccdf:check', NS)
            check_content = ''
            check_ref = None
            if check is not None:
                cc = check.find('xccdf:check-content', NS)
                if cc is not None and cc.text:
                    check_content = cc.text.strip()
                cr = check.find('xccdf:check-content-ref', NS)
                if cr is not None:
                    check_ref = {'href': cr.get('href'), 'name': cr.get('name')}

            # Identifiers (CCI)
            ccis = [ident.text for ident in rule_elem.findall("xccdf:ident[@system='http://cyber.mil/cci']", NS)]
            ref_id = ccis[0] if ccis else None

            # Assemble rule
            rule = {
                "evaluate-stig": {
                    "answer_file": os.path.basename(input_file),
                    "last_write": mtime + 'Z',
                    "afmod": False,
                    "old_status": "",
                    "new_status": ""
                },
                "group_id_src": gid_src,
                "group_tree": [{"id": gid_src, "title": group_title, "description": group_desc}],
                "group_id": gid_src,
                "group_title": group_title,
                "severity": rule_elem.get('severity'),
                "rule_id_src": rid_src,
                "rule_id": pretty_rid,
                "rule_version": rule_elem.find('xccdf:version', NS).text or "",
                "rule_title": rule_elem.find('xccdf:title', NS).text or "",
                "fix_text": fix_text,
                "weight": rule_elem.get('weight'),
                "check_content": check_content,
                "check_content_ref": check_ref,
                "classification": "UNCLASSIFIED",
                "discussion": discussion,
                "false_positives": desc_data.get('falsepositives',''),
                "false_negatives": desc_data.get('falsenegatives',''),
                "documentable": desc_data.get('documentable',''),
                "security_override_guidance": desc_data.get('severityoverrideguidance',''),
                "potential_impacts": desc_data.get('potentialimpacts',''),
                "third_party_tools": desc_data.get('thirdpartytools',''),
                "mitigations": desc_data.get('mitigations',''),
                "mitigation_control": desc_data.get('mitigationcontrol',''),
                "responsibility": desc_data.get('responsibility',''),
                "ia_controls": desc_data.get('iacontrols',''),
                "legacy_ids": [],
                "ccis": ccis,
                "reference_identifier": ref_id,
                "uuid": str(uuid.uuid4()),
                "stig_uuid": stig_uuid,
                "status": "not_reviewed",
                "overrides": {},
                "comments": "",
                "finding_details": ""
            }
            rules.append(rule)

        return rules
    
    def build_cklb(self, tree: ET.ElementTree, input_file: str) -> Dict:
        """
        Build complete CKLB structure from XCCDF XML.
        
        Args:
            tree: Parsed XML tree
            input_file: Input XML file path
            
        Returns:
            Complete CKLB data dictionary
        """
        stig_name, stig_id, release_info, stig_version = self.parse_benchmark(tree)
        stig_uuid = str(uuid.uuid4())
        rules = self.parse_rules(tree, input_file, stig_uuid)
        ref_id = rules[0]['reference_identifier'] if rules else None
        
        stig_obj = {
            "evaluate-stig": {
                "time": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
                "module": {"name": "cklb_generator", "version": self.config.VERSION}
            },
            "stig_name": stig_name,
            "display_name": stig_name.replace("Security Technical Implementation Guide","STIG"),
            "stig_id": stig_id,
            "release_info": release_info,
            "version": stig_version,
            "uuid": stig_uuid,
            "size": len(rules),
            "reference_identifier": ref_id,
            "rules": rules
        }
        
        cklb = {
            "evaluate-stig": {"version": "1.0"},
            "title": stig_name,
            "id": str(uuid.uuid4()),
            "stigs": [stig_obj],
            "active": True,
            "mode": 2,
            "has_path": False,
            "target_data": {
                "target_type": "host",
                "host_name": "",
                "ip_address": "", 
                "mac_address": "",
                "fqdn": "",
                "comments": "",
                "role": "",  
                "is_web_database": False,
                "technology_area": "",
                "web_db_site": "",
                "web_db_instance": ""
            },
            "cklb_version": "1.0"
        }
        
        return cklb
    
    def generate_cklb_from_xml(self, input_xml: Union[str, Path]) -> Dict:
        """
        Generate CKLB JSON from XCCDF XML file.
        
        Args:
            input_xml: Path to input XCCDF XML file
            
        Returns:
            CKLB data dictionary
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ET.ParseError: If XML is invalid
        """
        input_xml = Path(input_xml)
        
        if not input_xml.exists():
            raise FileNotFoundError(f"Input XML file not found: {input_xml}")
        
        try:
            tree = ET.parse(input_xml)
            return self.build_cklb(tree, str(input_xml))
        except ET.ParseError as e:
            logger.error(f"Invalid XML in {input_xml}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating CKLB from {input_xml}: {e}")
            raise
    
    def save_cklb_to_file(self, cklb_data: Dict, output_path: Union[str, Path]) -> Path:
        """
        Save CKLB data to file.
        
        Args:
            cklb_data: CKLB data dictionary
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        return self.file_utils.safe_json_save(cklb_data, output_path)
    
    def convert_xml_to_cklb(
        self, 
        input_xml: Union[str, Path], 
        output_cklb: Union[str, Path]
    ) -> Path:
        """
        Convert XCCDF XML to CKLB JSON file.
        
        Args:
            input_xml: Path to input XCCDF XML file
            output_cklb: Path for output CKLB file
            
        Returns:
            Path to generated CKLB file
        """
        cklb_data = self.generate_cklb_from_xml(input_xml)
        output_path = self.save_cklb_to_file(cklb_data, output_cklb)
        
        logger.info(f"Generated CKLB file: {output_path}")
        return output_path
    
    def extract_xccdf_from_zip(self, zip_path: Union[str, Path]) -> Optional[Path]:
        """
        Extract XCCDF file from ZIP archive.
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Path to extracted XCCDF file, or None if not found
        """
        zip_path = Path(zip_path)
        
        if not zip_path.exists():
            logger.error(f"ZIP file not found: {zip_path}")
            return None
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Look for XCCDF files
                xccdf_files = [
                    name for name in zip_file.namelist()
                    if name.lower().endswith('-xccdf.xml') or 
                       name.lower().endswith('_xccdf.xml') or
                       (name.lower().endswith('.xml') and 'xccdf' in name.lower())
                ]
                
                if not xccdf_files:
                    logger.warning(f"No XCCDF files found in {zip_path}")
                    return None
                
                # Use the first XCCDF file found
                xccdf_name = xccdf_files[0]
                
                # Extract to temporary directory
                temp_dir = Path(tempfile.mkdtemp())
                extracted_path = temp_dir / Path(xccdf_name).name
                
                with zip_file.open(xccdf_name) as source:
                    with open(extracted_path, 'wb') as target:
                        target.write(source.read())
                
                logger.info(f"Extracted XCCDF: {extracted_path}")
                return extracted_path
                
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {zip_path}")
            return None
        except Exception as e:
            logger.error(f"Error extracting XCCDF from {zip_path}: {e}")
            return None
    
    def convert_zip_to_cklb(
        self, 
        zip_path: Union[str, Path], 
        output_dir: Union[str, Path]
    ) -> List[Tuple[Optional[Path], Optional[str]]]:
        """
        Convert ZIP file containing XCCDF to CKLB.
        
        Args:
            zip_path: Path to ZIP file
            output_dir: Output directory for CKLB files
            
        Returns:
            List of (cklb_path, error_message) tuples
        """
        zip_path = Path(zip_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        try:
            # Extract XCCDF from ZIP
            xccdf_path = self.extract_xccdf_from_zip(zip_path)
            if not xccdf_path:
                results.append((None, f"No XCCDF file found in {zip_path.name}"))
                return results
            
            # Generate CKLB filename
            cklb_name = zip_path.stem + ".cklb"
            cklb_path = output_dir / cklb_name
            
            # Convert XCCDF to CKLB
            final_path = self.convert_xml_to_cklb(xccdf_path, cklb_path)
            results.append((final_path, None))
            
            # Clean up temporary XCCDF file
            try:
                xccdf_path.unlink()
                xccdf_path.parent.rmdir()
            except Exception:
                pass  # Ignore cleanup errors
            
        except Exception as e:
            error_msg = f"Error converting {zip_path.name}: {e}"
            logger.error(error_msg)
            results.append((None, error_msg))
        
        return results


# Convenience functions for backward compatibility
def generate_cklb_json(input_file: str) -> Dict:
    """Generate CKLB JSON from XCCDF XML file using default generator."""
    generator = CKLBGenerator()
    return generator.generate_cklb_from_xml(input_file)

def convert_xccdf_zip_to_cklb(zip_path: str, output_dir: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """Convert ZIP to CKLB using default generator."""
    generator = CKLBGenerator()
    results = generator.convert_zip_to_cklb(zip_path, output_dir)
    # Convert Path objects to strings for backward compatibility
    return [(str(path) if path else None, error) for path, error in results]
