#!/usr/bin/env python3
"""
scripts/verify_issue25_preflight.py
===================================
Authoritative Pre-Execution Preflight Verification Gate for Issue #25:
Corpus Scope vs. Task Scope Disparity.

Verifies 5 Core Pillars:
  1. Protected Core Substrates Bit-Invariance (10/10 established substrates):
     - Validates exact SHA256 hashes across benchmark, canonical EEG, temporal subgraphs,
       ask_terra.py, and established issue21 preflight artifacts.
  2. Corpus Doctrinal Census (N=20,000 opinions across 7 domains):
     - Substantive Private Law: 5,707 (28.54%)
     - General Constitutional & Statutory: 4,594 (22.97%)
     - Admin Law & Federal Courts: 4,501 (22.51%)
     - Criminal Procedure: 1,765 (8.83%)
     - Commerce Clause & Regulation: 1,614 (8.07%)
     - Civil Rights & Equal Protection: 1,153 (5.76%)
     - First Amendment: 666 (3.33%)
     - Combined Private Law + General Statutory: 10,301 opinions (51.51%)
     - Constitutional & Public-Law Core: 9,699 opinions (48.49%)
  3. Benchmark Suite Doctrinal Census (N=350 queries):
     - Total In-Domain (A, B, D): 275 queries
     - Total Out-of-Domain (C): 75 queries
     - In-Domain Constitutional & Public Law: 232 queries (84.36%)
     - In-Domain Substantive Private Law: 23 queries (8.36%)
     - In-Domain General Statutory: 20 queries (7.27%)
     - Category B Multi-Hop Precedent Suite: 100 queries across 5 constitutional domains (100.00%)
     - Category B Private Law / General Statutory: 0 queries (0.00%)
  4. Disparity & Distractor Matrix Verification:
     - Formally proves the structural distinction: high-distractor full-docket background vs.
       focused constitutional temporal reasoning benchmark.
  5. Macro Value Congruence:
     - Verifies exact string and rounding match for all 15 \\IssueTwentyFive* macros.

Serializes execution results to data/issue25_preflight.json and logs/issue25_preflight.txt.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Pillar 1: Protected Core Substrates Registry (10 Established Substrates)
# -----------------------------------------------------------------------------
PROTECTED_CORE_SUBSTRATES = {
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

PUBLIC_LAW_DOMAINS = [
    "admin_law_federal_courts",
    "criminal_procedure",
    "commerce_clause_economic",
    "civil_rights_equal_protection",
    "first_amendment",
]

PRIVATE_STATUTORY_DOMAINS = [
    "substantive_private_law",
    "general_constitutional_statutory",
]

EXPECTED_CORPUS_CENSUS = {
    "substantive_private_law": 5707,
    "general_constitutional_statutory": 4594,
    "admin_law_federal_courts": 4501,
    "criminal_procedure": 1765,
    "commerce_clause_economic": 1614,
    "civil_rights_equal_protection": 1153,
    "first_amendment": 666,
}

EXPECTED_MACROS = {
    "\\IssueTwentyFiveCorpusPrivateLawPct": "28.5\\%",
    "\\IssueTwentyFiveCorpusGeneralStatutoryPct": "23.0\\%",
    "\\IssueTwentyFiveCorpusCombinedPrivateStatutoryPct": "51.5\\%",
    "\\IssueTwentyFiveCorpusConstitutionalPublicPct": "48.5\\%",
    "\\IssueTwentyFiveBenchInDomainTotal": "275",
    "\\IssueTwentyFiveBenchConstitutionalPublicCount": "232",
    "\\IssueTwentyFiveBenchConstitutionalPublicPct": "84.4\\%",
    "\\IssueTwentyFiveBenchPrivateLawCount": "23",
    "\\IssueTwentyFiveBenchPrivateLawPct": "8.4\\%",
    "\\IssueTwentyFiveBenchGeneralStatutoryCount": "20",
    "\\IssueTwentyFiveBenchGeneralStatutoryPct": "7.3\\%",
    "\\IssueTwentyFiveCatBConstitutionalPublicCount": "100",
    "\\IssueTwentyFiveCatBConstitutionalPublicPct": "100.0\\%",
    "\\IssueTwentyFiveCatBPrivateLawCount": "0",
    "\\IssueTwentyFiveCatBPrivateLawPct": "0.0\\%",
}

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    log_lines = []
    def log(msg: str = ""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TERRA Issue #25 Pre-Execution Verification Gate")
    log("Corpus Scope vs. Task Scope Disparity Audit")
    log(f"Timestamp: {timestamp}")
    log("=" * 80)

    report = {
        "timestamp": timestamp,
        "issue": "Issue #25: Corpus Scope vs. Task Scope Disparity",
        "pillars": {},
        "verdict": "PENDING"
    }

    # -------------------------------------------------------------------------
    # Pillar 1: Protected Core Substrates Bit-Invariance (10/10)
    # -------------------------------------------------------------------------
    log("\n[Pillar 1/5] Verifying Protected Core Substrates Bit-Invariance (10/10 established substrates)...")
    p1_results = {}
    p1_pass = True
    for rel_path, expected_hash in PROTECTED_CORE_SUBSTRATES.items():
        full_path = ROOT_DIR / rel_path
        if not full_path.exists():
            log(f"  [FAIL] Missing file: {rel_path}")
            p1_results[rel_path] = {"status": "MISSING", "expected": expected_hash}
            p1_pass = False
            continue
        actual_hash = compute_sha256(full_path)
        if actual_hash != expected_hash:
            log(f"  [FAIL] Hash mismatch: {rel_path}")
            log(f"         Expected: {expected_hash}")
            log(f"         Actual:   {actual_hash}")
            p1_results[rel_path] = {"status": "HASH_MISMATCH", "expected": expected_hash, "actual": actual_hash}
            p1_pass = False
        else:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            p1_results[rel_path] = {"status": "PASS", "hash": actual_hash}

    report["pillars"]["pillar_1_substrates"] = {
        "pass": p1_pass,
        "verified_count": sum(1 for v in p1_results.values() if v.get("status") == "PASS"),
        "total_count": len(PROTECTED_CORE_SUBSTRATES),
        "details": p1_results
    }

    # -------------------------------------------------------------------------
    # Pillar 2: Corpus Doctrinal Census (N=20,000 Opinions)
    # -------------------------------------------------------------------------
    log("\n[Pillar 2/5] Performing Deep Census on 20,000-Opinion EEG Corpus...")
    eeg_path = ROOT_DIR / "dataset_20k_cap/terra_eeg_index_20k.json"
    with open(eeg_path, "r", encoding="utf-8") as f:
        eeg_data = json.load(f)

    opinions = eeg_data.get("nodes", {})
    total_opinions = len(opinions)
    log(f"  Total nodes parsed: {total_opinions}")

    domain_counts = {}
    for node_id, meta in opinions.items():
        domain = meta.get("category", "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    p2_pass = True
    if total_opinions != 20000:
        log(f"  [FAIL] Expected 20000 opinions, got {total_opinions}")
        p2_pass = False

    for domain, exp_count in EXPECTED_CORPUS_CENSUS.items():
        act_count = domain_counts.get(domain, 0)
        pct = (act_count / total_opinions) * 100.0
        match_str = "PASS" if act_count == exp_count else "FAIL"
        if act_count != exp_count:
            p2_pass = False
        log(f"  [{match_str}] Domain '{domain}': {act_count} ({pct:.2f}%) | Expected: {exp_count}")

    corpus_private_statutory = sum(domain_counts.get(d, 0) for d in PRIVATE_STATUTORY_DOMAINS)
    corpus_constitutional_public = sum(domain_counts.get(d, 0) for d in PUBLIC_LAW_DOMAINS)
    corpus_priv_pct = (corpus_private_statutory / total_opinions) * 100.0
    corpus_pub_pct = (corpus_constitutional_public / total_opinions) * 100.0

    log(f"  Combined Private + General Statutory: {corpus_private_statutory} ({corpus_priv_pct:.2f}%) [Majority: {corpus_priv_pct > 50.0}]")
    log(f"  Constitutional Public-Law Core:       {corpus_constitutional_public} ({corpus_pub_pct:.2f}%)")

    report["pillars"]["pillar_2_corpus_census"] = {
        "pass": p2_pass,
        "total_opinions": total_opinions,
        "domain_counts": domain_counts,
        "combined_private_statutory_count": corpus_private_statutory,
        "combined_private_statutory_pct": corpus_priv_pct,
        "constitutional_public_count": corpus_constitutional_public,
        "constitutional_public_pct": corpus_pub_pct
    }

    # -------------------------------------------------------------------------
    # Pillar 3: Benchmark Suite Doctrinal Census (N=350 Queries)
    # -------------------------------------------------------------------------
    log("\n[Pillar 3/5] Performing Deep Census on 350-Query Benchmark...")
    bench_path = ROOT_DIR / "terra_350_benchmark.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        bench_queries = json.load(f)

    total_queries = len(bench_queries)
    log(f"  Total benchmark queries parsed: {total_queries}")

    cat_counts = {}
    in_domain_queries = []
    out_of_domain_queries = []

    for q in bench_queries:
        cat_raw = q.get("category", "Unknown")
        cat_key = cat_raw[0] if cat_raw and cat_raw[0] in "ABCD" else cat_raw
        cat_counts[cat_key] = cat_counts.get(cat_key, 0) + 1
        if cat_key == "C":
            out_of_domain_queries.append(q)
        else:
            in_domain_queries.append(q)

    in_domain_total = len(in_domain_queries)
    out_of_domain_total = len(out_of_domain_queries)
    log(f"  In-domain queries (A, B, D): {in_domain_total}")
    log(f"  Out-of-domain queries (C):   {out_of_domain_total}")

    # Determine domain breakdown for in-domain queries
    in_domain_domain_counts = {}
    cat_b_domain_counts = {}

    for q in in_domain_queries:
        cat_raw = q.get("category", "")
        cat_key = cat_raw[0]
        if cat_key in ("A", "B"):
            domain = q.get("doctrinal_domain")
        elif cat_key == "D":
            target_id = q.get("target_nodes", [None])[0]
            domain = opinions.get(target_id, {}).get("category", "unknown")
        else:
            domain = "unknown"
        
        in_domain_domain_counts[domain] = in_domain_domain_counts.get(domain, 0) + 1
        if cat_key == "B":
            cat_b_domain_counts[domain] = cat_b_domain_counts.get(domain, 0) + 1

    in_domain_pub_count = sum(in_domain_domain_counts.get(d, 0) for d in PUBLIC_LAW_DOMAINS)
    in_domain_priv_count = in_domain_domain_counts.get("substantive_private_law", 0)
    in_domain_gen_count = in_domain_domain_counts.get("general_constitutional_statutory", 0)

    in_domain_pub_pct = (in_domain_pub_count / in_domain_total) * 100.0
    in_domain_priv_pct = (in_domain_priv_count / in_domain_total) * 100.0
    in_domain_gen_pct = (in_domain_gen_count / in_domain_total) * 100.0

    cat_b_total = len([q for q in in_domain_queries if q.get("category", "").startswith("B")])
    cat_b_pub_count = sum(cat_b_domain_counts.get(d, 0) for d in PUBLIC_LAW_DOMAINS)
    cat_b_priv_count = cat_b_domain_counts.get("substantive_private_law", 0)
    cat_b_gen_count = cat_b_domain_counts.get("general_constitutional_statutory", 0)

    cat_b_pub_pct = (cat_b_pub_count / cat_b_total) * 100.0
    cat_b_priv_pct = (cat_b_priv_count / cat_b_total) * 100.0

    log(f"  In-Domain Constitutional & Public Law: {in_domain_pub_count} / {in_domain_total} ({in_domain_pub_pct:.2f}%)")
    log(f"  In-Domain Substantive Private Law:     {in_domain_priv_count} / {in_domain_total} ({in_domain_priv_pct:.2f}%)")
    log(f"  In-Domain General Statutory:           {in_domain_gen_count} / {in_domain_total} ({in_domain_gen_pct:.2f}%)")
    log(f"  Category B Constitutional & Public:    {cat_b_pub_count} / {cat_b_total} ({cat_b_pub_pct:.2f}%)")
    log(f"  Category B Private Law:                {cat_b_priv_count} / {cat_b_total} ({cat_b_priv_pct:.2f}%)")

    p3_pass = (
        total_queries == 350 and
        in_domain_total == 275 and
        out_of_domain_total == 75 and
        in_domain_pub_count == 232 and
        in_domain_priv_count == 23 and
        in_domain_gen_count == 20 and
        cat_b_pub_count == 100 and
        cat_b_priv_count == 0 and
        cat_b_gen_count == 0
    )

    report["pillars"]["pillar_3_benchmark_census"] = {
        "pass": p3_pass,
        "total_queries": total_queries,
        "category_counts": cat_counts,
        "in_domain_total": in_domain_total,
        "out_of_domain_total": out_of_domain_total,
        "in_domain_domain_breakdown": in_domain_domain_counts,
        "in_domain_constitutional_public_count": in_domain_pub_count,
        "in_domain_constitutional_public_pct": in_domain_pub_pct,
        "in_domain_private_law_count": in_domain_priv_count,
        "in_domain_private_law_pct": in_domain_priv_pct,
        "in_domain_general_statutory_count": in_domain_gen_count,
        "in_domain_general_statutory_pct": in_domain_gen_pct,
        "category_b_constitutional_public_count": cat_b_pub_count,
        "category_b_constitutional_public_pct": cat_b_pub_pct,
        "category_b_private_law_count": cat_b_priv_count,
        "category_b_private_law_pct": cat_b_priv_pct
    }

    # -------------------------------------------------------------------------
    # Pillar 4: Disparity & Distractor Matrix Verification
    # -------------------------------------------------------------------------
    log("\n[Pillar 4/5] Verifying Disparity Ratios and High-Distractor Functionality...")
    # Corpus has 51.51% private/general statutory, but benchmark has 84.36% public law, Cat B has 100% public law.
    p4_pass = (
        corpus_priv_pct > 50.0 and
        in_domain_pub_pct > 80.0 and
        cat_b_pub_pct == 100.0 and
        cat_b_priv_count == 0
    )
    log(f"  Corpus majority private/statutory (51.51%): {'PASS' if corpus_priv_pct > 50.0 else 'FAIL'}")
    log(f"  Benchmark concentrated in constitutional/public law (84.36%): {'PASS' if in_domain_pub_pct > 80.0 else 'FAIL'}")
    log(f"  Category B 100% public law (0 private law chains): {'PASS' if cat_b_pub_pct == 100.0 else 'FAIL'}")

    report["pillars"]["pillar_4_disparity_matrix"] = {
        "pass": p4_pass,
        "corpus_distractor_ratio": corpus_priv_pct,
        "in_domain_public_law_focus_ratio": in_domain_pub_pct,
        "category_b_public_law_exclusivity": cat_b_pub_pct
    }

    # -------------------------------------------------------------------------
    # Pillar 5: Proposed Macro Value Congruence
    # -------------------------------------------------------------------------
    log("\n[Pillar 5/5] Verifying Proposed Macro Value Congruence (15 \\IssueTwentyFive* macros)...")
    computed_macro_values = {
        "\\IssueTwentyFiveCorpusPrivateLawPct": f"{domain_counts['substantive_private_law'] / total_opinions * 100:.1f}\\%",
        "\\IssueTwentyFiveCorpusGeneralStatutoryPct": f"{domain_counts['general_constitutional_statutory'] / total_opinions * 100:.1f}\\%",
        "\\IssueTwentyFiveCorpusCombinedPrivateStatutoryPct": f"{corpus_private_statutory / total_opinions * 100:.1f}\\%",
        "\\IssueTwentyFiveCorpusConstitutionalPublicPct": f"{corpus_constitutional_public / total_opinions * 100:.1f}\\%",
        "\\IssueTwentyFiveBenchInDomainTotal": str(in_domain_total),
        "\\IssueTwentyFiveBenchConstitutionalPublicCount": str(in_domain_pub_count),
        "\\IssueTwentyFiveBenchConstitutionalPublicPct": f"{in_domain_pub_pct:.1f}\\%",
        "\\IssueTwentyFiveBenchPrivateLawCount": str(in_domain_priv_count),
        "\\IssueTwentyFiveBenchPrivateLawPct": f"{in_domain_priv_pct:.1f}\\%",
        "\\IssueTwentyFiveBenchGeneralStatutoryCount": str(in_domain_gen_count),
        "\\IssueTwentyFiveBenchGeneralStatutoryPct": f"{in_domain_gen_pct:.1f}\\%",
        "\\IssueTwentyFiveCatBConstitutionalPublicCount": str(cat_b_pub_count),
        "\\IssueTwentyFiveCatBConstitutionalPublicPct": f"{cat_b_pub_pct:.1f}\\%",
        "\\IssueTwentyFiveCatBPrivateLawCount": str(cat_b_priv_count),
        "\\IssueTwentyFiveCatBPrivateLawPct": f"{cat_b_priv_pct:.1f}\\%",
    }

    p5_pass = True
    for macro_name, exp_val in EXPECTED_MACROS.items():
        comp_val = computed_macro_values.get(macro_name)
        if comp_val != exp_val:
            log(f"  [FAIL] Macro mismatch for {macro_name}: Expected '{exp_val}', Computed '{comp_val}'")
            p5_pass = False
        else:
            log(f"  [PASS] {macro_name} = {exp_val}")

    report["pillars"]["pillar_5_macro_congruence"] = {
        "pass": p5_pass,
        "macros": computed_macro_values
    }

    # -------------------------------------------------------------------------
    # Final Verdict & Artifact Serialization
    # -------------------------------------------------------------------------
    all_pillars_pass = p1_pass and p2_pass and p3_pass and p4_pass and p5_pass
    report["verdict"] = "PASS" if all_pillars_pass else "FAIL"

    log("\n" + "=" * 80)
    log(f"PREFLIGHT GATE VERDICT: {report['verdict']} (5/5 Pillars)")
    log("=" * 80)

    # Save artifacts
    data_out = ROOT_DIR / "data/issue25_preflight.json"
    with open(data_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log(f"Serialized preflight report to {data_out}")

    log_out = ROOT_DIR / "logs/issue25_preflight.txt"
    with open(log_out, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    log(f"Wrote preflight log to {log_out}")

    if not all_pillars_pass:
        sys.exit(1)

if __name__ == "__main__":
    main()
