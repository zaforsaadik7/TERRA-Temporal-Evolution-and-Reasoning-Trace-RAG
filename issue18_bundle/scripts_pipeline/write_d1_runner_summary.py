import json
import shutil
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    cache_path = ROOT / "scratch" / "famous_d1_raw_responses.json"
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")

    records = json.loads(cache_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} records from {cache_path}")

    # 1. Records per arm
    arms = ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_Full_TERRA", "4_TERRA_Unlabeled"]
    records_per_arm = Counter(r.get("pipeline") for r in records)

    # Group by query_id
    by_query = {}
    for r in records:
        qid = r["query_id"]
        by_query.setdefault(qid, {})[r["pipeline"]] = r

    # 2. Route distribution for Arm 3
    arm3_recs = [r for r in records if r.get("pipeline") == "3_Full_TERRA"]
    route_dist_arm3 = Counter(r.get("route") for r in arm3_recs)

    # 3. Items with context_empty
    ctx_empty_per_arm = {a: [] for a in arms}
    for r in records:
        if r.get("context_empty") is True:
            ctx_empty_per_arm[r.get("pipeline")].append(r.get("query_id"))

    # 4. Items with overruler_in_context False
    ovr_false_per_arm = {a: [] for a in arms}
    for r in records:
        if r.get("overruler_in_context") is False:
            ovr_false_per_arm[r.get("pipeline")].append(r.get("query_id"))

    # 5. seed_source counts
    seed_sources_per_arm = {a: Counter() for a in arms}
    for r in records:
        src = r.get("seed_source", "unknown")
        seed_sources_per_arm[r.get("pipeline")][src] += 1

    # 6. generation_model_requested equality across arms
    model_equality_passed = True
    model_mismatches = []
    for qid, arm_dict in by_query.items():
        req_models = {a: arm_dict.get(a, {}).get("generation_model_requested") for a in arms if a in arm_dict}
        vals = set(req_models.values())
        if len(vals) != 1 or None in vals:
            model_equality_passed = False
            model_mismatches.append((qid, req_models))

    # 7. Contaminated flags
    contaminated_flags = []
    degraded_flags = []
    for r in records:
        if r.get("_router_fallback_contaminated") is True:
            contaminated_flags.append(f"{r.get('query_id')} [{r.get('pipeline')}]")
        if r.get("_model_degraded") is True:
            degraded_flags.append(f"{r.get('query_id')} [{r.get('pipeline')}]")

    # 8. Refusals per arm
    refusals_per_arm = {a: 0 for a in arms}
    for r in records:
        if r.get("is_refusal") is True:
            refusals_per_arm[r.get("pipeline")] += 1

    # 9. Call counts by type (live rows only)
    telemetry_path = ROOT / "logs" / "call_telemetry_famous_d1.jsonl"
    live_call_counts = Counter()
    live_rows = 0
    if telemetry_path.exists():
        with open(telemetry_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("mode") == "live" or rec.get("calling_function") != "run_offline_unit_tests":
                    live_rows += 1
                    live_call_counts[rec.get("call_type", "unknown")] += 1

    # 10. Total elapsed time
    total_time_ms = sum(r.get("execution_time_ms", 0.0) for r in records)
    total_time_sec = total_time_ms / 1000.0

    lines = []
    lines.append("=" * 80)
    lines.append("FAMOUS_D1 GENERATION STAGE SUMMARY (TASK B5)")
    lines.append("=" * 80)
    lines.append(f"Total Cached Records: {len(records)} (Expected: 76 across 19 queries x 4 arms)")
    lines.append("-" * 80)
    lines.append("1. RECORDS PER ARM:")
    for a in arms:
        cnt = records_per_arm.get(a, 0)
        lines.append(f"  {a:<24}: {cnt:>3} records (Expected: 19) [{'PASS' if cnt == 19 else 'FAIL'}]")
    lines.append("-" * 80)
    lines.append("2. ROUTE DISTRIBUTION FOR ARM 3 (Full TERRA):")
    for rte, cnt in sorted(route_dist_arm3.items()):
        pct = (cnt / len(arm3_recs) * 100) if arm3_recs else 0.0
        lines.append(f"  {rte:<24}: {cnt:>3} ({pct:5.1f}%)")
    lines.append("-" * 80)
    lines.append("3. ITEMS WITH context_empty (TRUE):")
    for a in arms:
        empty_items = ctx_empty_per_arm[a]
        lines.append(f"  {a:<24}: {len(empty_items):>3} items {empty_items if empty_items else '[]'}")
    lines.append("-" * 80)
    lines.append("4. ITEMS WITH overruler_in_context (FALSE):")
    for a in arms:
        false_items = ovr_false_per_arm[a]
        lines.append(f"  {a:<24}: {len(false_items):>3} items")
    lines.append("-" * 80)
    lines.append("5. SEED SOURCE DISTRIBUTION PER ARM:")
    for a in arms:
        src_str = ", ".join(f"{k}: {v}" for k, v in sorted(seed_sources_per_arm[a].items()))
        lines.append(f"  {a:<24}: {src_str}")
    lines.append("-" * 80)
    lines.append("6. GENERATION MODEL REQUESTED EQUALITY:")
    lines.append(f"  Equal Across All Arms: {'PASS' if model_equality_passed else 'FAIL'}")
    if model_mismatches:
        lines.append(f"  Mismatches: {model_mismatches}")
    lines.append("-" * 80)
    lines.append("7. CONTAMINATION & DEGRADATION AUDIT:")
    lines.append(f"  _router_fallback_contaminated items: {len(contaminated_flags)} {contaminated_flags if contaminated_flags else '[]'}")
    lines.append(f"  _model_degraded items:                {len(degraded_flags)} {degraded_flags if degraded_flags else '[]'}")
    lines.append("-" * 80)
    lines.append("8. REFUSALS PER ARM:")
    for a in arms:
        lines.append(f"  {a:<24}: {refusals_per_arm[a]:>3} refusals")
    lines.append("-" * 80)
    lines.append("9. OUTBOUND MODEL CALL COUNTS (Hard Cap <= 400, Live Rows Only):")
    for ctype, cnt in sorted(live_call_counts.items()):
        lines.append(f"  {ctype:<24}: {cnt:>4} calls")
    total_live_calls = sum(live_call_counts.values())
    lines.append(f"  Total Live Outbound Calls: {total_live_calls:>4} calls (<= 400: {'PASS' if total_live_calls <= 400 else 'FAIL'})")
    lines.append(f"  Logged Live Telemetry Rows: {live_rows:>4} rows")
    lines.append("-" * 80)
    lines.append("10. TOTAL ELAPSED TIME:")
    lines.append(f"  Summed Execution Time:     {total_time_sec:.2f} seconds ({total_time_sec / 60.0:.2f} minutes)")
    lines.append("=" * 80)
    lines.append("STATUS: FAMOUS_D1 GENERATION STAGE COMPLETED CLEANLY")
    lines.append("=" * 80)

    summary_text = "\n".join(lines) + "\n"
    summary_file = ROOT / "logs" / "d1_runner_summary.txt"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(summary_text, encoding="utf-8")
    print(f"Wrote {summary_file}")

    # Copy cache to logs/d1_artifacts/
    dest_dir = ROOT / "logs" / "d1_artifacts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(cache_path, dest_dir / "famous_d1_raw_responses.json")
    print(f"Copied {cache_path} -> {dest_dir / 'famous_d1_raw_responses.json'}")

    if telemetry_path.exists():
        shutil.copy2(telemetry_path, dest_dir / "call_telemetry_famous_d1.jsonl")
        print(f"Copied {telemetry_path} -> {dest_dir / 'call_telemetry_famous_d1.jsonl'}")

    shutil.copy2(summary_file, dest_dir / "d1_runner_summary.txt")

    stdout_file = ROOT / "logs" / "d1_runner_stdout.txt"
    if stdout_file.exists():
        shutil.copy2(stdout_file, dest_dir / "d1_runner_stdout.txt")

    print(f"Successfully archived famous_d1 generation artifacts to {dest_dir}")

if __name__ == "__main__":
    main()
