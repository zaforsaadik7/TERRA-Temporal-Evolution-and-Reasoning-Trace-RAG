"""
scripts/apply_w1_updates.py - Apply Task W1 Benchmark Updates
============================================================
Rules:
- R5: Back up data/obscure_overruled_benchmark.json to data/backup/<binary sha256>.json.
      Log field-level diff before overwriting.
- R3: Contiguous substring assertions.
"""

import json
import shutil
import hashlib
from pathlib import Path

ROOT = Path(".")
BENCH_PATH = ROOT / "data" / "obscure_overruled_benchmark.json"
BACKUP_DIR = ROOT / "data" / "backup"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
DIFF_LOG = ROOT / "logs" / "benchmark_update_diff_W1.txt"

# 1. Compute binary hash of current benchmark and back up
with open(BENCH_PATH, "rb") as f:
    orig_bytes = f.read()
orig_hash = hashlib.sha256(orig_bytes).hexdigest()

backup_path = BACKUP_DIR / f"{orig_hash}.json"
shutil.copyfile(BENCH_PATH, backup_path)
print(f"[W1 BACKUP] Backed up benchmark to {backup_path}")

# Load benchmark
bench = json.loads(orig_bytes.decode("utf-8"))

# Load raw CAP text for 340_0602-01 to verify slice
cap_path = ROOT / "dataset_20k_cap" / "raw_cases" / "340_0602-01.json"
with open(cap_path, "r", encoding="utf-8") as f:
    cap_data = json.load(f)
raw_text = cap_data["casebody"]["opinions"][0]["text"]

new_target_slice = raw_text[9903:10197]

# Verify against logs/candidates_V3.txt
with open(ROOT / "logs" / "candidates_V3.txt", "r", encoding="utf-8") as f:
    cand_v3_text = f.read()

s75 = "This Court heretofore has struck down, under the Commerce Clause, state taxes upon the privilege of carrying on a business that was exclusively interstate in character."
s76 = "The constitutional infirmity of such a tax persists no matter how fairly it is apportioned to business done within the state."
assert s75 in cand_v3_text, "Sentence #75 missing from candidates_V3.txt"
assert s76 in cand_v3_text, "Sentence #76 missing from candidates_V3.txt"
assert new_target_slice == f"{s75} {s76}", "Slice 9903:10197 does not equal sentences #75 + #76"
print("[W1 ASSERTION] Slice 9903:10197 successfully asserted equal to sentences #75-#76 in candidates_V3.txt")

# Prepare diff log
diff_lines = []
diff_lines.append("=" * 80)
diff_lines.append("FIELD-LEVEL DIFF: TASK W1 BENCHMARK UPDATE")
diff_lines.append(f"Pre-update Binary SHA256: {orig_hash}")
diff_lines.append("=" * 80)
diff_lines.append("")

# Apply updates
for item in bench:
    qid = item["query_id"]
    
    if qid == "OBS_029":
        old_gh = item["grounding_target_holding"]
        diff_lines.append("[OBS_029] Spector Motor Service, Inc. v. O'Connor")
        diff_lines.append("  Field: grounding_target_holding")
        diff_lines.append(f"  OLD char_start: {old_gh.get('char_start')}")
        diff_lines.append(f"  NEW char_start: 9903")
        diff_lines.append(f"  OLD char_end:   {old_gh.get('char_end')}")
        diff_lines.append(f"  NEW char_end:   10197")
        diff_lines.append(f"  OLD char_length:{old_gh.get('char_length')}")
        diff_lines.append(f"  NEW char_length:294")
        diff_lines.append(f"  OLD sentence:   {repr(old_gh.get('sentence'))}")
        diff_lines.append(f"  NEW sentence:   {repr(new_target_slice)}")
        diff_lines.append("")
        
        item["grounding_target_holding"] = {
            "sentence": new_target_slice,
            "char_start": 9903,
            "char_end": 10197,
            "char_length": 294,
            "slice_equality_asserted": True
        }
        
    elif qid == "OBS_016":
        old_gold = item["gold_holding"]
        new_gold = "Under Paoli v. United States, admitting a co-defendant's confession that implicates the defendant at a joint trial, with a clear jury instruction limiting its use to the confessor, is not reversible error."
        diff_lines.append("[OBS_016] Paoli v. United States")
        diff_lines.append("  Field: gold_holding")
        diff_lines.append(f"  OLD gold_holding: {repr(old_gold)}")
        diff_lines.append(f"  NEW gold_holding: {repr(new_gold)}")
        diff_lines.append("")
        
        item["gold_holding"] = new_gold

# Write updated benchmark
new_bench_bytes = json.dumps(bench, indent=2, ensure_ascii=False).encode("utf-8")
new_hash = hashlib.sha256(new_bench_bytes).hexdigest()

with open(BENCH_PATH, "wb") as f:
    f.write(new_bench_bytes)

diff_lines.append("=" * 80)
diff_lines.append(f"Post-update Binary SHA256: {new_hash}")
diff_lines.append("=" * 80)

DIFF_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(DIFF_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(diff_lines) + "\n")

print(f"[W1 COMPLETE] Post-update SHA256: {new_hash}")
print(f"[W1 LOG] Wrote diff to {DIFF_LOG}")
