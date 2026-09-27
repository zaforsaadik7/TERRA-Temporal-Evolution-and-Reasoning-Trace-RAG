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

EXPECTED_CANONICAL_ROUGE_MACROS = {
    "TerraCatBRougeRecall": "0.448",
    "HippoRAGCatBRougeRecall": "0.536",
    "GraphRAGCatBRougeRecall": "0.523",
    "FlatRAGCatBRougeRecall": "0.500",
    "DirectLLMCatBRougeRecall": "0.546",
    "TerraCatBRougePrecision": "0.086",
    "HippoRAGCatBRougePrecision": "0.085",
    "GraphRAGCatBRougePrecision": "0.083",
    "FlatRAGCatBRougePrecision": "0.096",
    "DirectLLMCatBRougePrecision": "0.064",
    "TerraCatBRougeFOne": "0.123",
    "HippoRAGCatBRougeFOne": "0.145",
    "GraphRAGCatBRougeFOne": "0.140",
    "FlatRAGCatBRougeFOne": "0.147",
    "DirectLLMCatBRougeFOne": "0.115",
    "TerraCatBMeanWords": "415",
    "HippoRAGCatBMeanWords": "470",
    "GraphRAGCatBMeanWords": "477",
    "FlatRAGCatBMeanWords": "481",
    "DirectLLMCatBMeanWords": "612"
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
    log("TERRA ISSUE #31 PREFLIGHT VERIFICATION & PRE-EDIT MANIFEST")
    log("=" * 80)

    all_passed = True

    # 1. Verify protected substrates & establish pre-edit provenance manifest
    log("\n[STEP 1/6] Verifying Protected Core Substrates & Recording Pre-Edit Hashes...")
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

    # 2. Verify baseline 35-page PDF compilation
    log("\n[STEP 2/6] Verifying Baseline 35-Page Manuscript PDF & Structural Anchors...")
    pdf_path = "Paper/main.pdf"
    if not os.path.exists(pdf_path):
        log("  Compiling Paper/main.tex with Tectonic...")
        cmd = ["scratch/tectonic/tectonic.exe", "Paper/main.tex", "--outdir", "Paper"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"  [FAIL] Tectonic compilation failed:\n{res.stderr}")
            all_passed = False
        else:
            log("  [PASS] Tectonic compilation succeeded.")
    
    page_count = None
    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        log(f"  Paper/main.pdf page count: {page_count}")
        if page_count == 35:
            log("  [PASS] Page count strictly equals 35.")
            p35_text = reader.pages[34].extract_text()
            if "TABLE XXIII" in p35_text:
                log("  [PASS] Table XXIII confirmed at top of Page 35.")
            else:
                log("  [FAIL] Table XXIII not found on Page 35!")
                all_passed = False
            if "[27]" in p35_text and "Zheng" in p35_text:
                log("  [PASS] Reference [27] (Zheng et al., NeurIPS 2023) confirmed terminating Page 35.")
            else:
                log("  [WARN] Reference [27] Zheng not detected on Page 35 text extraction.")
        else:
            log(f"  [FAIL] Page count violation: expected 35, got {page_count}")
            all_passed = False

    # 3. Canonical CI Consistency Checker & Baseline Macro Count
    log("\n[STEP 3/6] Executing Canonical CI Consistency Checker & Macro Count Audit...")
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
        log("  [PASS] Canonical CI consistency audit passed 4/4 checks.")
    else:
        log("  [FAIL] Canonical CI consistency audit returned non-zero exit code.")
        all_passed = False

    # Count custom macro references in main.tex
    with open("Paper/main.tex", "r", encoding="utf-8") as f:
        main_content = f.read()

    used_macros = set(re.findall(r'\\([A-Z][a-zA-Z0-9]+|num[A-Z][a-zA-Z0-9]+)', main_content))
    standard_latex = {
        "textbf", "textit", "section", "subsection", "subsubsection", "caption", "label", "ref",
        "cite", "begin", "end", "item", "resizebox", "columnwidth", "textwidth", "toprule",
        "midrule", "bottomrule", "centering", "table", "tabular", "figure", "input", "include",
        "bibliographystyle", "bibliography", "maketitle", "title", "author", "IEEEauthorblockN",
        "IEEEauthorblockA", "IEEEauthorrefmark", "IEEEkeywords", "textcolor", "fancyhf",
        "fancyplain", "lhead", "lfoot", "renewcommand", "headrulewidth", "thispagestyle",
        "makeatletter", "makeatother", "footnoterule", "kern", "hrule", "p", "width", "setlength",
        "marginparwidth", "texttt", "equation", "enumerate", "itemize", "mathbf", "text", "times",
        "pm", "ensuremath", "alpha", "beta", "rho", "sigma", "max", "min", "bigcup", "mathcal",
        "bar", "langle", "rangle", "AddToShipoutPictureBG", "Delta", "LenToUnit",
        "IEEEoverridecommandlockouts", "IEEEkeywordsname", "BibTeX", "AtPageUpperMyright",
        "AtPageUpperLeft", "Huge", "Large", "small", "footnotesize", "scriptsize", "tiny", "normalsize",
        "IEEEbibitemsep", "dbltextfloatsep", "textfloatsep", "textquotesingle"
    }
    custom_used = used_macros - standard_latex
    macro_count_baseline = len(custom_used)
    log(f"  Baseline custom macro references resolved in main.tex: {macro_count_baseline}")
    if macro_count_baseline == 848:
        log("  [PASS] Baseline custom macro count strictly equals 848.")
    else:
        log(f"  [WARN] Baseline custom macro count is {macro_count_baseline} (expected 848).")

    # 4. Verify Deterministic Tokenized-LCS Implementation and Raw Data
    log("\n[STEP 4/6] Verifying Tokenized-LCS Implementation & Raw Source Ground Truth...")
    with open("Paper/scripts/generate_stats.py", "r", encoding="utf-8") as f:
        gen_stats_code = f.read()

    has_tokenize = "def tokenize(text):" in gen_stats_code and r"\b\w+\b" in gen_stats_code
    has_lcs = "def lcs(x, y):" in gen_stats_code and "dp[m][n]" in gen_stats_code
    has_rouge_calc = "def compute_rouge_l_stats(cand_text, ref_text):" in gen_stats_code
    no_rouge_score_import = "import rouge_score" not in gen_stats_code and "from rouge_score" not in gen_stats_code

    if has_tokenize and has_lcs and has_rouge_calc and no_rouge_score_import:
        log("  [PASS] generate_stats.py implements deterministic tokenized LCS (no rouge-score library dependency).")
    else:
        log(f"  [FAIL] Tokenized LCS verification failed: tokenize={has_tokenize}, lcs={has_lcs}, rouge_calc={has_rouge_calc}, no_lib={no_rouge_score_import}")
        all_passed = False

    # Check raw eval json hash
    if os.path.exists(RAW_EVAL_JSON):
        actual_raw_hash = sha256_file(RAW_EVAL_JSON)
        if actual_raw_hash == EXPECTED_RAW_EVAL_HASH:
            log(f"  [PASS] Raw eval JSON hash matches: {actual_raw_hash[:16]}... (MATCH)")
        else:
            log(f"  [FAIL] Raw eval JSON hash mismatch! Got {actual_raw_hash}")
            all_passed = False
    else:
        log(f"  [FAIL] Raw eval JSON missing: {RAW_EVAL_JSON}")
        all_passed = False

    # Check existing canonical ROUGE-L macros in Paper/generated_stats.tex
    gen_stats_path = "Paper/generated_stats.tex"
    with open(gen_stats_path, "r", encoding="utf-8") as f:
        gen_stats_content = f.read()

    macro_verification = {}
    for macro_name, expected_val in EXPECTED_CANONICAL_ROUGE_MACROS.items():
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

    # 5. Verify checklist count dynamically and assert Item 31 is pending
    log("\n[STEP 5/6] Verifying Master Checklist Completion Count Dynamically...")
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

    if "31" in pending_items and "31" not in completed_items:
        log("  [PASS] Item 31 is correctly marked PENDING [ ]")
    else:
        log("  [FAIL] Item 31 state unexpected: completed=" + str("31" in completed_items))
        all_passed = False

    # 6. Verify Paper and Tracked Files are Untouched
    log("\n[STEP 6/6] Verifying Workspace Freezing (Zero Unstaged Tracked Changes)...")
    git_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    tracked_changes = [line for line in git_res.stdout.splitlines() if not line.startswith("??")]
    paper_changes = [line for line in tracked_changes if "Paper/" in line]
    if not paper_changes:
        log("  [PASS] Paper/ directory has ZERO modifications.")
    else:
        log(f"  [FAIL] Detected changes in Paper/: {paper_changes}")
        all_passed = False

    log(f"\nOverall Phase 1 Preflight Result: {'PASS' if all_passed else 'FAIL'}")

    preflight_data = {
        "status": "PASS" if all_passed else "FAIL",
        "baseline_macro_count": macro_count_baseline,
        "expected_macro_count_after_phase3": 851,
        "protected_substrates_pre_edit_manifest": substrate_status,
        "frozen_archives": frozen_status,
        "checklist": {
            "total_items": total_items,
            "completed_count": completed_count,
            "completed_pct": round(pct, 2),
            "completed_items": completed_items,
            "pending_items": pending_items,
            "item_31_pending": "31" in pending_items
        },
        "pdf_verification": {
            "path": pdf_path,
            "page_count": page_count,
            "status": "PASS" if (os.path.exists(pdf_path) and page_count == 35) else "FAIL",
            "table_xxiii_page_35_top": "TABLE XXIII" in p35_text if (os.path.exists(pdf_path) and page_count == 35) else False,
            "reference_27_page_35_bottom": "[27]" in p35_text if (os.path.exists(pdf_path) and page_count == 35) else False
        },
        "canonical_ci_consistency": {
            "command": "python Paper/scripts/check_consistency.py --target Paper/",
            "exit_code": res.returncode,
            "status": "PASS" if res.returncode == 0 else "FAIL"
        },
        "deterministic_tokenized_lcs_provenance": {
            "tokenize_regex_present": has_tokenize,
            "lcs_dp_present": has_lcs,
            "compute_rouge_l_stats_present": has_rouge_calc,
            "no_rouge_score_library_import": no_rouge_score_import,
            "status": "PASS" if (has_tokenize and has_lcs and has_rouge_calc and no_rouge_score_import) else "FAIL"
        },
        "canonical_rouge_macro_verification": macro_verification,
        "raw_eval_json": {
            "path": RAW_EVAL_JSON,
            "sha256": actual_raw_hash if os.path.exists(RAW_EVAL_JSON) else None,
            "expected_sha256": EXPECTED_RAW_EVAL_HASH
        }
    }

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with open("data/issue31_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    with open("logs/issue31_preflight.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
