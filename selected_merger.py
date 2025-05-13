#test bug fix for selected merger eval-stig prop
import json
import argparse
from copy import deepcopy

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
    args = parser.parse_args()

    old_data = load_cklb(args.old_cklb)
    new_data = load_cklb(args.new_cklb)

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

    save_cklb(args.output, merged)

    print(f"Merged {updated} rules from old checklist.")
    if added:
        print("New rules in the updated checklist:")
        for gid, title in added:
            print(f"  {gid}: {title}")

if __name__ == "__main__":
    main()
