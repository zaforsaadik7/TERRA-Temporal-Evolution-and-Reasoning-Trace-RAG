import os
import sys
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
TARGET_HASH = "eeaf5d012420adeade0a396304b8ea09a51362576abe37fdd12fa00c26d39e7c"
CURRENT_FILE = ROOT / "data" / "obscure_overruled_benchmark.json"
STOPPED_FILE = ROOT / "logs" / "STOPPED_T1.txt"
DIFF_FILE = ROOT / "logs" / "query_diff.txt"

def get_hash(path: Path) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

print("Searching for file with hash:", TARGET_HASH)
found_file = None

# 1. Search candidate directories: data, data/backup, scratch, root .json
candidate_files = list((ROOT / "data").glob("*.json")) + \
                  list((ROOT / "data" / "backup").glob("*.json")) + \
                  list((ROOT / "scratch").glob("*.json")) + \
                  list(ROOT.glob("*.json"))

for p in candidate_files:
    if get_hash(p) == TARGET_HASH:
        found_file = p
        print(f"Found on-disk file: {p}")
        break

# 2. If not found on disk directly, check git history
if not found_file:
    try:
        git_log = subprocess.check_output(
            ["git", "log", "--all", "--name-only", "--pretty=format:%H"],
            cwd=str(ROOT), text=True, errors="replace"
        )
        commits = [line.strip() for line in git_log.splitlines() if len(line.strip()) == 40]
        for c in commits:
            try:
                blob = subprocess.check_output(
                    ["git", "show", f"{c}:data/obscure_overruled_benchmark.json"],
                    cwd=str(ROOT), text=False, stderr=subprocess.DEVNULL
                )
                h = hashlib.sha256(blob).hexdigest()
                if h == TARGET_HASH:
                    print(f"Found in git commit: {c}")
                    found_path = ROOT / "scratch" / f"bench_{TARGET_HASH[:8]}.json"
                    with open(found_path, "wb") as bf:
                        bf.write(blob)
                    found_file = found_path
                    break
            except subprocess.CalledProcessError:
                continue
    except Exception as e:
        print("Git search exception:", e)

if not found_file:
    print(f"File with hash {TARGET_HASH} not found anywhere on disk or git history.")
    with open(STOPPED_FILE, "w", encoding="utf-8") as sf:
        sf.write(f"STOPPED: No file with binary SHA-256 {TARGET_HASH} found in workspace, scratch, or git history.\n")
    sys.exit(0)

# If found, compute field-level differences against current file
current_hash = get_hash(CURRENT_FILE)
print(f"Comparing found file ({TARGET_HASH}) against current ({CURRENT_FILE} -> {current_hash})...")

with open(found_file, "r", encoding="utf-8") as f1:
    old_data = json.load(f1)
with open(CURRENT_FILE, "r", encoding="utf-8") as f2:
    new_data = json.load(f2)

old_map = {item["query_id"]: item for item in old_data}
new_map = {item["query_id"]: item for item in new_data}

all_qids = sorted(list(set(old_map.keys()) | set(new_map.keys())))

diff_lines = []
diff_lines.append("=" * 80)
diff_lines.append(f"T1 FIELD-LEVEL QUERY DIFF")
diff_lines.append(f"Reference File (SHA-256: {TARGET_HASH}): {found_file}")
diff_lines.append(f"Current File   (SHA-256: {current_hash}): {CURRENT_FILE}")
diff_lines.append("=" * 80)

total_diffs = 0

for qid in all_qids:
    if qid not in old_map:
        diff_lines.append(f"[{qid}] Added in current file.")
        total_diffs += 1
        continue
    if qid not in new_map:
        diff_lines.append(f"[{qid}] Removed from current file.")
        total_diffs += 1
        continue
    
    o_item = old_map[qid]
    n_item = new_map[qid]
    
    item_diffs = []
    all_keys = sorted(list(set(o_item.keys()) | set(n_item.keys())))
    for k in all_keys:
        ov = o_item.get(k)
        nv = n_item.get(k)
        if ov != nv:
            item_diffs.append((k, ov, nv))
            
    if item_diffs:
        diff_lines.append(f"\n--- {qid}: {n_item.get('target_case')} ({len(item_diffs)} field differences) ---")
        for k, ov, nv in item_diffs:
            total_diffs += 1
            diff_lines.append(f"  Field: {k}")
            diff_lines.append(f"    OLD ({TARGET_HASH[:8]}): {ov}")
            diff_lines.append(f"    NEW ({current_hash[:8]}): {nv}")

diff_lines.append("\n" + "=" * 80)
diff_lines.append(f"TOTAL FIELD-LEVEL DIFFERENCES FOUND: {total_diffs}")
diff_lines.append("=" * 80)

diff_text = "\n".join(diff_lines) + "\n"
with open(DIFF_FILE, "w", encoding="utf-8") as df:
    df.write(diff_text)

print(f"Wrote {total_diffs} field differences to {DIFF_FILE}")
