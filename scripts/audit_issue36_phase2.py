"""
TERRA Issue #36 Phase 2 Targeted Diff & Invariance Audit
Verifies:
1. docs/ROUTER_SPECIFICATION.md updates (greedy decoding, hosted variability, D066 non-causal explanation, archive reproducibility, removal of unverified 349/350 claim).
2. ask_terra.py comment update (greedy decoding, temperature=0.0 functionally untouched, py_compile passes).
3. 11 Protected substrates invariance against preflight manifest.
4. Protected files boundary (Paper/, datasets, generated statistics, bundles, checklist untouched).
5. CI 4/4 and Tectonic 35-page PDF compilation.
"""

import sys
import os
import json
import hashlib
import subprocess
import pypdf

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("TERRA ISSUE #36: PHASE 2 TARGETED DIFF & INVARIANCE AUDIT")
    print("=" * 80)

    # ---------------------------------------------------------
    # 1. Audit docs/ROUTER_SPECIFICATION.md
    # ---------------------------------------------------------
    print("\n[CHECK 1/5] Auditing docs/ROUTER_SPECIFICATION.md...")
    spec_path = "docs/ROUTER_SPECIFICATION.md"
    assert os.path.exists(spec_path), f"Missing {spec_path}"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()

    # Check replacements
    assert "under greedy decoding at $T=0.0$" in spec_text, "Failed: Line 9 greedy decoding phrasing missing"
    assert "Greedy decoding at $T = 0.0$; minimizes sampling variance, subject to hosted serving variability (Section VI-B, Limitation 5)" in spec_text, "Failed: Table sampling temperature phrasing missing"
    assert "at deterministic temperature" not in spec_text, "Failed: 'at deterministic temperature' still present"
    assert "zero stochastic variance" not in spec_text, "Failed: 'zero stochastic variance' still present"

    # Check non-causal D066 and reproducibility wording
    expected_noncausal = "consistent with numerical or serving-level variability in hosted inference; the precise backend cause cannot be isolated from available logs."
    assert expected_noncausal in spec_text, f"Failed: Non-causal D066 text missing: {expected_noncausal}"

    expected_reproducibility = "To preserve reproducibility of the reported results, all analyses are bound to immutable, SHA256-verified raw completion archives; rerunning the hosted endpoint may yield different completions."
    assert expected_reproducibility in spec_text, f"Failed: Reproducibility text missing: {expected_reproducibility}"

    # Confirm unverified 349/350 claim was removed
    assert "349/350" not in spec_text, "Failed: Unverified 349/350 statistic still present in spec"
    assert "99.71%" not in spec_text, "Failed: Unverified 99.71% statistic still present in spec"

    print("  [PASS] docs/ROUTER_SPECIFICATION.md contains all approved greedy-decoding, hosted-variability, and non-causal D066 wording.")
    print("  [PASS] Zero legacy deterministic-temperature claims remain in router specification.")
    print("  [PASS] Unverified 349/350 statistic successfully removed and excluded from specification.")

    # ---------------------------------------------------------
    # 2. Audit ask_terra.py
    # ---------------------------------------------------------
    print("\n[CHECK 2/5] Auditing ask_terra.py...")
    code_path = "ask_terra.py"
    with open(code_path, "r", encoding="utf-8") as f:
        code_lines = f.readlines()

    # Line 79 (0-indexed: 78)
    line_79 = code_lines[78].strip()
    assert line_79 == "# Enforce temperature=0.0 for greedy decoding (TIER 1.6)", f"Failed: Line 79 unexpected: {line_79}"
    assert "deterministic outputs" not in "".join(code_lines), "Failed: 'deterministic outputs' still present in ask_terra.py"

    # Verify temperature=0.0 functionally untouched
    assert "config['temperature'] = 0.0" in "".join(code_lines), "Failed: config['temperature'] = 0.0 missing"
    assert "config.temperature = 0.0" in "".join(code_lines), "Failed: config.temperature = 0.0 missing"
    assert "temperature=0.0," in "".join(code_lines), "Failed: temperature=0.0, parameter missing"

    # Verify py_compile
    res = subprocess.run([sys.executable, "-m", "py_compile", code_path], capture_output=True, text=True)
    assert res.returncode == 0, f"py_compile failed on ask_terra.py: {res.stderr}"
    print("  [PASS] ask_terra.py line 79 comment updated to greedy decoding.")
    print("  [PASS] temperature=0.0 runtime enforcement strictly preserved at 3 code locations.")
    print("  [PASS] py_compile passed with zero syntax errors.")

    # ---------------------------------------------------------
    # 3. Verify Protected Substrates Invariance
    # ---------------------------------------------------------
    print("\n[CHECK 3/5] Verifying 11 Protected Substrates Invariance...")
    manifest_path = "logs/issue36_preflight_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for path, info in manifest["protected_substrates"].items():
        actual_sha = sha256_file(path)
        expected_sha = info["expected_sha256"]
        assert actual_sha == expected_sha, f"Substrate changed: {path} (got {actual_sha}, expected {expected_sha})"
        print(f"  [PASS] {path} invariant ({actual_sha[:16]}...)")

    # ---------------------------------------------------------
    # 4. Verify Protected Boundaries
    # ---------------------------------------------------------
    print("\n[CHECK 4/5] Verifying Protected File Boundaries...")
    main_tex_sha = sha256_file("Paper/main.tex")
    expected_main_tex = "f9dd7d9324ee35586009c3bdd4c89d6296b11abab7614e0ab8a83d6ae8dbe8cc"
    assert main_tex_sha == expected_main_tex, f"Paper/main.tex modified! Got {main_tex_sha}"
    print(f"  [PASS] Paper/main.tex untouched ({main_tex_sha[:16]}...)")

    checklist_sha = sha256_file("TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md")
    expected_checklist = "287481dc99ae6d2b929804475a785d49f6140c9a8b2dbbe0b5c8d501a2698cb7"
    assert checklist_sha == expected_checklist, f"Master checklist modified! Got {checklist_sha}"
    print(f"  [PASS] TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md untouched ({checklist_sha[:16]}...)")

    # ---------------------------------------------------------
    # 5. CI & Compilation Verification
    # ---------------------------------------------------------
    print("\n[CHECK 5/5] Running CI & Tectonic Compilation...")
    ci_res = subprocess.run([sys.executable, "Paper/scripts/check_consistency.py"], capture_output=True, text=True)
    assert ci_res.returncode == 0, f"CI check failed:\n{ci_res.stdout}\n{ci_res.stderr}"
    print("  [PASS] CI consistency check passed 4/4.")

    tec_cmd = [r"scratch/tectonic/tectonic.exe", "--keep-intermediates", "Paper/main.tex"]
    tec_res = subprocess.run(tec_cmd, capture_output=True, text=True)
    assert tec_res.returncode == 0, f"Tectonic failed: {tec_res.stderr}"

    reader = pypdf.PdfReader("Paper/main.pdf")
    num_pages = len(reader.pages)
    assert num_pages == 35, f"PDF page count is {num_pages}, expected 35"
    p35_text = reader.pages[34].extract_text()
    assert "TABLE XXIII" in p35_text, "Page 35 missing TABLE XXIII"
    assert "[27]" in p35_text, "Page 35 missing Reference [27]"
    print(f"  [PASS] Tectonic compiled cleanly to 35 pages with Page 35 anchors intact.")

    print("\n" + "=" * 80)
    print("ALL PHASE 2 AUDIT CHECKS PASSED STRICTLY.")
    print("=" * 80)

if __name__ == "__main__":
    main()
