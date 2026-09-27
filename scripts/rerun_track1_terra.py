#!/usr/bin/env python3
"""
scripts/rerun_track1_terra.py

Re-runs Track 1 (120 Precedent Benchmark cases) for 5_Full_TERRA
with the NLI Smart Grader entailment gate actively wired.
Preserves 1_Direct_LLM and 2_Flat_Vector_RAG (240 rows), replacing only 5_Full_TERRA (120 rows).
"""

import os
import sys
import json
import time
import threading
import concurrent.futures

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from baselines.casefacts_harness import CaseFactsHarness, atomic_save
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, '.env'))

TRACK1_INPUT = os.path.join(ROOT_DIR, 'data', 'casefacts_eval_120.json')
TRACK1_OUTPUT = os.path.join(ROOT_DIR, 'scratch', 'casefacts_120_eval_raw.json')

file_lock = threading.Lock()

def rerun():
    print("=" * 80)
    print("RE-RUNNING TRACK 1 (5_Full_TERRA, N=120) WITH ACTIVE NLI SMART GRADER GATE")
    print("=" * 80)

    with open(TRACK1_INPUT, 'r', encoding='utf-8') as f:
        track1_items = json.load(f)
    print(f"Loaded {len(track1_items)} Track 1 items from {TRACK1_INPUT}")

    with open(TRACK1_OUTPUT, 'r', encoding='utf-8') as f:
        existing_rows = json.load(f)
    
    # Filter out old 5_Full_TERRA rows
    non_terra_rows = [r for r in existing_rows if r['pipeline'] != '5_Full_TERRA']
    print(f"Preserving {len(non_terra_rows)} existing baseline rows (Direct LLM + Flat RAG).")

    harness = CaseFactsHarness()
    tasks = [(item, "5_Full_TERRA") for item in track1_items]
    print(f"Executing {len(tasks)} Full TERRA tasks with active Smart Grader gate...")

    completed_terra = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_item = {
            executor.submit(harness.process_item, item, "5_Full_TERRA", False): item["id"]
            for item, pipe in tasks
        }

        for future in concurrent.futures.as_completed(future_to_item):
            item_id = future_to_item[future]
            try:
                res = future.result()
                with file_lock:
                    completed_terra.append(res)
                    combined = non_terra_rows + completed_terra
                    atomic_save(combined, TRACK1_OUTPUT)
                corr_str = "[CORRECT]" if res["consensus_correct"] or res["direct_match"] else "[INCORRECT]"
                short_circuit = "[REFUSAL/SHORT-CIRCUIT]" if "insufficient validated legal context" in res.get("answer", "") else "[EVALUATED]"
                print(f"[{len(completed_terra)}/{len(tasks)}] {item_id} | 5_Full_TERRA | GT: {res['ground_truth']:<12} | Pred: {res['parsed_label']:<24} | {short_circuit} | {corr_str}")
            except Exception as e:
                print(f"[ERROR] Task failed for {item_id}: {e}")

    print(f"\n[SUCCESS] Track 1 TERRA re-run completed! Updated {TRACK1_OUTPUT} (Total rows: {len(non_terra_rows) + len(completed_terra)})")

if __name__ == '__main__':
    rerun()
