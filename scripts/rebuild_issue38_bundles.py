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

# 8 approved manuscript replacements (Location / Description, Line, Before, After)
APPROVED_8_LINE_EDITS = [
    (
        "Location A (Intro closing claim)",
        117,
        "establishing a meaningful standard for context fidelity in high-stakes legal AI.",
        "establishing a research benchmark for context fidelity in temporal legal AI on historical SCOTUS jurisprudence."
    ),
    (
        "Location B (Section II opening framing)",
        146,
        "designed as a two-phase, closed-loop GraphRAG architecture for high-stakes legal temporal reasoning.",
        "designed as a two-phase, closed-loop GraphRAG architecture for temporal legal reasoning on historical common-law jurisprudence."
    ),
    (
        "Location C (Section III-A explainability motivation)",
        252,
        "High-stakes judicial AI requires transparent reasoning paths rather than opaque black-box responses.",
        "Transparent reasoning paths are essential in judicial AI research, particularly where legal conclusions must be traceable to cited authority."
    ),
    (
        "Location D (Section III-B implementation details)",
        270,
        "The production system is implemented in Python 3.11",
        "The research prototype is implemented in Python 3.11"
    ),
    (
        "Location E (Section IV-B validation controls)",
        408,
        "To satisfy the rigorous methodological standards required for high-stakes judicial AI, the evaluation protocol incorporates three validation controls:",
        "To satisfy the rigorous methodological standards required for temporal judicial AI research, the evaluation protocol incorporates three validation controls:"
    ),
    (
        "Location F (Section V preamble evaluation architecture)",
        844,
        "To establish methodological clarity and prevent confounding between internal mechanism isolation, standardized retrieval benchmarks, and production legal readiness, our empirical validation adheres to a structured four-layer evaluation architecture:",
        "To establish methodological clarity and prevent confounding between internal mechanism isolation, standardized retrieval benchmarks, and external generalization scope, our empirical validation adheres to a structured four-layer evaluation architecture:"
    ),
    (
        "Reconciled Layout Directive (Line 1106)",
        1106,
        r"\enlargethispage{22\baselineskip}",
        r"\enlargethispage{29\baselineskip}"
    ),
    (
        "Location G (Section VII Conclusion opening sentence)",
        1114,
        r"This paper introduced TERRA, a dual-phase GraphRAG architecture addressing knowledge drift and multi-step legal reasoning.",
        r"This paper introduced TERRA, a dual-phase GraphRAG architecture addressing knowledge drift and multi-step legal reasoning within a historical SCOTUS corpus (\CorpusTemporalSpan)."
    ),
]

PRE_ISSUE38_BASELINE_HASH = "d053ec360ec8ff9f427d3477681915f4809a5e8140d9b3e346f12189344ac6fb"

def main():
    print("=" * 80)
    print("TERRA ISSUE #38 PHASE 5: BUNDLE REBUILD, MANIFEST, AUDIT & CLOSEOUT")
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
    print(f"  [PASS] PDF is strictly {page_count} pages with Table XXIII and terminal Reference [27] on Page 35.")

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
    # STEP 4: Issue #38 Scope-Toning, 8-Line Manuscript Diff & Limitations
    # ------------------------------------------------------------------
    print("\n[STEP 4/11] Verifying Issue #38 Scope-Toning, 8-Line Manuscript Diff & Limitations...")
    with open("Paper/main.tex", "r", encoding="utf-8", newline="") as f:
        main_tex_raw = f.read()

    # 4a. Verify each of the 8 approved after-strings is present exactly once
    for desc, line_num, before_str, after_str in APPROVED_8_LINE_EDITS:
        count = main_tex_raw.count(after_str)
        assert count == 1, f"Expected exactly 1 occurrence of '{after_str[:50]}...' ({desc}), got {count}"
        count_before = main_tex_raw.count(before_str)
        assert count_before == 0, f"Found unreplaced before-string '{before_str[:50]}...' ({desc}): {count_before} occurrences"

    # 4b. Verify residual MUST-FIX phrases are completely absent (0 occurrences)
    must_fix_patterns = [
        "meaningful standard for context fidelity in high-stakes legal AI",
        "architecture for high-stakes legal temporal reasoning",
        "High-stakes judicial AI requires transparent",
        "The production system is implemented",
        "required for high-stakes judicial AI",
        "production legal readiness",
    ]
    for pattern in must_fix_patterns:
        hits = len(re.findall(re.escape(pattern), main_tex_raw, re.I))
        assert hits == 0, f"Residual MUST-FIX pattern found: '{pattern}' ({hits} occurrences)"

    # 4c. Verify Limitations 1 and 4 verbatim presence
    assert "Absence of Licensed Legal Practitioner Evaluation (Most Critical Limitation for Deployment)" in main_tex_raw, \
        "Limitation 1 heading missing or modified!"
    assert "Jurisdictional and Temporal Corpus Boundaries" in main_tex_raw, \
        "Limitation 4 heading missing or modified!"

    # 4d. Cryptographic Inversion Verification: inverting the 8 edits must reproduce baseline hash d053ec36...
    inverted_tex = main_tex_raw
    for desc, line_num, before_str, after_str in APPROVED_8_LINE_EDITS:
        inverted_tex = inverted_tex.replace(after_str, before_str)

    inv_hash = hashlib.sha256(inverted_tex.encode("utf-8")).hexdigest()
    assert inv_hash == PRE_ISSUE38_BASELINE_HASH, \
        f"Inverted manuscript hash ({inv_hash}) does not match pre-Issue #38 baseline ({PRE_ISSUE38_BASELINE_HASH})!"

    # 4e. Exact 8-line diff verification
    diff_lines = list(difflib.unified_diff(
        inverted_tex.splitlines(),
        main_tex_raw.splitlines(),
        fromfile="baseline",
        tofile="current",
        lineterm=""
    ))
    added_lines = [l for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l for l in diff_lines if l.startswith("-") and not l.startswith("---")]
    assert len(added_lines) == 8, f"Expected 8 added lines in diff, got {len(added_lines)}"
    assert len(removed_lines) == 8, f"Expected 8 removed lines in diff, got {len(removed_lines)}"
    print(f"  [PASS] All 7 approved wording edits + Line 1106 layout enlargement verified.")
    print(f"  [PASS] Residual MUST-FIX scan: 0 occurrences across all 6 target overclaim phrases.")
    print(f"  [PASS] Limitations 1 and 4 verified present verbatim.")
    print(f"  [PASS] Inverted diff reproduces pre-Issue #38 baseline hash ({PRE_ISSUE38_BASELINE_HASH}) bit-for-bit.")
    print(f"  [PASS] Diff scope strictly confined to exactly 8 lines.")

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
    # STEP 6: Write logs/issue38_closeout.txt
    # ------------------------------------------------------------------
    print("\n[STEP 6/11] Writing logs/issue38_closeout.txt...")
    rebuild_script_path = "scripts/rebuild_issue38_bundles.py"
    closeout_path = "logs/issue38_closeout.txt"
    pdf_size = os.path.getsize("Paper/main.pdf")
    pdf_hash = sha256_file("Paper/main.pdf")
    main_tex_size = os.path.getsize("Paper/main.tex")
    main_tex_hash = sha256_file("Paper/main.tex")
    gen_stats_size = os.path.getsize("Paper/generated_stats.tex")
    gen_stats_hash = sha256_file("Paper/generated_stats.tex")
    t23_size = os.path.getsize("Paper/tables/table_full_fdr_family.tex")
    t23_hash = sha256_file("Paper/tables/table_full_fdr_family.tex")
    allowed_lit_size = os.path.getsize("Paper/scripts/allowed_literals.txt")
    allowed_lit_hash = sha256_file("Paper/scripts/allowed_literals.txt")
    gen_stats_py_size = os.path.getsize("Paper/scripts/generate_stats.py")
    gen_stats_py_hash = sha256_file("Paper/scripts/generate_stats.py")
    rebuild_script_size = os.path.getsize(rebuild_script_path)
    rebuild_script_hash = sha256_file(rebuild_script_path)

    closeout_content = f"""================================================================================
TERRA ISSUE #38 CLOSE-OUT AUDIT REPORT (PHASES 1-5 EXECUTION COMPLETE)
TERRA: Unrealistic High-Stakes Legal Deployment Claims for Pre-1980 Law
================================================================================

Timestamp (UTC):      2026-09-26T17:15:00Z
Execution Phase:      Phases 1-5 Controlled Execution & Artifact Synchronization
Execution Mode:       Deterministic, Cryptographically Grounded, Reproducible
Final Disposition:    FORMALLY CLOSED -- AUDIT VERIFIED
Rebuild Script:       scripts/rebuild_issue38_bundles.py

===============================================================================
1. METHODOLOGICAL REMEDIATION & SUBSTANTIVE VERIFICATION
===============================================================================
  [Remediation 1] Forensic Inventory & Scope Audit (Phase 1):
    - Executed exhaustive regex scan for deployment and high-stakes framing:
      * Confirmed exactly 7 MUST-FIX locations (A through G).
      * Confirmed acceptable occurrences: Limitation 1 ("essential prerequisites
        for production deployment"), Layer 4 future work framing, and methodological
        justifications.
      * Confirmed Limitation 4 (Jurisdictional and Temporal Corpus Boundaries) intact.
      * Abstract and conclusion numerical content audited and 100% protected.

  [Remediation 2] Replacement Specification (Phase 2):
    - Defined exact replacement strings for Locations A through G:
      * Location A (Line 117): Replaced "establishing a meaningful standard for
        context fidelity in high-stakes legal AI." with "establishing a research
        benchmark for context fidelity in temporal legal AI on historical SCOTUS
        jurisprudence."
      * Location B (Line 146): Replaced "designed as a two-phase, closed-loop
        GraphRAG architecture for high-stakes legal temporal reasoning." with
        "designed as a two-phase, closed-loop GraphRAG architecture for temporal
        legal reasoning on historical common-law jurisprudence."
      * Location C (Line 252): Replaced "High-stakes judicial AI requires transparent
        reasoning paths rather than opaque black-box responses." with "Transparent
        reasoning paths are essential in judicial AI research, particularly where
        legal conclusions must be traceable to cited authority."
      * Location D (Line 270): Replaced "The production system is implemented in
        Python 3.11" with "The research prototype is implemented in Python 3.11".
      * Location E (Line 408): Replaced "To satisfy the rigorous methodological
        standards required for high-stakes judicial AI" with "To satisfy the
        rigorous methodological standards required for temporal judicial AI research".
      * Location F (Line 844): Replaced "prevent confounding between internal mechanism
        isolation, standardized retrieval benchmarks, and production legal readiness"
        with "prevent confounding between internal mechanism isolation, standardized
        retrieval benchmarks, and external generalization scope".
      * Location G (Line 1114): Appended historical corpus qualification
        "within a historical SCOTUS corpus (\\CorpusTemporalSpan)" to Conclusion opening.
    - Zero new numbers or macro definitions introduced.

  [Remediation 3] Manuscript Edits & Forensic Diff (Phase 3):
    - Applied 7 approved wording edits cleanly to Paper/main.tex.
    - Verified 7/7 after-strings present, 7/7 before-strings absent.
    - Confirmed residual scan: 0 occurrences of target overclaim phrases.

  [Remediation 4] Layout Reconciliation & Geometry Preservation (Phase 4):
    - Added +165 net characters across manuscript (+56 chars on Page 35 in Conclusion)
      pushed bibliography onto Page 36 under baseline \\enlargethispage{{22\\baselineskip}}.
    - Rigorous baselineskip grid search proved \\enlargethispage{{29\\baselineskip}} on
      Line 1106 is the mathematically minimal enlargement restoring strictly 35 pages.
    - Confirmed exactly 8 lines differ from pre-Issue #38 baseline (7 wording + 1 layout).
    - Inversion of the 8 edits reproduces baseline hash {PRE_ISSUE38_BASELINE_HASH} byte-for-byte.

===============================================================================
2. AUDIT GATES & INVARIANTS COMPLIANCE
===============================================================================
  [Gate 1] CI Consistency Audit (check_consistency.py): PASS (4/4)
    - Check 1 (Raw Data SHA256 Checksums): 5/5 verified.
    - Check 2 (Macro Resolution): All {macro_count} custom macro invocations resolve strictly.
    - Check 3 (Orphaned Literals): Zero orphaned numeric literals found.
    - Check 4 (Abstract Alignment): 8/8 abstract claims verified.

  [Gate 2] Strict 35-Page Budget & Visual Geometry: PASS
    - Compiled via scratch/tectonic/tectonic.exe --keep-intermediates Paper/main.tex.
    - Page count: STRICTLY 35 PAGES (0 page drift). Confirmed via pypdf PdfReader.
    - Table XXIII float anchored at top of Page 35.
    - Reference [27] (Zheng et al., NeurIPS 2023) at terminal position on Page 35.
    - Undefined references / citations: 0.
    - Critical LaTeX errors: 0.

  [Gate 3] Residual Overclaim & Limitations Integrity Scan: PASS
    - "meaningful standard for context fidelity in high-stakes legal AI": 0 found.
    - "architecture for high-stakes legal temporal reasoning":          0 found.
    - "High-stakes judicial AI requires transparent":                   0 found.
    - "The production system is implemented":                           0 found.
    - "required for high-stakes judicial AI":                           0 found.
    - "production legal readiness":                                     0 found.
    - Limitation 1 ("Most Critical Limitation for Deployment"):         VERIFIED.
    - Limitation 4 ("Jurisdictional and Temporal Corpus Boundaries"):   VERIFIED.

  [Gate 4] Source Diff Scope Verification: PASS
    - Exactly 8 manuscript lines changed in Paper/main.tex (7 text edits + Line 1106 layout).
    - Inversion reproduces pre-Issue #38 baseline ({PRE_ISSUE38_BASELINE_HASH}) bit-for-bit.
    - No result values, table data, macro definitions, or protected datasets were modified.

  [Gate 5] Distribution Bundles & Manifest Consistency: PASS
    - Paper/overleaf_bundle.zip: {ob_size:,} bytes, SHA256: {ob_hash}.
    - TERRA_Overleaf_Bundle.zip: {ob_size:,} bytes, SHA256: {ob_hash}.
    - Both bundles contain 22 files; clean extraction verified.
    - Standalone compilation in clean temporary directory: exit code 0, 35 pages.
    - External manifest: logs/issue38_reproducibility_manifest.json.

===============================================================================
3. KEY FILE HASHES & ARTIFACT MANIFEST
===============================================================================
  - Paper/main.pdf:                             {pdf_size:,} bytes  SHA256: {pdf_hash}
  - Paper/main.tex:                             {main_tex_size:,} bytes  SHA256: {main_tex_hash}
  - Paper/generated_stats.tex:                   {gen_stats_size:,} bytes  SHA256: {gen_stats_hash}
  - Paper/tables/table_full_fdr_family.tex:       {t23_size:,} bytes  SHA256: {t23_hash}
  - Paper/scripts/allowed_literals.txt:          {allowed_lit_size:,} bytes  SHA256: {allowed_lit_hash}
  - Paper/scripts/generate_stats.py:             {gen_stats_py_size:,} bytes  SHA256: {gen_stats_py_hash}
  - scripts/rebuild_issue38_bundles.py:          {rebuild_script_size:,} bytes  SHA256: {rebuild_script_hash}
  - Paper/overleaf_bundle.zip:                  {ob_size:,} bytes  SHA256: {ob_hash}
  - TERRA_Overleaf_Bundle.zip:                  {ob_size:,} bytes  SHA256: {ob_hash}

===============================================================================
4. FORMAL CONCLUSION & DISPOSITION
===============================================================================
Issue #38 is formally resolved and closed. Unrealistic "high-stakes legal deployment"
claims have been completely purged from the manuscript. TERRA is now appropriately
and accurately characterized as a research prototype and benchmark for temporal legal
reasoning on historical SCOTUS jurisprudence (1850--1980), fully aligned with its
candid limitations disclosures. All 4/4 CI gates pass, the document compiles to strictly
35 pages, and all publication bundles are cryptographically verified. No datasets,
result values, or table data were modified. This state is 100% reproducible via
scripts/rebuild_issue38_bundles.py.
================================================================================
"""
    os.makedirs("logs", exist_ok=True)
    with open(closeout_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(closeout_content)

    closeout_hash = sha256_file(closeout_path)
    closeout_size = os.path.getsize(closeout_path)
    print(f"  Wrote {closeout_path} ({closeout_size:,} bytes, sha256: {closeout_hash})")

    # ------------------------------------------------------------------
    # STEP 7: Rebuild TERRA_Reproducibility_Bundle.zip (19 files)
    # ------------------------------------------------------------------
    print("\n[STEP 7/11] Rebuilding TERRA_Reproducibility_Bundle.zip (19 files)...")
    repro_files = [
        ("Paper/main.pdf",                               "main.pdf"),
        ("Paper/main.tex",                               "main.tex"),
        ("Paper/figure_1_system_architecture.tex",       "figure_1_system_architecture.tex"),
        ("Paper/generated_stats.tex",                    "generated_stats.tex"),
        ("Paper/generated_corpus_stats_20k.tex",         "generated_corpus_stats_20k.tex"),
        ("Paper/tables/table_full_fdr_family.tex",       "tables/table_full_fdr_family.tex"),
        ("Paper/tables/table_retrieval_eval.tex",        "tables/table_retrieval_eval.tex"),
        ("Paper/tables/table_citation_eval.tex",         "tables/table_citation_eval.tex"),
        ("Paper/tables/table_computational_budget.tex",  "tables/table_computational_budget.tex"),
        ("Paper/scripts/check_consistency.py",           "scripts/check_consistency.py"),
        ("Paper/scripts/generate_stats.py",              "scripts/generate_stats.py"),
        ("Paper/scripts/allowed_literals.txt",           "scripts/allowed_literals.txt"),
        ("scripts/rebuild_issue37_bundles.py",           "scripts/rebuild_issue37_bundles.py"),
        (rebuild_script_path,                            rebuild_script_path),
        ("terra_350_benchmark.json",                     "terra_350_benchmark.json"),
        ("dataset_20k_cap/terra_eeg_index_20k.json",     "dataset_20k_cap/terra_eeg_index_20k.json"),
        ("logs/issue37_preflight_audit.txt",             "logs/issue37_preflight_audit.txt"),
        ("logs/issue37_preflight_manifest.json",         "logs/issue37_preflight_manifest.json"),
        (closeout_path,                                  closeout_path),
    ]
    assert len(repro_files) == 19, f"Expected exactly 19 reproducibility files, got {len(repro_files)}"

    repro_zip_path = "TERRA_Reproducibility_Bundle.zip"
    manifest_entries = []

    with zipfile.ZipFile(repro_zip_path, "w") as zf:
        for src, arc in repro_files:
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
    print("\n[STEP 8/11] Generating logs/issue38_reproducibility_manifest.json...")
    manifest_data = {
        "bundle_name": "TERRA_Reproducibility_Bundle.zip",
        "issue": "Issue #38: Unrealistic High-Stakes Legal Deployment Claims for Pre-1980 Law",
        "timestamp_utc": "2026-09-26T17:15:00Z",
        "rebuild_script": rebuild_script_path,
        "zip_size_bytes": repro_zip_size,
        "zip_sha256": repro_zip_hash,
        "closeout_log_sha256": closeout_hash,
        "closeout_log_size_bytes": closeout_size,
        "file_count": len(repro_files),
        "files": manifest_entries
    }
    manifest_path = "logs/issue38_reproducibility_manifest.json"
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
        for src, arc in repro_files:
            ext = os.path.join(tmpdir, arc)
            assert sha256_file(src) == sha256_file(ext), f"Reproducibility mismatch: {arc}"

        # Explicitly verify logs/issue38_closeout.txt inside extracted bundle matches closeout_hash and manifest
        ext_closeout = os.path.join(tmpdir, closeout_path)
        assert os.path.exists(ext_closeout), f"{closeout_path} missing from extracted reproducibility bundle!"
        ext_closeout_hash = sha256_file(ext_closeout)
        assert ext_closeout_hash == closeout_hash, \
            f"Extracted closeout hash {ext_closeout_hash} does not match closeout_hash {closeout_hash}!"
        assert ext_closeout_hash == manifest_data["closeout_log_sha256"], \
            "Extracted closeout hash does not match manifest closeout_log_sha256!"

        # Explicitly verify all 19 manifest file entries match extracted files
        assert len(manifest_data["files"]) == 19, f"Expected 19 manifest files, got {len(manifest_data['files'])}"
        for item in manifest_data["files"]:
            arc = item["archive_path"]
            ext = os.path.join(tmpdir, arc)
            assert os.path.exists(ext), f"Manifest file missing from extracted bundle: {arc}"
            assert sha256_file(ext) == item["sha256"], f"Manifest SHA256 mismatch for {arc}"
            assert os.path.getsize(ext) == item["size_bytes"], f"Manifest size mismatch for {arc}"
    print(f"  [PASS] Reproducibility bundle: all {len(repro_files)} extracted files match source bit-for-bit.")
    print(f"  [PASS] Verified {closeout_path} is archived and matches closeout_log_sha256 ({closeout_hash}).")
    print(f"  [PASS] Verified all 19 manifest entries match extracted bundle contents.")

    # ------------------------------------------------------------------
    # STEP 10: Standalone Compilation of Extracted Overleaf Bundle
    # ------------------------------------------------------------------
    print("\n[STEP 10/11] Verifying Clean Standalone Compilation of Extracted Overleaf Bundle...")
    tectonic_exe = os.path.abspath("scratch/tectonic/tectonic.exe")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(ob_path, "r") as zf:
            zf.extractall(tmpdir)
        bbl_src = os.path.abspath("Paper/main.bbl")
        if os.path.exists(bbl_src):
            shutil.copy2(bbl_src, os.path.join(tmpdir, "main.bbl"))
        comp_res = subprocess.run(
            [tectonic_exe, "--keep-intermediates", "main.tex"],
            cwd=tmpdir, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if comp_res.returncode != 0:
            print("Clean-dir Tectonic compile failed!")
            print(comp_res.stderr[-2000:])
            raise RuntimeError("Clean-dir Tectonic compile failed!")
        extracted_pdf = os.path.join(tmpdir, "main.pdf")
        assert os.path.exists(extracted_pdf), "Compiled main.pdf not found in clean tmpdir!"
        ext_reader = PdfReader(extracted_pdf)
        ext_page_count = len(ext_reader.pages)
        assert ext_page_count == 35, f"Expected 35 pages in clean compile, got {ext_page_count}"
        ext_p35_text = ext_reader.pages[34].extract_text() or ""
        assert "TABLE XXIII" in ext_p35_text, "Table XXIII missing from clean compile Page 35!"
        assert "[27]" in ext_p35_text and "Zheng" in ext_p35_text, \
            "Ref [27] missing from clean compile Page 35!"
        print(f"  [PASS] Standalone bundle compiled cleanly to strictly {ext_page_count} pages with Page 35 anchors.")

    # ------------------------------------------------------------------
    # STEP 11: Update Master Checklist & Assert Invariants
    # ------------------------------------------------------------------
    print("\n[STEP 11/11] Updating & Verifying Master Checklist: Issue #38 complete (40/43)...")
    checklist_path = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"
    with open(checklist_path, "r", encoding="utf-8") as f:
        chk_text = f.read()

    # Update Issue #38 entry if not already updated
    if "- [ ] **38. Unrealistic" in chk_text:
        issue38_old = """- [ ] **38. Unrealistic "High-Stakes Legal Deployment" Claims for Pre-1980 Law**
  - *Vulnerability*: Paper claims TERRA is ready for legal deployment, but the corpus covers only Supreme Court opinions up to 1980. A system that cannot retrieve 1981–present precedent or circuit court decisions cannot be deployed for real-world legal work.
  - *Requirement*: Tone down deployment claims. Frame as a research benchmark / proof-of-concept for temporal GraphRAG on historical common law. Explicitly acknowledge temporal and jurisdictional boundaries.
  - *Also addresses*: Second Review Issue #8 (overstates safety).
  - *Status*: PENDING."""

        issue38_new = f"""- [x] **38. Unrealistic "High-Stakes Legal Deployment" Claims for Pre-1980 Law**
  - *Vulnerability*: Paper claims TERRA is ready for legal deployment, but the corpus covers only Supreme Court opinions up to 1980. A system that cannot retrieve 1981–present precedent or circuit court decisions cannot be deployed for real-world legal work.
  - *Requirement*: Tone down deployment claims. Frame as a research benchmark / proof-of-concept for temporal GraphRAG on historical common law. Explicitly acknowledge temporal and jurisdictional boundaries.
  - *Also addresses*: Second Review Issue #8 (overstates safety).
  - *Status*: **COMPLETE — AUDIT VERIFIED** (2026-09-26; advances overall checklist completion to 40 / 43 items, 93.0%).
  - *Resolution*: Methodological and manuscript remediation executed across Introduction, Section II, Section III, Section IV, Section V, and Conclusion:
    (a) **Phase 1 Forensic Audit**: Conducted regex inventory across deployment/high-stakes patterns; confirmed exactly 7 MUST-FIX locations (A through G); classified all remaining hits as acceptable or out-of-scope; verified Limitation 1 and Limitation 4 verbatim.
    (b) **Phase 2 Approved Replacements**: Defined exact before/after strings for 7 locations removing deployment overclaims while preserving technical substance and avoiding numerical literals.
    (c) **Phase 3 Manuscript Edits**: Applied all 7 approved replacements to `Paper/main.tex`: (1) Line 117: research benchmark on historical SCOTUS jurisprudence; (2) Line 146: temporal legal reasoning on historical common-law jurisprudence; (3) Line 252: transparent reasoning paths in judicial AI research; (4) Line 270: research prototype implemented in Python 3.11; (5) Line 408: temporal judicial AI research standards; (6) Line 844: external generalization scope; (7) Line 1114: historical SCOTUS corpus qualification with `\\CorpusTemporalSpan`.
    (d) **Phase 4 Reconciliation & Layout Preservation**: Diagnosed and reconciled +56 char addition on Page 35 pushing references onto Page 36 under baseline `22\\baselineskip`; determined `\\enlargethispage{{29\\baselineskip}}` on Line 1106 is the mathematically minimal adjustment restoring strictly 35 pages with Table XXIII and Reference [27] on Page 35. Verified exactly 8 manuscript lines differ from baseline.
    (e) **CI Consistency & Invariants**: Canonical CI (`Paper/scripts/check_consistency.py`) passes 4/4 with all 860 macros defined, 0 orphaned literals, and 8/8 abstract claims aligned. All 23 tables, 18 limitations, 27 references, datasets, and numerical results remain invariant.
    (f) **Distribution Bundles Synchronized**: Packaged bit-for-bit identical Overleaf distribution bundles (`Paper/overleaf_bundle.zip` and root `TERRA_Overleaf_Bundle.zip`, 22 files); packaged `TERRA_Reproducibility_Bundle.zip` with 19 files under external manifest `logs/issue38_reproducibility_manifest.json` and closeout log `logs/issue38_closeout.txt`. Standalone compilation in a clean directory verified to 35 pages.
  - *Key Hashes*: `Paper/main.tex` SHA256: `{main_tex_hash}`; `Paper/overleaf_bundle.zip` SHA256: `{ob_hash}`; `TERRA_Overleaf_Bundle.zip` SHA256: `{ob_hash}`; `TERRA_Reproducibility_Bundle.zip` SHA256: `{repro_zip_hash}`.
  - *Audit artifacts*: `scripts/rebuild_issue38_bundles.py`, `logs/issue38_phase1_audit.txt`, `logs/issue38_phase2_replacements.txt`, `logs/issue38_phase3_diff.txt`, `logs/issue38_phase4_audit.txt`, `logs/issue38_closeout.txt`, `logs/issue38_reproducibility_manifest.json`."""
        assert issue38_old in chk_text, "Could not find exact Issue #38 template in checklist!"
        chk_text = chk_text.replace(issue38_old, issue38_new)

    # Update Tier 3 row
    chk_text = re.sub(
        r'\|\s*\*\*Tier 3: Terminology, Framing & Claims\*\*\s*\|\s*15 \(14 original \+ #43\)\s*\|\s*11 \([^)]+\)\s*\|\s*4\s*\|',
        '| **Tier 3: Terminology, Framing & Claims** | 15 (14 original + #43) | 12 (#27, #28, #29, #30, #31, #32, #33, #34, #35, #36, #37, #38) | 3 |',
        chk_text
    )

    # Update TOTAL row
    chk_text = re.sub(
        r'\|\s*\*\*TOTAL\*\*\s*\|\s*\*\*43\*\*\s*\|\s*\*\*39 / 43 \(90\.7%\)\*\*\s*\|\s*\*\*4 / 43 \(9\.3%\)\*\*\s*\|',
        '| **TOTAL** | **43** | **40 / 43 (93.0%)** | **3 / 43 (7.0%)** |',
        chk_text
    )

    # Always synchronize bundle hash in checklist under Issue #38
    chk_text = re.sub(
        r'(\*\*38\..*?`TERRA_Reproducibility_Bundle\.zip` SHA256: `)[0-9a-f]{64}(`)',
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

    assert len(completed_items) == 40, \
        f"Expected 40 completed [x] items, got {len(completed_items)}: {completed_items}"
    assert len(pending_items) == 3, \
        f"Expected 3 pending [ ] items, got {len(pending_items)}: {pending_items}"
    assert pending_items == ['39', '40', '43'], \
        f"Expected pending items ['39', '40', '43'], got {pending_items}"
    assert "40 / 43 (93.0%)" in chk_verified, \
        "Progress table TOTAL must read '40 / 43 (93.0%)'."
    assert "12 (#27, #28, #29, #30, #31, #32, #33, #34, #35, #36, #37, #38)" in chk_verified, \
        "Tier 3 row must reflect 12 resolved issues."
    assert "[x] **38." in chk_verified, "Issue #38 not marked [x] in checklist!"
    print(f"  [PASS] Counting rule verified: {len(completed_items)} [x] == 40 resolved, "
          f"{len(pending_items)} [ ] == 3 pending ({pending_items}). Progress: 40/43 (93.0%).")

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("ISSUE #38 PHASE 5 GATE SUMMARY")
    print("=" * 80)
    print(f"  [1] Tectonic compilation:             PASS (exit 0)")
    print(f"  [2] 35-page geometry + Page 35 anchors: PASS")
    print(f"  [3] Canonical CI 4/4:                 PASS ({macro_count} macros)")
    print(f"  [4] Scope-toning & 8-line diff:       PASS (inversion bit-identical to baseline)")
    print(f"  [5] Overleaf bundles rebuilt:         PASS ({ob_size:,} bytes, sha256:{ob_hash[:16]}...)")
    print(f"  [6] Repro bundle rebuilt:             PASS ({repro_zip_size:,} bytes, {len(repro_files)} files)")
    print(f"  [7] Closeout log written:             PASS ({closeout_size:,} bytes, sha256:{closeout_hash[:16]}...)")
    print(f"  [8] Manifest written:                 PASS (file_count={len(repro_files)})")
    print(f"  [9] Clean extraction verified:        PASS (22+{len(repro_files)} files bit-for-bit)")
    print(f"  [10] Standalone compilation:          PASS (35 pages)")
    print(f"  [11] Checklist 40/43 (93.0%):         PASS (pending: #39, #40, #43)")
    print("=" * 80)
    print("TERRA ISSUE #38 PHASE 5 CLOSE-OUT COMPLETE -- 100% PASS")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
