import os
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from pypdf import PdfReader

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

EXPECTED_CANONICAL_MACROS = {
    "DirectLLMCatBFaithfulness": "0.335",
    "DirectLLMCatBFaithfulnessStd": "0.166",
    "TerraCatBFaithfulness": "0.254",
    "TerraCatBFaithfulnessStd": "0.226",
    "CatBTerraVsDirectLLMDelta": "-0.081",
    "CatBTerraVsDirectLLMWilcoxonP": "0.0009",
    "CatBTerraVsDirectLLMAdjQ": "0.0023",
    "TerraVsDirectLLMCatBWinRate": "27.0\\%",
    "CatBTerraMacroCitationRecall": "57.85\\%",
    "CatBDirectMacroCitationRecall": "43.55\\%",
    "CombinedTerraVsDirectLLMDelta": "+0.173"
}

RAW_EVAL_JSON = "scratch/canonical_v2/terra_canonical_v2_eval.json"
EXPECTED_RAW_EVAL_HASH = "95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507"

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
    log("TERRA ISSUE #30 PREFLIGHT VERIFICATION & PRE-EDIT MANIFEST")
    log("=" * 80)

    all_passed = True

    # 1. Verify protected substrates & establish pre-edit provenance manifest
    log("\n[STEP 1/5] Verifying Protected Core Substrates & Recording Pre-Edit Hashes...")
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

    log("\nVerifying Frozen Historical Archives...")
    frozen_status = {}
    for rel_path, expected_hash in FROZEN_ARCHIVES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing frozen archive: {rel_path}")
            frozen_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_passed = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (FROZEN MATCH)")
            frozen_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            frozen_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_passed = False

    # 2. Verify checklist count dynamically and assert Item 30 is pending
    log("\n[STEP 2/5] Verifying Master Checklist Completion Count Dynamically...")
    checklist_path = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"
    with open(checklist_path, "r", encoding="utf-8") as f:
        checklist_content = f.read()

    matches = re.findall(r'^- \[([ x])] \*\*(\d+)\.', checklist_content, flags=re.MULTILINE)
    completed_items = [num for mark, num in matches if mark == 'x']
    pending_items = [num for mark, num in matches if mark == ' ']
    total_items = len(matches)
    completed_count = len(completed_items)
    pct = (completed_count / total_items) * 100.0 if total_items > 0 else 0.0

    log(f"  Total Checklist Items: {total_items}")
    log(f"  Currently Completed:   {completed_count} / {total_items} ({pct:.1f}%)")
    log(f"  Completed IDs:         {', '.join(completed_items)}")
    log(f"  Pending IDs:           {', '.join(pending_items)}")

    if "30" in pending_items and "30" not in completed_items:
        log("  [PASS] Item 30 is correctly marked PENDING [ ]")
    else:
        log("  [FAIL] Item 30 state unexpected: completed=" + str("30" in completed_items))
        all_passed = False

    # 3. Baseline compilation check
    log("\n[STEP 3/5] Verifying Baseline 35-Page Manuscript Compilation...")
    pdf_path = "Paper/main.pdf"
    if not os.path.exists(pdf_path):
        log("  Compiling Paper/main.tex with Tectonic...")
        cmd = ["scratch/tectonic/tectonic.exe", "--keep-intermediates", "Paper/main.tex"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"  [FAIL] Tectonic compilation failed:\n{res.stderr}")
            all_passed = False
        else:
            log("  [PASS] Tectonic compilation succeeded.")
    
    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        log(f"  Paper/main.pdf page count: {page_count}")
        if page_count == 35:
            log("  [PASS] Page count strictly equals 35.")
            last_page_text = reader.pages[34].extract_text()
            if "[27]" in last_page_text:
                log("  [PASS] Reference [27] confirmed terminating on Page 35.")
            else:
                log("  [WARN] Reference [27] not detected on Page 35 text extraction.")
        else:
            log(f"  [FAIL] Page count violation: expected 35, got {page_count}")
            all_passed = False

    # 4. Consistency Checker
    log("\n[STEP 4/5] Executing Canonical CI Consistency Checker...")
    log("  Command: python Paper/scripts/check_consistency.py --target Paper/")
    res = subprocess.run([sys.executable, "Paper/scripts/check_consistency.py", "--target", "Paper/"],
                         capture_output=True, text=True)
    log(f"  Exit code: {res.returncode}")
    for line in res.stdout.strip().splitlines():
        log(f"    {line}")
    if res.stderr.strip():
        for line in res.stderr.strip().splitlines():
            log(f"    [STDERR] {line}")
    if res.returncode == 0:
        log("  [PASS] Consistency checker passed 4/4 checks.")
    else:
        log("  [FAIL] Consistency checker returned non-zero exit code.")
        all_passed = False

    # 5. Verify Metric Provenance Document & Canonical Macro Values
    log("\n[STEP 5/5] Verifying Metric Provenance Document & Canonical Macro Values...")
    provenance_doc = "docs/ISSUE30_METRIC_PROVENANCE_AUDIT.md"
    if os.path.exists(provenance_doc):
        log(f"  [PASS] Provenance audit document exists: {provenance_doc}")
    else:
        log(f"  [FAIL] Provenance audit document missing: {provenance_doc}")
        all_passed = False

    # Check raw eval json hash
    if os.path.exists(RAW_EVAL_JSON):
        actual_raw_hash = sha256_file(RAW_EVAL_JSON)
        if actual_raw_hash == EXPECTED_RAW_EVAL_HASH:
            log(f"  [PASS] Raw eval JSON hash matches: {actual_raw_hash[:16]}...")
        else:
            log(f"  [FAIL] Raw eval JSON hash mismatch! Got {actual_raw_hash}")
            all_passed = False
    else:
        log(f"  [FAIL] Raw eval JSON missing: {RAW_EVAL_JSON}")
        all_passed = False

    # Check macros in Paper/generated_stats.tex
    gen_stats_path = "Paper/generated_stats.tex"
    with open(gen_stats_path, "r", encoding="utf-8") as f:
        gen_stats_content = f.read()

    macro_verification = {}
    for macro_name, expected_val in EXPECTED_CANONICAL_MACROS.items():
        pattern = r'\\newcommand\{\\' + macro_name + r'\}\{(.*?)\}'
        m = re.search(pattern, gen_stats_content)
        if m:
            actual_val = m.group(1).strip()
            if actual_val == expected_val:
                log(f"  [PASS] \\{macro_name} = {actual_val} (MATCH)")
                macro_verification[macro_name] = {"status": "PASS", "value": actual_val}
            else:
                log(f"  [FAIL] \\{macro_name} value mismatch! Expected {expected_val}, got {actual_val}")
                macro_verification[macro_name] = {"status": "MISMATCH", "expected": expected_val, "actual": actual_val}
                all_passed = False
        else:
            log(f"  [FAIL] Macro \\{macro_name} not found in {gen_stats_path}")
            macro_verification[macro_name] = {"status": "MISSING", "expected": expected_val}
            all_passed = False

    log(f"\nOverall Phase 1 Preflight Result: {'PASS' if all_passed else 'FAIL'}")

    preflight_data = {
        "status": "PASS" if all_passed else "FAIL",
        "protected_substrates_pre_edit_manifest": substrate_status,
        "frozen_archives": frozen_status,
        "checklist": {
            "total_items": total_items,
            "completed_count": completed_count,
            "completed_pct": round(pct, 2),
            "completed_items": completed_items,
            "pending_items": pending_items,
            "item_30_pending": "30" in pending_items
        },
        "pdf_verification": {
            "path": pdf_path,
            "page_count": page_count if os.path.exists(pdf_path) else None,
            "status": "PASS" if (os.path.exists(pdf_path) and page_count == 35) else "FAIL"
        },
        "canonical_macro_verification": macro_verification,
        "raw_eval_json": {
            "path": RAW_EVAL_JSON,
            "sha256": actual_raw_hash if os.path.exists(RAW_EVAL_JSON) else None,
            "expected_sha256": EXPECTED_RAW_EVAL_HASH
        }
    }

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with open("data/issue30_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    with open("logs/issue30_preflight.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
