import json
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
raw_path = ROOT / "dataset_20k_cap" / "raw_cases" / "391_0234-01.json"
with open(raw_path, "r", encoding="utf-8") as f:
    raw = json.load(f)
text = raw["casebody"]["opinions"][0]["text"]
pos = text.find("must be overruled")

bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
with open(bench_path, "r", encoding="utf-8") as f:
    bench = json.load(f)
obs005 = [x for x in bench if x["query_id"] == "OBS_005"][0]
start = obs005["grounding_overruling_sentence"]["char_start"]
end = obs005["grounding_overruling_sentence"]["char_end"]

content = f"{pos}\n{start}, {end}\n"

for name in ["slice_check_obs005.txt", "slice_check.txt"]:
    out_path = ROOT / "logs" / name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Position: {pos}")
print(f"Bounds: {start}, {end}")
print("Wrote logs/slice_check_obs005.txt and logs/slice_check.txt")
