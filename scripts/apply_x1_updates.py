import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
w2_candidates_path = ROOT / "logs" / "candidates_W2.txt"

# 1. Read existing and compute binary hash for backup
with open(bench_path, "rb") as f:
    bench_bytes = f.read()
curr_sha256 = hashlib.sha256(bench_bytes).hexdigest()

backup_dir = ROOT / "data" / "backup"
backup_dir.mkdir(parents=True, exist_ok=True)
backup_path = backup_dir / f"{curr_sha256}.json"
with open(backup_path, "wb") as f:
    f.write(bench_bytes)
print(f"Backed up current benchmark to {backup_path}")

# Load candidate text from logs/candidates_W2.txt
w2_text = open(w2_candidates_path, "r", encoding="utf-8").read()

# Load CAP raw cases to assert slices
with open(ROOT / "dataset_20k_cap" / "raw_cases" / "383_0663-01.json", "r", encoding="utf-8") as f:
    text_007 = json.load(f)["casebody"]["opinions"][0]["text"]
slice_007 = text_007[5997:6349]
# OBS_007 spans sentences #48, #49, #50, #51
sent48 = text_007[5997:6217]
sent49 = text_007[6218:6288]
sent50 = text_007[6289:6301]
sent51 = text_007[6302:6349]
assert text_007[5997:6349] == sent48 + " " + sent49 + " " + sent50 + " " + sent51
assert repr(sent48) in w2_text, "sent48 not in candidates_W2.txt"
assert repr(sent49) in w2_text, "sent49 not in candidates_W2.txt"
assert repr(sent50) in w2_text, "sent50 not in candidates_W2.txt"
assert repr(sent51) in w2_text, "sent51 not in candidates_W2.txt"

with open(ROOT / "dataset_20k_cap" / "raw_cases" / "419_0522-01.json", "r", encoding="utf-8") as f:
    text_009 = json.load(f)["casebody"]["opinions"][0]["text"]
slice_009 = text_009[17635:18132]
# OBS_009 spans sentences #102 and #103
sent102 = text_009[17635:18027]
sent103 = text_009[18028:18132]
assert text_009[17635:18132] == sent102 + " " + sent103
assert repr(sent102) in w2_text, "sent102 not in candidates_W2.txt"
assert repr(sent103) in w2_text, "sent103 not in candidates_W2.txt"

with open(ROOT / "dataset_20k_cap" / "raw_cases" / "437_0001-01.json", "r", encoding="utf-8") as f:
    text_burks = json.load(f)["casebody"]["opinions"][0]["text"]
slice_burks = text_burks[14399:14654]
assert repr(slice_burks) in w2_text, "Burks supporting slice not in candidates_W2.txt"

# Load benchmark
bench = json.loads(bench_bytes.decode("utf-8"))
diff_lines = []

for it in bench:
    qid = it["query_id"]
    if qid == "OBS_007":
        old_span = it["grounding_overruling_sentence"]
        new_span = {
            "sentence": slice_007,
            "char_start": 5997,
            "char_end": 6349,
            "char_length": len(slice_007),
            "slice_equality_asserted": True
        }
        diff_lines.append(f"[{qid}] grounding_overruling_sentence:")
        diff_lines.append(f"  OLD: {old_span}")
        diff_lines.append(f"  NEW: {new_span}")
        it["grounding_overruling_sentence"] = new_span

    elif qid == "OBS_009":
        old_span = it["grounding_overruling_sentence"]
        new_span = {
            "sentence": slice_009,
            "char_start": 17635,
            "char_end": 18132,
            "char_length": len(slice_009),
            "slice_equality_asserted": True
        }
        diff_lines.append(f"[{qid}] grounding_overruling_sentence:")
        diff_lines.append(f"  OLD: {old_span}")
        diff_lines.append(f"  NEW: {new_span}")
        it["grounding_overruling_sentence"] = new_span

    elif qid in ("OBS_012", "OBS_021"):
        supporting_span = {
            "node": "437_0001-01",
            "char_start": 14399,
            "char_end": 14654,
            "sentence": slice_burks,
            "char_length": len(slice_burks),
            "slice_equality_asserted": True
        }
        diff_lines.append(f"[{qid}] overruling_supporting_span: {supporting_span}")
        diff_lines.append(f"[{qid}] overruling_names_target: False")
        it["overruling_supporting_span"] = supporting_span
        it["overruling_names_target"] = False

diff_log_path = ROOT / "logs" / "benchmark_update_diff_X1.txt"
with open(diff_log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(diff_lines) + "\n")
print(f"Logged field-level diff to {diff_log_path}")

# Write new benchmark JSON
new_bench_bytes = json.dumps(bench, indent=2, ensure_ascii=False).encode("utf-8")
with open(bench_path, "wb") as f:
    f.write(new_bench_bytes)

new_sha256 = hashlib.sha256(new_bench_bytes).hexdigest()
print(f"Updated benchmark written. New binary SHA256: {new_sha256}")
