import os
import shutil
import json

def import_cklbs(selected_files, dest_dir=None):
    """
    Import one or more CKLB files into the specified destination directory.
    If dest_dir is None, defaults to 'user_docs/cklb_artifacts'.
    Returns a list of (filename, status) tuples.
    """
    if dest_dir is None:
        dest_dir = os.path.join("user_docs", "cklb_artifacts")
    os.makedirs(dest_dir, exist_ok=True)
    results = []
    for file_path in selected_files:
        if not os.path.isfile(file_path):
            results.append((file_path, "File not found"))
            continue
        dest_path = os.path.join(dest_dir, os.path.basename(file_path))
        try:
            shutil.copy2(file_path, dest_path)
            results.append((file_path, "Imported"))
        except Exception as e:
            results.append((file_path, f"Error: {e}"))
    return results

def compare_cklb_versions(file_a_list, file_b):
    """
    Compare one or more CKLB files (A) to a second CKLB file (B).
    Returns a string with highlighted rule and finding differences.
    Ignores comment differences. Only .cklb files are allowed.
    Warns if the STIGs are obviously mismatched (e.g., Redhat vs Windows), using 'stig_id' as the primary property.
    """
    import os
    import json
    def load_cklb(path):
        with open(path, 'r') as f:
            return json.load(f)
    def get_rules(cklb):
        # Try to get rules from common keys
        if 'stigs' in cklb and isinstance(cklb['stigs'], list) and cklb['stigs']:
            stig = cklb['stigs'][0]
            return stig.get('rules', [])
        for key in ['rules', 'Rules', 'stig_rules', 'stigRules']:
            if key in cklb:
                return cklb[key]
        for v in cklb.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'rule_id' in v[0]:
                return v
        return []
    def rule_key(rule):
        # Extract only the SV-xxxxxx prefix (before any 'r' or non-digit after SV-)
        import re
        val = rule.get('rule_id') or rule.get('id') or rule.get('Rule_ID')
        if val:
            m = re.match(r'(SV-\d+)', val)
            if m:
                return m.group(1)
        return val
    def findings_key(rule):
        return rule.get('status') or rule.get('finding') or rule.get('Finding')
    def get_stig_id(cklb):
        # Use 'stig_id' as primary property
        if 'stigs' in cklb and isinstance(cklb['stigs'], list) and cklb['stigs']:
            stig = cklb['stigs'][0]
            return stig.get('stig_id')
        return cklb.get('stig_id')
    # Load B
    cklb_b = load_cklb(file_b)
    stig_b = get_stig_id(cklb_b)
    rules_b_list = get_rules(cklb_b)
    rules_b = {rule_key(r): r for r in rules_b_list}
    output = []
    for file_a in file_a_list:
        if not file_a.endswith('.cklb') or not file_b.endswith('.cklb'):
            output.append(f"[ERROR] Only .cklb files are supported: {os.path.basename(file_a)} or {os.path.basename(file_b)}")
            continue
        cklb_a = load_cklb(file_a)
        stig_a = get_stig_id(cklb_a)
        if stig_a and stig_b and stig_a != stig_b:
            output.append(f"[ERROR] Mismatched STIG IDs: '{stig_a}' vs '{stig_b}'. Comparison cancelled.")
            continue
        rules_a = {rule_key(r): r for r in get_rules(cklb_a)}
        output.append(f"=== Comparing {os.path.basename(file_a)} to {os.path.basename(file_b)} ===\n")
        all_rule_ids = set(rules_a.keys()) | set(rules_b.keys())
        # Find rules in B but not in A
        new_in_b = [rid for rid in rules_b.keys() if rid not in rules_a]
        if new_in_b:
            output.append(f"New rules in {os.path.basename(file_b)} (not in {os.path.basename(file_a)}):")
            output.append(f"{'id':<16} {'rule title'}")
            output.append(f"{'-'*16} {'-'*40}")
            for rid in new_in_b:
                rule = rules_b[rid]
                title = rule.get('rule_title') or rule.get('title') or ''
                output.append(f"{rid:<16} {title}")
            output.append("")
        # Only show rules unique to A or B, not status diffs
        for rid in sorted(all_rule_ids):
            ra = rules_a.get(rid)
            rb = rules_b.get(rid)
            if ra and not rb:
                output.append(f"[ONLY IN A] Rule {rid}")
            elif rb and not ra:
                # Already handled above as new_in_b
                continue
        output.append("")
    return '\n'.join(output)
