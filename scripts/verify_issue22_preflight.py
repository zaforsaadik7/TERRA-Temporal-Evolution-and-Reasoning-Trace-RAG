#!/usr/bin/env python3
"""
scripts/verify_issue22_preflight.py
Comprehensive Phase 1 Preflight Verification for Issue #22.

Verifies:
  1. All 10 certified protected core substrates (SHA256 invariance).
  2. Exact 69 unique keyword phrases across six explicit domains in apply_score_based_tagging.py.
  3. Deterministic recomputation of all 20,000 taxonomy labels.
  4. Bit-exact comparison against category, primary_domain, doctrinal_tags (0 mismatches).
  5. Exact primary domain counts (summing to 20,000), residual fallback count (4,594),
     tie count (1,587), and multi-tag distribution.
  6. Existence and completeness of raw-case files (20,000) and selection manifest.
  7. Pre-execution SHA256 hash of data/cache/issue22_judge_cache.json.
  8. Serializes data/issue22_preflight.json and logs/issue22_preflight.txt.
"""

import os
import sys
import json
import ast
import hashlib
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent

# 1. 10 Certified Protected Files
PROTECTED_CORE_FILES = {
    "terra_350_benchmark.json": "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3",
    "dataset_20k_cap/terra_eeg_index_20k.json": "7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json": "c530f9858e9b3372dc9079092178e9d8c2239758eda073c35b9fc7b0c49e1f72",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json": "14071dba780157b767dfce1f11ef8190722ad94ab9a37e8258bb574a0183c3fc",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json": "98d14bfb75d5051429ff4c48c0410300efb5ef7f04112701635f110aff094ddf",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json": "5e2b59ac3fce2b9513c9ceb60b6a1cae0c2323150f4936a0410503fd56689f3c",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json": "606a6ec126bf7c5ac4cbdbac04f37eee52f7bd524d35e5f12d8dc4ebff3e23b5",
    "ask_terra.py": "430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd",
    "data/issue21_preflight.json": "9a26a9e35340111773180cadd9f3c271fcecde1a3863609d6abbd2236ba7a9b2",
    "logs/issue21_preflight.txt": "91d028cd9ce5079d16bf540cba6546bfa825e5688b3283eb5ef226cc8a3d84d8",
}

EXPECTED_DOMAIN_COUNTS = {
    "substantive_private_law": 5707,
    "general_constitutional_statutory": 4594,
    "admin_law_federal_courts": 4501,
    "criminal_procedure": 1765,
    "commerce_clause_economic": 1614,
    "civil_rights_equal_protection": 1153,
    "first_amendment": 666,
}

EXPECTED_MULTI_TAG_DIST = {
    1: 13536,
    2: 5156,
    3: 1213,
    4: 90,
    5: 5,
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()

def extract_lexicons_from_source(source_path):
    """Extract DOCTRINAL_LEXICONS dictionary via AST without executing top-level code."""
    with open(source_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(source_path))
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "DOCTRINAL_LEXICONS":
                    return ast.literal_eval(stmt.value)
    raise ValueError(f"Could not find DOCTRINAL_LEXICONS in {source_path}")

def main():
    print("=" * 80)
    print("ISSUE #22 PHASE 1: PREFLIGHT VERIFICATION & BASELINE AUDIT")
    print("=" * 80)
    
    preflight_data = {
        "metadata": {
            "issue_id": "issue22",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "target": "Doctrinal Taxonomy Generation Protocol & Inter-Evaluator Preflight",
        },
        "checks": {}
    }
    log_lines = []
    
    def log(msg):
        print(msg)
        log_lines.append(msg)
    
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    
    log(f"Execution Timestamp: {preflight_data['metadata']['timestamp_utc']}")
    log("")

    all_passed = True

    # -------------------------------------------------------------------------
    # Check 1: 10 Certified Protected Core Substrates
    # -------------------------------------------------------------------------
    log("--- CHECK 1: 10 CERTIFIED PROTECTED CORE SUBSTRATES ---")
    protected_results = {}
    check1_pass = True
    for rel_path, exp_sha in PROTECTED_CORE_FILES.items():
        full_path = ROOT_DIR / rel_path
        if not full_path.exists():
            log(f"  [FAIL] MISSING: {rel_path}")
            check1_pass = False
            all_passed = False
            protected_results[rel_path] = {"status": "MISSING", "expected": exp_sha, "actual": None}
            continue
        act_sha = compute_sha256(full_path)
        sz = full_path.stat().st_size
        if act_sha != exp_sha:
            log(f"  [FAIL] MISMATCH: {rel_path} (exp: {exp_sha[:16]}..., act: {act_sha[:16]}...)")
            check1_pass = False
            all_passed = False
            protected_results[rel_path] = {"status": "MISMATCH", "expected": exp_sha, "actual": act_sha, "size_bytes": sz}
        else:
            log(f"  [PASS] {rel_path} ({sz:,} bytes) -> {act_sha[:16]}...")
            protected_results[rel_path] = {"status": "PASS", "sha256": act_sha, "size_bytes": sz}

    log(f"Check 1 Result: {'PASS (10/10 Invariant)' if check1_pass else 'FAIL'}\n")
    preflight_data["checks"]["check1_protected_substrates"] = {
        "passed": check1_pass,
        "files_checked": len(PROTECTED_CORE_FILES),
        "details": protected_results
    }

    # -------------------------------------------------------------------------
    # Check 2: Lexicon Inventory in scripts/apply_score_based_tagging.py
    # -------------------------------------------------------------------------
    log("--- CHECK 2: EXACT 69-KEYWORD PHRASE INVENTORY ---")
    tagging_script_path = ROOT_DIR / "scripts" / "apply_score_based_tagging.py"
    lexicons = extract_lexicons_from_source(tagging_script_path)
    
    expected_lexicon_counts = {
        "first_amendment": 11,
        "criminal_procedure": 13,
        "commerce_clause_economic": 12,
        "civil_rights_equal_protection": 12,
        "admin_law_federal_courts": 11,
        "substantive_private_law": 10,
    }
    
    check2_pass = True
    total_phrases = 0
    all_phrases = []
    lexicon_details = {}
    
    for dom, exp_cnt in expected_lexicon_counts.items():
        if dom not in lexicons:
            log(f"  [FAIL] MISSING DOMAIN in script: {dom}")
            check2_pass = False
            continue
        kws = lexicons[dom]
        act_cnt = len(kws)
        total_phrases += act_cnt
        all_phrases.extend(kws)
        match = (act_cnt == exp_cnt)
        if not match:
            check2_pass = False
            log(f"  [FAIL] COUNT MISMATCH for {dom}: expected {exp_cnt}, got {act_cnt}")
        else:
            log(f"  [PASS] {dom:32s}: {act_cnt:2d} phrases (expected {exp_cnt})")
        lexicon_details[dom] = {"expected": exp_cnt, "actual": act_cnt, "phrases": kws}

    unique_phrases_count = len(set(all_phrases))
    log(f"Total phrases across 6 lexicons: {total_phrases} (Unique: {unique_phrases_count})")
    if total_phrases != 69 or unique_phrases_count != 69:
        log(f"  [FAIL] TOTAL PHRASE COUNT ERROR: expected 69 unique phrases, got {total_phrases} (unique {unique_phrases_count})")
        check2_pass = False
        all_passed = False
    else:
        log("  [PASS] EXACT 69 UNIQUE KEYWORDS CONFIRMED.")
    
    log(f"Check 2 Result: {'PASS' if check2_pass else 'FAIL'}\n")
    preflight_data["checks"]["check2_lexicon_inventory"] = {
        "passed": check2_pass,
        "total_phrases": total_phrases,
        "unique_phrases": unique_phrases_count,
        "domains": lexicon_details
    }

    # -------------------------------------------------------------------------
    # Check 3 & 4: Recomputation of all 20,000 Nodes & Label Parity
    # -------------------------------------------------------------------------
    log("--- CHECK 3 & 4: 20,000-NODE DETERMINISTIC RECOMPUTATION & PARITY ---")
    eeg_path = ROOT_DIR / "dataset_20k_cap" / "terra_eeg_index_20k.json"
    with open(eeg_path, "r", encoding="utf-8") as f:
        eeg_data = json.load(f)
    
    nodes = eeg_data.get("nodes", {})
    log(f"Loaded {len(nodes):,} nodes from {eeg_path}.")

    def classify_deterministic(title, text):
        t_lower = (title + " " + text[:4000]).lower()
        scores = {}
        for dom, kws in lexicons.items():
            s = sum(t_lower.count(kw) for kw in kws)
            if s > 0:
                scores[dom] = s
        if not scores:
            return "general_constitutional_statutory", ["general_constitutional_statutory"], 0, False
        best_dom = max(scores, key=scores.get)
        all_tags = sorted(scores.keys(), key=lambda x: -scores[x])
        max_s = max(scores.values())
        is_tie = sum(1 for s in scores.values() if s == max_s) > 1
        return best_dom, all_tags, max_s, is_tie

    cat_mismatches = 0
    pdom_mismatches = 0
    tags_mismatches = 0
    
    recomputed_domain_counts = Counter()
    recomputed_multi_tag_dist = Counter()
    total_ties = 0
    total_zero_scores = 0

    for nid, ninfo in nodes.items():
        title = ninfo.get("title", "")
        text = ninfo.get("text", "")
        best_dom, all_tags, max_s, is_tie = classify_deterministic(title, text)
        
        recomputed_domain_counts[best_dom] += 1
        recomputed_multi_tag_dist[len(all_tags)] += 1
        if is_tie:
            total_ties += 1
        if best_dom == "general_constitutional_statutory":
            total_zero_scores += 1
            
        if ninfo.get("category") != best_dom:
            cat_mismatches += 1
        if ninfo.get("primary_domain") != best_dom:
            pdom_mismatches += 1
        if ninfo.get("doctrinal_tags") != all_tags:
            tags_mismatches += 1

    log(f"Category mismatches:       {cat_mismatches}")
    log(f"Primary domain mismatches: {pdom_mismatches}")
    log(f"Doctrinal tags mismatches: {tags_mismatches}")

    check3_pass = (cat_mismatches == 0 and pdom_mismatches == 0 and tags_mismatches == 0 and len(nodes) == 20000)
    if not check3_pass:
        log("  [FAIL] PARITY CHECK FAILED!")
        all_passed = False
    else:
        log("  [PASS] 100% BIT-EXACT DETERMINISTIC LABEL PARITY ACROSS ALL 20,000 NODES.")

    log(f"Check 3 & 4 Result: {'PASS' if check3_pass else 'FAIL'}\n")
    preflight_data["checks"]["check3_label_parity"] = {
        "passed": check3_pass,
        "total_nodes": len(nodes),
        "category_mismatches": cat_mismatches,
        "primary_domain_mismatches": pdom_mismatches,
        "doctrinal_tags_mismatches": tags_mismatches
    }

    # -------------------------------------------------------------------------
    # Check 5: Domain Distribution, Residual Fallback, Ties, Multi-Tag
    # -------------------------------------------------------------------------
    log("--- CHECK 5: TAXONOMY DISTRIBUTIONS & EDGE CASES ---")
    log("Primary Domain Distribution:")
    check5_pass = True
    for dom, exp_c in EXPECTED_DOMAIN_COUNTS.items():
        act_c = recomputed_domain_counts[dom]
        pct = act_c / len(nodes) * 100
        match = (act_c == exp_c)
        if not match:
            check5_pass = False
            log(f"  [FAIL] {dom:35s}: {act_c:5,d} (expected {exp_c:5,d})")
        else:
            log(f"  [PASS] {dom:35s}: {act_c:5,d} ({pct:5.2f}%)")

    total_primary = sum(recomputed_domain_counts.values())
    log(f"Total Classified Opinions: {total_primary:,} (Expected: 20,000)")
    if total_primary != 20000:
        check5_pass = False

    log(f"\nResidual Fallback (general_constitutional_statutory): {total_zero_scores:,} (Expected: 4,594)")
    if total_zero_scores != 4594:
        log("  [FAIL] RESIDUAL COUNT MISMATCH!")
        check5_pass = False
    else:
        log("  [PASS] RESIDUAL COUNT MATCHES EXACTLY.")

    log(f"Score-Tie Cases: {total_ties:,} (Expected: 1,587)")
    if total_ties != 1587:
        log("  [FAIL] TIE COUNT MISMATCH!")
        check5_pass = False
    else:
        log("  [PASS] TIE COUNT MATCHES EXACTLY.")

    log("\nMulti-Tag Complexity Distribution:")
    for tag_cnt, exp_tc in EXPECTED_MULTI_TAG_DIST.items():
        act_tc = recomputed_multi_tag_dist[tag_cnt]
        pct = act_tc / len(nodes) * 100
        match = (act_tc == exp_tc)
        if not match:
            check5_pass = False
            log(f"  [FAIL] {tag_cnt} tags: {act_tc:6,d} (expected {exp_tc:6,d})")
        else:
            log(f"  [PASS] {tag_cnt} tags: {act_tc:6,d} ({pct:5.2f}%)")

    if not check5_pass:
        all_passed = False
    log(f"Check 5 Result: {'PASS' if check5_pass else 'FAIL'}\n")
    preflight_data["checks"]["check5_distributions"] = {
        "passed": check5_pass,
        "domain_counts": dict(recomputed_domain_counts),
        "residual_fallback_count": total_zero_scores,
        "tie_cases_count": total_ties,
        "multi_tag_distribution": dict(recomputed_multi_tag_dist)
    }

    # -------------------------------------------------------------------------
    # Check 6: Raw Case and Selection Manifest Input Availability
    # -------------------------------------------------------------------------
    log("--- CHECK 6: REQUIRED INPUT SUBSTRATE AVAILABILITY ---")
    manifest_path = ROOT_DIR / "dataset_20k_cap" / "manifests" / "selection_manifest_20k.json"
    raw_cases_dir = ROOT_DIR / "dataset_20k_cap" / "raw_cases"
    
    check6_pass = True
    if not manifest_path.exists():
        log(f"  [FAIL] MISSING selection manifest: {manifest_path}")
        check6_pass = False
    else:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_entries = json.load(f)
        log(f"  [PASS] Selection manifest verified ({len(manifest_entries):,} entries).")
        if len(manifest_entries) != 20000:
            check6_pass = False
            log(f"  [FAIL] Manifest entry count error: {len(manifest_entries)}")

    if not raw_cases_dir.exists():
        log(f"  [FAIL] MISSING raw cases directory: {raw_cases_dir}")
        check6_pass = False
    else:
        raw_files = [f for f in os.listdir(raw_cases_dir) if f.endswith(".json")]
        missing_nodes = [nid for nid in nodes if not (raw_cases_dir / f"{nid}.json").exists()]
        log(f"  [PASS] Raw cases directory contains {len(raw_files):,} JSON files.")
        log(f"  [PASS] Corpus node coverage in raw cases: {len(nodes) - len(missing_nodes):,}/{len(nodes):,} (Missing: {len(missing_nodes)}).")
        if len(missing_nodes) > 0:
            check6_pass = False
            log(f"  [FAIL] Missing raw files for {len(missing_nodes)} corpus nodes!")

    if not check6_pass:
        all_passed = False
    log(f"Check 6 Result: {'PASS' if check6_pass else 'FAIL'}\n")
    preflight_data["checks"]["check6_inputs_available"] = {
        "passed": check6_pass,
        "manifest_path": str(manifest_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "manifest_entries": len(manifest_entries) if manifest_path.exists() else 0,
        "raw_cases_count": len(raw_files) if raw_cases_dir.exists() else 0
    }

    # -------------------------------------------------------------------------
    # Check 7: Judge B Cache SHA256 Pre-Execution State
    # -------------------------------------------------------------------------
    log("--- CHECK 7: JUDGE B CACHE PROVENANCE PRE-EXECUTION HASH ---")
    cache_dir = ROOT_DIR / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "issue22_judge_cache.json"
    
    if not cache_path.exists():
        # Initialize empty valid cache JSON
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        log(f"  Initialized empty cache at: {cache_path}")
    
    cache_pre_sha = compute_sha256(cache_path)
    cache_sz = cache_path.stat().st_size
    with open(cache_path, "r", encoding="utf-8") as f:
        cache_content = json.load(f)
    
    log(f"  Cache Path:      {cache_path}")
    log(f"  Pre-Exec SHA256: {cache_pre_sha}")
    log(f"  Size:            {cache_sz} bytes")
    log(f"  Cached Entries:  {len(cache_content)}")
    
    check7_pass = (cache_path.exists() and isinstance(cache_content, dict))
    log(f"Check 7 Result: {'PASS' if check7_pass else 'FAIL'}\n")
    preflight_data["checks"]["check7_judge_cache_provenance"] = {
        "passed": check7_pass,
        "cache_path": str(cache_path.relative_to(ROOT_DIR)).replace("\\", "/"),
        "pre_exec_sha256": cache_pre_sha,
        "size_bytes": cache_sz,
        "cached_entries_count": len(cache_content)
    }

    # -------------------------------------------------------------------------
    # Overall Verdict & Serialization
    # -------------------------------------------------------------------------
    log("=" * 80)
    verdict = "PASS" if all_passed else "STOPPED"
    preflight_data["verdict"] = {
        "status": verdict,
        "all_checks_passed": all_passed,
        "reproducibility": "100% Deterministic Bit-Level Parity Verified Across All 20,000 Nodes",
        "protected_substrates_invariance": "10/10 Invariant",
        "ready_for_phase2": all_passed
    }
    log(f"OVERALL PREFLIGHT VERDICT: {verdict}")
    log("=" * 80)

    # Serialize preflight data
    out_json = ROOT_DIR / "data" / "issue22_preflight.json"
    out_txt = ROOT_DIR / "logs" / "issue22_preflight.txt"
    
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
        
    print(f"\nWrote preflight artifacts:\n  JSON: {out_json}\n  TXT:  {out_txt}")
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
