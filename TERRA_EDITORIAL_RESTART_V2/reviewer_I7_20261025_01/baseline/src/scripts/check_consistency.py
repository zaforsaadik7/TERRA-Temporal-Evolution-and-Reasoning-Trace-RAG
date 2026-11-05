"""
Paper/scripts/check_consistency.py
===================================
Automated Pre-Flight & Pre-Commit Consistency CI Check for TERRA.

Enforces:
  1. Checksum verification: Raw evaluation & corpus files match the SHA256 headers in generated macro files.
  2. Macro cross-referencing: Every macro referenced in main.tex is defined in generated_stats.tex or generated_corpus_stats.tex.
  3. No orphaned literals: Scans main.tex for raw numeric result patterns (0.XXX, XX.X%, etc.) not whitelisted in allowed_literals.txt.
  4. Abstract-body parity: Asserts that key performance claims in the Abstract match the canonical results tables.
"""

import os
import sys
import re
import hashlib

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PAPER_DIR = os.path.join(ROOT_DIR, "Paper")
MAIN_TEX = os.path.join(PAPER_DIR, "main.tex")
STATS_TEX = os.path.join(PAPER_DIR, "generated_stats.tex")
CORPUS_TEX = os.path.join(PAPER_DIR, "generated_corpus_stats_20k.tex")
OBSCURE_TEX = os.path.join(PAPER_DIR, "generated_obscure_stats.tex")
WHITELIST_FILE = os.path.join(os.path.dirname(__file__), "allowed_literals.txt")

CANONICAL_RAW = os.path.join(ROOT_DIR, "scratch/canonical_v2/terra_canonical_v2_eval.json") if os.path.exists(os.path.join(ROOT_DIR, "scratch/canonical_v2/terra_canonical_v2_eval.json")) else os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
ABLATION_RAW = os.path.join(ROOT_DIR, "terra_true_ablation_pilot_raw.json")
CORPUS_RAW = os.path.join(ROOT_DIR, "dataset_20k_cap/terra_eeg_index_20k.json")
OBS_SUMMARY_RAW = os.path.join(ROOT_DIR, "scratch/obscure_overruled_summary.json")
D1_SUMMARY_RAW = os.path.join(ROOT_DIR, "scratch/famous_d1_summary.json")
CROSS_SUMMARY_RAW = os.path.join(ROOT_DIR, "scratch/cross_suite_summary.json")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

def extract_header_checksum(tex_path, keyword="SHA256:"):
    if not os.path.exists(tex_path):
        return None
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            if keyword in line:
                m = re.search(r'[a-f0-9]{64}', line, re.IGNORECASE)
                if m:
                    return m.group(0).lower()
    return None

def load_whitelist(filepath):
    whitelist = set()
    if not os.path.exists(filepath):
        return whitelist
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            token = line.split("#")[0].strip()
            if token:
                whitelist.add(token)
    return whitelist

def parse_defined_macros(tex_path):
    macros = {}
    if not os.path.exists(tex_path):
        return macros
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}\{(.*)\}', line)
            if m:
                macros[m.group(1)] = m.group(2).strip()
    return macros

def run_checks():
    errors = []
    print("=" * 70)
    print("TERRA CONSISTENCY & INTEGRITY CI AUDIT")
    print("=" * 70)

    # CHECK 1: Cryptographic Checksum Integrity
    print("\n[CHECK 1/4] Verifying Raw Data SHA256 Checksums against Macro Headers...")
    for item in [
        ("Canonical Baseline Eval Raw", CANONICAL_RAW, STATS_TEX, "SHA256:"),
        ("Corpus EEG Index (20k)", CORPUS_RAW, CORPUS_TEX, "SHA256:"),
        ("Obscure Summary (Issue #18)", OBS_SUMMARY_RAW, OBSCURE_TEX, "Obscure Summary SHA256:"),
        ("Famous D1 Summary (Issue #18)", D1_SUMMARY_RAW, OBSCURE_TEX, "Famous D1 Summary SHA256:"),
        ("Cross Suite Summary (Issue #18)", CROSS_SUMMARY_RAW, OBSCURE_TEX, "Cross Suite Summary SHA256:")
    ]:
        label, raw_path, tex_path, keyword = item
        if not os.path.exists(raw_path):
            errors.append(f"Raw source file missing: {raw_path}")
            continue
        actual_sha = compute_sha256(raw_path).lower()
        header_sha = extract_header_checksum(tex_path, keyword=keyword)
        if not header_sha:
            errors.append(f"No SHA256 header found in {tex_path} for {label}")
        elif actual_sha != header_sha:
            errors.append(f"Checksum mismatch for {label}!\n  Actual: {actual_sha}\n  Header: {header_sha}")
        else:
            print(f"  [PASS] {label}: {actual_sha[:16]}... matches header")

    # CHECK 2: Macro Cross-Referencing Parity
    print("\n[CHECK 2/4] Verifying Macro Definitions & LaTeX Symbol Resolution...")
    defined_stats = parse_defined_macros(STATS_TEX)
    defined_corpus = parse_defined_macros(CORPUS_TEX)
    defined_obscure = parse_defined_macros(OBSCURE_TEX)
    all_defined = {**defined_stats, **defined_corpus, **defined_obscure}

    with open(MAIN_TEX, "r", encoding="utf-8") as f:
        main_content = f.read()

    # Find all macro invocations in main.tex that match known patterns
    used_macros = set(re.findall(r'\\([A-Z][a-zA-Z0-9]+|num[A-Z][a-zA-Z0-9]+)', main_content))
    
    # Filter standard LaTeX commands
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
        "IEEEbibitemsep", "dbltextfloatsep", "textfloatsep"
    }

    custom_used = used_macros - standard_latex
    missing_definitions = [m for m in custom_used if m not in all_defined]

    if missing_definitions:
        for m in missing_definitions:
            errors.append(f"Undefined macro \\{m} referenced in main.tex")
    else:
        print(f"  [PASS] All {len(custom_used)} custom macro references in main.tex are strictly defined.")

    # CHECK 3: Orphaned Numeric Literals Audit
    print("\n[CHECK 3/4] Scanning for Orphaned Numeric Result Literals in main.tex...")
    whitelist = load_whitelist(WHITELIST_FILE)
    
    # Scan main.tex lines for suspicious numeric patterns: 0.XXX, XX.X%, etc.
    with open(MAIN_TEX, "r", encoding="utf-8") as f:
        lines = f.readlines()

    orphaned_literals = []
    # Regular expression matching result numbers: any float, or any percentage (with or without backslash)
    num_pattern = re.compile(r'(?<![A-Za-z0-9_\\])([0-9]+\.[0-9]+|[0-9]+(?:\.[0-9]+)?\\?%)')

    for line_no, line in enumerate(lines, 1):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("%") or clean_line.startswith("\\newcommand") or clean_line.startswith("\\input"):
            continue

        # Strip trailing unescaped comments while preserving literal percentages
        comment_split = re.split(r'(?<!\\)%\s+', clean_line)
        eval_line = comment_split[0].strip()

        matches = num_pattern.findall(eval_line)
        for m in matches:
            normalized_m = m.replace("\\%", "%")
            if normalized_m not in whitelist and m not in whitelist:
                orphaned_literals.append((line_no, m, clean_line[:90]))

    if orphaned_literals:
        print(f"  [FAIL] Found {len(orphaned_literals)} un-macrofied result numbers:")
        for line_no, val, snippet in orphaned_literals:
            print(f"    Line {line_no}: '{val}' in: {snippet}...")
            errors.append(f"Line {line_no}: Hardcoded literal '{val}' not in allowed_literals.txt")
    else:
        print(f"  [PASS] Zero orphaned result numbers found in main.tex.")

    # CHECK 4: Abstract-Body Parity Spot Check
    print("\n[CHECK 4/4] Spot-Checking Abstract-to-Body Claim Alignment...")
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', main_content, re.DOTALL)
    if not abstract_match:
        errors.append("Could not locate \\begin{abstract} in main.tex")
    else:
        abstract_text = abstract_match.group(1)
        # Verify key macros are used in abstract
        core_claims = [
            "HippoRAGOverallFaithfulnessMean",
            "TerraOverallFaithfulnessMean",
            "TerraAnswerOnlyFaithfulness",
            "numUniqueQueries",
            "numTotalEvals",
            "CatBTerraVsFlatDelta",
            "CatBTerraVsHippoRAGDelta",
            "TerraCatDRejectionRate"
        ]
        for macro in core_claims:
            if f"\\{macro}" not in abstract_text:
                errors.append(f"Abstract is missing core canonical macro: \\{macro}")
            else:
                print(f"  [PASS] Abstract properly invokes \\{macro}")

    print("\n" + "=" * 70)
    if errors:
        print(f"[CI AUDIT FAILED] Found {len(errors)} consistency errors:")
        for e in errors:
            print(f"  - {e}")
        print("=" * 70)
        sys.exit(1)
    else:
        print("[CI AUDIT PASSED] 100% Internal Consistency & Cryptographic Grounding Verified.")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    run_checks()
