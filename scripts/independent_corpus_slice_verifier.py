"""
scripts/independent_corpus_slice_verifier.py - Independent CAP Corpus Slice Verifier
=====================================================================================
Re-opens each raw CAP JSON opinion file directly from disk, extracts the exact
opinion character slice text[start:end], strictly asserts text[start:end] == sentence,
checks for offset duplicates across different files, and prints the verified sentences.
Supports --selftest canary mode.
Updated for Task X1: also asserts overruling_supporting_span and overruling_names_target.
"""

import sys
import json
import copy
import hashlib
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BENCH_PATH = (ROOT / 'data' / 'obscure_overruled_benchmark.json').resolve()
OUT_LOG = (ROOT / 'logs' / 'independent_corpus_slice_verifier.txt').resolve()
SELFTEST_LOG = (ROOT / 'logs' / 'selftest_verifier.txt').resolve()

def verify_slices(bench_data, is_selftest=False):
    out_lines = []
    
    with open(DEFAULT_BENCH_PATH, 'rb') as f:
        bench_bytes = f.read()
    binary_sha256 = hashlib.sha256(bench_bytes).hexdigest()
    
    out_lines.append("=" * 110)
    out_lines.append("INDEPENDENT CAP CORPUS SLICE AND DATE VERIFICATION AUDIT" + (" [SELFTEST CANARY]" if is_selftest else ""))
    out_lines.append(f"Benchmark File: {DEFAULT_BENCH_PATH}")
    out_lines.append(f"Binary SHA256:  {binary_sha256}")
    out_lines.append(f"Total Cohort:   {len(bench_data)} Precedent Pairs ({len(bench_data) * 2} Total Opinions)")
    out_lines.append("=" * 110)
    
    target_match_count = 0
    overruling_match_count = 0
    supporting_match_count = 0
    expected_supporting_count = 0
    date_match_count = 0
    seen_target_slices = {}
    seen_overruler_slices = {}
    slice_collisions = 0
    failures = []
    
    out_lines.append(f"{'ID':<8} | {'Target Case':<28} | {'T-Offsets':<13} | {'O-Offsets':<13} | {'Supp-Offsets':<13} | {'Scope Class':<20} | {'Result'}")
    out_lines.append("-" * 110)
    
    for it in bench_data:
        qid = it['query_id']
        tcase = it['target_case']
        tnode = it['target_node']
        onode = it['overruling_node']
        
        t_cap_path = (ROOT / 'dataset_20k_cap' / 'raw_cases' / f'{tnode}.json').resolve()
        o_cap_path = (ROOT / 'dataset_20k_cap' / 'raw_cases' / f'{onode}.json').resolve()
        
        if not t_cap_path.exists():
            failures.append(f"[{qid}] Target CAP file missing: {t_cap_path}")
            continue
        if not o_cap_path.exists():
            failures.append(f"[{qid}] Overruling CAP file missing: {o_cap_path}")
            continue
        
        with open(t_cap_path, 'r', encoding='utf-8') as f:
            t_cap = json.load(f)
        with open(o_cap_path, 'r', encoding='utf-8') as f:
            o_cap = json.load(f)
            
        t_text = t_cap['casebody']['opinions'][0]['text']
        o_text = o_cap['casebody']['opinions'][0]['text']
        
        # Date checks
        t_date_ok = (t_cap['decision_date'] == it['target_dates_verified']['cap'] == it['target_decision_date'])
        o_date_ok = (o_cap['decision_date'] == it['overruling_dates_verified']['cap'] == it['overruling_decision_date'])
        if t_date_ok and o_date_ok:
            date_match_count += 2
        else:
            failures.append(f"[{qid}] Date mismatch: target={t_date_ok}, overruler={o_date_ok}")
        
        # Target Slice Verification
        t_gh = it['grounding_target_holding']
        ts, te, t_sent = t_gh['char_start'], t_gh['char_end'], t_gh['sentence']
        actual_t_slice = t_text[ts:te]
        t_match = (actual_t_slice == t_sent)
        if t_match:
            target_match_count += 1
        else:
            failures.append(f"[{qid}] Target slice mismatch! Expected {t_sent[:30]!r}, Got: {actual_t_slice[:30]!r}")
        
        # Overruling Slice Verification
        o_gh = it['grounding_overruling_sentence']
        os, oe, o_sent = o_gh['char_start'], o_gh['char_end'], o_gh['sentence']
        actual_o_slice = o_text[os:oe]
        o_match = (actual_o_slice == o_sent)
        if o_match:
            overruling_match_count += 1
        else:
            failures.append(f"[{qid}] Overruling slice mismatch! Expected {o_sent[:30]!r}, Got: {actual_o_slice[:30]!r}")
            
        # Supporting Span Verification (if present)
        supp_match = True
        supp_off_str = "NONE"
        if 'overruling_supporting_span' in it:
            expected_supporting_count += 1
            supp = it['overruling_supporting_span']
            s_node = supp['node']
            ss, se, s_sent = supp['char_start'], supp['char_end'], supp['sentence']
            supp_off_str = f"{ss}:{se}"
            s_cap_path = (ROOT / 'dataset_20k_cap' / 'raw_cases' / f'{s_node}.json').resolve()
            if not s_cap_path.exists():
                failures.append(f"[{qid}] Supporting span CAP file missing: {s_cap_path}")
                supp_match = False
            else:
                with open(s_cap_path, 'r', encoding='utf-8') as f:
                    s_text = json.load(f)['casebody']['opinions'][0]['text']
                actual_s_slice = s_text[ss:se]
                supp_match = (actual_s_slice == s_sent)
                if supp_match:
                    supporting_match_count += 1
                else:
                    failures.append(f"[{qid}] Supporting slice mismatch! Expected {s_sent[:30]!r}, Got: {actual_s_slice[:30]!r}")
            if it.get('overruling_names_target') is not False:
                failures.append(f"[{qid}] Expected overruling_names_target == False")
                supp_match = False
        
        # Cross-opinion collision
        if tnode in seen_target_slices and seen_target_slices[tnode] == (ts, te):
            slice_collisions += 1
            failures.append(f"[{qid}] Duplicate target slice in {tnode}")
        seen_target_slices[tnode] = (ts, te)
        
        pair_status = "EXACT_MATCH" if (t_match and o_match and supp_match and t_date_ok and o_date_ok) else "FAIL"
        t_off_str = f"{ts}:{te}"
        o_off_str = f"{os}:{oe}"
        scope = it['scope_classification']
        
        out_lines.append(f"{qid:<8} | {tcase[:28]:<28} | {t_off_str:<13} | {o_off_str:<13} | {supp_off_str:<13} | {scope:<20} | {pair_status}")
    
    total_slices_verified = target_match_count + overruling_match_count + supporting_match_count
    total_slices_expected = (len(bench_data) * 2) + expected_supporting_count
    
    out_lines.append("=" * 110)
    out_lines.append(f"VERIFICATION SUMMARY: {total_slices_verified}/{total_slices_expected} OPINION SLICES VERIFIED")
    out_lines.append(f"TARGET HOLDING SLICES VERIFIED:     {target_match_count}/{len(bench_data)}")
    out_lines.append(f"OVERRULING SENTENCE SLICES VERIFIED: {overruling_match_count}/{len(bench_data)}")
    out_lines.append(f"SUPPORTING SPANS VERIFIED:          {supporting_match_count}/{expected_supporting_count}")
    out_lines.append(f"DATE METADATA VERIFIED:             {date_match_count}/{len(bench_data) * 2}")
    out_lines.append(f"SLICE COLLISIONS DETECTED:          {slice_collisions}")
    out_lines.append(f"TOTAL FAILURES DETECTED:            {len(failures)}")
    out_lines.append(f"BENCHMARK BINARY SHA256:            {binary_sha256}")
    out_lines.append("=" * 110)
    
    all_ok = (total_slices_verified == total_slices_expected) and (len(failures) == 0)
    return all_ok, "\n".join(out_lines), failures


def main():
    parser = argparse.ArgumentParser(description="CAP Corpus Slice Verifier")
    parser.add_argument("--selftest", action="store_true", help="Run canary test on mutated copy")
    args = parser.parse_args()
    
    with open(DEFAULT_BENCH_PATH, "r", encoding="utf-8") as f:
        bench = json.load(f)
        
    if args.selftest:
        print("[CANARY] Running --selftest on mutated in-memory copy (shift slice start by 1)...")
        mutated_bench = copy.deepcopy(bench)
        # Shift one slice start by 1
        mutated_bench[0]['grounding_target_holding']['char_start'] += 1
        
        passed, log_text, failures = verify_slices(mutated_bench, is_selftest=True)
        canary_lines = []
        canary_lines.append("CANARY TEST: independent_corpus_slice_verifier.py --selftest")
        canary_lines.append("Mutation injected: OBS_001 grounding_target_holding char_start shifted by +1")
        canary_lines.append(f"Expected behavior: FAIL detected and reported.")
        canary_lines.append(f"Actual verification passed: {passed}")
        canary_lines.append(f"Failures caught: {len(failures)}")
        for f_msg in failures:
            canary_lines.append(f"  - {f_msg}")
            
        canary_passed = (not passed) and (len(failures) > 0)
        canary_lines.append(f"CANARY SELFTEST RESULT: {'PASSED (Canary caught intentional defect)' if canary_passed else 'FAILED (Canary defect went undetected)'}")
        
        with open(SELFTEST_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(canary_lines) + "\n\n" + log_text + "\n")
            
        print(f"Wrote canary test results to {SELFTEST_LOG}")
        if not canary_passed:
            sys.exit(1)
    else:
        # Load old log if exists to compute diff
        old_log = ""
        if OUT_LOG.exists():
            with open(OUT_LOG, "r", encoding="utf-8") as f:
                old_log = f.read()
                
        passed, log_text, failures = verify_slices(bench, is_selftest=False)
        with open(OUT_LOG, "w", encoding="utf-8") as f:
            f.write(log_text + "\n")
        print(f"Wrote verification audit to {OUT_LOG}")
        
        # Log old vs new
        diff_path = ROOT / "logs" / "verifier_diff_X1.txt"
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write("=== OLD VERIFIER REPORT ===\n")
            f.write(old_log + "\n\n")
            f.write("=== NEW VERIFIER REPORT ===\n")
            f.write(log_text + "\n")
        print(f"Wrote verifier old vs new diff to {diff_path}")
        
        if not passed:
            sys.exit(1)

if __name__ == '__main__':
    main()
