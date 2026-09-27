import json
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
BENCH_PATH = ROOT / "data" / "obscure_overruled_benchmark.json"
BACKUP_DIR = ROOT / "data" / "backup"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

REWRITES = {
    "OBS_012": "Under the Supreme Court's decision in Forman v. United States (1960), where a convicted defendant appeals and seeks a new trial, and the appeal includes a challenge to the denial of his motion for judgment of acquittal, does the Double Jeopardy Clause bar a retrial if the conviction is reversed?",
    "OBS_011": "Under the Supreme Court's decision in Low v. Austin (1872), does the Import-Export Clause of the Constitution prohibit a state from taxing, as property, imported goods that are still in their original unbroken packages?"
}

# 1. Compute binary hash before modification
with open(BENCH_PATH, "rb") as f:
    orig_bytes = f.read()
orig_sha = hashlib.sha256(orig_bytes).hexdigest()

backup_path = BACKUP_DIR / f"{orig_sha}.json"
shutil.copyfile(BENCH_PATH, backup_path)
print(f"[U3] Backed up benchmark to {backup_path}")

# 2. Apply rewrites
bench_data = json.loads(orig_bytes.decode("utf-8"))

diff_log_lines = []
alignment_log_lines = []

diff_log_lines.append("=" * 100)
diff_log_lines.append(f"U3 FIELD-LEVEL DIFF: PRE-EDIT (SHA: {orig_sha}) VS POST-EDIT")
diff_log_lines.append("=" * 100)

alignment_log_lines.append("=" * 100)
alignment_log_lines.append("U3 QUERY-GOLD ALIGNMENT FOR REWRITTEN QUERIES (OBS_011, OBS_012)")
alignment_log_lines.append("=" * 100)

for item in bench_data:
    qid = item["query_id"]
    if qid in REWRITES:
        old_q = item["query"]
        new_q = REWRITES[qid]
        item["query"] = new_q
        
        diff_log_lines.append(f"\n[{qid}] query:")
        diff_log_lines.append(f"  OLD: \"{old_q}\"")
        diff_log_lines.append(f"  NEW: \"{new_q}\"")
        
        gold_h = item.get("gold_holding", "")
        tgt_s = item.get("grounding_target_holding", {}).get("sentence", "")
        ovr_s = item.get("grounding_overruling_sentence", {}).get("sentence", "")
        
        alignment_log_lines.append(f"\n--- {qid}: {item.get('target_case')} -> {item.get('overruling_case')} ---")
        alignment_log_lines.append(f"OLD QUERY:           \"{old_q}\"")
        alignment_log_lines.append(f"NEW QUERY:           \"{new_q}\"")
        alignment_log_lines.append(f"GOLD HOLDING:        \"{gold_h}\"")
        alignment_log_lines.append(f"TARGET SENTENCE:     \"{tgt_s}\"")
        alignment_log_lines.append(f"OVERRULING SENTENCE: \"{ovr_s}\"")

# 3. Write back benchmark
with open(BENCH_PATH, "w", encoding="utf-8") as f:
    json.dump(bench_data, f, indent=2, ensure_ascii=False)

with open(ROOT / "logs" / "benchmark_update_diff_U3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(diff_log_lines) + "\n")

with open(ROOT / "logs" / "query_gold_alignment_U3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(alignment_log_lines) + "\n")

# Keep obscure_benchmark_30_queries.json in sync
queries_json_path = ROOT / "data" / "obscure_benchmark_30_queries.json"
generated_queries = [
    {
        "query_id": x["query_id"],
        "query": x["query"],
        "target_case": x.get("target_case", ""),
        "target_node": x.get("target_node", "")
    }
    for x in bench_data
]
with open(queries_json_path, "w", encoding="utf-8") as f:
    json.dump(generated_queries, f, indent=2, ensure_ascii=False)

# Keep queries_from_benchmark.txt in sync
with open(ROOT / "logs" / "queries_from_benchmark.txt", "w", encoding="utf-8") as f:
    for x in bench_data:
        f.write(f"{x['query_id']} | {x['query']}\n")

# 4. Rerun scripts/leak_audit.py unchanged
print("[U3] Rerunning scripts/leak_audit.py...")
res = subprocess.run(
    [str(ROOT / "venv" / "Scripts" / "python.exe"), str(ROOT / "scripts" / "leak_audit.py")],
    capture_output=True,
    text=True,
    encoding="utf-8"
)
assert res.returncode == 0, f"leak_audit.py failed: {res.stderr}"
print("[U3] leak_audit.py completed cleanly.")
print("Wrote logs/benchmark_update_diff_U3.txt, logs/query_gold_alignment_U3.txt, and updated logs/leak_audit.txt")
