import os
import json
import time
from collections import Counter

raw_path = "terra_baselines_eval_raw.json"
audit_path = "baselines/audit_payloads.jsonl"
benchmark_path = "terra_350_benchmark.json"

with open(benchmark_path, "r", encoding="utf-8") as f:
    bench = json.load(f)
total_queries = len(bench)
total_expected_evals = total_queries * 5

raw_records = []
if os.path.exists(raw_path):
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

audit_entries = []
if os.path.exists(audit_path):
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_entries = [json.loads(line) for line in f if line.strip()]

gen_entries = [e for e in audit_entries if e.get("event") == "generation"]
sc_entries = [e for e in audit_entries if e.get("event") == "short_circuit"]

q_counts = Counter(r["query_id"] for r in raw_records)
completed_queries = sum(1 for qid, count in q_counts.items() if count == 5)

print("=" * 70)
print(f"TERRA 350 BENCHMARK LIVE PROGRESS MONITOR")
print("=" * 70)
print(f"Completed Queries:        {completed_queries} / {total_queries} ({completed_queries / total_queries * 100:.1f}%)")
print(f"Raw Evaluation Records:   {len(raw_records)} / {total_expected_evals} ({len(raw_records) / total_expected_evals * 100:.1f}%)")
print(f"Intercepted Generations:  {len(gen_entries)}")
print(f"Short-Circuits Logged:    {len(sc_entries)}")
print(f"Reconciliation Equation:  {len(gen_entries)} (G) + {len(sc_entries)} (S) = {len(gen_entries) + len(sc_entries)}")

if audit_entries:
    latest = audit_entries[-1]
    print(f"\nLatest Audit Event:")
    print(f"  Time:     {latest.get('timestamp')}")
    print(f"  Event:    {latest.get('event')}")
    print(f"  Query ID: {latest.get('query_id')}")
    print(f"  Pipeline: {latest.get('pipeline')}")
print("=" * 70)
