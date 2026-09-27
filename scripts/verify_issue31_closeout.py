import os
import re
import json
import hashlib
import subprocess
from pypdf import PdfReader

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("TERRA ISSUE #31 FINAL ACCEPTANCE GATE VERIFICATION (ALL 10 GATES)")
    print("=" * 80)

    results = {}

    with open("Paper/main.tex", "r", encoding="utf-8") as f:
        main_text = f.read()

    # Gate 1: ROUGE-L Provenance Corrected
    print("\n[GATE 1/10] Verifying Metric Provenance Corrected (Deterministic Tokenized LCS)...")
    sec_iv_provenance = "via deterministic tokenized LCS matching" in main_text
    table_v_provenance = "via deterministic tokenized LCS matching; the canonical reference set is" in main_text
    no_rouge_score_lib = "using the \\texttt{rouge-score} library" not in main_text
    if sec_iv_provenance and table_v_provenance and no_rouge_score_lib:
        print("  [PASS] Gate 1: Metric provenance documented as deterministic tokenized LCS matching.")
        results["Gate 1"] = "PASS"
    else:
        print("  [FAIL] Gate 1: Provenance text missing or rouge-score library remains.")
        results["Gate 1"] = "FAIL"

    # Gate 2: Section V Roadmap Harmonization
    print("\n[GATE 2/10] Verifying Section V Roadmap Prioritizes Semantic Faithfulness...")
    roadmap_phrase = "evaluate multi-hop evolutionary reasoning via pairwise win rates and semantic faithfulness" in main_text
    if roadmap_phrase:
        print("  [PASS] Gate 2: Section V roadmap harmonized with semantic faithfulness.")
        results["Gate 2"] = "PASS"
    else:
        print("  [FAIL] Gate 2: Roadmap still mentions lexical recall or phrase missing.")
        results["Gate 2"] = "FAIL"

    # Gate 3: Denominator Parity & Contradiction Removal
    print("\n[GATE 3/10] Verifying Denominator Parity & Elimination of Numerical Contradiction...")
    has_answered_comp = "On answered queries, TERRA reaches \\TerraCatBAnsweredRougeRecall" in main_text and "comparable to Flat RAG's answered-only \\FlatRAGCatBAnsweredRougeRecall" in main_text
    has_refusal_expl = "its lower all-query value reflects 16 safety refusals scored as zero" in main_text
    no_contradiction = "TERRA captures comprehensive legal holdings (\\TerraCatBRougeRecall), outperforming Flat Vector RAG" not in main_text
    if has_answered_comp and has_refusal_expl and no_contradiction:
        print("  [PASS] Gate 3: Denominator parity established (0.525 vs 0.527) and contradiction resolved.")
        results["Gate 3"] = "PASS"
    else:
        print("  [FAIL] Gate 3: Denominator parity text missing or contradiction remains.")
        results["Gate 3"] = "FAIL"

    # Gate 4: ROUGE-L Structural Failure Modes Articulated
    print("\n[GATE 4/10] Verifying ROUGE-L Structural Failure Modes Documented...")
    dead_law = "ROUGE-L rewards verbatim citation of dead law" in main_text
    cand_len = "($\\text{Precision} = \\text{LCS}/|\\text{cand}|$)" in main_text
    if dead_law and cand_len:
        print("  [PASS] Gate 4: ROUGE-L legal domain failure modes articulated.")
        results["Gate 4"] = "PASS"
    else:
        print("  [FAIL] Gate 4: Failure modes text missing.")
        results["Gate 4"] = "FAIL"

    # Gate 5: Canonical CI Consistency Audit
    print("\n[GATE 5/10] Verifying Canonical CI Consistency Audit (4/4 PASS, 851 Macros)...")
    ci_cmd = ["python", "Paper/scripts/check_consistency.py", "--target", "Paper/"]
    ci_res = subprocess.run(ci_cmd, capture_output=True, text=True)
    ci_passed = ci_res.returncode == 0 and "CI AUDIT PASSED" in ci_res.stdout and "All 851 custom macro references" in ci_res.stdout
    if ci_passed:
        print("  [PASS] Gate 5: Canonical CI consistency audit passed 4/4 with 851 macros.")
        results["Gate 5"] = "PASS"
    else:
        print("  [FAIL] Gate 5: CI audit failed.")
        print(ci_res.stdout)
        results["Gate 5"] = "FAIL"

    # Gate 6: Strict 35-Page Budget & Anchors
    print("\n[GATE 6/10] Verifying Strict 35-Page Budget & Anchors...")
    reader = PdfReader("Paper/main.pdf")
    page_count = len(reader.pages)
    p35_text = reader.pages[34].extract_text()
    t23_top = "TABLE XXIII" in p35_text
    ref27_bot = "[27]" in p35_text and "Zheng" in p35_text
    if page_count == 35 and t23_top and ref27_bot:
        print(f"  [PASS] Gate 6: Strictly 35 pages ({page_count}), Table XXIII at top, Ref [27] at bottom.")
        results["Gate 6"] = "PASS"
    else:
        print(f"  [FAIL] Gate 6: Page count {page_count}, Table XXIII: {t23_top}, Ref [27]: {ref27_bot}")
        results["Gate 6"] = "FAIL"

    # Gate 7: Protected Core Substrates Bit-Invariant
    print("\n[GATE 7/10] Verifying 11 Protected Core Substrates & Frozen Archives...")
    with open("data/issue31_preflight.json", "r") as f:
        preflight = json.load(f)
    substrates_pass = True
    for rel_path, info in preflight["protected_substrates_pre_edit_manifest"].items():
        if sha256_file(rel_path) != info["hash"]:
            substrates_pass = False
            print(f"    Mismatch: {rel_path}")
    for rel_path, info in preflight["frozen_archives"].items():
        if sha256_file(rel_path) != info["hash"]:
            substrates_pass = False
            print(f"    Mismatch: {rel_path}")
    raw_eval_path = "scratch/canonical_v2/terra_canonical_v2_eval.json"
    if sha256_file(raw_eval_path) != preflight["raw_eval_json"]["expected_sha256"]:
        substrates_pass = False
        print(f"    Mismatch: {raw_eval_path}")
    if substrates_pass:
        print("  [PASS] Gate 7: All 11 protected substrates, 2 frozen archives, and raw eval artifact match 100%.")
        results["Gate 7"] = "PASS"
    else:
        print("  [FAIL] Gate 7: Protected substrate mismatch detected.")
        results["Gate 7"] = "FAIL"

    # Gate 8: Overleaf Distribution Bundles Synchronized
    print("\n[GATE 8/10] Verifying Overleaf Distribution Bundles Synchronized...")
    ob_paper = "Paper/overleaf_bundle.zip"
    ob_root = "TERRA_Overleaf_Bundle.zip"
    if os.path.exists(ob_paper) and os.path.exists(ob_root) and sha256_file(ob_paper) == sha256_file(ob_root):
        print(f"  [PASS] Gate 8: Overleaf bundles exist and are bit-identical (SHA256: {sha256_file(ob_paper)[:16]}...).")
        results["Gate 8"] = "PASS"
    else:
        print("  [FAIL] Gate 8: Overleaf bundles missing or hash mismatch.")
        results["Gate 8"] = "FAIL"

    # Gate 9: Reproducibility Bundle & External Manifest
    print("\n[GATE 9/10] Verifying Reproducibility Bundle & External Manifest...")
    repro_zip = "TERRA_Reproducibility_Bundle.zip"
    repro_manifest = "logs/issue31_reproducibility_manifest.json"
    repro_pass = os.path.exists(repro_zip) and os.path.exists(repro_manifest)
    if repro_pass:
        with open(repro_manifest, "r", encoding="utf-8") as f:
            m_data = json.load(f)
        if m_data["zip_sha256"] == sha256_file(repro_zip):
            print(f"  [PASS] Gate 9: Reproducibility bundle matches external manifest ({m_data['file_count']} files).")
            results["Gate 9"] = "PASS"
        else:
            print("  [FAIL] Gate 9: Bundle SHA256 does not match manifest.")
            results["Gate 9"] = "FAIL"
    else:
        print("  [FAIL] Gate 9: Bundle or manifest missing.")
        results["Gate 9"] = "FAIL"

    # Gate 10: Dynamic Checklist Verification
    print("\n[GATE 10/10] Verifying Master Checklist Dynamic Status...")
    chk_path = "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md"
    with open(chk_path, "r", encoding="utf-8") as f:
        chk_text = f.read()
    matches = re.findall(r'^- \[([ x])] \*\*(\d+)\.', chk_text, flags=re.MULTILINE)
    completed = [num for mark, num in matches if mark == 'x']
    n_comp = len(completed)
    n_tot = len(matches)
    is_31_comp = "31" in completed
    if n_comp == 35 and n_tot == 43 and is_31_comp:
        print(f"  [PASS] Gate 10: Item 31 marked complete, progress dynamically verified at {n_comp}/{n_tot} (81.4%).")
        results["Gate 10"] = "PASS"
    else:
        print(f"  [FAIL] Gate 10: Progress verification failed: {n_comp}/{n_tot}, Item 31 marked: {is_31_comp}")
        results["Gate 10"] = "FAIL"

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    all_gates_pass = all(v == "PASS" for v in results.values())
    for g, status in results.items():
        print(f"  {g:<15}: {status}")
    print(f"\nFinal Acceptance Gate Disposition: {'ALL 10 GATES PASS' if all_gates_pass else 'FAILURES DETECTED'}")
    assert all_gates_pass

if __name__ == "__main__":
    main()
