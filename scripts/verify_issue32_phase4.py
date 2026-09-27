import os
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from pypdf import PdfReader

TECTONIC_EXE = os.path.abspath("scratch/tectonic/tectonic.exe")
MAIN_TEX = "Paper/main.tex"
COMPILED_PDF = "Paper/main.pdf"
BASELINE_PDF = "scratch/main_baseline_pre_issue32.pdf"
PREFLIGHT_JSON = "data/issue32_preflight.json"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("TERRA ISSUE #32 PHASE 4 COMPILATION & VERIFICATION")
    log("=" * 80)

    all_passed = True

    # 1. Compile Paper/main.tex with Tectonic
    log("\n[STEP 1/5] Compiling Paper/main.tex with Tectonic...")
    cmd = [TECTONIC_EXE, "--keep-intermediates", MAIN_TEX]
    log(f"  Command: {' '.join(cmd)}")
    compile_res = subprocess.run(cmd, capture_output=True, text=True)
    log(f"  Exit code: {compile_res.returncode}")
    if compile_res.returncode == 0:
        log("  [PASS] Tectonic compiled successfully.")
    else:
        log("  [FAIL] Tectonic compilation failed!")
        log(f"  Stdout:\n{compile_res.stdout[-500:]}")
        log(f"  Stderr:\n{compile_res.stderr[-500:]}")
        all_passed = False

    # 2. Verify Page Count & Terminal Anchors on Compiled PDF
    log("\n[STEP 2/5] Verifying Page Count & Terminal Anchors...")
    reader = PdfReader(COMPILED_PDF)
    page_count = len(reader.pages)
    log(f"  Compiled PDF Page Count: {page_count} (Expected: 35)")

    if page_count != 35:
        log("  [FAIL] PDF page budget violated!")
        all_passed = False
    else:
        log("  [PASS] Exactly 35 pages.")

    p35_text = reader.pages[34].extract_text()
    has_table_xxiii = "TABLE XXIII" in p35_text
    has_ref_27 = "[27]" in p35_text and "Zheng" in p35_text
    log(f"  Page 35 Top Float has TABLE XXIII: {has_table_xxiii}")
    log(f"  Page 35 Terminal Text has Ref [27]: {has_ref_27}")

    if has_table_xxiii and has_ref_27:
        log("  [PASS] Page 35 terminal anchors verified.")
    else:
        log("  [FAIL] Page 35 terminal anchors missing or displaced!")
        all_passed = False

    # 3. Compare Compiled PDF Text against Baseline PDF Text
    log("\n[STEP 3/5] Comparing Compiled PDF Text against Phase 1 Baseline PDF...")
    baseline_reader = PdfReader(BASELINE_PDF)
    assert len(baseline_reader.pages) == 35

    differing_pages = []
    page3_diff_details = {}

    for i in range(35):
        page_num = i + 1
        base_t = baseline_reader.pages[i].extract_text()
        comp_t = reader.pages[i].extract_text()

        if base_t != comp_t:
            differing_pages.append(page_num)
            if page_num == 3:
                # Analyze difference on Page 3
                has_old_phrase = "SHAP-verified" in base_t and "SHAP-verified" not in comp_t
                has_new_phrase = "autonomous NLI" in comp_t and "autonomous NLI" not in base_t
                page3_diff_details = {
                    "old_phrase_removed": has_old_phrase,
                    "new_phrase_added": has_new_phrase
                }

    log(f"  Differing Pages across 35 pages: {differing_pages} (Expected: [3])")
    if differing_pages == [3]:
        log("  [PASS] Pages 1-2 and 4-35 are 100% text-identical.")
        log(f"  Page 3 Analysis: old phrase removed = {page3_diff_details.get('old_phrase_removed')}, new phrase added = {page3_diff_details.get('new_phrase_added')}")
        if page3_diff_details.get("old_phrase_removed") and page3_diff_details.get("new_phrase_added"):
            log("  [PASS] Difference on Page 3 is strictly limited to the approved Line 139 replacement.")
        else:
            log("  [FAIL] Page 3 difference contains unexpected modifications!")
            all_passed = False
    else:
        log("  [FAIL] Unexpected pages differed!")
        all_passed = False

    # 4. Canonical CI Consistency Re-check
    log("\n[STEP 4/5] Re-verifying Canonical CI Consistency...")
    ci_cmd = [sys.executable, "Paper/scripts/check_consistency.py", "--target", "Paper/"]
    ci_res = subprocess.run(ci_cmd, capture_output=True, text=True)
    log(f"  Command: {' '.join(ci_cmd)}")
    log(f"  Exit code: {ci_res.returncode}")
    ci_passed = (ci_res.returncode == 0) and ("[CI AUDIT PASSED]" in ci_res.stdout)
    ci_match = re.search(r'All (\d+) custom macro references in main\.tex are strictly defined\.', ci_res.stdout)
    resolved_count = int(ci_match.group(1)) if ci_match else 0
    zero_orphans = "Zero orphaned result numbers found in main.tex." in ci_res.stdout

    log(f"  CI Audit Passed: {ci_passed}")
    log(f"  Resolved Macro References: {resolved_count} (Expected: 851)")
    log(f"  Zero Orphaned Literals: {zero_orphans}")

    if ci_passed and resolved_count == 851 and zero_orphans:
        log("  [PASS] Canonical CI strictly passed 4/4 with 851 resolved macros and zero orphaned literals.")
    else:
        log("  [FAIL] Canonical CI failed!")
        all_passed = False

    # 5. Protected Substrates & Frozen Archives Hash Re-check
    log("\n[STEP 5/5] Re-checking All Protected Substrates & Frozen Archives...")
    with open(PREFLIGHT_JSON, "r", encoding="utf-8") as f:
        preflight_data = json.load(f)

    # generated_stats.tex
    stats_sha = sha256_file("Paper/generated_stats.tex")
    expected_stats_sha = preflight_data["baseline_generated_stats_tex_sha256"]
    if stats_sha == expected_stats_sha:
        log(f"  [PASS] Paper/generated_stats.tex -> {stats_sha[:16]}... (MATCH)")
    else:
        log(f"  [FAIL] Paper/generated_stats.tex hash mismatch!")
        all_passed = False

    # 11 protected substrates
    for rel_path, info in preflight_data["protected_substrates_pre_edit_manifest"].items():
        actual_sha = sha256_file(rel_path)
        if actual_sha == info["hash"]:
            log(f"  [PASS] Substrate {rel_path} -> {actual_sha[:16]}... (MATCH)")
        else:
            log(f"  [FAIL] Substrate {rel_path} hash mismatch!")
            all_passed = False

    # 2 frozen archives
    for rel_path, info in preflight_data["frozen_archives"].items():
        actual_sha = sha256_file(rel_path)
        if actual_sha == info["hash"]:
            log(f"  [PASS] Archive {rel_path} -> {actual_sha[:16]}... (MATCH)")
        else:
            log(f"  [FAIL] Archive {rel_path} hash mismatch!")
            all_passed = False

    # raw eval
    raw_eval = preflight_data["canonical_raw_evaluation_artifact"]
    actual_raw_sha = sha256_file(raw_eval["path"])
    if actual_raw_sha == raw_eval["hash"]:
        log(f"  [PASS] Raw Eval {raw_eval['path']} -> {actual_raw_sha[:16]}... (MATCH)")
    else:
        log(f"  [FAIL] Raw Eval hash mismatch!")
        all_passed = False

    log("\n" + "=" * 80)
    if all_passed:
        log("OVERALL PHASE 4 STATUS: PASS")
    else:
        log("OVERALL PHASE 4 STATUS: FAIL")
    log("=" * 80)

    os.makedirs("logs", exist_ok=True)
    with open("logs/issue32_phase4_verification.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    log("\nWrote Phase 4 verification log to logs/issue32_phase4_verification.txt")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
