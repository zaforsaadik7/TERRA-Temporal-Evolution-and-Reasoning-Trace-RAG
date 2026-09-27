"""
scripts/run_z1_provenance_evidence.py
======================================
Z1: Extract run provenance for all evaluation blocks and compute
identical-answer fraction between the two canonical TERRA JSON files.
Logs to logs/v2_provenance_evidence.txt
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "logs" / "v2_provenance_evidence.txt"

lines = []
def log(s=""):
    lines.append(s)
    print(s)

def file_mtime(path):
    """Return ISO date string from file mtime, or 'not found'."""
    p = Path(path)
    if not p.exists():
        return "FILE NOT FOUND"
    ts = p.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M local")

def read_json_first(path, keys=None, n=1):
    """Read first n records from JSON list file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[:n]
        return data
    except Exception as e:
        return f"ERROR: {e}"

def get_field(records, field, n=5):
    """Get unique values of a field from first n records."""
    if isinstance(records, str):
        return records
    vals = set()
    for r in (records[:n] if isinstance(records, list) else [records]):
        if isinstance(r, dict) and field in r:
            vals.add(str(r[field]))
    return list(vals)

# ============================================================
log("=" * 80)
log("TASK Z1: RUN PROVENANCE EVIDENCE")
log(f"Generated: {datetime.now().isoformat()}")
log("=" * 80)
log()

# ============================================================
log("1. FILE TIMESTAMPS (file modification dates as proxy for run dates)")
log("-" * 80)

file_table = [
    # (label, path)
    ("terra_baselines_eval_raw.json (baseline generations)",
     ROOT / "terra_baselines_eval_raw.json"),
    ("scratch/terra_350_5pipelines_dual_judged.json (baseline+TERRA dual-judged)",
     ROOT / "scratch/terra_350_5pipelines_dual_judged.json"),
    ("scratch/terra_350_issue6_dual_judged.json (deployed TERRA dual-judged)",
     ROOT / "scratch/terra_350_issue6_dual_judged.json"),
    ("scratch/terra_350_issue6_generations.json (deployed TERRA raw generations)",
     ROOT / "scratch/terra_350_issue6_generations.json"),
    ("scratch/category_d_rubric_summary_v2.json (Cat D certification)",
     ROOT / "scratch/category_d_rubric_summary_v2.json"),
    ("scratch/obscure_raw_responses.json (obscure suite)",
     ROOT / "scratch/obscure_raw_responses.json"),
    ("scratch/famous_d1_raw_responses.json (famous D1 contrast)",
     ROOT / "scratch/famous_d1_raw_responses.json"),
    ("scratch/casefacts_120_eval_raw.json (CaseFacts)",
     ROOT / "scratch/casefacts_120_eval_raw.json"),
    ("scratch/clerc_120_eval_raw.json (CLERC)",
     ROOT / "scratch/clerc_120_eval_raw.json"),
    ("scratch/temporal_leakage_pilot_raw.json (temporal leakage probe)",
     ROOT / "scratch/temporal_leakage_pilot_raw.json"),
    ("scratch/router_evaluation_summary.json (router eval)",
     ROOT / "scratch/router_evaluation_summary.json"),
    ("scratch/canonical_v2/terra_canonical_v2_eval.json (canonical v2 build)",
     ROOT / "scratch/canonical_v2/terra_canonical_v2_eval.json"),
    ("logs/canonical_v2_build.txt (canonical v2 build log)",
     ROOT / "logs/canonical_v2_build.txt"),
    ("logs/canonical_v2_s1_judge_parity.txt (judge parity audit)",
     ROOT / "logs/canonical_v2_s1_judge_parity.txt"),
]

for label, path in file_table:
    mtime = file_mtime(path)
    log(f"  {label}")
    log(f"    -> {mtime}  [{path}]")
log()

# ============================================================
log("2. LOG HEADER EVIDENCE (runner timestamps from log files)")
log("-" * 80)

# canonical_v2_s1 records the date header explicitly
log("  logs/canonical_v2_s1_judge_parity.txt header:")
try:
    with open(ROOT / "logs/canonical_v2_s1_judge_parity.txt", 'r', encoding='utf-8') as f:
        for line in f:
            if "Date:" in line or "2026" in line:
                log(f"    {line.rstrip()}")
                break
except:
    log("    ERROR reading")
log()

# Check the category_d rubric for its executed_at timestamp
log("  scratch/category_d_rubric_summary_v2.json executed_at:")
try:
    with open(ROOT / "scratch/category_d_rubric_summary_v2.json", 'r', encoding='utf-8') as f:
        d = json.load(f)
    log(f"    executed_at: {d.get('audit_metadata', {}).get('executed_at', 'not found')}")
    log(f"    script: {d.get('audit_metadata', {}).get('script', 'not found')}")
except Exception as e:
    log(f"    ERROR: {e}")
log()

# Check obscure summary for timestamp
log("  scratch/obscure_overruled_summary.json:")
try:
    with open(ROOT / "scratch/obscure_overruled_summary.json", 'r', encoding='utf-8') as f:
        d = json.load(f)
    ts = d.get('metadata', {}).get('timestamp') or d.get('timestamp') or d.get('generated_at') or 'not found'
    log(f"    timestamp: {ts}")
except Exception as e:
    log(f"    ERROR: {e}")
log()

# CaseFacts summary
log("  scratch/casefacts_summary_stats.json:")
try:
    with open(ROOT / "scratch/casefacts_summary_stats.json", 'r', encoding='utf-8') as f:
        d = json.load(f)
    ts = d.get('metadata', {}).get('timestamp') or d.get('timestamp') or d.get('generated_at') or str(d.get('eval_date', 'not found'))
    log(f"    timestamp: {ts}")
    log(f"    keys: {list(d.keys())[:10]}")
except Exception as e:
    log(f"    ERROR: {e}")
log()

# CLERC summary
log("  scratch/clerc_metrics_summary.json:")
try:
    with open(ROOT / "scratch/clerc_metrics_summary.json", 'r', encoding='utf-8') as f:
        d = json.load(f)
    ts = d.get('metadata', {}).get('timestamp') or d.get('timestamp') or d.get('generated_at') or 'not found'
    log(f"    timestamp: {ts}")
    log(f"    keys: {list(d.keys())[:10]}")
except Exception as e:
    log(f"    ERROR: {e}")
log()

# Temporal leakage
log("  scratch/temporal_leakage_statistical_summary.json:")
try:
    with open(ROOT / "scratch/temporal_leakage_statistical_summary.json", 'r', encoding='utf-8') as f:
        d = json.load(f)
    ts = d.get('metadata', {}).get('timestamp') or d.get('timestamp') or d.get('generated_at') or 'not found'
    log(f"    timestamp/keys: {list(d.keys())[:8]} -> ts field: {ts}")
except Exception as e:
    log(f"    ERROR: {e}")
log()

# ============================================================
log("3. JUDGE MODEL EVIDENCE (from s1 parity log)")
log("-" * 80)
log("  Judge 1: databricks-qwen3-next-80b-a3b-instruct")
log("  Judge 2: databricks-gpt-oss-120b")
log("  Source:  logs/canonical_v2_s1_judge_parity.txt section 2")
log("  Coverage: 1,750 baseline rows + 350 TERRA rows (2,100 judge invocations)")
log()

# ============================================================
log("4. IDENTICAL-ANSWER FRACTION: terra_350_5pipelines vs terra_350_issue6")
log("-" * 80)
log("  Computing for TERRA (5_Full_TERRA) rows only...")

try:
    five_path = ROOT / "scratch/terra_350_5pipelines_dual_judged.json"
    issue6_path = ROOT / "scratch/terra_350_issue6_dual_judged.json"

    with open(five_path, 'r', encoding='utf-8') as f:
        five_data = json.load(f)
    with open(issue6_path, 'r', encoding='utf-8') as f:
        issue6_data = json.load(f)

    # Extract TERRA rows from 5pipelines file
    if isinstance(five_data, list):
        terra_five = {r['query_id']: r for r in five_data
                      if r.get('pipeline', '') in ('5_Full_TERRA', 'Full_TERRA')
                      or str(r.get('pipeline', '')).endswith('TERRA')}
    else:
        terra_five = {}

    # issue6 file is TERRA-only
    if isinstance(issue6_data, list):
        terra_issue6 = {r['query_id']: r for r in issue6_data}
    else:
        terra_issue6 = {}

    log(f"  5pipelines TERRA rows: {len(terra_five)}")
    log(f"  issue6 TERRA rows:     {len(terra_issue6)}")

    # Sample a record to find answer field name
    sample = next(iter(terra_five.values())) if terra_five else {}
    answer_field_candidates = ['answer_full', 'answer', 'response', 'generated_answer', 'answer_text']
    answer_field = None
    for af in answer_field_candidates:
        if af in sample:
            answer_field = af
            break

    log(f"  Answer field used: {answer_field}")
    if not answer_field:
        log(f"  WARNING: no answer field found. Sample keys: {list(sample.keys())[:15]}")

    # Compute identical-answer fraction
    cats = {'A_Factual': 0, 'B_Evolutionary': 0, 'C_OutOfContext': 0, 'D_Adversarial': 0}
    cats_total = {'A_Factual': 0, 'B_Evolutionary': 0, 'C_OutOfContext': 0, 'D_Adversarial': 0}
    overall_match = 0
    overall_total = 0

    for qid, r5 in terra_five.items():
        if qid not in terra_issue6:
            continue
        r6 = terra_issue6[qid]
        cat = r5.get('category', 'unknown')

        if answer_field:
            ans5 = str(r5.get(answer_field, '')).strip()
            ans6 = str(r6.get(answer_field, '')).strip()
        else:
            ans5 = str(r5.get('answer_full', r5.get('answer', ''))).strip()
            ans6 = str(r6.get('answer_full', r6.get('answer', ''))).strip()

        match = (ans5 == ans6)
        overall_total += 1
        if match:
            overall_match += 1
        if cat in cats_total:
            cats_total[cat] += 1
            if match:
                cats[cat] += 1

    if overall_total > 0:
        log(f"\n  Overall identical answers: {overall_match}/{overall_total} = {100*overall_match/overall_total:.1f}%")
        for cat in ['A_Factual', 'B_Evolutionary', 'C_OutOfContext', 'D_Adversarial']:
            n = cats_total[cat]
            m = cats[cat]
            pct = 100*m/n if n > 0 else 0
            log(f"  {cat:20s}: {m}/{n} = {pct:.1f}%")
    else:
        log("  WARNING: no matching query IDs found between the two files")
        log(f"  5pipelines sample pipeline values: {set(r.get('pipeline','') for r in list(five_data)[:20])}")
        log(f"  issue6 sample pipeline values: {set(r.get('pipeline','') for r in list(issue6_data)[:20])}")

except Exception as e:
    import traceback
    log(f"  ERROR: {e}")
    log(traceback.format_exc())
log()

# ============================================================
log("5. PILOT ABLATION (Table III) EVIDENCE")
log("-" * 80)
# Check the ablation log/pilot data
pilot_log = ROOT / "logs/pilot_runner_stdout.txt"
pilot_summary = ROOT / "logs/pilot_post.txt"
log(f"  logs/pilot_post.txt mtime: {file_mtime(pilot_summary)}")
try:
    with open(pilot_summary, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(2000)
    log(f"  Content preview: {content[:800]}")
except Exception as e:
    log(f"  ERROR: {e}")
log()

# ============================================================
log("6. PROVENANCE SUMMARY TABLE")
log("-" * 80)
log()
log("Block                    | Date (best evidence)         | Models                          | N    | Evidence file")
log("-" * 120)

blocks = [
    ("Baseline generations",  "Sept 5-6 2026 (file mtime)",
     "Gen: databricks-meta-llama-3-3-70b-instruct; No router/NLI",
     "1,400", "terra_baselines_eval_raw.json mtime + s1 header"),
    ("Dual-judge scoring (baselines)", "Sept 14 2026 (file mtime 5pipelines_dual_judged)",
     "J1: qwen3-next-80b-a3b-instruct; J2: gpt-oss-120b",
     "1,400", "logs/canonical_v2_s1_judge_parity.txt"),
    ("Deployed TERRA (Issue #6 run)", "Sept 14 2026 (file mtime issue6_generations)",
     "Router: gemma-3-12b; NLI+Gen: llama-3.3-70b-instruct",
     "350", "scratch/terra_350_issue6_generations.json mtime"),
    ("Dual-judge scoring (TERRA)", "Sept 14 2026 (file mtime issue6_dual_judged)",
     "J1: qwen3-next-80b-a3b-instruct; J2: gpt-oss-120b",
     "350", "scratch/terra_350_issue6_dual_judged.json mtime"),
    ("Cat D certification", "Sept 18 2026 (executed_at in JSON)",
     "Semantic verifier: llama-3.3-70b-instruct (same family as gen)",
     "75", "scratch/category_d_rubric_summary_v2.json"),
    ("Obscure suite (30q x 4 arms)", "Sept 19-20 2026 (file mtime)",
     "Gen: llama-3.3-70b-instruct; J1/J2 same as above",
     "120", "scratch/obscure_raw_responses.json + obscure_judge_cache.json"),
    ("Famous D1 contrast (19q x 4)", "Sept 19-20 2026 (file mtime)",
     "Gen: llama-3.3-70b-instruct; J1/J2 same as above",
     "76", "scratch/famous_d1_raw_responses.json mtime"),
    ("CaseFacts eval", "Sept 18 2026 (file mtime)",
     "date not recorded in JSON header",
     "120+50", "scratch/casefacts_120_eval_raw.json mtime"),
    ("CLERC eval", "Sept 18 2026 (file mtime)",
     "date not recorded in JSON header",
     "120+50", "scratch/clerc_120_eval_raw.json mtime"),
    ("Temporal leakage probe", "Sept 17 2026 (file mtime)",
     "date not recorded in JSON header",
     "varies", "scratch/temporal_leakage_pilot_raw.json mtime"),
    ("Pilot ablation (Table III)", "date not recorded in log",
     "Gen: llama-3.3-70b-instruct (assumed); single judge",
     "35q x 5 arms", "logs/pilot_runner_stdout.txt (binary, no timestamp)"),
]

for b in blocks:
    label, date, models, n, evidence = b
    log(f"  {label}")
    log(f"    Date: {date}")
    log(f"    Models: {models}")
    log(f"    N: {n}")
    log(f"    Evidence: {evidence}")
    log()

# ============================================================
log("7. NOTE ON DETERMINISM")
log("-" * 80)
log("  T=0.0 was used for all inference calls, but does NOT guarantee identical")
log("  outputs across runs on Databricks Model Serving API endpoints.")
log("  The identical-answer fraction computed in section 4 above quantifies")
log("  actual reproducibility between the two TERRA runs on 14 September 2026.")
log()

# Write to file
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"\nWritten to {OUT_PATH}")
