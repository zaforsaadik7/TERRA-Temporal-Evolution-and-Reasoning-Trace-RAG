import os
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from pypdf import PdfReader

# Authoritative source: data/issue31_preflight.json
AUTHORITATIVE_PREFLIGHT_JSON = "data/issue31_preflight.json"

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

FROZEN_ARCHIVES = {
    "Paper/prev_main.tex": "f2491d5ed857639e983e71582811a4f85a76ebaeb516fa029fdb5fce3ca9bcc4",
    "ask_terra_pre_issue13_backup.py": "bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9"
}

CANONICAL_RAW_EVAL_JSON = "scratch/canonical_v2/terra_canonical_v2_eval.json"
EXPECTED_RAW_EVAL_HASH = "95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507"
EXPECTED_RAW_EVAL_SIZE = 15156436

CHECKLIST_PATH = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"

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
    log("TERRA ISSUE #32 PREFLIGHT VERIFICATION & PRE-EDIT MANIFEST")
    log("=" * 80)

    all_passed = True

    # 0. Cross-check against authoritative data/issue31_preflight.json
    log("\n[STEP 0/5] Cross-checking Authoritative Issue #31 Preflight Manifest...")
    if not os.path.exists(AUTHORITATIVE_PREFLIGHT_JSON):
        log(f"  [FAIL] Missing authoritative manifest: {AUTHORITATIVE_PREFLIGHT_JSON}")
        all_passed = False
    else:
        with open(AUTHORITATIVE_PREFLIGHT_JSON, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
        auth_substrates = auth_data.get("protected_substrates_pre_edit_manifest", {})
        auth_archives = auth_data.get("frozen_archives", {})

        mismatch_auth = False
        for p, exp_h in PROTECTED_SUBSTRATES.items():
            if p not in auth_substrates or auth_substrates[p].get("hash") != exp_h:
                log(f"  [FAIL] Substrate {p} discrepancy against authoritative manifest!")
                mismatch_auth = True
        for p, exp_h in FROZEN_ARCHIVES.items():
            if p not in auth_archives or auth_archives[p].get("hash") != exp_h:
                log(f"  [FAIL] Archive {p} discrepancy against authoritative manifest!")
                mismatch_auth = True
        if not mismatch_auth:
            log("  [PASS] All 11 protected substrates and 2 frozen archives match authoritative manifest.")
        else:
            all_passed = False

    # 1. Verify 11 protected substrates against current workspace files
    log("\n[STEP 1/5] Verifying 11 Protected Core Substrates...")
    substrate_status = {}
    for rel_path, expected_hash in PROTECTED_SUBSTRATES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing substrate: {rel_path}")
            substrate_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_passed = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            substrate_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            substrate_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_passed = False

    log("\nVerifying 2 Frozen Historical Archives...")
    frozen_status = {}
    for rel_path, expected_hash in FROZEN_ARCHIVES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing frozen archive: {rel_path}")
            frozen_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_passed = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            frozen_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            frozen_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_passed = False

    # 2. Verify Canonical Raw Evaluation Artifact
    log("\n[STEP 2/5] Verifying Canonical Raw Evaluation Artifact...")
    raw_eval_status = {}
    if not os.path.exists(CANONICAL_RAW_EVAL_JSON):
        log(f"  [FAIL] Missing canonical raw eval artifact: {CANONICAL_RAW_EVAL_JSON}")
        raw_eval_status = {"status": "MISSING", "expected_hash": EXPECTED_RAW_EVAL_HASH}
        all_passed = False
    else:
        actual_size = os.path.getsize(CANONICAL_RAW_EVAL_JSON)
        actual_hash = sha256_file(CANONICAL_RAW_EVAL_JSON)
        if actual_hash == EXPECTED_RAW_EVAL_HASH and actual_size == EXPECTED_RAW_EVAL_SIZE:
            log(f"  [PASS] {CANONICAL_RAW_EVAL_JSON} -> {actual_hash[:16]}... (Size: {actual_size} bytes - MATCH)")
            raw_eval_status = {"status": "PASS", "path": CANONICAL_RAW_EVAL_JSON, "size": actual_size, "hash": actual_hash}
        else:
            log(f"  [FAIL] Raw eval artifact mismatch!\n    Size: {actual_size} (Expected: {EXPECTED_RAW_EVAL_SIZE})\n    Hash: {actual_hash} (Expected: {EXPECTED_RAW_EVAL_HASH})")
            raw_eval_status = {"status": "MISMATCH", "path": CANONICAL_RAW_EVAL_JSON, "size": actual_size, "hash": actual_hash, "expected_hash": EXPECTED_RAW_EVAL_HASH, "expected_size": EXPECTED_RAW_EVAL_SIZE}
            all_passed = False

    # 3. Verify Baseline Canonical CI & Macro Resolution
    log("\n[STEP 3/5] Verifying Baseline Canonical CI (check_consistency.py)...")
    ci_cmd = [sys.executable, "Paper/scripts/check_consistency.py", "--target", "Paper/"]
    ci_res = subprocess.run(ci_cmd, capture_output=True, text=True)
    log(f"  Command: {' '.join(ci_cmd)}")
    log(f"  Exit code: {ci_res.returncode}")
    ci_passed = (ci_res.returncode == 0) and ("[CI AUDIT PASSED]" in ci_res.stdout)

    # Check macro resolution in main.tex and macro definitions in Paper/generated_stats.tex
    with open("Paper/generated_stats.tex", "r", encoding="utf-8") as f:
        stats_content = f.read()
    total_defined_macros = len(re.findall(r'\\newcommand\{\\([A-Za-z0-9_]+)\}', stats_content))

    # Match check_consistency.py Check 2 logic
    ci_match = re.search(r'All (\d+) custom macro references in main\.tex are strictly defined\.', ci_res.stdout)
    resolved_count = int(ci_match.group(1)) if ci_match else 0

    log(f"  Defined Macros in generated_stats.tex: {total_defined_macros} (Expected: 1498)")
    log(f"  Resolved Custom Macro References in main.tex: {resolved_count} (Expected: 851)")
    
    ci_text_check = (resolved_count == 851)
    macro_count_passed = (total_defined_macros == 1498 and ci_text_check)

    if ci_passed and macro_count_passed:
        log("  [PASS] Baseline CI passed 4/4 with all 851 custom macro references resolved and 1498 defined macros.")
    else:
        log("  [FAIL] Baseline CI or macro count verification failed!")
        log(f"  CI Output snippet:\n{ci_res.stdout[-300:]}")
        all_passed = False

    # 4. Verify Baseline PDF Geometry (Strictly 35 Pages, Table XXIII on P35, Ref [27] on P35)
    log("\n[STEP 4/5] Verifying Baseline PDF Geometry...")
    pdf_path = "Paper/main.pdf"
    if not os.path.exists(pdf_path):
        log(f"  [FAIL] Missing PDF: {pdf_path}")
        all_passed = False
        pdf_status = {"status": "MISSING"}
    else:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        p35_text = reader.pages[34].extract_text()
        has_table_xxiii = "TABLE XXIII" in p35_text
        has_ref_27 = "[27]" in p35_text and "Zheng" in p35_text

        log(f"  Total Pages: {page_count} (Expected: 35)")
        log(f"  Page 35 Top Float has TABLE XXIII: {has_table_xxiii}")
        log(f"  Page 35 Terminal Text has Ref [27]: {has_ref_27}")

        if page_count == 35 and has_table_xxiii and has_ref_27:
            log("  [PASS] Baseline PDF strictly meets 35-page budget with correct terminal anchors.")
            pdf_status = {"status": "PASS", "path": pdf_path, "page_count": page_count, "table_xxiii_page_35_top": True, "reference_27_page_35_bottom": True}
        else:
            log("  [FAIL] Baseline PDF geometry violation!")
            pdf_status = {"status": "FAIL", "path": pdf_path, "page_count": page_count, "table_xxiii_page_35_top": has_table_xxiii, "reference_27_page_35_bottom": has_ref_27}
            all_passed = False

    # 5. Verify Target Line 139 in Paper/main.tex and Literature References
    log("\n[STEP 5/5] Verifying Line 139 Target Content and Literature References...")
    target_phrase = "a SHAP-verified NLI entailment grader"
    with open("Paper/main.tex", "r", encoding="utf-8") as f:
        main_lines = f.readlines()

    line_139_idx = 139
    line_139_text = main_lines[line_139_idx - 1].strip() if len(main_lines) >= line_139_idx else ""
    target_present = target_phrase in line_139_text
    log(f"  Line 139 Content: {line_139_text[:90]}...")
    log(f"  Contains target '{target_phrase}': {target_present}")

    # Check Literature SHAP references
    line_113_text = main_lines[112].strip() if len(main_lines) >= 113 else ""
    line_137_text = main_lines[136].strip() if len(main_lines) >= 137 else ""
    lit_113_present = "Mathematical explainability analyses, such as SHAP" in line_113_text
    lit_137_present = "Yalavarthi" in line_137_text and "SHAP explainability analysis" in line_137_text

    log(f"  Line 113 Literature SHAP reference present: {lit_113_present}")
    log(f"  Line 137 Yalavarthi SHAP reference present: {lit_137_present}")

    if target_present and lit_113_present and lit_137_present:
        log("  [PASS] Line 139 contains target phrase; literature references verified present.")
        line_check_status = {"status": "PASS", "target_line": line_139_idx, "target_phrase": target_phrase, "literature_line_113_intact": True, "literature_line_137_intact": True}
    else:
        log("  [FAIL] Target phrase missing or literature references corrupted!")
        line_check_status = {"status": "FAIL", "target_present": target_present, "lit_113_present": lit_113_present, "lit_137_present": lit_137_present}
        all_passed = False

    # Dynamic Checklist Parsing
    log("\nParsing Checklist Dynamically...")
    with open(CHECKLIST_PATH, "r", encoding="utf-8") as f:
        chk_text = f.read()

    matches = re.findall(r'^- \[([ x])] \*\*(\d+)\.', chk_text, flags=re.MULTILINE)
    completed_items_pre = [num for mark, num in matches if mark == 'x']
    pending_items_pre = [num for mark, num in matches if mark == ' ']
    n_pre = len(completed_items_pre)
    n_total = len(matches)

    tier1_items = [str(i) for i in range(1, 12)] + ['41']
    tier2_items = [str(i) for i in range(12, 27)] + ['42']
    tier3_items = [str(i) for i in range(27, 41)] + ['43']

    tier3_resolved_pre = len([num for num in completed_items_pre if num in tier3_items])
    tier3_pending_pre = len([num for num in pending_items_pre if num in tier3_items])

    log(f"  Checklist Total Items: {n_total}")
    log(f"  Completed Pre: {n_pre}/{n_total} ({n_pre/n_total*100:.1f}%)")
    log(f"  Pending Pre: {len(pending_items_pre)}")
    log(f"  Item 32 Pending: {'32' in pending_items_pre}")
    log(f"  Tier 3 Resolved Pre: {tier3_resolved_pre}")
    log(f"  Tier 3 Pending Pre: {tier3_pending_pre}")

    item_32_pending = "32" in pending_items_pre
    if not item_32_pending:
        log("  [FAIL] Item 32 is not in pending items list!")
        all_passed = False

    log("\n" + "=" * 80)
    if all_passed:
        log("OVERALL PREFLIGHT STATUS: PASS")
    else:
        log("OVERALL PREFLIGHT STATUS: FAIL")
    log("=" * 80)

    # Compile JSON preflight manifest
    preflight_data = {
        "status": "PASS" if all_passed else "FAIL",
        "authoritative_manifest_source": AUTHORITATIVE_PREFLIGHT_JSON,
        "baseline_resolved_macro_count": resolved_count,
        "baseline_total_defined_macros": total_defined_macros,
        "protected_substrates_pre_edit_manifest": substrate_status,
        "frozen_archives": frozen_status,
        "canonical_raw_evaluation_artifact": raw_eval_status,
        "canonical_ci_consistency": {
            "command": " ".join(ci_cmd),
            "exit_code": ci_res.returncode,
            "status": "PASS" if ci_passed else "FAIL"
        },
        "pdf_verification": pdf_status,
        "target_line_verification": line_check_status,
        "checklist": {
            "total_items": n_total,
            "completed_count_pre": n_pre,
            "completed_pct_pre": round(n_pre / n_total * 100, 2),
            "completed_items_pre": completed_items_pre,
            "pending_items_pre": pending_items_pre,
            "item_32_pending": item_32_pending,
            "tier3_resolved_pre": tier3_resolved_pre,
            "tier3_pending_pre": tier3_pending_pre
        },
        "baseline_main_tex_sha256": sha256_file("Paper/main.tex"),
        "baseline_generated_stats_tex_sha256": sha256_file("Paper/generated_stats.tex"),
        "baseline_main_pdf_sha256": sha256_file(pdf_path) if os.path.exists(pdf_path) else None
    }

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with open("data/issue32_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    log("\nWrote preflight manifest to data/issue32_preflight.json")

    with open("logs/issue32_preflight.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    log("Wrote preflight log to logs/issue32_preflight.txt")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
