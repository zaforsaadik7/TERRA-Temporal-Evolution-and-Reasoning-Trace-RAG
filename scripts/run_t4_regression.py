import os
import sys
import json
import hashlib
import subprocess
import importlib.util
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
OUT_LOG = ROOT / "logs" / "t4_regression.txt"
STOP_LOG = ROOT / "logs" / "STOPPED_T4e.txt"

sys.path.insert(0, str(ROOT))

# Configure environment variables for offline parity test
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "mock_key_for_offline_import")
os.environ["TERRA_GRAPH_PATH"] = "dataset_20k_cap/terra_eeg_index_20k.json"
os.environ["TERRA_VECTOR_DB_PATH"] = "./dataset_20k_cap/vector_db_20k"

# 1. Check git show HEAD:ask_terra.py
head_bytes = subprocess.check_output(["git", "show", "HEAD:ask_terra.py"], cwd=str(ROOT))
head_text = head_bytes.decode("utf-8", errors="replace")

if "arm4" in head_text.lower():
    with open(STOP_LOG, "w", encoding="utf-8") as f:
        f.write("STOPPED: git show HEAD:ask_terra.py contains 'arm4'.\n")
    print("STOPPED: git show HEAD:ask_terra.py contains 'arm4'.")
    sys.exit(0)

# Save as scratch/ask_terra_head.py
head_path = ROOT / "scratch" / "ask_terra_head.py"
with open(head_path, "wb") as f:
    f.write(head_bytes)
print("Saved scratch/ask_terra_head.py cleanly.")

# Dynamically import HEAD module and Working module
spec_head = importlib.util.spec_from_file_location("ask_terra_head", str(head_path))
mod_head = importlib.util.module_from_spec(spec_head)
spec_head.loader.exec_module(mod_head)

import ask_terra as mod_work

# 2. Select first 5 query_ids sorted of each category A, B, C, D in terra_350_benchmark.json
with open(ROOT / "terra_350_benchmark.json", "r", encoding="utf-8") as f:
    bench_350 = json.load(f)

cats = {"A": [], "B": [], "C": [], "D": []}
for item in bench_350:
    c = item.get("category", "")
    prefix = c[0].upper() if c else ""
    if prefix in cats:
        cats[prefix].append(item)

sampled_20 = []
for p in ["A", "B", "C", "D"]:
    sorted_items = sorted(cats[p], key=lambda x: x.get("id", x.get("query_id", "")))
    sampled_20.extend(sorted_items[:5])

print(f"Selected 20 queries across A, B, C, D: {[x.get('id', x.get('query_id')) for x in sampled_20]}")

log_lines = []
log_lines.append("=" * 110)
log_lines.append("T4(e) REGRESSION: HEAD VS WORKING (arm4_unlabeled=False) OVER 20 BENCHMARK QUERIES")
log_lines.append("=" * 110)
header = f"{'QUERY_ID':<10} | {'HEAD_LEN':<10} | {'WORK_LEN':<10} | {'HEAD_SHA256':<20} | {'WORK_SHA256':<20} | {'STATUS'}"
log_lines.append(header)
log_lines.append("-" * 110)

all_lens = []

for item in sampled_20:
    qid = item.get("id", item.get("query_id"))
    query = item.get("query") or item.get("text")
    
    # Run local retrieval using ChromaDB query on actual query text
    chroma_res = mod_work.collection.query(query_texts=[query], n_results=5)
    metas = chroma_res['metadatas'][0] if chroma_res and 'metadatas' in chroma_res and chroma_res['metadatas'] else []
    
    # 1. Build context & prompt with HEAD module
    head_ctx = mod_head.extract_graph_context(metas, max_depth=2)
    head_inst2 = "2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."
    head_prompt = f"You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.\n\n[CONTEXT DATA]\n{head_ctx}\n\n[INSTRUCTIONS]\n1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.\n{head_inst2}\n\nQuestion: {query}\n\nAnswer:"
    
    # 2. Build context & prompt with Working module (arm4_unlabeled=False)
    work_ctx = mod_work.extract_graph_context(metas, max_depth=2, arm4_unlabeled=False)
    work_inst2 = "2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."
    work_prompt = f"You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.\n\n[CONTEXT DATA]\n{work_ctx}\n\n[INSTRUCTIONS]\n1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.\n{work_inst2}\n\nQuestion: {query}\n\nAnswer:"
    
    h_bytes = head_prompt.encode("utf-8")
    w_bytes = work_prompt.encode("utf-8")
    
    h_len = len(h_bytes)
    w_len = len(w_bytes)
    all_lens.append(w_len)
    
    h_sha = hashlib.sha256(h_bytes).hexdigest()
    w_sha = hashlib.sha256(w_bytes).hexdigest()
    
    status = "IDENTICAL" if (h_sha == w_sha and head_ctx == work_ctx) else "DIFFERENT"
    log_lines.append(f"{qid:<10} | {h_len:<10} | {w_len:<10} | {h_sha[:18]:<20} | {w_sha[:18]:<20} | {status}")

# Check if all 20 lengths are equal
if len(set(all_lens)) == 1:
    log_lines.append("\nTEST_DEFECT: All 20 lengths are identical!")
    print("TEST_DEFECT detected.")
else:
    log_lines.append(f"\nUnique lengths across 20 queries: {len(set(all_lens))} distinct values. Variation verified.")

log_lines.append("=" * 110)

output_text = "\n".join(log_lines) + "\n"
with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write(output_text)

print(f"Wrote T4(e) regression results to {OUT_LOG}")
