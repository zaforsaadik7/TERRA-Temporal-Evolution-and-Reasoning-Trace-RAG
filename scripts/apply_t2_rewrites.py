import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
BENCH_PATH = ROOT / "data" / "obscure_overruled_benchmark.json"
BACKUP_DIR = ROOT / "data" / "backup"
LOGS_DIR = ROOT / "logs"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Compute binary hash before edit
with open(BENCH_PATH, "rb") as f:
    bench_bytes = f.read()
before_hash = hashlib.sha256(bench_bytes).hexdigest()

# 2. Copy to data/backup/ named by binary hash
backup_file = BACKUP_DIR / f"{before_hash}.json"
shutil.copy2(BENCH_PATH, backup_file)
print(f"Backed up benchmark to: {backup_file}")

# 3. Exactly 7 rewrites
REWRITES = {
    "OBS_001": "Under the Supreme Court's decision in Bonelli Cattle Co. v. Arizona (1973), when a navigable river is artificially rechanneled and former riverbed is exposed as dry land, does title to the exposed land vest in the riparian upland owner under federal common law rather than in the State?",
    "OBS_011": "Under the Supreme Court's decision in Low v. Austin (1872), does the Import-Export Clause of the Constitution prohibit a state from levying an ad valorem property tax on imported goods that remain in their original unbroken packages?",
    "OBS_012": "Under the Supreme Court's decision in Forman v. United States (1960), if a court of appeals finds the evidence insufficient to sustain a conviction but the defendant had sought a new trial as an alternative remedy, does the Double Jeopardy Clause bar the court from ordering a retrial?",
    "OBS_015": "Under the Supreme Court's decision in Lustig v. United States (1949), is evidence obtained by state police officers through an unlawful search admissible in a federal criminal trial when federal officers did not participate in the search?",
    "OBS_024": "Under the Supreme Court's decision in Moore v. Illinois Central Railroad Co. (1941), must an employee first exhaust his administrative remedies under the Railway Labor Act before bringing a state-law breach of contract action for wrongful discharge?",
    "OBS_029": "Under the Supreme Court's decision in Spector Motor Service, Inc. v. O'Connor (1951), does the Commerce Clause prohibit a state from levying a franchise tax on a foreign corporation for the privilege of doing business in the state, if the corporation's business activities within the state are exclusively interstate commerce?",
    "OBS_030": "Under the Supreme Court's decision in Cohen v. Hurley (1961), may a state disbar an attorney for refusing, on Fifth Amendment grounds, to testify in a state judicial investigation of professional misconduct, consistently with the Fourteenth Amendment?"
}

bench = json.loads(bench_bytes.decode("utf-8"))

alignment_rows = []
field_diff_rows = []

for item in bench:
    qid = item["query_id"]
    if qid in REWRITES:
        old_q = item["query"]
        new_q = REWRITES[qid]
        
        gold_h = item.get("gold_holding", "")
        tgt_s = item.get("grounding_target_holding", {}).get("sentence", "")
        ovr_s = item.get("grounding_overruling_sentence", {}).get("sentence", "")
        
        alignment_rows.append(f"=== {qid} ({item.get('target_case')}) ===")
        alignment_rows.append(f"OLD QUERY:            {old_q}")
        alignment_rows.append(f"NEW QUERY:            {new_q}")
        alignment_rows.append(f"GOLD HOLDING:         {gold_h}")
        alignment_rows.append(f"TARGET SENTENCE:      {tgt_s}")
        alignment_rows.append(f"OVERRULING SENTENCE:  {ovr_s}\n")
        
        field_diff_rows.append(f"[{qid}] query modified:")
        field_diff_rows.append(f"  - OLD: {old_q}")
        field_diff_rows.append(f"  + NEW: {new_q}\n")
        
        # Apply rewrite
        item["query"] = new_q

# Save updated benchmark
with open(BENCH_PATH, "w", encoding="utf-8") as f:
    json.dump(bench, f, indent=2)

with open(BENCH_PATH, "rb") as f:
    after_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Benchmark updated. New binary SHA-256: {after_hash}")

# Write logs/benchmark_update_diff.txt
with open(LOGS_DIR / "benchmark_update_diff.txt", "w", encoding="utf-8") as f:
    f.write(f"BENCHMARK UPDATE FIELD-LEVEL DIFF (Pre-hash: {before_hash} -> Post-hash: {after_hash})\n")
    f.write("=" * 80 + "\n")
    f.write("\n".join(field_diff_rows))

# Write logs/query_gold_alignment.txt
with open(LOGS_DIR / "query_gold_alignment.txt", "w", encoding="utf-8") as f:
    f.write("T2 QUERY-GOLD-HOLDING-SENTENCE ALIGNMENT AUDIT (7 REWRITES)\n")
    f.write("=" * 80 + "\n\n")
    f.write("\n".join(alignment_rows))

print("Wrote logs/benchmark_update_diff.txt and logs/query_gold_alignment.txt")
