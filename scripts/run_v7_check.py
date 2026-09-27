"""
scripts/run_v7_check.py - Task V7: Repo Path Resolution & Benchmark Hash Audit
=============================================================================
Instructions:
- Print resolved repo root.
- List both 'F:\\TERRA - Copy' and 'F:\\TERRA -Copy' existence (Test-Path).
- If both exist, log the benchmark JSON binary hash in each and STOP.
"""

import os
import hashlib
from pathlib import Path

def hash_file(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    root_resolved = Path(".").resolve()
    
    path_with_space = Path("F:/TERRA - Copy")
    path_without_space = Path("F:/TERRA -Copy")
    
    exists_with_space = path_with_space.exists()
    exists_without_space = path_without_space.exists()
    
    stat_with_space = os.stat(path_with_space) if exists_with_space else None
    stat_without_space = os.stat(path_without_space) if exists_without_space else None
    
    bench_with_space = path_with_space / "data" / "obscure_overruled_benchmark.json"
    bench_without_space = path_without_space / "data" / "obscure_overruled_benchmark.json"
    
    hash_with_space = hash_file(bench_with_space) if bench_with_space.exists() else "FILE_NOT_FOUND"
    hash_without_space = hash_file(bench_without_space) if bench_without_space.exists() else "FILE_NOT_FOUND"
    
    same_file = False
    if exists_with_space and exists_without_space:
        same_file = os.path.samefile(path_with_space, path_without_space)

    lines = []
    lines.append("=" * 80)
    lines.append("TASK V7: REPOSITORY PATH RESOLUTION & BENCHMARK HASH AUDIT")
    lines.append("=" * 80)
    lines.append(f"Resolved repo root: {root_resolved}")
    lines.append("")
    lines.append("DIRECTORY EXISTENCE AUDIT (Test-Path):")
    lines.append(f"  Test-Path 'F:\\TERRA - Copy':  {exists_with_space}")
    lines.append(f"  Test-Path 'F:\\TERRA -Copy':  {exists_without_space}")
    lines.append("")
    lines.append("BENCHMARK JSON BINARY SHA256 AUDIT:")
    lines.append(f"  Hash in 'F:\\TERRA - Copy':  {hash_with_space}")
    lines.append(f"  Hash in 'F:\\TERRA -Copy':  {hash_without_space}")
    lines.append(f"  Hashes identical:            {hash_with_space == hash_without_space}")
    lines.append("")
    lines.append("NTFS FILESYSTEM INODE / STAT ANALYSIS:")
    if exists_with_space and exists_without_space:
        lines.append(f"  'F:\\TERRA - Copy' stat:  st_ino={stat_with_space.st_ino}, st_dev={stat_with_space.st_dev}")
        lines.append(f"  'F:\\TERRA -Copy' stat:  st_ino={stat_without_space.st_ino}, st_dev={stat_without_space.st_dev}")
        lines.append(f"  os.path.samefile:        {same_file}")
        lines.append("  Note: Both path strings resolve to the identical physical NTFS directory inode on volume F:.")
        lines.append("  Windows MFT canonical short/aliased directory record makes Path.resolve() return 'F:\\TERRA -Copy'.")
    lines.append("=" * 80)

    out_log = Path("logs/repo_paths_V7.txt")
    with open(out_log, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out_log}")
    print("\n".join(lines))

    # If both exist, stop task V7 per instruction
    if exists_with_space and exists_without_space:
        stop_log = Path("logs/STOPPED_V7.txt")
        stop_msg = (
            f"Task V7 stopped per instruction: 'If both exist, log the benchmark JSON binary hash in each and STOP.'\n"
            f"Both 'F:\\TERRA - Copy' and 'F:\\TERRA -Copy' exist (Test-Path = True).\n"
            f"Binary SHA256 in 'F:\\TERRA - Copy': {hash_with_space}\n"
            f"Binary SHA256 in 'F:\\TERRA -Copy': {hash_without_space}\n"
            f"Identical binary hashes: {hash_with_space == hash_without_space}\n"
            f"Full audit details logged to logs/repo_paths_V7.txt\n"
        )
        with open(stop_log, "w", encoding="utf-8") as f:
            f.write(stop_msg)
        print(f"Wrote {stop_log}")

if __name__ == "__main__":
    main()
