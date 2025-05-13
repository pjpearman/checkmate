#!/usr/bin/env python3
"""
generate_cklb.py: Convert an XCCDF STIG XML into a CKLB JSON file for eMASS ingestion.
"""
import argparse
import os
import uuid
import json
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Namespace mapping for XCCDF 1.1
NS = {'xccdf': 'http://checklists.nist.gov/xccdf/1.1'}

def parse_benchmark(tree):

    root = tree.getroot()
    stig_name = root.find('xccdf:title', NS).text or ""
    stig_id = root.get('id') or ""
    release_info = root.find("xccdf:plain-text[@id='release-info']", NS).text or ""
    stig_version = root.find('xccdf:version', NS).text or ""
    return stig_name, stig_id, release_info, stig_version

def parse_rules(tree, input_file, stig_uuid):
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

        # group metadata
        group_title = grp.find('xccdf:title', NS).text or ""
        group_desc = grp.find('xccdf:description', NS).text or ""

        # description sections
        desc_elem = rule_elem.find('xccdf:description', NS)
        desc_data = {}
        for sec in ['VulnDiscussion','FalsePositives','FalseNegatives','Documentable',
                    'SeverityOverrideGuidance','PotentialImpacts','ThirdPartyTools',
                    'Mitigations','MitigationControl','Responsibility','IAControls']:
            node = desc_elem.find(f'xccdf:{sec}', NS) if desc_elem is not None else None
            desc_data[sec.lower()] = node.text or "" if node is not None else ""

        # extract fix text: handle both nested and flat
        fix_text = ""
        fix_elem = rule_elem.find('xccdf:fix/xccdf:fixtext', NS)
        if fix_elem is None:
            fix_elem = rule_elem.find('xccdf:fixtext', NS)
        if fix_elem is not None and fix_elem.text:
            fix_text = fix_elem.text.strip()

        # check content
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

        # identifiers (CCI)
        ccis = [ident.text for ident in rule_elem.findall("xccdf:ident[@system='http://cyber.mil/cci']", NS)]
        ref_id = ccis[0] if ccis else None

        # assemble rule
        r = {
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
            "discussion": desc_data.get('vulndiscussion',''),
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
        rules.append(r)

    return rules

def build_cklb(tree, input_file):
    stig_name, stig_id, release_info, stig_version = parse_benchmark(tree)
    stig_uuid = str(uuid.uuid4())
    rules = parse_rules(tree, input_file, stig_uuid)
    ref_id = rules[0]['reference_identifier'] if rules else None
    stig_obj = {
        "evaluate-stig": {"time": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
                           "module": {"name": "cklb_generator", "version": "1.1"}},
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
    cklb = {"evaluate-stig": {"version": "1.0"},
            "title": stig_name,
            "id": str(uuid.uuid4()),
            "stigs": [stig_obj],
            "active": True,
            "mode": 2,
            "has_path": False,
            "target_data": {"target_type": "host","host_name": "","ip_address": "", 
                             "mac_address": "","fqdn": "","comments": "","role": "",  
                             "is_web_database": False,"technology_area": "","web_db_site": "","web_db_instance": ""},
            "cklb_version": "1.0"}
    return cklb

def generate_cklb_json(input_file):
    tree = ET.parse(input_file)
    cklb = build_cklb(tree, input_file)
    return cklb

def main():
    parser = argparse.ArgumentParser(description="Generate a CKLB JSON file from an XCCDF STIG XML")
    parser.add_argument('input_xml', help='Path to the XCCDF XML input')
    parser.add_argument('output_cklb', help='Path for the generated CKLB JSON')
    args = parser.parse_args()
    if not os.path.isfile(args.input_xml):
        print(f"Input file not found: {args.input_xml}")
        exit(1)
    tree = ET.parse(args.input_xml)
    cklb = build_cklb(tree, args.input_xml)
    with open(args.output_cklb,'w') as f:
        json.dump(cklb,f,indent=2)
    print(f"Generated CKLB file: {args.output_cklb}")

if __name__ == '__main__':
    main()
