import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

BEFORE_HASH_FILE = LOGS_DIR / "protected_hashes_before.txt"
AFTER_HASH_FILE = LOGS_DIR / "protected_hashes_after.txt"
HASH_COMPARE_FILE = LOGS_DIR / "hash_compare.txt"
CHECKSUMS_FILE = ROOT / "scratch" / "substrate_checksums.sha256"
MANIFEST_AUDIT_FILE = LOGS_DIR / "manifest_char_count_audit.txt"

# 1. Compute protected_hashes_after.txt
print("[T6] Computing protected_hashes_after.txt...")
files_to_hash = [
    ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json",
    ROOT / "dataset_20k_cap" / "vector_db_20k" / "chroma.sqlite3",
    ROOT / "terra_350_benchmark.json",
    ROOT / "terra_baselines_eval_raw.json",
]

raw_cases_dir = ROOT / "dataset_20k_cap" / "raw_cases"
if raw_cases_dir.exists():
    for p in sorted(raw_cases_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".json":
            files_to_hash.append(p)

after_lines = []
for file_path in files_to_hash:
    rel_path = file_path.relative_to(ROOT).as_posix()
    if not file_path.exists():
        after_lines.append(f"MISSING  {rel_path}")
        continue
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    after_lines.append(f"{h.hexdigest()}  {rel_path}")

with open(AFTER_HASH_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(after_lines) + "\n")
print(f"[T6] Wrote {len(after_lines)} hashes to {AFTER_HASH_FILE}")

# 2. Compare before vs after
print("[T6] Comparing before vs after protected hashes...")
before_dict = {}
if BEFORE_HASH_FILE.exists():
    with open(BEFORE_HASH_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("  ", 1)
            if len(parts) == 2:
                before_dict[parts[1]] = parts[0]

after_dict = {}
with open(AFTER_HASH_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) == 2:
            after_dict[parts[1]] = parts[0]

# Substrate checksums
substrate_dict = {}
if CHECKSUMS_FILE.exists():
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("  ", 1)
            if len(parts) == 2:
                substrate_dict[parts[1]] = parts[0]

compare_lines = []
compare_lines.append("=" * 100)
compare_lines.append("T6 HASH COMPARE: BEFORE VS AFTER (AND SUBSTRATE CHECKSUMS)")
compare_lines.append("=" * 100)

all_keys = sorted(set(before_dict.keys()) | set(after_dict.keys()))
diff_count = 0
match_count = 0

for k in all_keys:
    h_before = before_dict.get(k, "NOT_IN_BEFORE")
    h_after = after_dict.get(k, "NOT_IN_AFTER")
    status = "MATCH" if h_before == h_after else "DIFFERENT"
    if status == "MATCH":
        match_count += 1
    else:
        diff_count += 1
    compare_lines.append(f"{status:<9} | {k} | before: {h_before[:16]} | after: {h_after[:16]}")

compare_lines.append("-" * 100)
compare_lines.append(f"TOTAL FILES COMPARED: {len(all_keys)}")
compare_lines.append(f"MATCH: {match_count}")
compare_lines.append(f"DIFFERENT: {diff_count}")
compare_lines.append("=" * 100)

# Substrate checksums comparison block
compare_lines.append("\n" * 2 + "=" * 100)
compare_lines.append("SUBSTRATE CHECKSUMS (scratch/substrate_checksums.sha256) COMPARISON")
compare_lines.append("=" * 100)
for sub_path, sub_hash in substrate_dict.items():
    current_hash = after_dict.get(sub_path, "NOT_FOUND")
    sub_status = "MATCH" if sub_hash == current_hash else "DIFFERENT"
    compare_lines.append(f"{sub_status:<9} | {sub_path} | substrate: {sub_hash} | current: {current_hash}")
compare_lines.append("=" * 100)

with open(HASH_COMPARE_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(compare_lines) + "\n")
print(f"[T6] Wrote hash comparison to {HASH_COMPARE_FILE}")

# 3. Selection Manifest char_count comparison
print("[T6] Auditing selection_manifest_20k.json char_count vs len(opinions[0].text)...")
manifest_path = ROOT / "dataset_20k_cap" / "manifests" / "selection_manifest_20k.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest_items = json.load(f)

matched_char_count = 0
mismatched_char_count = 0
missing_raw_files = 0
mismatch_details = []

for idx, item in enumerate(manifest_items):
    vol = item.get("volume")
    fname = item.get("file_name", "")
    if not fname.endswith(".json"):
        raw_filename = f"{vol}_{fname}.json"
    else:
        raw_filename = f"{vol}_{fname}"
    
    raw_path = raw_cases_dir / raw_filename
    manifest_cc = item.get("char_count")
    
    if not raw_path.exists():
        missing_raw_files += 1
        mismatched_char_count += 1
        mismatch_details.append(f"{raw_filename} | MISSING_RAW_FILE | manifest_char_count: {manifest_cc} | opinion_len: N/A")
        continue
    
    try:
        with open(raw_path, "r", encoding="utf-8") as rf:
            raw_data = json.load(rf)
        casebody = raw_data.get("casebody", {})
        opinions = casebody.get("opinions", [])
        if opinions and len(opinions) > 0:
            op_text = opinions[0].get("text", "") or ""
            op_len = len(op_text)
        else:
            op_len = 0
            
        if manifest_cc == op_len:
            matched_char_count += 1
        else:
            mismatched_char_count += 1
            delta = op_len - manifest_cc if manifest_cc is not None else 0
            mismatch_details.append(
                f"{raw_filename} | manifest_char_count: {manifest_cc} | opinion_0_text_len: {op_len} | delta: {delta}"
            )
    except Exception as e:
        mismatched_char_count += 1
        mismatch_details.append(f"{raw_filename} | ERROR_READING: {e}")

manifest_log_lines = []
manifest_log_lines.append("=" * 100)
manifest_log_lines.append("T6 MANIFEST AUDIT: selection_manifest_20k.json char_count vs len(opinions[0].text)")
manifest_log_lines.append("=" * 100)
manifest_log_lines.append(f"Total manifest records: {len(manifest_items)}")
manifest_log_lines.append(f"Matched char_count == len(opinions[0].text): {matched_char_count}")
manifest_log_lines.append(f"Mismatched: {mismatched_char_count}")
manifest_log_lines.append(f"Missing raw files: {missing_raw_files}")
manifest_log_lines.append("=" * 100)
manifest_log_lines.append("MISMATCH DETAILS (Every Mismatch):")
manifest_log_lines.append("-" * 100)
manifest_log_lines.extend(mismatch_details)
manifest_log_lines.append("=" * 100)

with open(MANIFEST_AUDIT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(manifest_log_lines) + "\n")

print(f"[T6] Manifest audit completed. Matched: {matched_char_count}, Mismatched: {mismatched_char_count}")
print(f"[T6] Wrote manifest audit log to {MANIFEST_AUDIT_FILE}")
