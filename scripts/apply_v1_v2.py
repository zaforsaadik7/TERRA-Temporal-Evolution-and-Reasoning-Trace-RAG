import os
import sys
import json
import shutil
import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
BENCH_PATH = ROOT / "data" / "obscure_overruled_benchmark.json"
DIFF_LOG = ROOT / "logs" / "benchmark_update_diff_V1_V2.txt"

# 1. Binary hash before edit
with open(BENCH_PATH, "rb") as f:
    bench_bytes_before = f.read()
sha_before = hashlib.sha256(bench_bytes_before).hexdigest()

backup_path = ROOT / "data" / "backup" / f"{sha_before}.json"
backup_path.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(BENCH_PATH, backup_path)
print(f"Backed up benchmark to {backup_path}")

# Load raw CAP files to extract exact text
def get_cap_text(node_id: str) -> str:
    p = ROOT / "dataset_20k_cap" / "raw_cases" / f"{node_id}.json"
    assert p.exists(), f"Missing CAP file: {p}"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["casebody"]["opinions"][0]["text"]

# Load candidates_U2.txt to assert text matches candidates
with open(ROOT / "logs" / "candidates_U2.txt", "r", encoding="utf-8") as f:
    cand_u2_text = f.read()

# Target replacements for V1
replacements_v1 = {
    "OBS_001": {
        "node": "429_0363-01",
        "char_start": 26707,
        "char_end": 26842,
    },
    "OBS_011": {
        "node": "423_0276-01",
        "char_start": 32603,
        "char_end": 32724,
    },
    "OBS_015": {
        "node": "364_0206-01",
        "char_start": 2043,
        "char_end": 2230,
    }
}

bench = json.loads(bench_bytes_before.decode("utf-8"))
diff_lines = []
diff_lines.append("=" * 100)
diff_lines.append(f"FIELD-LEVEL DIFF: BENCHMARK UPDATE (V1 & V2)")
diff_lines.append(f"Pre-update Binary SHA256: {sha_before}")
diff_lines.append("=" * 100)

diff_lines.append("\n--- V1: OVERRULING-SPAN REPLACEMENTS ---")

for item in bench:
    qid = item["query_id"]
    if qid in replacements_v1:
        cfg = replacements_v1[qid]
        raw_text = get_cap_text(cfg["node"])
        s, e = cfg["char_start"], cfg["char_end"]
        extracted_sent = raw_text[s:e]
        
        # Assertions per V1
        assert raw_text[s:e] == extracted_sent
        assert extracted_sent in raw_text
        
        # Verify candidate text in candidates_U2.txt
        if qid == "OBS_001":
            assert "For all of these reasons, we have now decided that Bonelli’s application of federal common law to cases such as this must be overruled." in cand_u2_text
            assert extracted_sent == "For all of these reasons, we have now decided that Bonelli’s application of federal common law to cases such as this must be overruled."
        elif qid == "OBS_011":
            assert "It follows from the foregoing that Low v. Austin was wrongly decided. That decision therefore must be, and is, overruled." in cand_u2_text
            assert extracted_sent == "It follows from the foregoing that Low v. Austin was wrongly decided. That decision therefore must be, and is, overruled."
        elif qid == "OBS_015":
            assert "In a word, we re-examine here the validity of what has come to be called the silver platter doctrine. For the reasons that follow we conclude that this doctrine can no longer be accepted." in cand_u2_text
            assert extracted_sent == "In a word, we re-examine here the validity of what has come to be called the silver platter doctrine. For the reasons that follow we conclude that this doctrine can no longer be accepted."
            
        old_gh = item["grounding_overruling_sentence"]
        diff_lines.append(f"\n[{qid}] {item.get('target_case')} -> {item.get('overruling_case')}")
        diff_lines.append(f"  Field: grounding_overruling_sentence")
        diff_lines.append(f"  OLD char_start: {old_gh['char_start']}")
        diff_lines.append(f"  NEW char_start: {s}")
        diff_lines.append(f"  OLD char_end:   {old_gh['char_end']}")
        diff_lines.append(f"  NEW char_end:   {e}")
        diff_lines.append(f"  OLD sentence:   {repr(old_gh['sentence'])}")
        diff_lines.append(f"  NEW sentence:   {repr(extracted_sent)}")
        diff_lines.append(f"  Scope class unchanged: {item.get('scope_classification')}")
        
        item["grounding_overruling_sentence"]["char_start"] = s
        item["grounding_overruling_sentence"]["char_end"] = e
        item["grounding_overruling_sentence"]["sentence"] = extracted_sent

# V2: Update OBS_007 query
diff_lines.append("\n\n--- V2: OBS_007 QUERY REWRITE ---")
v2_query = "Under the Supreme Court's decision in Breedlove v. Suttles (1937), does a state law imposing an annual poll tax as a condition for voting in state elections violate the Equal Protection Clause of the Fourteenth Amendment?"

for item in bench:
    if item["query_id"] == "OBS_007":
        old_query = item["query"]
        assert old_query != v2_query
        diff_lines.append(f"\n[OBS_007]")
        diff_lines.append(f"  Field: query")
        diff_lines.append(f"  OLD query: {repr(old_query)}")
        diff_lines.append(f"  NEW query: {repr(v2_query)}")
        item["query"] = v2_query

# Write updated benchmark
with open(BENCH_PATH, "w", encoding="utf-8") as f:
    json.dump(bench, f, indent=2, ensure_ascii=False)

with open(BENCH_PATH, "rb") as f:
    bench_bytes_after = f.read()
sha_after = hashlib.sha256(bench_bytes_after).hexdigest()

diff_lines.append("\n" + "=" * 100)
diff_lines.append(f"Post-update Binary SHA256: {sha_after}")
diff_lines.append("=" * 100)

DIFF_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(DIFF_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(diff_lines) + "\n")

print(f"Updated benchmark written. Logged diff to {DIFF_LOG}")
print(f"New binary SHA-256: {sha_after}")
