#!/usr/bin/env python3
"""
scripts/rerun_track2_terra.py

Re-runs Track 2 (50 Out-of-Corpus Refusal Control cases) for 5_Full_TERRA
with the NLI Smart Grader entailment gate actively wired.
Preserves 1_Direct_LLM and 2_Flat_Vector_RAG (100 rows), replacing only 5_Full_TERRA (50 rows).
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

TRACK2_INPUT = os.path.join(ROOT_DIR, 'data', 'casefacts_refusal_control_50.json')
TRACK2_OUTPUT = os.path.join(ROOT_DIR, 'scratch', 'casefacts_50_refusal_eval_raw.json')

file_lock = threading.Lock()

def rerun():
    print("=" * 80)
    print("RE-RUNNING TRACK 2 (5_Full_TERRA) WITH NLI SMART GRADER WIRED")
    print("=" * 80)

    with open(TRACK2_INPUT, 'r', encoding='utf-8') as f:
        track2_items = json.load(f)
    print(f"Loaded {len(track2_items)} Track 2 items from {TRACK2_INPUT}")

    with open(TRACK2_OUTPUT, 'r', encoding='utf-8') as f:
        existing_rows = json.load(f)
    
    # Filter out old 5_Full_TERRA rows
    non_terra_rows = [r for r in existing_rows if r['pipeline'] != '5_Full_TERRA']
    print(f"Preserving {len(non_terra_rows)} existing baseline rows (Direct LLM + Flat RAG).")

    harness = CaseFactsHarness()
    updated_results = list(non_terra_rows)

    tasks = [(item, "5_Full_TERRA") for item in track2_items]
    print(f"Executing {len(tasks)} Full TERRA tasks with active Smart Grader gate...")

    completed_terra = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_item = {
            executor.submit(harness.process_item, item, "5_Full_TERRA", True): item["id"]
            for item, pipe in tasks
        }

        for future in concurrent.futures.as_completed(future_to_item):
            item_id = future_to_item[future]
            try:
                res = future.result()
                with file_lock:
                    completed_terra.append(res)
                    combined = non_terra_rows + completed_terra
                    atomic_save(combined, TRACK2_OUTPUT)
                corr_str = "[REFUSED/CORRECT]" if res["consensus_correct"] or res["direct_match"] else "[NON-REFUSAL]"
                print(f"[{len(completed_terra)}/{len(tasks)}] {item_id} | 5_Full_TERRA | GT: {res['ground_truth']:<22} | Pred: {res['parsed_label']:<22} | {corr_str}")
            except Exception as e:
                print(f"[ERROR] Task failed for {item_id}: {e}")

    print(f"\n[SUCCESS] Re-run completed! Updated {TRACK2_OUTPUT} (Total rows: {len(non_terra_rows) + len(completed_terra)})")

if __name__ == '__main__':
    rerun()
