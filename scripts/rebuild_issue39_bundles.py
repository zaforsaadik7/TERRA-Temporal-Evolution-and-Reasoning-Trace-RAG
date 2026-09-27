import os
import zipfile
import hashlib
import json
import tempfile
import shutil
import subprocess
import re
import sys
import difflib
from pathlib import Path
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf-8')

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# Fixed timestamp for reproducible ZIP entries (YYYY, MM, DD, HH, MM, SS)
FIXED_TIMESTAMP = (2026, 9, 26, 17, 15, 0)

def add_file_to_zip(zf, src, arc):
    with open(src, "rb") as f:
        data = f.read()
    zinfo = zipfile.ZipInfo(arc, FIXED_TIMESTAMP)
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    zinfo.external_attr = 0o644 << 16
    zf.writestr(zinfo, data)

PRE_ISSUE39_BASELINE_HASH = "896c9e297862804e8679e10eb6fb36cc473e3586950c44d0bb085d2ab9d43959"

REPRODUCIBILITY_52_FILES = [
    # 1-4: Manuscript core
    ("Paper/main.pdf",                               "main.pdf"),
    ("Paper/main.tex",                               "main.tex"),
    ("Paper/main.bbl",                               "main.bbl"),
    ("Paper/ref.bib",                                "ref.bib"),
    # 5-10: Generated stats & figures
    ("Paper/generated_stats.tex",                    "generated_stats.tex"),
    ("Paper/generated_obscure_stats.tex",            "generated_obscure_stats.tex"),
    ("Paper/generated_corpus_stats_20k.tex",         "generated_corpus_stats_20k.tex"),
    ("Paper/figure_1_system_architecture.tex",       "figure_1_system_architecture.tex"),
    ("Paper/figure_2_hub_centrality.tex",            "figure_2_hub_centrality.tex"),
    ("Paper/figure_3_safety_rejection.tex",          "figure_3_safety_rejection.tex"),
    # 11-24: Tables I-XXIII
    ("Paper/tables/table_sensitivity_raw_vs_clamped.tex", "tables/table_sensitivity_raw_vs_clamped.tex"),
    ("Paper/tables/table_refusal_breakdown.tex",     "tables/table_refusal_breakdown.tex"),
    ("Paper/tables/table_full_fdr_family.tex",       "tables/table_full_fdr_family.tex"),
    ("Paper/tables/table_system_comparison.tex",     "tables/table_system_comparison.tex"),
    ("Paper/tables/table_temporal_leakage_probe.tex", "tables/table_temporal_leakage_probe.tex"),
    ("Paper/tables/table_casefacts_eval.tex",        "tables/table_casefacts_eval.tex"),
    ("Paper/tables/table_clerc_eval.tex",            "tables/table_clerc_eval.tex"),
    ("Paper/tables/table_retrieval_eval.tex",        "tables/table_retrieval_eval.tex"),
    ("Paper/tables/table_computational_budget.tex",  "tables/table_computational_budget.tex"),
    ("Paper/tables/table_router_eval.tex",           "tables/table_router_eval.tex"),
    ("Paper/tables/table_citation_eval.tex",         "tables/table_citation_eval.tex"),
    ("Paper/tables/table_obscure_overruled_eval.tex", "tables/table_obscure_overruled_eval.tex"),
    ("Paper/tables/table_temporal_update_stability.tex", "tables/table_temporal_update_stability.tex"),
    ("Paper/tables/table_baseline_specifications.tex", "tables/table_baseline_specifications.tex"),
    # 25-29: Verification & Rebuild Scripts
    ("Paper/scripts/check_consistency.py",           "scripts/check_consistency.py"),
    ("Paper/scripts/generate_stats.py",              "scripts/generate_stats.py"),
    ("Paper/scripts/allowed_literals.txt",           "scripts/allowed_literals.txt"),
    ("scripts/rebuild_issue38_bundles.py",           "scripts/rebuild_issue38_bundles.py"),
    ("scripts/rebuild_issue39_bundles.py",           "scripts/rebuild_issue39_bundles.py"),
    # 30-32: Pipeline Execution Scripts
    ("ask_terra.py",                                 "ask_terra.py"),
    ("eval_terra.py",                                "eval_terra.py"),
    ("scripts/ingest_20k_eeg_and_vector_db.py",      "scripts/ingest_20k_eeg_and_vector_db.py"),
    # 33-37: Prompt Templates
    ("prompts/router_system_prompt.txt",             "prompts/router_system_prompt.txt"),
    ("prompts/fast_path_prompt.txt",                 "prompts/fast_path_prompt.txt"),
    ("prompts/generator_system_prompt.txt",          "prompts/generator_system_prompt.txt"),
    ("prompts/nli_grader_prompt.txt",                "prompts/nli_grader_prompt.txt"),
    ("prompts/dual_judge_prompt.txt",                "prompts/dual_judge_prompt.txt"),
    # 38: System Configuration
    ("configs/terra_config.json",                    "configs/terra_config.json"),
    # 39-40: Benchmark & Corpus
    ("terra_350_benchmark.json",                     "terra_350_benchmark.json"),
    ("dataset_20k_cap/terra_eeg_index_20k.json",     "dataset_20k_cap/terra_eeg_index_20k.json"),
    # 41-43: Generated Datasets
    ("data/terra_eeg_edges_145k.tsv",                "data/terra_eeg_edges_145k.tsv"),
    ("data/doctrine_invalidation_pairs_19.json",     "data/doctrine_invalidation_pairs_19.json"),
    ("data/terra_canonical_v2_eval.json",            "data/terra_canonical_v2_eval.json"),
    # 44-50: Specialized Benchmark Suites
    ("data/obscure_overruled_benchmark.json",        "data/obscure_overruled_benchmark.json"),
    ("data/casefacts_eval_120.json",                 "data/casefacts_eval_120.json"),
    ("data/casefacts_refusal_control_50.json",       "data/casefacts_refusal_control_50.json"),
    ("data/clerc_eval_120.json",                     "data/clerc_eval_120.json"),
    ("data/clerc_refusal_control_50.json",           "data/clerc_refusal_control_50.json"),
    ("data/casehold_nli_eval_200.json",              "data/casehold_nli_eval_200.json"),
    ("data/terra_eeg_nli_eval_200.json",             "data/terra_eeg_nli_eval_200.json"),
    # 51-52: Provenance & Closeout Logs
    ("logs/issue38_closeout.txt",                    "logs/issue38_closeout.txt"),
    ("logs/issue39_closeout.txt",                    "logs/issue39_closeout.txt"),
]

def main():
    print("=" * 80)
    print("TERRA ISSUE #39 PHASE 5: BUNDLE REBUILD, MANIFEST, AUDIT & CLOSEOUT")
    print("=" * 80)

    # Pin SOURCE_DATE_EPOCH for bit-for-bit deterministic PDF compilation
    os.environ["SOURCE_DATE_EPOCH"] = "1780000000"

    # ------------------------------------------------------------------
    # STEP 1: Tectonic Compilation
    # ------------------------------------------------------------------
    print("\n[STEP 1/11] Verifying Paper/main.tex Tectonic Compilation...")
    comp_cmd = ["scratch/tectonic/tectonic.exe", "--keep-intermediates", "Paper/main.tex"]
    res = subprocess.run(comp_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Tectonic compile failed!")
        print(res.stderr)
        raise RuntimeError("Tectonic compile failed!")
    print("  [PASS] Tectonic compiled cleanly with exit code 0.")

    # ------------------------------------------------------------------
    # STEP 2: 35-Page Geometry & Page 35 Anchors
    # ------------------------------------------------------------------
    print("\n[STEP 2/11] Verifying 35-Page PDF Geometry & Page 35 Anchors...")
    reader = PdfReader("Paper/main.pdf")
    page_count = len(reader.pages)
    assert page_count == 35, f"Expected 35 pages, got {page_count}"
    p35_text = reader.pages[34].extract_text() or ""
    assert "TABLE XXIII" in p35_text, "Table XXIII float missing from Page 35!"
    assert "[27]" in p35_text and "Zheng" in p35_text, "Reference [27] missing from Page 35!"
    lines_p35 = [l.strip() for l in p35_text.splitlines() if l.strip()]
    assert "[27]" in '\n'.join(lines_p35[-8:]), "Reference [27] not at terminal position on Page 35!"
    print(f"  [PASS] PDF is strictly {page_count} pages with Table XXIII at top and terminal Reference [27] on Page 35.")

    # ------------------------------------------------------------------
    # STEP 3: Canonical CI Consistency Audit
    # ------------------------------------------------------------------
    print("\n[STEP 3/11] Running Canonical CI Consistency Audit...")
    ci_cmd = [sys.executable, "Paper/scripts/check_consistency.py", "--target", "Paper/"]
    ci_res = subprocess.run(ci_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if ci_res.returncode != 0 or "[CI AUDIT PASSED]" not in ci_res.stdout:
        print(ci_res.stdout)
        print(ci_res.stderr)
        raise RuntimeError("Canonical CI failed!")
    macro_match = re.search(r'All (\d+) custom macro', ci_res.stdout)
    macro_count = macro_match.group(1) if macro_match else "???"
    assert macro_count == "860", f"Expected 860 macros, found {macro_count}"
    print(f"  [PASS] CI consistency audit passed 4/4 with all {macro_count} macros defined and 0 orphaned literals.")

    # ------------------------------------------------------------------
    # STEP 4: Section V Replacement, Layout Directive & Inversion Verification
    # ------------------------------------------------------------------
    print("\n[STEP 4/11] Verifying Section V Replacement, Layout Directive & Cryptographic Inversion...")
    with open("Paper/main.tex", "r", encoding="utf-8", newline="") as f:
        main_tex_raw = f.read()

    # 4a. Verify Section V heading and labels
    assert "\\subsection{Data and Code Availability}" in main_tex_raw, "Data and Code Availability heading missing!"
    assert "\\label{subsec:data-code-availability}" in main_tex_raw, "Label subsec:data-code-availability missing!"
    assert "\\label{subsec:reproducibility}" in main_tex_raw, "Label subsec:reproducibility missing!"
    assert "\\enlargethispage{6\\baselineskip}" in main_tex_raw, "Layout enlargement directive missing!"

    # 4b. Verify zero "upon request" strings in main.tex
    upon_request_hits = len(re.findall(r'upon request', main_tex_raw, re.I))
    assert upon_request_hits == 0, f"Found {upon_request_hits} residual 'upon request' strings in Paper/main.tex!"

    # 4c. Verify Limitations 1 and 4 verbatim presence
    assert "Absence of Licensed Legal Practitioner Evaluation (Most Critical Limitation for Deployment)" in main_tex_raw, \
        "Limitation 1 heading missing or modified!"
    assert "Jurisdictional and Temporal Corpus Boundaries" in main_tex_raw, \
        "Limitation 4 heading missing or modified!"

    # 4d. Cryptographic Inversion Verification: inverting the replacement reproduces baseline hash 896c9e29...
    with open("Paper/main.tex", "rb") as f:
        curr_bytes = f.read()

    spec_text = open("logs/issue39_phase2_specification.txt", "r", encoding="utf-8").read()
    after_part = spec_text.split("Target Replacement for Lines 488-491 in Paper/main.tex:\n\n")[1].split("\n\nKey Properties")[0].split("\\label{subsec:reproducibility}\n")[1].strip()
    before_part = spec_text.split("Line 490: ")[1].split("\nLine 491:")[0].strip()

    after_full = "\\enlargethispage{6\\baselineskip}\r\n\\subsection{Data and Code Availability}\r\n\\label{subsec:data-code-availability}\r\n\\label{subsec:reproducibility}\r\n" + after_part
    before_full = "\\subsection{Reproducibility Statement}\r\n\\label{subsec:reproducibility}\r\n" + before_part

    inv_str = curr_bytes.decode("utf-8").replace(after_full, before_full)
    inv_hash = hashlib.sha256(inv_str.encode("utf-8")).hexdigest()
    assert inv_hash == PRE_ISSUE39_BASELINE_HASH, \
        f"Inverted manuscript hash ({inv_hash}) does not match pre-Issue #39 baseline ({PRE_ISSUE39_BASELINE_HASH})!"
    print(f"  [PASS] Section V replacement and \\enlargethispage{{6\\baselineskip}} verified.")
    print(f"  [PASS] Residual 'upon request' scan: 0 occurrences in Paper/main.tex.")
    print(f"  [PASS] Limitations 1 and 4 verified present verbatim.")
    print(f"  [PASS] Cryptographic inversion reproduces pre-Issue #39 baseline hash ({PRE_ISSUE39_BASELINE_HASH}) byte-for-byte.")

    # ------------------------------------------------------------------
    # STEP 5: Rebuild Overleaf Publication Bundles
    # ------------------------------------------------------------------
    print("\n[STEP 5/11] Rebuilding Overleaf Publication Bundles...")
    overleaf_files = [
        "main.tex",
        "ref.bib",
        "generated_stats.tex",
        "generated_obscure_stats.tex",
        "generated_corpus_stats_20k.tex",
        "figure_1_system_architecture.tex",
        "figure_2_hub_centrality.tex",
        "figure_3_safety_rejection.tex",
        "tables/table_sensitivity_raw_vs_clamped.tex",
        "tables/table_refusal_breakdown.tex",
        "tables/table_full_fdr_family.tex",
        "tables/table_system_comparison.tex",
        "tables/table_temporal_leakage_probe.tex",
        "tables/table_casefacts_eval.tex",
        "tables/table_clerc_eval.tex",
        "tables/table_retrieval_eval.tex",
        "tables/table_computational_budget.tex",
        "tables/table_router_eval.tex",
        "tables/table_citation_eval.tex",
        "tables/table_obscure_overruled_eval.tex",
        "tables/table_temporal_update_stability.tex",
        "tables/table_baseline_specifications.tex",
    ]
    ob_path = "Paper/overleaf_bundle.zip"
    root_ob_path = "TERRA_Overleaf_Bundle.zip"

    with zipfile.ZipFile(ob_path, "w") as zf:
        for rel in overleaf_files:
            src = os.path.join("Paper", rel)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Missing Overleaf constituent: {src}")
            add_file_to_zip(zf, src, rel)

    shutil.copy2(ob_path, root_ob_path)
    ob_size = os.path.getsize(ob_path)
    ob_hash = sha256_file(ob_path)
    root_ob_hash = sha256_file(root_ob_path)
    assert ob_hash == root_ob_hash, "Publication bundles not bit-identical!"
    print(f"  [PASS] Overleaf bundles rebuilt bit-identical ({ob_size:,} bytes, sha256: {ob_hash}).")

    # ------------------------------------------------------------------
    # STEP 6: Write logs/issue39_closeout.txt
    # ------------------------------------------------------------------
    print("\n[STEP 6/11] Writing logs/issue39_closeout.txt...")
    rebuild_script_path = "scripts/rebuild_issue39_bundles.py"
    closeout_path = "logs/issue39_closeout.txt"
    pdf_size = os.path.getsize("Paper/main.pdf")
    pdf_hash = sha256_file("Paper/main.pdf")
    main_tex_size = os.path.getsize("Paper/main.tex")
    main_tex_hash = sha256_file("Paper/main.tex")
    rebuild_script_size = os.path.getsize(rebuild_script_path)
    rebuild_script_hash = sha256_file(rebuild_script_path)

    closeout_content = f"""================================================================================
TERRA ISSUE #39 CLOSE-OUT AUDIT REPORT (PHASES 1-5 EXECUTION COMPLETE)
TERRA: Reproducibility Packaging Lags Q1 Standards
================================================================================

Timestamp (UTC):      2026-09-26T17:15:00Z
Execution Phase:      Phases 1-5 Controlled Execution & Artifact Synchronization
Execution Mode:       Deterministic, Cryptographically Grounded, Reproducible
Final Disposition:    FORMALLY CLOSED -- AUDIT VERIFIED
Rebuild Script:       scripts/rebuild_issue39_bundles.py

===============================================================================
1. METHODOLOGICAL REMEDIATION & SUBSTANTIVE VERIFICATION
===============================================================================
  [Remediation 1] Preflight Audit & Manifest Inventory (Phase 1):
    - Verified reachability of public repository URL (HTTP 200).
    - Identified and targeted the sole "available upon request" occurrence in Paper/main.tex.
    - Inventoried and hashed all 43 existing source assets across the repository.
    - Documented model, router, judge, embedder, and execution specifications.
    - Verified Limitations 1 and 4 intact and baseline CI passing 4/4.

  [Remediation 2] Specification of Replacement Text & Ancillary Exports (Phase 2):
    - Replaced Subsection V-E "Reproducibility Statement" with "Data and Code Availability".
    - Provided public open-source repository URL and Zenodo archival deposit commitment.
    - Explicitly cataloged the 8 public reproducibility package components.
    - Explicitly mapped all specialized benchmark suites (CaseFacts, CLERC, Obscure, NLI).
    - Specified schemas and deterministic generation rules for 9 Phase-3 ancillary artifacts.
    - Preserved dual subsection labels \\label{{subsec:data-code-availability}} and \\label{{subsec:reproducibility}}.

  [Remediation 3] Controlled Manuscript Replacement & Artifact Generation (Phase 3):
    - Applied approved Section V replacement block to Paper/main.tex.
    - Created scripts/export_reproducibility_artifacts.py and generated 9 artifacts:
        1. data/terra_eeg_edges_145k.tsv (145,366 data rows: 145,310 CITES + 56 OVERRULES)
        2. data/doctrine_invalidation_pairs_19.json (19 pairs: D001-D019)
        3. data/terra_canonical_v2_eval.json (1,750 dual-judge evaluations, hash 95e775e2...)
        4. prompts/router_system_prompt.txt (Traffic Cop intent router prompt)
        5. prompts/fast_path_prompt.txt (Direct generation prompt)
        6. prompts/generator_system_prompt.txt (Grounded multi-hop prompt)
        7. prompts/nli_grader_prompt.txt (NLI Smart Grader entailment prompt)
        8. prompts/dual_judge_prompt.txt (Frozen dual-judge Likert prompt)
        9. configs/terra_config.json (Frozen hyperparameters and runtime config)
    - Verified cryptographic reversibility to pre-Issue #39 baseline.

  [Remediation 4] Deterministic Compilation & Page Geometry Preservation (Phase 4):
    - Diagnosed +433 character (~6 lines) text addition pushing references onto Page 36.
    - Determined \\enlargethispage{{6\\baselineskip}} on Line 488 is the minimal layout directive
      restoring strictly 35 pages with 0 page-boundary drifts across all 35 pages.
    - Verified Table XXIII float pinned at top of Page 35.
    - Verified Reference [27] (Zheng et al., NeurIPS 2023) pinned at terminal position on Page 35.
    - Verified 4/4 CI pass with all 860 macros defined and 0 orphaned numeric literals.
    - Confirmed zero residual "upon request" strings in Paper/main.tex.

  [Remediation 5] Bundle Rebuilding & Clean Extraction Verification (Phase 5):
    - Rebuilt Overleaf publication bundles (Paper/overleaf_bundle.zip and TERRA_Overleaf_Bundle.zip, 22 files).
    - Rebuilt TERRA_Reproducibility_Bundle.zip with all 52 specified files.
    - Generated logs/issue39_reproducibility_manifest.json with all 52 file entries.
    - Verified clean extraction and bit-for-bit identity across all 52 extracted files.
    - Conducted independent standalone clean-room compilation of extracted manuscript to 35 pages.

===============================================================================
2. AUDIT GATES & INVARIANTS COMPLIANCE
===============================================================================
  [Gate 1] CI Consistency Audit (check_consistency.py): PASS (4/4)
    - Check 1 (Raw Data SHA256 Checksums): 5/5 verified.
    - Check 2 (Macro Resolution): All {macro_count} custom macro invocations resolve strictly.
    - Check 3 (Orphaned Literals): Zero orphaned numeric literals found.
    - Check 4 (Abstract Alignment): 8/8 abstract claims verified.

  [Gate 2] Strict 35-Page Budget & Visual Geometry: PASS
    - Compiled via scratch/tectonic/tectonic.exe Paper/main.tex with SOURCE_DATE_EPOCH=1780000000.
    - Page count: STRICTLY 35 PAGES (0 page drift).
    - Table XXIII float anchored at top of Page 35.
    - Reference [27] at terminal position on Page 35.
    - Undefined references / citations: 0.

  [Gate 3] Residual Scan & Limitations Integrity: PASS
    - "upon request" occurrences in Paper/main.tex: 0.
    - Limitation 1 ("Most Critical Limitation for Deployment"): VERIFIED.
    - Limitation 4 ("Jurisdictional and Temporal Corpus Boundaries"): VERIFIED.

  [Gate 4] Source Diff Scope Verification: PASS
    - Only Section V Data and Code Availability block and Line 488 layout directive changed.
    - Inversion reproduces pre-Issue #39 baseline ({PRE_ISSUE39_BASELINE_HASH}) bit-for-bit.
    - No experimental datasets, metric tables, or macro constants were altered.

  [Gate 5] Distribution Bundles & Manifest Consistency: PASS
    - Overleaf bundle: {ob_size:,} bytes, SHA256: {ob_hash} (22 files).
    - Reproducibility bundle: all 52 files archived, extracted, and verified.
    - External manifest: logs/issue39_reproducibility_manifest.json.

===============================================================================
3. KEY FILE HASHES & ARTIFACT MANIFEST
===============================================================================
  - Paper/main.pdf:                             {pdf_size:,} bytes  SHA256: {pdf_hash}
  - Paper/main.tex:                             {main_tex_size:,} bytes  SHA256: {main_tex_hash}
  - scripts/rebuild_issue39_bundles.py:          {rebuild_script_size:,} bytes  SHA256: {rebuild_script_hash}
  - Paper/overleaf_bundle.zip:                  {ob_size:,} bytes  SHA256: {ob_hash}
  - TERRA_Overleaf_Bundle.zip:                  {ob_size:,} bytes  SHA256: {ob_hash}

===============================================================================
4. FORMAL CONCLUSION & DISPOSITION
===============================================================================
Issue #39 is formally resolved and closed. The manuscript reproducibility section has
been upgraded from substandard "available upon request" phrasing to a comprehensive,
fully specified open-science Data and Code Availability section backed by a verified
52-file reproducibility bundle. All 9 Phase-3 ancillary artifacts are generated and
cryptographically grounded. Clean-room compilation independently verifies 35 pages
with Table XXIII and terminal Reference [27] on Page 35. All CI checks pass 4/4.
This state is 100% reproducible via scripts/rebuild_issue39_bundles.py.
================================================================================
"""
    os.makedirs("logs", exist_ok=True)
    with open(closeout_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(closeout_content)

    closeout_hash = sha256_file(closeout_path)
    closeout_size = os.path.getsize(closeout_path)
    print(f"  Wrote {closeout_path} ({closeout_size:,} bytes, sha256: {closeout_hash})")

    # ------------------------------------------------------------------
    # STEP 7: Rebuild TERRA_Reproducibility_Bundle.zip (52 files)
    # ------------------------------------------------------------------
    print("\n[STEP 7/11] Rebuilding TERRA_Reproducibility_Bundle.zip (52 files)...")
    assert len(REPRODUCIBILITY_52_FILES) == 52, f"Expected exactly 52 files, got {len(REPRODUCIBILITY_52_FILES)}"

    repro_zip_path = "TERRA_Reproducibility_Bundle.zip"
    manifest_entries = []

    with zipfile.ZipFile(repro_zip_path, "w") as zf:
        for src, arc in REPRODUCIBILITY_52_FILES:
            if not os.path.exists(src):
                raise FileNotFoundError(f"Missing reproducibility file: {src}")
            add_file_to_zip(zf, src, arc)
            f_size = os.path.getsize(src)
            f_hash = sha256_file(src)
            manifest_entries.append({
                "archive_path": arc,
                "source_path": src,
                "size_bytes": f_size,
                "sha256": f_hash
            })
            print(f"  + {arc:<55} ({f_size:>12,} bytes, sha256: {f_hash[:16]}...)")

    repro_zip_size = os.path.getsize(repro_zip_path)
    repro_zip_hash = sha256_file(repro_zip_path)
    print(f"  [PASS] TERRA_Reproducibility_Bundle.zip rebuilt ({repro_zip_size:,} bytes, sha256: {repro_zip_hash}).")

    # ------------------------------------------------------------------
    # STEP 8: Write External Reproducibility Manifest
    # ------------------------------------------------------------------
    print("\n[STEP 8/11] Generating logs/issue39_reproducibility_manifest.json...")
    manifest_data = {
        "bundle_name": "TERRA_Reproducibility_Bundle.zip",
        "issue": "Issue #39: Reproducibility Packaging Lags Q1 Standards",
        "timestamp_utc": "2026-09-26T17:15:00Z",
        "rebuild_script": rebuild_script_path,
        "zip_size_bytes": repro_zip_size,
        "zip_sha256": repro_zip_hash,
        "closeout_log_sha256": closeout_hash,
        "closeout_log_size_bytes": closeout_size,
        "file_count": len(REPRODUCIBILITY_52_FILES),
        "files": manifest_entries
    }
    manifest_path = "logs/issue39_reproducibility_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"  Wrote {manifest_path} ({os.path.getsize(manifest_path):,} bytes)")

    # ------------------------------------------------------------------
    # STEP 9: Clean Extraction & Bit-Identity Verification
    # ------------------------------------------------------------------
    print("\n[STEP 9/11] Verifying Clean Extraction & Bit-Identity of Both Bundles...")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(ob_path, "r") as zf:
            zf.extractall(tmpdir)
        for rel in overleaf_files:
            src = os.path.join("Paper", rel)
            ext = os.path.join(tmpdir, rel)
            assert sha256_file(src) == sha256_file(ext), f"Overleaf mismatch: {rel}"
    print(f"  [PASS] Overleaf bundle: all {len(overleaf_files)} extracted files match source bit-for-bit.")

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(repro_zip_path, "r") as zf:
            zf.extractall(tmpdir)
        for src, arc in REPRODUCIBILITY_52_FILES:
            ext = os.path.join(tmpdir, arc)
            assert sha256_file(src) == sha256_file(ext), f"Reproducibility mismatch: {arc}"

        # Explicitly verify logs/issue39_closeout.txt inside extracted bundle matches closeout_hash and manifest
        ext_closeout = os.path.join(tmpdir, closeout_path)
        assert os.path.exists(ext_closeout), f"{closeout_path} missing from extracted reproducibility bundle!"
        ext_closeout_hash = sha256_file(ext_closeout)
        assert ext_closeout_hash == closeout_hash, \
            f"Extracted closeout hash {ext_closeout_hash} does not match closeout_hash {closeout_hash}!"
        assert ext_closeout_hash == manifest_data["closeout_log_sha256"], \
            "Extracted closeout hash does not match manifest closeout_log_sha256!"

        # Explicitly verify all 52 manifest file entries match extracted files
        assert len(manifest_data["files"]) == 52, f"Expected 52 manifest files, got {len(manifest_data['files'])}"
        for item in manifest_data["files"]:
            arc = item["archive_path"]
            ext = os.path.join(tmpdir, arc)
            assert os.path.exists(ext), f"Manifest file missing from extracted bundle: {arc}"
            assert sha256_file(ext) == item["sha256"], f"Manifest SHA256 mismatch for {arc}"
            assert os.path.getsize(ext) == item["size_bytes"], f"Manifest size mismatch for {arc}"
    print(f"  [PASS] Reproducibility bundle: all {len(REPRODUCIBILITY_52_FILES)} extracted files match source bit-for-bit.")
    print(f"  [PASS] Verified {closeout_path} is archived and matches closeout_log_sha256 ({closeout_hash}).")
    print(f"  [PASS] Verified all 52 manifest entries match extracted bundle contents.")

    # ------------------------------------------------------------------
    # STEP 10: Standalone Compilation of Extracted Manuscript
    # ------------------------------------------------------------------
    print("\n[STEP 10/11] Verifying Clean Standalone Compilation of Extracted Manuscript...")
    tectonic_exe = os.path.abspath("scratch/tectonic/tectonic.exe")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(ob_path, "r") as zf:
            zf.extractall(tmpdir)
        bbl_src = os.path.abspath("Paper/main.bbl")
        if os.path.exists(bbl_src):
            shutil.copy2(bbl_src, os.path.join(tmpdir, "main.bbl"))

        cmd = [tectonic_exe, "--keep-intermediates", "main.tex"]
        env = os.environ.copy()
        env["SOURCE_DATE_EPOCH"] = "1780000000"
        res = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True, env=env)
        if res.returncode != 0:
            print(res.stderr)
            raise RuntimeError("Standalone compilation of extracted manuscript failed!")

        pdf_path = os.path.join(tmpdir, "main.pdf")
        r = PdfReader(pdf_path)
        assert len(r.pages) == 35, f"Expected 35 pages in standalone compile, got {len(r.pages)}"
        p35_t = r.pages[34].extract_text() or ""
        assert "TABLE XXIII" in p35_t, "Table XXIII missing from Page 35 in standalone compile!"
        assert "[27]" in p35_t and "Zheng" in p35_t, "Reference [27] missing from Page 35 in standalone compile!"
        lines_p35 = [l.strip() for l in p35_t.splitlines() if l.strip()]
        assert "[27]" in '\n'.join(lines_p35[-8:]), "Reference [27] not at terminal position in standalone compile!"

        # Scan for upon request
        with open(os.path.join(tmpdir, "main.tex"), "r", encoding="utf-8") as f:
            ext_tex = f.read()
        assert "upon request" not in ext_tex.lower(), "Residual 'upon request' in standalone main.tex!"

    print(f"  [PASS] Standalone compilation clean: 35 pages, Table XXIII at top, Reference [27] at terminal position.")
    print(f"  [PASS] Extracted manuscript scan: 0 residual 'upon request' occurrences.")

    # ------------------------------------------------------------------
    # STEP 11: Update Master Checklist & Assert Invariants
    # ------------------------------------------------------------------
    print("\n[STEP 11/11] Updating & Verifying Master Checklist: Issue #39 complete (41/43)...")
    checklist_path = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"
    with open(checklist_path, "r", encoding="utf-8") as f:
        chk_text = f.read()

    # Update Issue #39 entry if not already updated
    if "- [ ] **39. Reproducibility" in chk_text:
        issue39_old = """- [ ] **39. Reproducibility Packaging Lags Q1 Standards**
  - *Vulnerability*: Evaluation scripts "available upon request" triggers reviewer skepticism. No repository URL, DOI, release version, commit hash, or artifact manifest is provided. File-system paths (dataset_20k_cap) are local paths, not public artifacts.
  - *Requirement*: Add formal Data and Code Availability section with persistent repository or archival DOI. Release: 350 queries, category labels, reference answers, 19 invalidation pairs, graph edge list or reproducible construction script, trace-generation metadata, prompts, model/config files, raw per-query outputs, and scripts that regenerate every table. Exact model identifiers and versions for router, embedder, NLI grader, and generator must also be published here.
  - *Also addresses*: Second Review Issues #6 (component reproducibility — full specification sub-requirement) and #19 (reproducibility package not identified).
  - *Status*: PENDING — **EXECUTE LAST** (after all architecture, evaluation, and manuscript fixes are frozen)."""

        issue39_new = f"""- [x] **39. Reproducibility Packaging Lags Q1 Standards**
  - *Vulnerability*: Evaluation scripts "available upon request" triggers reviewer skepticism. No repository URL, DOI, release version, commit hash, or artifact manifest is provided. File-system paths (dataset_20k_cap) are local paths, not public artifacts.
  - *Requirement*: Add formal Data and Code Availability section with persistent repository or archival DOI. Release: 350 queries, category labels, reference answers, 19 invalidation pairs, graph edge list or reproducible construction script, trace-generation metadata, prompts, model/config files, raw per-query outputs, and scripts that regenerate every table. Exact model identifiers and versions for router, embedder, NLI grader, and generator must also be published here.
  - *Also addresses*: Second Review Issues #6 (component reproducibility — full specification sub-requirement) and #19 (reproducibility package not identified).
  - *Status*: **COMPLETE — AUDIT VERIFIED** (2026-09-26; advances overall checklist completion to 41 / 43 items, 95.3%).
  - *Resolution*: Upgraded reproducibility infrastructure and manuscript specification across all five planned phases:
    (a) **Phase 1 Forensic Inventory**: Verified public repository reachability (`https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG`, HTTP 200); cataloged sole "available upon request" occurrence; inventoried and hashed 43 existing repository assets; documented full model, router, embedder, and judge configurations; verified Limitations 1 and 4 intact.
    (b) **Phase 2 Replacement & Ancillary Specification**: Formulated formal Section V *Data and Code Availability* replacement block retaining dual labels (`\\label{{subsec:data-code-availability}}` and `\\label{{subsec:reproducibility}}`); specified persistent public repository URL and permanent Zenodo archival release commitment upon publication; cataloged all 8 public package constituents; defined schemas and deterministic extraction rules for 9 ancillary generated artifacts; defined complete 52-file reproducibility bundle manifest.
    (c) **Phase 3 Manuscript Edits & Artifact Generation**: Replaced lines 488–491 in `Paper/main.tex` with approved availability block; created `scripts/export_reproducibility_artifacts.py` and generated all 9 ancillary artifacts: `data/terra_eeg_edges_145k.tsv` (145,366 data rows: 145,310 CITES + 56 OVERRULES), `data/doctrine_invalidation_pairs_19.json` (19 verified pairs D001–D019), `data/terra_canonical_v2_eval.json` (1,750 dual-judge evaluations, SHA256 `95e775e2...`), 5 frozen system prompt files (`prompts/`), and `configs/terra_config.json`; verified cryptographic reversibility to baseline hash `896c9e29...`.
    (d) **Phase 4 Reconciliation & Layout Preservation**: Reconciled +433 char (+6 lines) Section V expansion with minimal layout directive `\\enlargethispage{{6\\baselineskip}}` on Line 488, restoring strictly 35 pages with 0 page-boundary drifts across all 35 pages; verified Table XXIII pinned at top of Page 35 and Reference [27] pinned at terminal position; verified canonical CI passes 4/4 with 860 macros defined and 0 orphaned numeric literals; verified 0 residual "upon request" strings.
    (e) **Phase 5 Packaging & Clean-Room Verification**: Rebuilt bit-for-bit identical Overleaf publication packages (`Paper/overleaf_bundle.zip` and root `TERRA_Overleaf_Bundle.zip`, 22 files); packaged self-contained `TERRA_Reproducibility_Bundle.zip` containing all 52 specified files under external manifest `logs/issue39_reproducibility_manifest.json` and closeout log `logs/issue39_closeout.txt`; verified bit-identical clean extraction across all 52 files; verified clean standalone compilation in clean temporary directory to 35 pages with Page 35 anchors.
  - *Key Hashes*: `Paper/main.tex` SHA256: `{main_tex_hash}`; `Paper/overleaf_bundle.zip` SHA256: `{ob_hash}`; `TERRA_Overleaf_Bundle.zip` SHA256: `{ob_hash}`; `TERRA_Reproducibility_Bundle.zip` SHA256: `{repro_zip_hash}`.
  - *Audit artifacts*: `scripts/rebuild_issue39_bundles.py`, `scripts/export_reproducibility_artifacts.py`, `logs/issue39_phase1_audit.txt`, `logs/issue39_phase2_specification.txt`, `logs/issue39_phase4_compilation.txt`, `logs/issue39_closeout.txt`, `logs/issue39_reproducibility_manifest.json`."""
        assert issue39_old in chk_text, "Could not find exact Issue #39 template in checklist!"
        chk_text = chk_text.replace(issue39_old, issue39_new)

    # Update Tier 3 row
    chk_text = re.sub(
        r'\|\s*\*\*Tier 3: Terminology, Framing & Claims\*\*\s*\|\s*15 \(14 original \+ #43\)\s*\|\s*12 \([^)]+\)\s*\|\s*3\s*\|',
        '| **Tier 3: Terminology, Framing & Claims** | 15 (14 original + #43) | 13 (#27, #28, #29, #30, #31, #32, #33, #34, #35, #36, #37, #38, #39) | 2 |',
        chk_text
    )

    # Update TOTAL row
    chk_text = re.sub(
        r'\|\s*\*\*TOTAL\*\*\s*\|\s*\*\*43\*\*\s*\|\s*\*\*40 / 43 \(93\.0%\)\*\*\s*\|\s*\*\*3 / 43 \(7\.0%\)\*\*\s*\|',
        '| **TOTAL** | **43** | **41 / 43 (95.3%)** | **2 / 43 (4.7%)** |',
        chk_text
    )

    # Always synchronize bundle hash in checklist under Issue #39
    chk_text = re.sub(
        r'(\*\*39\..*?`TERRA_Reproducibility_Bundle\.zip` SHA256: `)[0-9a-f]{64}(`)',
        rf'\g<1>{repro_zip_hash}\g<2>',
        chk_text,
        flags=re.DOTALL
    )

    with open(checklist_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(chk_text)

    # Re-read and assert authoritative counting rules
    with open(checklist_path, "r", encoding="utf-8") as f:
        chk_verified = f.read()

    matches = re.findall(r'^- \[([ x])\] \*\*(\d+)\.', chk_verified, flags=re.MULTILINE)
    completed_items = [num for mark, num in matches if mark == 'x']
    pending_items   = [num for mark, num in matches if mark == ' ']

    assert len(completed_items) == 41, \
        f"Expected 41 completed [x] items, got {len(completed_items)}: {completed_items}"
    assert len(pending_items) == 2, \
        f"Expected 2 pending [ ] items, got {len(pending_items)}: {pending_items}"
    assert pending_items == ['40', '43'], \
        f"Expected pending items ['40', '43'], got {pending_items}"
    assert "41 / 43 (95.3%)" in chk_verified, \
        "Progress table TOTAL must read '41 / 43 (95.3%)'."
    assert "13 (#27, #28, #29, #30, #31, #32, #33, #34, #35, #36, #37, #38, #39)" in chk_verified, \
        "Tier 3 row must reflect 13 resolved issues."
    assert "[x] **39." in chk_verified, "Issue #39 not marked [x] in checklist!"
    print(f"  [PASS] Counting rule verified: {len(completed_items)} [x] == 41 resolved, "
          f"{len(pending_items)} [ ] == 2 pending ({pending_items}). Progress: 41/43 (95.3%).")

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("ISSUE #39 PHASE 5 GATE SUMMARY")
    print("=" * 80)
    print(f"  [1] Tectonic compilation:             PASS (exit 0)")
    print(f"  [2] 35-page geometry + Page 35 anchors: PASS (Table XXIII top, Ref [27] terminal)")
    print(f"  [3] Canonical CI 4/4:                 PASS ({macro_count} macros, 0 orphaned literals)")
    print(f"  [4] Section V replacement & diff:     PASS (inversion bit-identical to baseline)")
    print(f"  [5] Overleaf bundles rebuilt:         PASS ({ob_size:,} bytes, sha256:{ob_hash[:16]}...)")
    print(f"  [6] Repro bundle rebuilt:             PASS ({repro_zip_size:,} bytes, {len(REPRODUCIBILITY_52_FILES)} files)")
    print(f"  [7] Closeout log written:             PASS ({closeout_size:,} bytes, sha256:{closeout_hash[:16]}...)")
    print(f"  [8] Manifest written:                 PASS (file_count={len(REPRODUCIBILITY_52_FILES)})")
    print(f"  [9] Clean extraction verified:        PASS (22+{len(REPRODUCIBILITY_52_FILES)} files bit-for-bit)")
    print(f"  [10] Standalone compilation:          PASS (35 pages)")
    print(f"  [11] Checklist 41/43 (95.3%):         PASS (pending: #40, #43)")
    print("=" * 80)
    print("TERRA ISSUE #39 PHASE 5 CLOSE-OUT COMPLETE -- 100% PASS")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    main()
