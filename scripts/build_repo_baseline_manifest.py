#!/usr/bin/env python3
"""
scripts/build_repo_baseline_manifest.py
Builds a complete, cryptographically verified repository baseline manifest.

Captures:
  - Every tracked and untracked file in the repository (excluding .git, .venv, venv, __pycache__, .gemini)
  - File size (bytes)
  - File modification timestamp (UTC ISO format)
  - File SHA256 checksum (buffered 1MB reads)
  - Current Git status (TRACKED_CLEAN, TRACKED_MODIFIED, TRACKED_STAGED, UNTRACKED, etc.)
  - Current issue / round identifier (post_issue19_baseline)
  - Git HEAD commit hash and current branch

Outputs:
  - logs/baseline_manifest_post_issue19.json
  - logs/baseline_manifest_post_issue19.txt
"""

import os
import sys
import time
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.abspath(".")
OUTPUT_JSON = os.path.join(ROOT_DIR, "logs", "baseline_manifest_post_issue19.json")
OUTPUT_TXT = os.path.join(ROOT_DIR, "logs", "baseline_manifest_post_issue19.txt")

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".gemini", "node_modules"}

def get_git_info():
    """Retrieve Git commit, branch, and status mappings."""
    info = {
        "head_commit": "UNKNOWN",
        "head_branch": "UNKNOWN",
        "tracked_files": {},
        "status_map": {}
    }
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, text=True).strip()
        info["head_commit"] = head
    except Exception as e:
        info["head_commit"] = f"ERROR: {e}"

    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT_DIR, text=True).strip()
        info["head_branch"] = branch or "DETACHED"
    except Exception as e:
        info["head_branch"] = f"ERROR: {e}"

    # Get tracked files
    try:
        ls_out = subprocess.check_output(["git", "ls-files"], cwd=ROOT_DIR, text=True)
        for line in ls_out.strip().splitlines():
            if line:
                norm_p = line.replace("\\", "/")
                info["tracked_files"][norm_p] = True
    except Exception as e:
        print(f"Warning: git ls-files failed: {e}")

    # Get git status porcelain (uall to list all untracked files individually)
    try:
        st_out = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT_DIR, text=True)
        for line in st_out.strip().splitlines():
            if not line:
                continue
            code = line[:2]
            path_part = line[3:].strip()
            # Handle quoted paths in git output
            if path_part.startswith('"') and path_part.endswith('"'):
                path_part = path_part[1:-1]
            norm_p = path_part.replace("\\", "/")
            info["status_map"][norm_p] = code
    except Exception as e:
        print(f"Warning: git status failed: {e}")

    return info

def hash_file(rel_path):
    """Compute SHA256, size, and mtime for a file."""
    full_path = os.path.join(ROOT_DIR, rel_path.replace("/", os.sep))
    h = hashlib.sha256()
    try:
        stat = os.stat(full_path)
        sz = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        with open(full_path, "rb") as f:
            while chunk := f.read(1048576):
                h.update(chunk)
        return {
            "path": rel_path,
            "size_bytes": sz,
            "mtime_utc": mtime,
            "sha256": h.hexdigest(),
            "error": None
        }
    except Exception as e:
        return {
            "path": rel_path,
            "size_bytes": 0,
            "mtime_utc": None,
            "sha256": None,
            "error": str(e)
        }

def classify_git_status(rel_path, git_info):
    """Determine clean status string for file."""
    code = git_info["status_map"].get(rel_path)
    if code:
        if code == "??":
            return "UNTRACKED"
        elif code.startswith("M") or code.endswith("M"):
            return "TRACKED_MODIFIED"
        elif code.startswith("A"):
            return "TRACKED_STAGED_ADD"
        elif code.startswith("D") or code.endswith("D"):
            return "TRACKED_DELETED"
        elif code.startswith("R"):
            return "TRACKED_RENAMED"
        else:
            return f"GIT_STATUS_{code.strip()}"
    elif rel_path in git_info["tracked_files"]:
        return "TRACKED_CLEAN"
    else:
        return "UNTRACKED"

def main():
    print("=" * 80, flush=True)
    print("BUILDING COMPLETE REPOSITORY BASELINE MANIFEST (POST-ISSUE #19)", flush=True)
    print("=" * 80, flush=True)

    start_time = time.time()
    created_at = datetime.now(timezone.utc).isoformat()

    print("Querying Git status and tracking metadata...", flush=True)
    git_info = get_git_info()
    print(f"Git HEAD: {git_info['head_commit']} (branch: {git_info['head_branch']})", flush=True)
    print(f"Tracked files registered by Git: {len(git_info['tracked_files'])}", flush=True)
    print(f"Git status entries flagged: {len(git_info['status_map'])}", flush=True)

    print("\nScanning filesystem for all repository files...", flush=True)
    all_rel_paths = []
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            full_p = os.path.join(dirpath, f)
            rel_p = os.path.relpath(full_p, ROOT_DIR).replace("\\", "/")
            all_rel_paths.append(rel_p)

    rel_out_json = os.path.relpath(OUTPUT_JSON, ROOT_DIR).replace("\\", "/")
    rel_out_txt = os.path.relpath(OUTPUT_TXT, ROOT_DIR).replace("\\", "/")
    all_rel_paths = [p for p in all_rel_paths if p not in (rel_out_json, rel_out_txt)]
    all_rel_paths.sort()
    total_files = len(all_rel_paths)
    print(f"Found {total_files} repository files to process (excluding self-referential manifest outputs).", flush=True)

    print("\nComputing SHA256 hashes and file metadata across worker pool...", flush=True)
    file_records = []
    completed = 0
    total_bytes = 0
    status_counts = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_path = {executor.submit(hash_file, p): p for p in all_rel_paths}
        for future in as_completed(future_to_path):
            res = future.result()
            rel_p = res["path"]
            git_st = classify_git_status(rel_p, git_info)
            res["git_status"] = git_st
            status_counts[git_st] = status_counts.get(git_st, 0) + 1
            total_bytes += res["size_bytes"]
            file_records.append(res)
            completed += 1
            if completed % 5000 == 0 or completed == total_files:
                pct = (completed / total_files) * 100.0
                elapsed = time.time() - start_time
                print(f"  Processed {completed}/{total_files} files ({pct:.1f}%) in {elapsed:.1f}s", flush=True)

    # Sort records deterministically by path
    file_records.sort(key=lambda x: x["path"])

    elapsed_total = time.time() - start_time
    print(f"\nAll {total_files} files hashed and cataloged in {elapsed_total:.2f} seconds.", flush=True)
    print("Status Breakdown:")
    for st, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {st:25s}: {count:5d} files", flush=True)

    # Build manifest payload
    manifest = {
        "manifest_metadata": {
            "manifest_version": "1.0.0",
            "issue_round_identifier": "post_issue19_baseline",
            "created_at_utc": created_at,
            "git_head_commit": git_info["head_commit"],
            "git_head_branch": git_info["head_branch"],
            "total_files_count": total_files,
            "total_size_bytes": total_bytes,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "generation_elapsed_seconds": round(elapsed_total, 2),
            "status_summary": status_counts
        },
        "files": {rec["path"]: {
            "size_bytes": rec["size_bytes"],
            "mtime_utc": rec["mtime_utc"],
            "sha256": rec["sha256"],
            "git_status": rec["git_status"],
            "error": rec["error"]
        } for rec in file_records}
    }

    # Save JSON manifest
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nSaved JSON Manifest: {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON) / (1024*1024):.2f} MB)", flush=True)

    # Save human-readable summary text file
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("TERRA REPOSITORY BASELINE MANIFEST (POST-ISSUE #19)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Created At:       {created_at}\n")
        f.write(f"Issue / Round:    post_issue19_baseline\n")
        f.write(f"Git HEAD Commit:  {git_info['head_commit']}\n")
        f.write(f"Git Branch:       {git_info['head_branch']}\n")
        f.write(f"Total Files:      {total_files:,}\n")
        f.write(f"Total Size:       {total_bytes:,} bytes ({total_bytes / (1024*1024):.2f} MB)\n")
        f.write(f"Elapsed Time:     {elapsed_total:.2f} seconds\n\n")
        f.write("Git Status Breakdown:\n")
        for st, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {st:25s}: {count:5d} files\n")
        f.write("\nKey Core File Hashes at Baseline:\n")
        core_sample_paths = [
            "Paper/main.tex",
            "Paper/main.pdf",
            "Paper/generated_stats.tex",
            "Paper/tables/table_temporal_update_stability.tex",
            "terra_350_benchmark.json",
            "dataset_20k_cap/terra_eeg_index_20k.json",
            "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md",
            "logs/issue19_closeout.txt",
            "TERRA_Overleaf_Bundle.zip"
        ]
        for p in core_sample_paths:
            entry = manifest["files"].get(p)
            if entry:
                f.write(f"  {p:55s} | {entry['size_bytes']:8d} bytes | {entry['sha256']}\n")
            else:
                f.write(f"  {p:55s} | NOT FOUND\n")
        f.write("=" * 80 + "\n")
    print(f"Saved Text Summary:  {OUTPUT_TXT}", flush=True)

if __name__ == "__main__":
    main()
