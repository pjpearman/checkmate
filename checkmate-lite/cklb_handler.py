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
    Warns if the STIGs are obviously mismatched (e.g., Redhat vs Windows).
    """
    def load_cklb(path):
        with open(path, 'r') as f:
            return json.load(f)
    def get_rules(cklb):
        # Try to get rules from common keys
        for key in ['rules', 'Rules', 'stig_rules', 'stigRules']:
            if key in cklb:
                return cklb[key]
        # Fallback: try to find a list of dicts
        for v in cklb.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'rule_id' in v[0]:
                return v
        return []
    def rule_key(rule):
        return rule.get('rule_id') or rule.get('id') or rule.get('Rule_ID')
    def findings_key(rule):
        # Use status or finding fields
        return rule.get('status') or rule.get('finding') or rule.get('Finding')
    def get_stig_name(cklb):
        # Try common keys for STIG name
        for k in ['stig_name', 'title', 'display_name']:
            if k in cklb:
                return cklb[k]
        # Try nested
        if 'stigs' in cklb and cklb['stigs'] and isinstance(cklb['stigs'], list):
            s = cklb['stigs'][0]
            for k in ['stig_name', 'title', 'display_name']:
                if k in s:
                    return s[k]
        return None
    # Load B
    cklb_b = load_cklb(file_b)
    stig_b = get_stig_name(cklb_b)
    rules_b = {rule_key(r): r for r in get_rules(cklb_b)}
    output = []
    for file_a in file_a_list:
        if not file_a.endswith('.cklb') or not file_b.endswith('.cklb'):
            output.append(f"[ERROR] Only .cklb files are supported: {os.path.basename(file_a)} or {os.path.basename(file_b)}")
            continue
        cklb_a = load_cklb(file_a)
        stig_a = get_stig_name(cklb_a)
        # Error handling for mismatched STIGs
        if stig_a and stig_b and stig_a != stig_b:
            # Heuristic: warn if the main product/OS is different
            def main_tag(name):
                if not name:
                    return ''
                name = name.lower()
                for tag in ['windows', 'redhat', 'rhel', 'ubuntu', 'apache', 'sql', 'oracle', 'linux', 'unix', 'forest', 'site', 'server', 'client']:
                    if tag in name:
                        return tag
                return name.split()[0] if name.split() else name
            tag_a = main_tag(stig_a)
            tag_b = main_tag(stig_b)
            if tag_a != tag_b:
                output.append(f"[WARNING] Mismatched STIGs: '{stig_a}' vs '{stig_b}'.\nAre you sure you want to compare these? (Press 'y' to continue, any other key to cancel)")
                print(f"[WARNING] Mismatched STIGs: '{stig_a}' vs '{stig_b}'.")
                import sys
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                if ch.lower() != 'y':
                    output.append("Comparison cancelled by user.")
                    continue
        rules_a = {rule_key(r): r for r in get_rules(cklb_a)}
        output.append(f"=== Comparing {os.path.basename(file_a)} to {os.path.basename(file_b)} ===\n")
        all_rule_ids = set(rules_a.keys()) | set(rules_b.keys())
        for rid in sorted(all_rule_ids):
            ra = rules_a.get(rid)
            rb = rules_b.get(rid)
            if ra and not rb:
                output.append(f"[ONLY IN A] Rule {rid}")
            elif rb and not ra:
                output.append(f"[ONLY IN B] Rule {rid}")
            elif ra and rb:
                # Compare findings/status, ignore comments
                finding_a = findings_key(ra)
                finding_b = findings_key(rb)
                if finding_a != finding_b:
                    output.append(f"[DIFF] Rule {rid}:\n  A: {finding_a}\n  B: {finding_b}")
        output.append("")
    return '\n'.join(output)
