"""
scripts/build_paper.py
======================
Master build pipeline for the TERRA paper.

Execution Order:
  1. Generate Corpus Topology Stats (Paper/scripts/generate_corpus_stats.py)
  2. Generate Benchmark Evaluation Stats (Paper/scripts/generate_stats.py)
  3. Run Consistency CI Audit (Paper/scripts/check_consistency.py)
  4. Bundle LaTeX Manuscript for Overleaf / Local Compilation (scripts/bundle_paper_for_compilation.py)

STRICT RULE: If ANY step fails or returns a non-zero exit code, execution halts
immediately with sys.exit(code). No zip archive is created or updated on failure.
"""

import os
import sys
import subprocess

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_BIN = sys.executable

def run_step(step_num, step_name, command_args):
    print("\n" + "=" * 75)
    print(f"STEP {step_num}: {step_name.upper()}")
    print("=" * 75)
    print(f"Executing: {' '.join(command_args)}")
    
    result = subprocess.run(command_args, cwd=ROOT_DIR)
    if result.returncode != 0:
        print("\n" + "!" * 75)
        print(f"[BUILD PIPELINE FAILED] Step {step_num} ({step_name}) exited with error code {result.returncode}!")
        print("Halting paper build. Packaging aborted.")
        print("!" * 75 + "\n")
        sys.exit(result.returncode)
    print(f"[STEP {step_num} PASSED]")

def main():
    print("*" * 75)
    print("TERRA END-TO-END VERIFIED PAPER BUILD PIPELINE")
    print("*" * 75)

    # Step 1: Generate Corpus Stats
    run_step(
        1,
        "Generate Corpus Topology Stats",
        [PYTHON_BIN, os.path.join(ROOT_DIR, "Paper/scripts/generate_corpus_stats.py")]
    )

    # Step 2: Generate Evaluation Stats
    run_step(
        2,
        "Generate Benchmark Evaluation Stats",
        [PYTHON_BIN, os.path.join(ROOT_DIR, "Paper/scripts/generate_stats.py")]
    )

    # Step 3: Consistency CI Audit
    run_step(
        3,
        "Run Consistency CI Check",
        [PYTHON_BIN, os.path.join(ROOT_DIR, "Paper/scripts/check_consistency.py")]
    )

    # Step 4: Bundle Manuscript
    run_step(
        4,
        "Package LaTeX Manuscript (Overleaf Bundle)",
        [PYTHON_BIN, os.path.join(ROOT_DIR, "scripts/bundle_paper_for_compilation.py")]
    )

    print("\n" + "*" * 75)
    print("[BUILD SUCCESS] All verification and compilation steps completed cleanly.")
    print("*" * 75)

if __name__ == "__main__":
    main()
