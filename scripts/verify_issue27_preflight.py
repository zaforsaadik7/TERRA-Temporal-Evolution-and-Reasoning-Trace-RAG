import os
import hashlib
import json
import re

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

PROTECTED_SUBSTRATES = {
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
    "ask_terra_pre_issue13_backup.py": "bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9"
}

ACTIVE_TEX_FILES = [
    "Paper/main.tex",
    "Paper/figure_1_system_architecture.tex",
    "Paper/figure_2_hub_centrality.tex",
    "Paper/figure_3_safety_rejection.tex",
    "Paper/tables/table_retrieval_eval.tex",
    "Paper/tables/table_citation_eval.tex",
    "Paper/tables/table_computational_budget.tex",
    "Paper/tables/table_system_comparison.tex",
    "Paper/tables/table_temporal_update_stability.tex",
    "Paper/tables/table_baseline_specifications.tex",
    "Paper/tables/table_casefacts_eval.tex",
    "Paper/tables/table_clerc_eval.tex",
    "Paper/tables/table_full_fdr_family.tex",
    "Paper/tables/table_obscure_overruled_eval.tex",
    "Paper/tables/table_refusal_breakdown.tex",
    "Paper/tables/table_sensitivity_raw_vs_clamped.tex",
    "Paper/tables/table_temporal_leakage_probe.tex",
    "Paper/tables/table_router_eval.tex",
]

def main():
    print("=" * 70)
    print("TERRA ISSUE #27 PREFLIGHT VERIFICATION & NOMENCLATURE AUDIT")
    print("=" * 70)

    # 1. Verify protected substrates
    print("\n[STEP 1/3] Verifying Protected Core Substrates Bit-Invariance...")
    substrate_status = {}
    all_substrates_pass = True
    for rel_path, expected_hash in PROTECTED_SUBSTRATES.items():
        if not os.path.exists(rel_path):
            print(f"  [FAIL] Missing substrate: {rel_path}")
            substrate_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_substrates_pass = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            print(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            substrate_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            print(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            substrate_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_substrates_pass = False

    # 2. Scan active LaTeX files for PRECEDES
    print("\n[STEP 2/3] Scanning Active Paper LaTeX Files for 'PRECEDES'...")
    precedes_matches = {}
    for tex_path in ACTIVE_TEX_FILES:
        if not os.path.exists(tex_path):
            print(f"  [WARN] Active file not found: {tex_path}")
            continue
        with open(tex_path, "r", encoding="utf-8", errors="ignore") as f:
            for lno, line in enumerate(f, 1):
                if "PRECEDES" in line:
                    precedes_matches.setdefault(tex_path, []).append((lno, line.strip()))
                    print(f"  [FOUND] {tex_path}:{lno}: {line.strip()[:80]}")

    if not precedes_matches:
        print("  [CLEAN] Zero occurrences of 'PRECEDES' in active LaTeX files.")
    else:
        print(f"  [INFO] Found {sum(len(v) for v in precedes_matches.values())} occurrence(s) in active LaTeX files (to be remediated).")

    # 3. Check macro ledger for edge counts
    print("\n[STEP 3/3] Checking Macro Ledger for Edge Counts...")
    with open("Paper/generated_stats.tex", "r", encoding="utf-8") as f:
        stats = f.read()
    with open("Paper/generated_corpus_stats_20k.tex", "r", encoding="utf-8") as f:
        corpus_stats = f.read()

    m_cites = re.search(r'\\newcommand\{\\IssueTwentyOneTotalCitesEdges\}\{([^}]+)\}', stats)
    m_over = re.search(r'\\newcommand\{\\IssueTwentyOneOverrulesEdges\}\{([^}]+)\}', stats)
    m_prec = re.search(r'\\newcommand\{\\CorpusPrecedentEdges\}\{([^}]+)\}', corpus_stats)

    cites_val = m_cites.group(1) if m_cites else "NOT_FOUND"
    over_val = m_over.group(1) if m_over else "NOT_FOUND"
    prec_val = m_prec.group(1) if m_prec else "NOT_FOUND"

    print(f"  \\IssueTwentyOneTotalCitesEdges: {cites_val}")
    print(f"  \\IssueTwentyOneOverrulesEdges:  {over_val}")
    print(f"  \\CorpusPrecedentEdges:          {prec_val}")

    # Write output preflight artifacts
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    preflight_data = {
        "issue": "Issue #27: The PRECEDES Edge Is Conceptually Misnamed",
        "timestamp_utc": "2026-09-25T14:10:00Z",
        "all_substrates_pass": all_substrates_pass,
        "protected_substrates": substrate_status,
        "precedes_matches_in_active_tex": {k: [f"L{lno}: {txt}" for lno, txt in v] for k, v in precedes_matches.items()},
        "macros": {
            "IssueTwentyOneTotalCitesEdges": cites_val,
            "IssueTwentyOneOverrulesEdges": over_val,
            "CorpusPrecedentEdges": prec_val
        }
    }

    with open("data/issue27_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)

    with open("logs/issue27_preflight.txt", "w", encoding="utf-8") as f:
        f.write("TERRA ISSUE #27 PREFLIGHT VERIFICATION LOG\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"All 11 Protected Substrates Pass: {all_substrates_pass}\n")
        for k, v in substrate_status.items():
            f.write(f"  {k}: {v['status']}\n")
        f.write("\nActive Paper PRECEDES Matches:\n")
        for k, v in precedes_matches.items():
            for lno, txt in v:
                f.write(f"  {k}:{lno}: {txt}\n")
        f.write("\nMacro Values:\n")
        f.write(f"  CorpusPrecedentEdges: {prec_val}\n")
        f.write(f"  IssueTwentyOneTotalCitesEdges: {cites_val}\n")
        f.write(f"  IssueTwentyOneOverrulesEdges: {over_val}\n")

    print("\nPreflight artifacts written to:")
    print("  - data/issue27_preflight.json")
    print("  - logs/issue27_preflight.txt")

    if not all_substrates_pass:
        print("\n[CRITICAL ERROR] Protected substrate verification failed!")
        exit(1)
    else:
        print("\n[PREFLIGHT GATE PASSED] Ready for Phase 2 execution.")

if __name__ == "__main__":
    main()
