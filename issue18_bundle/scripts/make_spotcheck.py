"""
scripts/make_spotcheck.py - Task G5: Blinded Spot-Check Kit Generator
====================================================================
With seed 42, selects 30 distinct obscure responses:
  - 10 where the two judges disagree
  - 10 from the primary-comparison discordant cells (b or c; filled from random if fewer)
  - 10 random
Writes:
  - review/obscure_spotcheck_blinded.md
  - review/obscure_spotcheck_key.json
"""

import os
import sys
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.audit_obscure_overruled_benchmark import (
    load_suite_metadata, prepare_blinded_shuffled_eval_items,
    build_judge_prompt, compute_judge_cache_key, JUDGE_MODELS,
    combine_judgments, map_raw_label
)

def main():
    raw_path = ROOT / "scratch" / "obscure_raw_responses.json"
    judge_path = ROOT / "scratch" / "obscure_judge_cache.json"

    assert raw_path.exists(), f"Missing {raw_path}"
    assert judge_path.exists(), f"Missing {judge_path}"

    with open(raw_path, "r", encoding="utf-8") as f:
        cached_responses = json.load(f)
    with open(judge_path, "r", encoding="utf-8") as f:
        judge_cache = json.load(f)
    gold_map = load_suite_metadata("obscure")

    joined_responses = []
    for r in cached_responses:
        qid = r["query_id"]
        ginfo = gold_map.get(qid, {})
        joined = dict(r)
        joined["target_case"] = ginfo.get("target_case", "")
        joined["overruling_case"] = ginfo.get("overruling_case", "")
        joined["gold_holding"] = ginfo.get("gold_holding", "")
        joined_responses.append(joined)

    blinded_payload, full_items, seed = prepare_blinded_shuffled_eval_items(joined_responses, shuffle_seed=42)
    id_to_full = {item["candidate_id"]: item for item in full_items}

    all_evals = []
    for bp in blinded_payload:
        cid = bp["candidate_id"]
        orig = id_to_full[cid]
        qid = orig["query_id"]
        arm = orig["pipeline"]
        ans = orig["answer"]
        prompt = build_judge_prompt(
            query=bp["query"], target_case=bp["target_case"],
            overruling_case=bp["overruling_case"], gold_holding=bp["gold_holding"],
            answer=ans
        )
        k1 = compute_judge_cache_key(qid, arm, JUDGE_MODELS[0], prompt, ans)
        k2 = compute_judge_cache_key(qid, arm, JUDGE_MODELS[1], prompt, ans)
        j1 = judge_cache[k1]["classification"]
        j2 = judge_cache[k2]["classification"]
        comb = combine_judgments(j1, j2)
        all_evals.append({
            "candidate_id": cid,
            "query_id": qid,
            "arm": arm,
            "query": bp["query"],
            "target_case": bp["target_case"],
            "overruling_case": bp["overruling_case"],
            "gold_holding": bp["gold_holding"],
            "answer": ans,
            "j1": j1,
            "j2": j2,
            "m1": map_raw_label(j1),
            "m2": map_raw_label(j2),
            "combined": comb["combined_class"],
            "is_safe": comb["is_safe"],
            "key": f"{qid}_{arm}"
        })

    rng = random.Random(42)

    # 1. 10 where the two judges disagree
    pool1 = sorted([x for x in all_evals if x["m1"] != x["m2"]], key=lambda x: x["key"])
    s1 = rng.sample(pool1, 10)
    selected_keys = set(x["key"] for x in s1)

    # 2. 10 from primary-comparison discordant cells (b or c)
    arm4_safe = {x["query_id"]: x["is_safe"] for x in all_evals if x["arm"] == "4_TERRA_Unlabeled"}
    arm2_safe = {x["query_id"]: x["is_safe"] for x in all_evals if x["arm"] == "2_Flat_Vector_RAG"}
    b_qids = set(q for q in arm4_safe if arm4_safe[q] and not arm2_safe[q])
    c_qids = set(q for q in arm4_safe if not arm4_safe[q] and arm2_safe[q])
    discordant_qids = b_qids | c_qids

    pool2 = sorted([
        x for x in all_evals
        if x["query_id"] in discordant_qids and x["arm"] in ["4_TERRA_Unlabeled", "2_Flat_Vector_RAG"]
        and x["key"] not in selected_keys
    ], key=lambda x: x["key"])

    if len(pool2) >= 10:
        s2 = rng.sample(pool2, 10)
    else:
        s2 = pool2[:]
        remaining_for_s2 = sorted([x for x in all_evals if x["key"] not in selected_keys and x["key"] not in set(y["key"] for y in s2)], key=lambda x: x["key"])
        s2.extend(rng.sample(remaining_for_s2, 10 - len(s2)))

    for x in s2:
        selected_keys.add(x["key"])

    # 3. 10 random
    pool3 = sorted([x for x in all_evals if x["key"] not in selected_keys], key=lambda x: x["key"])
    s3 = rng.sample(pool3, 10)
    for x in s3:
        selected_keys.add(x["key"])

    total_selected = s1 + s2 + s3
    assert len(total_selected) == 30
    assert len(selected_keys) == 30

    # Shuffle the final 30 items so strata are fully blinded
    rng.shuffle(total_selected)

    review_dir = ROOT / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    key_data = {}
    md_lines = []
    md_lines.append("# Obscure Precedent Spot-Check Evaluation (Blinded)")
    md_lines.append("")
    md_lines.append("Instructions: For each generated answer below, evaluate whether the response recognizes that the historical doctrine was overruled or superseded, presents the old rule as current law, or refuses to answer.")
    md_lines.append("")
    md_lines.append("Fill in each blank field inside the square brackets `[ ]`:")
    md_lines.append("- `Says the case was overruled/superseded (yes/no/partly): [ ]`")
    md_lines.append("- `Presents the old rule as current law (yes/no): [ ]`")
    md_lines.append("- `Refuses (yes/no): [ ]`")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    for idx, item in enumerate(total_selected, 1):
        item_id = f"S{idx:02d}"
        key_data[item_id] = {
            "query_id": item["query_id"],
            "arm": item["arm"],
            "j1_label": item["j1"],
            "j2_label": item["j2"],
            "combined_class": item["combined"]
        }

        md_lines.append(f"## Item {item_id}")
        md_lines.append("")
        md_lines.append(f"**Query**: {item['query']}")
        md_lines.append(f"**Target Case**: {item['target_case']}")
        md_lines.append(f"**Overruling Case**: {item['overruling_case']}")
        md_lines.append(f"**Historical Holding**: {item['gold_holding']}")
        md_lines.append("")
        md_lines.append("**Generated Answer**:")
        md_lines.append("```")
        md_lines.append(item["answer"])
        md_lines.append("```")
        md_lines.append("")
        md_lines.append("**Evaluation**:")
        md_lines.append("- Says the case was overruled/superseded (yes/no/partly): [ ]")
        md_lines.append("- Presents the old rule as current law (yes/no): [ ]")
        md_lines.append("- Refuses (yes/no): [ ]")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    out_md = review_dir / "obscure_spotcheck_blinded.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[SPOTCHECK] Wrote blinded evaluation sheet: {out_md} ({out_md.stat().st_size} bytes)")

    out_key = review_dir / "obscure_spotcheck_key.json"
    with open(out_key, "w", encoding="utf-8") as f:
        json.dump(key_data, f, indent=2)
    print(f"[SPOTCHECK] Wrote evaluation key: {out_key} ({out_key.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
