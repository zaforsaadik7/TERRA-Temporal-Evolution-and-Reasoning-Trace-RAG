"""
scripts/write_obscure_item_outcomes.py - Task G4: Obscure Item Outcomes CSV
==========================================================================
Writes logs/obscure_item_outcomes.csv from caches:
  query_id, scope_class, per-arm both judges' labels, combined class,
  context_empty, overruler_in_context, route.
No commentary.
"""

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.audit_obscure_overruled_benchmark import (
    load_suite_metadata, prepare_blinded_shuffled_eval_items,
    build_judge_prompt, compute_judge_cache_key, JUDGE_MODELS,
    combine_judgments
)

def main():
    raw_path = ROOT / "scratch" / "obscure_raw_responses.json"
    judge_path = ROOT / "scratch" / "obscure_judge_cache.json"
    bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"

    assert raw_path.exists(), f"Missing {raw_path}"
    assert judge_path.exists(), f"Missing {judge_path}"
    assert bench_path.exists(), f"Missing {bench_path}"

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
        joined["scope_classification"] = ginfo.get("scope_classification") or ginfo.get("scope_type", "")
        joined["scope_type"] = ginfo.get("scope_type") or ginfo.get("scope_classification", "")
        joined_responses.append(joined)

    blinded_payload, full_items, seed = prepare_blinded_shuffled_eval_items(joined_responses, shuffle_seed=42)
    id_to_full = {item["candidate_id"]: item for item in full_items}

    # Collect outcomes per query and arm
    items_by_query = {}
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

        j1_label = judge_cache[k1]["classification"]
        j2_label = judge_cache[k2]["classification"]
        comb = combine_judgments(j1_label, j2_label)

        if qid not in items_by_query:
            items_by_query[qid] = {
                "query_id": qid,
                "scope_class": orig.get("scope_classification", ""),
                "arms": {}
            }

        items_by_query[qid]["arms"][arm] = {
            "j1": j1_label,
            "j2": j2_label,
            "combined": comb["combined_class"]
        }

        if arm == "3_Full_TERRA":
            items_by_query[qid]["context_empty"] = orig.get("context_empty", False)
            items_by_query[qid]["overruler_in_context"] = orig.get("overruler_in_context", False)

    # Extract route from original cached responses for 3_Full_TERRA
    arm3_by_qid = {r["query_id"]: r for r in cached_responses if r.get("pipeline") == "3_Full_TERRA"}
    for qid in items_by_query:
        r3 = arm3_by_qid.get(qid, {})
        items_by_query[qid]["route"] = r3.get("route", "")
        if "context_empty" not in items_by_query[qid]:
            items_by_query[qid]["context_empty"] = r3.get("context_empty", False)
        if "overruler_in_context" not in items_by_query[qid]:
            items_by_query[qid]["overruler_in_context"] = r3.get("overruler_in_context", False)

    fieldnames = [
        "query_id",
        "scope_class",
        "arm1_direct_j1",
        "arm1_direct_j2",
        "arm1_direct_combined",
        "arm2_flat_j1",
        "arm2_flat_j2",
        "arm2_flat_combined",
        "arm3_full_terra_j1",
        "arm3_full_terra_j2",
        "arm3_full_terra_combined",
        "arm4_terra_unlabeled_j1",
        "arm4_terra_unlabeled_j2",
        "arm4_terra_unlabeled_combined",
        "context_empty",
        "overruler_in_context",
        "route"
    ]

    out_csv = ROOT / "logs" / "obscure_item_outcomes.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    sorted_qids = sorted(list(items_by_query.keys()))
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for qid in sorted_qids:
            qdata = items_by_query[qid]
            row = {
                "query_id": qid,
                "scope_class": qdata["scope_class"],
                "arm1_direct_j1": qdata["arms"].get("1_Direct_LLM", {}).get("j1", ""),
                "arm1_direct_j2": qdata["arms"].get("1_Direct_LLM", {}).get("j2", ""),
                "arm1_direct_combined": qdata["arms"].get("1_Direct_LLM", {}).get("combined", ""),
                "arm2_flat_j1": qdata["arms"].get("2_Flat_Vector_RAG", {}).get("j1", ""),
                "arm2_flat_j2": qdata["arms"].get("2_Flat_Vector_RAG", {}).get("j2", ""),
                "arm2_flat_combined": qdata["arms"].get("2_Flat_Vector_RAG", {}).get("combined", ""),
                "arm3_full_terra_j1": qdata["arms"].get("3_Full_TERRA", {}).get("j1", ""),
                "arm3_full_terra_j2": qdata["arms"].get("3_Full_TERRA", {}).get("j2", ""),
                "arm3_full_terra_combined": qdata["arms"].get("3_Full_TERRA", {}).get("combined", ""),
                "arm4_terra_unlabeled_j1": qdata["arms"].get("4_TERRA_Unlabeled", {}).get("j1", ""),
                "arm4_terra_unlabeled_j2": qdata["arms"].get("4_TERRA_Unlabeled", {}).get("j2", ""),
                "arm4_terra_unlabeled_combined": qdata["arms"].get("4_TERRA_Unlabeled", {}).get("combined", ""),
                "context_empty": qdata.get("context_empty", False),
                "overruler_in_context": qdata.get("overruler_in_context", False),
                "route": qdata.get("route", "")
            }
            writer.writerow(row)

    print(f"[G4] Successfully wrote {len(sorted_qids)} items to {out_csv}")

if __name__ == "__main__":
    main()
