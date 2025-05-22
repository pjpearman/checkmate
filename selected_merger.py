import json
import argparse
import sys
from copy import deepcopy
import os

def find_new_rules(old_data, new_data):
    """Return a list of new rule dicts (group_id_src, rule_title, stig uuid, stig display_name)."""
    old_gids = {rule.get("group_id_src") for stig in old_data.get("stigs", []) for rule in stig.get("rules", [])}
    new_rules = []
    for stig in new_data.get("stigs", []):
        for rule in stig.get("rules", []):
            gid = rule.get("group_id_src")
            if gid not in old_gids:
                new_rules.append({
                    "group_id_src": gid,
                    "rule_title": rule.get("rule_title", ""),
                    "stig_uuid": stig.get("uuid"),
                    "stig_display": stig.get("display_name"),
                })
    return new_rules

def check_stig_id_match(old_data, new_data):
    """Return (is_match, old_stig_id, new_stig_id, new_rules)"""
    old_stig_id = old_data.get("stigs", [{}])[0].get("stig_id", "UNKNOWN") if old_data.get("stigs") else "UNKNOWN"
    new_stig_id = new_data.get("stigs", [{}])[0].get("stig_id", "UNKNOWN") if new_data.get("stigs") else "UNKNOWN"
    new_rules = find_new_rules(old_data, new_data)
    return old_stig_id == new_stig_id, old_stig_id, new_stig_id, new_rules

def load_cklb(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cklb(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Merge old CKLB data into new CKLB file")
    parser.add_argument("old_cklb", help="Path to old CKLB (JSON)")
    parser.add_argument("new_cklb", help="Path to new CKLB (JSON)")
    parser.add_argument("-o", "--output", default="merged.cklb", help="Output path for merged CKLB")
    parser.add_argument("--force", action="store_true", help="Proceed even if STIG IDs do not match")
    parser.add_argument("--prefix", help="Manual host‐name prefix (overrides target_data.host_name)")
    args = parser.parse_args()

    old_data = load_cklb(args.old_cklb)
    new_data = load_cklb(args.new_cklb)

    is_match, old_stig_id, new_stig_id, new_rules = check_stig_id_match(old_data, new_data)
    if not is_match and not args.force:
        msg = ("STIG ID mismatch. Old: {} New: {}. New rules: {}. "
               "Use --force to override.").format(old_stig_id, new_stig_id, len(new_rules))
        print(f"ERROR: {msg}")
        sys.exit(2)

    old_lookup = {}
    for stig in old_data.get("stigs", []):
        for rule in stig.get("rules", []):
            gid = rule.get("group_id_src")
            if gid:
                old_lookup[gid] = rule

    merged = deepcopy(new_data)
    updated, added = 0, []

    for stig in merged.get("stigs", []):
        for rule in stig.get("rules", []):
            gid = rule.get("group_id_src")
            if gid in old_lookup:
                old = old_lookup[gid]
                rule["status"] = old.get("status", rule.get("status"))
                rule["comments"] = old.get("comments", rule.get("comments"))
                rule["finding_details"] = old.get("finding_details", rule.get("finding_details"))
                if "evaluate-stig" in rule and "evaluate-stig" in old:
                    rule["evaluate-stig"]["old_status"] = old["evaluate-stig"].get("old_status", "")
                    rule["evaluate-stig"]["new_status"] = old["evaluate-stig"].get("new_status", "")
                updated += 1
            else:
                added.append((gid, rule.get("rule_title", "UNKNOWN TITLE")))

    # Preserve host metadata and versioning
    if "target_data" in old_data:
        merged["target_data"] = old_data["target_data"]
    if "cklb_version" in old_data:
        merged["cklb_version"] = old_data["cklb_version"]

    # Remove invalid top-level fields
    merged.pop("evaluate-stig", None)

    # Determine host_prefix for output naming
    host_prefix = args.prefix or old_data.get("target_data", {}).get("host_name")
    if not host_prefix:
        host_prefix = os.path.splitext(os.path.basename(args.old_cklb))[0]
        print(f"WARNING: No host_name found – defaulting to '{host_prefix}'")
    # Guarantee uniqueness in output directory
    out_dir = os.path.dirname(os.path.abspath(args.output))
    new_name = os.path.basename(args.new_cklb)
    base = f"{host_prefix}_{new_name}"
    out_name = base
    counter = 1
    while os.path.exists(os.path.join(out_dir, out_name)):
        out_name = f"{base}_{counter}"
        counter += 1
    merged_output_path = os.path.join(out_dir, out_name)

    save_cklb(merged_output_path, merged)

    print(f"Merged {updated} rules from old checklist.")
    print(f"Output: {merged_output_path}")
    if added:
        print("New rules in the updated checklist:")
        for gid, title in added:
            print(f"  {gid}: {title}")

if __name__ == "__main__":
    main()
