import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
queries_json_path = ROOT / "data" / "obscure_benchmark_30_queries.json"
out_txt_path = ROOT / "logs" / "queries_from_benchmark.txt"

with open(bench_path, "r", encoding="utf-8") as f:
    bench = json.load(f)

# 1. Generate text dump
txt_lines = []
generated_queries_json = []

for item in bench:
    qid = item["query_id"]
    query = item["query"]
    txt_lines.append(f"{qid} | {query}")
    generated_queries_json.append({
        "query_id": qid,
        "query": query,
        "target_case": item.get("target_case", ""),
        "target_node": item.get("target_node", "")
    })

out_txt_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_txt_path, "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines) + "\n")

# 2. Regenerate data/obscure_benchmark_30_queries.json and data/30_queries.json
with open(queries_json_path, "w", encoding="utf-8") as f:
    json.dump(generated_queries_json, f, indent=2, ensure_ascii=False)

q30_path = ROOT / "data" / "30_queries.json"
with open(q30_path, "w", encoding="utf-8") as f:
    json.dump(generated_queries_json, f, indent=2, ensure_ascii=False)

# 3. Assert queries are identical
with open(queries_json_path, "r", encoding="utf-8") as f:
    reloaded = json.load(f)

bench_queries = [x["query"] for x in bench]
reloaded_queries = [x["query"] for x in reloaded]
assert bench_queries == reloaded_queries, "Queries in regenerated JSON do not match benchmark JSON!"

with open(q30_path, "r", encoding="utf-8") as f:
    reloaded_30 = json.load(f)
assert bench_queries == [x["query"] for x in reloaded_30], "Queries in 30_queries.json do not match benchmark JSON!"

# 4. Binary SHA256 of both files
with open(bench_path, "rb") as f:
    bench_sha = hashlib.sha256(f.read()).hexdigest()

with open(queries_json_path, "rb") as f:
    queries_json_sha = hashlib.sha256(f.read()).hexdigest()

log_summary_path = ROOT / "logs" / "dump_queries_hashes.txt"
with open(log_summary_path, "w", encoding="utf-8") as f:
    f.write(f"benchmark_json_sha256: {bench_sha}\n")
    f.write(f"obscure_benchmark_30_queries_json_sha256: {queries_json_sha}\n")
    f.write("assertion_queries_identical: PASSED\n")

print(f"Dumped 30 queries to {out_txt_path}")
print(f"Regenerated {queries_json_path}")
print(f"Benchmark SHA256: {bench_sha}")
print(f"Queries JSON SHA256: {queries_json_sha}")
