"""
scripts/run_v2_harness.py
=========================
Executes scripts/generate_stats_v2.py under full redirection of any Paper/ writes
to scratch/w_out_v2/<relative_path>.
Guarantees ZERO writes to Paper/.
"""

import builtins
import io
import os
import sys
import shutil
import re
import difflib
import runpy
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRATCH_DIR = ROOT_DIR / "scratch"
W_OUT_V2_DIR = SCRATCH_DIR / "w_out_v2"
REAL_PAPER_DIR = ROOT_DIR / "Paper"
GEN_SCRIPT_V2 = ROOT_DIR / "scripts" / "generate_stats_v2.py"

# Clean and recreate scratch/w_out_v2
if W_OUT_V2_DIR.exists():
    shutil.rmtree(W_OUT_V2_DIR)
W_OUT_V2_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Tracked redirections and writes
# ----------------------------------------------------------------------
redirected_paths = []
stopped_on_write = False
stopped_reason = ""

orig_builtins_open = builtins.open
orig_io_open = io.open
orig_path_open = Path.open
orig_path_write_text = Path.write_text


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with orig_builtins_open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def resolve_target(path, mode="r"):
    global stopped_on_write, stopped_reason
    try:
        p = Path(path).resolve()
    except Exception:
        p = Path(os.path.abspath(str(path)))

    is_write = any(m in mode for m in ["w", "a", "x", "+"])
    if not is_write:
        return path, False

    try:
        rel = p.relative_to(ROOT_DIR)
    except ValueError:
        try:
            rel_w = p.relative_to(W_OUT_V2_DIR)
            return path, False
        except ValueError:
            stopped_on_write = True
            stopped_reason = f"Write outside scratch/w_out_v2/: {p} with mode {mode}"
            raise RuntimeError(stopped_reason)

    parts = rel.parts
    if len(parts) > 0 and parts[0].lower() == "paper":
        dst = W_OUT_V2_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        redirected_paths.append((str(p), str(dst), mode))
        return dst, True
    else:
        try:
            p.relative_to(W_OUT_V2_DIR)
            return path, False
        except ValueError:
            stopped_on_write = True
            stopped_reason = f"Write outside scratch/w_out_v2/: {p} with mode {mode}"
            raise RuntimeError(stopped_reason)


def patched_builtins_open(file, mode="r", *args, **kwargs):
    target, redirected = resolve_target(file, mode)
    return orig_builtins_open(target, mode, *args, **kwargs)


def patched_io_open(file, mode="r", *args, **kwargs):
    target, redirected = resolve_target(file, mode)
    return orig_io_open(target, mode, *args, **kwargs)


def patched_path_open(self, mode="r", *args, **kwargs):
    target, redirected = resolve_target(self, mode)
    return orig_path_open(target, mode, *args, **kwargs)


def patched_path_write_text(self, data, encoding=None, errors=None, newline=None):
    target, redirected = resolve_target(self, "w")
    return orig_path_write_text(target, data, encoding=encoding, errors=errors, newline=newline)


builtins.open = patched_builtins_open
io.open = patched_io_open
Path.open = patched_path_open
Path.write_text = patched_path_write_text


def main():
    print("=" * 80)
    print("TASK U2: RUN GENERATE_STATS_V2 UNDER REDIRECTION HARNESS")
    print("=" * 80)
    print(f"Target Output Directory: {W_OUT_V2_DIR}")

    paper_stats = REAL_PAPER_DIR / "generated_stats.tex"
    hash_before = compute_file_sha256(paper_stats)
    print(f"Paper/generated_stats.tex hash before: {hash_before}")
    assert hash_before == "a502528e554ba7e1e2e0a7e570b053878a02b4597ba6439670597ddbef388bf4"

    script_path = str(GEN_SCRIPT_V2)
    print(f"Executing: {script_path} via runpy...")
    sys.argv = [script_path]
    runpy.run_path(script_path, run_name="__main__")
    print("Execution completed.")

    print("\nRedirected Writes:")
    for orig_p, dst_p, md in redirected_paths:
        print(f"  [mode={md}] {orig_p} -> {dst_p}")

    hash_after = compute_file_sha256(paper_stats)
    print(f"\nPaper/generated_stats.tex hash after:  {hash_after}")
    assert hash_before == hash_after, "CRITICAL ERROR: Paper/generated_stats.tex was modified!"
    print("-> PASS: Real Paper/ directory was completely untouched.")

    expected_files = [
        W_OUT_V2_DIR / "Paper" / "generated_stats.tex",
        W_OUT_V2_DIR / "Paper" / "tables" / "table_sensitivity_raw_vs_clamped.tex",
        W_OUT_V2_DIR / "Paper" / "tables" / "table_full_fdr_family.tex"
    ]
    for ef in expected_files:
        assert ef.exists(), f"Missing redirected output file: {ef}"
        print(f"Verified generated file: {ef} ({ef.stat().st_size} bytes)")

    print("\nTask U2 redirection execution PASSED perfectly!")


if __name__ == "__main__":
    main()
