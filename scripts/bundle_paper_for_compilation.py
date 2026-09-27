"""
scripts/bundle_paper_for_compilation.py
=======================================
Bundles all LaTeX sources, figures, bibliography, and generated statistics macros
into a clean, submission-ready ZIP archive for direct compilation on Overleaf or arXiv.
Also performs pre-flight linter checks (balanced braces, unresolved references, required files).
"""

import os
import sys
import zipfile
import re
from datetime import datetime

PAPER_DIR = "Paper"
BUNDLE_OUTPUT = "TERRA_Overleaf_Bundle.zip"

REQUIRED_FILES = [
    "main.tex",
    "ref.bib",
    "figure_1_system_architecture.tex",
    "figure_2_hub_centrality.tex",
    "figure_3_safety_rejection.tex"
]

def check_latex_syntax(main_tex_path):
    print("Pre-flight syntax checking main.tex...")
    with open(main_tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    errors = []
    # Check open/close braces
    open_braces = content.count("{") - content.count(r"\{")
    close_braces = content.count("}") - content.count(r"\}")
    if open_braces != close_braces:
        errors.append(f"Unbalanced curly braces: {open_braces} open vs {close_braces} close.")

    # Check for \input references
    inputs = re.findall(r'\\input\{([^}]+)\}', content)
    for inp in inputs:
        inp_filename = inp if inp.endswith(".tex") else f"{inp}.tex"
        full_inp_path = os.path.join(PAPER_DIR, inp_filename)
        if not os.path.exists(full_inp_path):
            errors.append(f"Referenced input file missing: {inp_filename}")

    # Check for \bibliography or \addbibresource
    bibs = re.findall(r'\\bibliography\{([^}]+)\}', content)
    for b in bibs:
        b_name = b if b.endswith(".bib") else f"{b}.bib"
        if not os.path.exists(os.path.join(PAPER_DIR, b_name)):
            errors.append(f"Referenced bibliography file missing: {b_name}")

    return errors

def create_bundle():
    print("=" * 70)
    print("BUNDLING TERRA LATEX MANUSCRIPT FOR COMPILATION")
    print("=" * 70)

    main_tex = os.path.join(PAPER_DIR, "main.tex")
    if not os.path.exists(main_tex):
        print(f"[ERROR] {main_tex} does not exist.")
        return False

    errors = check_latex_syntax(main_tex)
    if errors:
        print("[WARNING] Syntax issues detected:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("  Syntax checks passed: braces balanced, all inputs resolved.")

    # Include generated stats, all input-referenced files, and all tables
    files_to_bundle = list(REQUIRED_FILES)
    if os.path.exists(os.path.join(PAPER_DIR, "generated_stats.tex")) and "generated_stats.tex" not in files_to_bundle:
        files_to_bundle.append("generated_stats.tex")
    if os.path.exists(os.path.join(PAPER_DIR, "generated_corpus_stats_20k.tex")) and "generated_corpus_stats_20k.tex" not in files_to_bundle:
        files_to_bundle.append("generated_corpus_stats_20k.tex")

    # Automatically add any file referenced via \input{} in main.tex
    with open(main_tex, "r", encoding="utf-8") as f:
        content = f.read()
    inputs = re.findall(r'\\input\{([^}]+)\}', content)
    for inp in inputs:
        inp_filename = inp if inp.endswith(".tex") else f"{inp}.tex"
        inp_norm = os.path.normpath(inp_filename).replace("\\", "/")
        if inp_norm not in files_to_bundle and os.path.exists(os.path.join(PAPER_DIR, inp_norm)):
            files_to_bundle.append(inp_norm)

    # Scan and include all .tex files in tables/ directory
    tables_dir = os.path.join(PAPER_DIR, "tables")
    if os.path.exists(tables_dir):
        for t_file in sorted(os.listdir(tables_dir)):
            if t_file.endswith(".tex"):
                t_rel = f"tables/{t_file}"
                if t_rel not in files_to_bundle:
                    files_to_bundle.append(t_rel)

    print(f"\nPackaging {len(files_to_bundle)} files into {BUNDLE_OUTPUT}...")
    with zipfile.ZipFile(BUNDLE_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_bundle:
            fpath = os.path.join(PAPER_DIR, fname)
            if os.path.exists(fpath):
                arc_name = fname.replace("\\", "/")
                zf.write(fpath, arcname=arc_name)
                print(f"  + Added: {arc_name} ({os.path.getsize(fpath)} bytes)")
            else:
                print(f"  ! Skipped missing: {fname}")

    print(f"\n[SUCCESS] Bundle created: {BUNDLE_OUTPUT} ({os.path.getsize(BUNDLE_OUTPUT)} bytes)")
    print("Upload this zip directly to Overleaf for instant compilation.")
    return True

if __name__ == "__main__":
    create_bundle()
