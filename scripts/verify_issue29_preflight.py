import os
import hashlib
import json
import re
import glob
from pathlib import Path

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

PROTECTED_SUBSTRATES = {
    "terra_350_benchmark.json": "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3",
    "dataset_20k_cap/terra_eeg_index_20k.json": "7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json": "c530f9858e9b3372dc9079092178e9d8c2239758eda073c35b9fc7b0c49e1f72",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json": "14071dba780157b767dfce1f11ef8190722ad94ab9a37e8258bb574a0183c3fc",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json": "98d14bfb75d5051429ff4c48c0410300efb5ef7f04112701635f110aff094ddf",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json": "5e2b59ac3fce2b9513c9ceb60b6a1cae0c2323150f4936a0410503fd56689f3c",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json": "606a6ec126bf7c5ac4cbdbac04f37eee52f7bd524d35e5f12d8dc4ebff3e23b5",
    "ask_terra.py": "430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd",
    "data/issue21_preflight.json": "9a26a9e35340111773180cadd9f3c271fcecde1a3863609d6abbd2236ba7a9b2",
    "logs/issue21_preflight.txt": "91d028cd9ce5079d16bf540cba6546bfa825e5688b3283eb5ef226cc8a3d84d8",
    "ask_terra_pre_issue13_backup.py": "bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9"
}

FROZEN_ARCHIVES = {
    "Paper/prev_main.tex": "f2491d5ed857639e983e71582811a4f85a76ebaeb516fa029fdb5fce3ca9bcc4",
    "ask_terra_pre_issue13_backup.py": "bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9"
}

# Explicit six required patterns (plus singular/plural variants)
TARGET_PATTERNS = [
    "Thinking Trace",
    "thinking trace",
    "Cognitive Trajectory",
    "cognitive reasoning trajectory",
    "chain-of-thought",
    "CoT"
]

REGEX_PATTERNS = [
    ("Thinking Trace / thinking trace", re.compile(r'thinking\s+trace\w*', re.IGNORECASE)),
    ("Cognitive Trajectory / cognitive reasoning trajectory", re.compile(r'cognitive\s+(?:reasoning\s+)?trajector\w*', re.IGNORECASE)),
    ("chain-of-thought", re.compile(r'chain[\s-]of[\s-]thought', re.IGNORECASE)),
    ("CoT", re.compile(r'\bCoT\b'))
]

def main():
    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TERRA ISSUE #29 PREFLIGHT VERIFICATION & TERMINOLOGY INFLATION AUDIT")
    log("=" * 80)

    # 1. Verify protected substrates & establish pre-edit provenance manifest
    log("\n[STEP 1/4] Verifying Protected Core Substrates & Recording Pre-Edit Hashes...")
    substrate_status = {}
    all_substrates_pass = True
    for rel_path, expected_hash in PROTECTED_SUBSTRATES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing substrate: {rel_path}")
            substrate_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_substrates_pass = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            substrate_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            substrate_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_substrates_pass = False

    if not all_substrates_pass:
        log("\n[ABORT] Protected substrates failed bit-invariance!")
        return False

    # Verify frozen archives
    log("\n[STEP 2/4] Verifying Frozen Historical Archives...")
    frozen_status = {}
    all_frozen_pass = True
    for rel_path, expected_hash in FROZEN_ARCHIVES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing frozen archive: {rel_path}")
            frozen_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_frozen_pass = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (FROZEN MATCH)")
            frozen_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            frozen_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_frozen_pass = False

    # 3. Verify checklist count dynamically
    log("\n[STEP 3/4] Verifying Master Checklist Completion Count Dynamically...")
    checklist_path = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"
    with open(checklist_path, "r", encoding="utf-8") as f:
        checklist_content = f.read()

    matches = re.findall(r'^- \[([ x])] \*\*(\d+)\.', checklist_content, flags=re.MULTILINE)
    completed_items = [num for mark, num in matches if mark == 'x']
    pending_items = [num for mark, num in matches if mark == ' ']
    total_items = len(matches)
    completed_count = len(completed_items)
    pct = (completed_count / total_items) * 100.0 if total_items > 0 else 0.0

    log(f"  Total Checklist Items: {total_items}")
    log(f"  Currently Completed:   {completed_count} / {total_items} ({pct:.1f}%)")
    log(f"  Completed IDs:         {', '.join(completed_items)}")
    log(f"  Pending IDs:           {', '.join(pending_items)}")

    # 4. Six-pattern terminology audit across all active .tex files
    log("\n[STEP 4/4] Scanning All Active Paper/**/*.tex Files Across 6 Target Patterns...")
    all_tex_files = sorted(glob.glob("Paper/**/*.tex", recursive=True))
    active_tex_files = [
        f for f in all_tex_files
        if not os.path.basename(f).startswith("prev_main")
        and not os.path.basename(f).endswith("_bak.tex")
    ]
    log(f"  Auditing {len(active_tex_files)} active .tex files...")

    pattern_hits = []
    for tex_path in active_tex_files:
        norm_path = tex_path.replace("\\", "/")
        with open(tex_path, "r", encoding="utf-8", errors="ignore") as f:
            for lno, line in enumerate(f, 1):
                line_str = line.strip()
                matched_patterns = []
                for pat in TARGET_PATTERNS:
                    if pat in line_str and pat not in matched_patterns:
                        matched_patterns.append(pat)
                for desc, reg in REGEX_PATTERNS:
                    m = reg.search(line_str)
                    if m and m.group(0) not in matched_patterns:
                        matched_patterns.append(m.group(0))

                for pat in matched_patterns:
                    is_exemption = False
                    exemption_type = None
                    if norm_path == "Paper/main.tex" and lno == 180 and "Thinking Trace:" in line_str:
                        is_exemption = True
                        exemption_type = "Equation 1 Legacy Internal Key"
                    elif norm_path == "Paper/main.tex" and "cotragintegratingchainthought" in line_str:
                        is_exemption = True
                        exemption_type = "Approved Third-Party Literature Citation"

                    hit_entry = {
                        "file": norm_path,
                        "line": lno,
                        "pattern": pat,
                        "text": line_str[:120],
                        "is_exemption": is_exemption,
                        "exemption_type": exemption_type
                    }
                    pattern_hits.append(hit_entry)
                    status_tag = f"[EXEMPTED: {exemption_type}]" if is_exemption else "[TARGET FOR REMEDIATION]"
                    log(f"  {status_tag} {norm_path}:{lno} [{pat}] -> {line_str[:90]}")

    log(f"\n  Total Pattern Hits Recorded: {len(pattern_hits)}")
    targets_for_remediation = [h for h in pattern_hits if not h["is_exemption"]]
    exempted_hits = [h for h in pattern_hits if h["is_exemption"]]
    log(f"  Exempted Hits:              {len(exempted_hits)}")
    log(f"  Targets For Phase 2 Edits:  {len(targets_for_remediation)}")

    preflight_data = {
        "status": "PASS" if all_substrates_pass and all_frozen_pass else "FAIL",
        "protected_substrates_pre_edit_manifest": substrate_status,
        "frozen_archives": frozen_status,
        "checklist": {
            "total_items": total_items,
            "completed_count": completed_count,
            "completed_pct": round(pct, 2),
            "completed_items": completed_items,
            "pending_items": pending_items
        },
        "active_tex_count": len(active_tex_files),
        "target_patterns": TARGET_PATTERNS,
        "all_pattern_hits": pattern_hits,
        "exempted_hits": exempted_hits,
        "targets_for_remediation": targets_for_remediation
    }

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with open("data/issue29_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    with open("logs/issue29_preflight.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    log("\n" + "=" * 80)
    log(f"PREFLIGHT SUMMARY: {preflight_data['status']}")
    log(f"Pre-edit hash manifest recorded in data/issue29_preflight.json")
    log("=" * 80)
    return preflight_data["status"] == "PASS"

if __name__ == "__main__":
    main()
