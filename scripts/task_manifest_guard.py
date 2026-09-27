#!/usr/bin/env python3
"""
scripts/task_manifest_guard.py
Scoped Allowlist & Preflight/Postflight Invariance Guard for TERRA Issues.

Enforces User Annotation 1 Governance:
  1. Defines a scoped file allowlist for an issue / task.
  2. Generates immutable preflight manifest (logs/<issue>_preflight_manifest.json).
  3. Evaluates postflight changes:
     - Reports expected changes (within allowlist).
     - Reports unexpected changes (outside allowlist; fails if any found).
     - Reports 100% bit-invariance on all protected core files.
  4. Generates logs/<issue>_manifest_audit.json and logs/<issue>_manifest_audit.txt.

Usage:
  # 1. Before task:
  python scripts/task_manifest_guard.py preflight --issue issue20 --allowlist "Paper/main.tex" "Paper/tables/*" "logs/issue20_*" "scratch/issue20_*"

  # 2. After task:
  python scripts/task_manifest_guard.py postflight --issue issue20
"""

import os
import sys
import fnmatch
import time
import json
import hashlib
import argparse
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(".")
DEFAULT_BASELINE = os.path.join(ROOT_DIR, "logs", "baseline_manifest_post_issue19.json")
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".gemini", "node_modules"}

# Core protected files that must remain strictly invariant unless explicitly allowlisted
PROTECTED_CORE_FILES = [
    "terra_350_benchmark.json",
    "dataset_20k_cap/terra_eeg_index_20k.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json",
    "ask_terra.py",
    "data/issue21_preflight.json",
    "logs/issue21_preflight.txt",
    "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md",
]

def hash_file(rel_path):
    """Compute SHA256, size, and mtime for a file."""
    full_path = os.path.join(ROOT_DIR, rel_path.replace("/", os.sep))
    if not os.path.isfile(full_path):
        return None
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
        }
    except Exception as e:
        return {
            "path": rel_path,
            "size_bytes": 0,
            "mtime_utc": None,
            "sha256": None,
            "error": str(e)
        }

def scan_all_repo_files():
    """List all relative file paths in workspace (excluding git, venvs)."""
    paths = []
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            full_p = os.path.join(dirpath, f)
            rel_p = os.path.relpath(full_p, ROOT_DIR).replace("\\", "/")
            paths.append(rel_p)
    paths.sort()
    return paths

def matches_any_pattern(path, patterns):
    """Check if path matches any of the glob patterns."""
    for pat in patterns:
        norm_pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(path, norm_pat):
            return True
        if norm_pat.endswith("/") and path.startswith(norm_pat):
            return True
    return False

def cmd_preflight(args):
    issue_id = args.issue
    allowlist = args.allowlist or []
    out_json = os.path.join(ROOT_DIR, "logs", f"{issue_id}_preflight_manifest.json")
    out_txt = os.path.join(ROOT_DIR, "logs", f"{issue_id}_preflight_manifest.txt")

    print("=" * 80)
    print(f"PREFLIGHT MANIFEST GENERATION FOR {issue_id.upper()}")
    print("=" * 80)
    print(f"Issue Identifier: {issue_id}")
    print(f"Allowlist Patterns ({len(allowlist)}):")
    for pat in allowlist:
        print(f"  + {pat}")

    # Load baseline manifest if present
    baseline_hashes = {}
    if os.path.exists(args.baseline):
        print(f"Loading baseline manifest: {args.baseline} ...", end=" ", flush=True)
        with open(args.baseline, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        baseline_hashes = {p: v["sha256"] for p, v in b_data.get("files", {}).items()}
        print(f"loaded {len(baseline_hashes)} baseline file records.")
    else:
        print(f"Notice: Baseline manifest {args.baseline} not found; proceeding with live scan.")

    # Find currently existing files matching allowlist patterns
    all_files = scan_all_repo_files()
    matched_allowlist_files = [p for p in all_files if matches_any_pattern(p, allowlist)]

    print(f"\nScanning current states of allowlisted files ({len(matched_allowlist_files)} existing)...")
    allowlist_snapshots = {}
    for p in matched_allowlist_files:
        rec = hash_file(p)
        if rec:
            allowlist_snapshots[p] = rec

    # Snapshot protected core files
    print(f"Snapshotting protected core files ({len(PROTECTED_CORE_FILES)} core files)...")
    protected_snapshots = {}
    for p in PROTECTED_CORE_FILES:
        rec = hash_file(p)
        if rec:
            protected_snapshots[p] = rec
        else:
            protected_snapshots[p] = {"path": p, "missing": True}

    # Snapshot baseline manifest files themselves in metadata
    base_json_rel = os.path.relpath(args.baseline, ROOT_DIR).replace("\\", "/")
    base_txt_rel = os.path.splitext(base_json_rel)[0] + ".txt"
    base_snapshots = {}
    for bp in [base_json_rel, base_txt_rel]:
        b_rec = hash_file(bp)
        if b_rec and b_rec.get("sha256"):
            base_snapshots[bp] = b_rec

    payload = {
        "metadata": {
            "issue_id": issue_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_manifest_source": base_json_rel,
            "baseline_manifest_snapshots": base_snapshots,
            "allowlist_patterns": allowlist,
            "allowlist_existing_files_count": len(allowlist_snapshots),
            "protected_core_files_count": len(protected_snapshots)
        },
        "allowlist_existing_files": allowlist_snapshots,
        "protected_core_files": protected_snapshots
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"TASK PREFLIGHT MANIFEST: {issue_id.upper()}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Timestamp:       {payload['metadata']['created_at_utc']}\n")
        f.write(f"Issue:           {issue_id}\n")
        f.write(f"Allowlist Rules: {len(allowlist)} patterns\n")
        for pat in allowlist:
            f.write(f"  - {pat}\n")
        f.write(f"\nExisting Matching Files ({len(allowlist_snapshots)}):\n")
        for p, rec in sorted(allowlist_snapshots.items()):
            f.write(f"  {p:55s} | {rec['size_bytes']:8d} B | {rec['sha256']}\n")
        f.write(f"\nProtected Core Files Invariance Baseline ({len(protected_snapshots)}):\n")
        for p, rec in sorted(protected_snapshots.items()):
            sha = rec.get("sha256") or "MISSING"
            f.write(f"  {p:55s} | {sha}\n")
        f.write("=" * 80 + "\n")

    print(f"\nPreflight Manifest successfully created:")
    print(f"  JSON: {out_json}")
    print(f"  Text: {out_txt}")
    return 0

def cmd_postflight(args):
    issue_id = args.issue
    preflight_json = args.preflight or os.path.join(ROOT_DIR, "logs", f"{issue_id}_preflight_manifest.json")
    out_audit_json = os.path.join(ROOT_DIR, "logs", f"{issue_id}_manifest_audit.json")
    out_audit_txt = os.path.join(ROOT_DIR, "logs", f"{issue_id}_manifest_audit.txt")

    print("=" * 80)
    print(f"POSTFLIGHT MANIFEST AUDIT FOR {issue_id.upper()}")
    print("=" * 80)

    if not os.path.exists(preflight_json):
        print(f"ERROR: Preflight manifest not found: {preflight_json}")
        print("Run 'preflight' command before executing the task.")
        return 1

    with open(preflight_json, "r", encoding="utf-8") as f:
        pre_data = json.load(f)

    meta = pre_data["metadata"]
    allowlist = meta["allowlist_patterns"]
    pre_allow_files = pre_data["allowlist_existing_files"]
    pre_protected = pre_data["protected_core_files"]

    # Load baseline manifest if present
    baseline_files = {}
    if os.path.exists(args.baseline):
        with open(args.baseline, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        baseline_files = b_data.get("files", {})

    print(f"Comparing current repository state against preflight snapshot ({meta['created_at_utc']})...")

    # Scan current repo files
    current_files = scan_all_repo_files()
    current_hashes = {}
    for p in current_files:
        full_p = os.path.join(ROOT_DIR, p.replace("/", os.sep))
        try:
            stat = os.stat(full_p)
            cur_sz = stat.st_size
            cur_mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        except Exception:
            continue

        b_entry = baseline_files.get(p)
        is_allowlisted = matches_any_pattern(p, allowlist)
        is_protected = p in pre_protected

        # Fast path: If unchanged from baseline and not in allowlist/protected, reuse baseline hash
        if b_entry and cur_sz == b_entry.get("size_bytes") and cur_mtime == b_entry.get("mtime_utc") and not is_allowlisted and not is_protected:
            current_hashes[p] = {
                "path": p,
                "size_bytes": cur_sz,
                "mtime_utc": cur_mtime,
                "sha256": b_entry["sha256"]
            }
        else:
            rec = hash_file(p)
            if rec and rec["sha256"]:
                current_hashes[p] = rec

    # 1. Evaluate Allowlisted Files (Expected Changes)
    expected_changes = []
    expected_created = []
    expected_unchanged = []

    for p, cur in current_hashes.items():
        if matches_any_pattern(p, allowlist):
            if p in pre_allow_files:
                pre_sha = pre_allow_files[p]["sha256"]
                if cur["sha256"] != pre_sha:
                    expected_changes.append({
                        "path": p,
                        "pre_sha256": pre_sha,
                        "post_sha256": cur["sha256"],
                        "size_delta": cur["size_bytes"] - pre_allow_files[p]["size_bytes"]
                    })
                else:
                    expected_unchanged.append(p)
            else:
                # Newly created file matching allowlist
                expected_created.append({
                    "path": p,
                    "sha256": cur["sha256"],
                    "size_bytes": cur["size_bytes"]
                })

    # Check for deleted allowlist files
    expected_deleted = []
    for p in pre_allow_files:
        if p not in current_hashes:
            expected_deleted.append(p)

    out_audit_json_rel = os.path.relpath(out_audit_json, ROOT_DIR).replace("\\", "/")
    out_audit_txt_rel = os.path.relpath(out_audit_txt, ROOT_DIR).replace("\\", "/")

    # 2. Check for Unexpected Changes (Files modified or created OUTSIDE allowlist)
    unexpected_changes = []
    unexpected_created = []
    unexpected_deleted = []
    protected_violations = []

    # Verify baseline manifest invariance
    base_snapshots = meta.get("baseline_manifest_snapshots", {})
    for bp, b_rec in base_snapshots.items():
        cur_b = hash_file(bp)
        if not cur_b or cur_b.get("sha256") != b_rec.get("sha256"):
            b_now = cur_b.get("sha256") if cur_b else "MISSING"
            protected_violations.append(f"BASELINE_MANIFEST_MODIFIED: {bp} (was {b_rec.get('sha256')}, now {b_now})")

    # Check against baseline or preflight for all non-allowlisted files
    comparison_pool = baseline_files if baseline_files else {}
    for p, cur in current_hashes.items():
        if matches_any_pattern(p, allowlist):
            continue  # Covered by allowlist
        if p in base_snapshots or p in (out_audit_json_rel, out_audit_txt_rel):
            continue  # Handled separately or audit outputs
        if p in comparison_pool:
            base_sha = comparison_pool[p]["sha256"]
            if cur["sha256"] != base_sha:
                unexpected_changes.append({
                    "path": p,
                    "baseline_sha256": base_sha,
                    "current_sha256": cur["sha256"],
                    "size_delta": cur["size_bytes"] - comparison_pool[p]["size_bytes"]
                })
        else:
            # File exists now but was NOT in baseline and NOT in allowlist
            unexpected_created.append({
                "path": p,
                "sha256": cur["sha256"],
                "size_bytes": cur["size_bytes"]
            })

    if comparison_pool:
        for p in comparison_pool:
            if matches_any_pattern(p, allowlist):
                continue
            if p in base_snapshots or p in (out_audit_json_rel, out_audit_txt_rel):
                continue
            if p not in current_hashes:
                unexpected_deleted.append(p)

    # 3. Verify Protected Core Files
    for p, p_rec in pre_protected.items():
        if matches_any_pattern(p, allowlist):
            continue  # Explicitly allowlisted for this task
        expected_sha = p_rec.get("sha256")
        if p not in current_hashes:
            protected_violations.append(f"PROTECTED_FILE_DELETED: {p}")
        elif current_hashes[p]["sha256"] != expected_sha:
            protected_violations.append(f"PROTECTED_FILE_MODIFIED: {p} (was {expected_sha}, now {current_hashes[p]['sha256']})")

    audit_passed = (len(unexpected_changes) == 0 and
                    len(unexpected_created) == 0 and
                    len(unexpected_deleted) == 0 and
                    len(protected_violations) == 0)

    # Build audit payload
    audit_payload = {
        "audit_metadata": {
            "issue_id": issue_id,
            "audited_at_utc": datetime.now(timezone.utc).isoformat(),
            "preflight_timestamp": meta["created_at_utc"],
            "audit_verdict": "PASS" if audit_passed else "FAIL",
            "allowlist_patterns": allowlist,
        },
        "summary": {
            "expected_modified_count": len(expected_changes),
            "expected_created_count": len(expected_created),
            "expected_deleted_count": len(expected_deleted),
            "expected_unchanged_count": len(expected_unchanged),
            "unexpected_modified_count": len(unexpected_changes),
            "unexpected_created_count": len(unexpected_created),
            "unexpected_deleted_count": len(unexpected_deleted),
            "protected_violations_count": len(protected_violations)
        },
        "expected_modifications": expected_changes,
        "expected_creations": expected_created,
        "expected_deletions": expected_deleted,
        "unexpected_modifications": unexpected_changes,
        "unexpected_creations": unexpected_created,
        "unexpected_deletions": unexpected_deleted,
        "protected_violations": protected_violations
    }

    with open(out_audit_json, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2)

    with open(out_audit_txt, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"TASK MANIFEST AUDIT REPORT: {issue_id.upper()}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Timestamp:       {audit_payload['audit_metadata']['audited_at_utc']}\n")
        f.write(f"Preflight Time:  {meta['created_at_utc']}\n")
        f.write(f"Audit Verdict:   {audit_payload['audit_metadata']['audit_verdict']}\n\n")

        f.write(f"Allowlist Rules ({len(allowlist)} patterns):\n")
        for pat in allowlist:
            f.write(f"  - {pat}\n")

        f.write(f"\n1. EXPECTED CHANGES (Within Allowlist: {len(expected_changes)} mod, {len(expected_created)} new, {len(expected_deleted)} del):\n")
        for rec in expected_changes:
            f.write(f"  [MODIFIED] {rec['path']} (delta: {rec['size_delta']:+d} bytes)\n")
        for rec in expected_created:
            f.write(f"  [CREATED]  {rec['path']} ({rec['size_bytes']} bytes)\n")
        for p in expected_deleted:
            f.write(f"  [DELETED]  {p}\n")
        if not expected_changes and not expected_created and not expected_deleted:
            f.write("  (No changes detected in allowlisted paths)\n")

        f.write(f"\n2. UNEXPECTED CHANGES (Outside Allowlist: {len(unexpected_changes)} mod, {len(unexpected_created)} new, {len(unexpected_deleted)} del):\n")
        if unexpected_changes or unexpected_created or unexpected_deleted:
            for rec in unexpected_changes:
                f.write(f"  [FORBIDDEN MOD] {rec['path']} (was {rec['baseline_sha256']}, now {rec['current_sha256']})\n")
            for rec in unexpected_created:
                f.write(f"  [FORBIDDEN NEW] {rec['path']} ({rec['size_bytes']} bytes)\n")
            for p in unexpected_deleted:
                f.write(f"  [FORBIDDEN DEL] {p}\n")
        else:
            f.write("  [NONE] Zero unexpected changes detected outside allowlist.\n")

        f.write(f"\n3. PROTECTED CORE FILES INVARIANCE ({len(pre_protected)} files verified):\n")
        if protected_violations:
            for v in protected_violations:
                f.write(f"  [VIOLATION] {v}\n")
        else:
            f.write("  [100% INVARIANT] All protected core files remain perfectly bit-invariant.\n")

        f.write("=" * 80 + "\n")
        f.write(f"FINAL AUDIT VERDICT: {audit_payload['audit_metadata']['audit_verdict']}\n")
        f.write("=" * 80 + "\n")

    print("\nAudit Summary:")
    print(f"  Expected Modifications:  {len(expected_changes)}")
    print(f"  Expected Creations:      {len(expected_created)}")
    print(f"  Expected Deletions:      {len(expected_deleted)}")
    print(f"  Unexpected Modifications:{len(unexpected_changes)}")
    print(f"  Unexpected Creations:    {len(unexpected_created)}")
    print(f"  Unexpected Deletions:    {len(unexpected_deleted)}")
    print(f"  Protected Violations:    {len(protected_violations)}")
    print(f"\nFINAL VERDICT: {audit_payload['audit_metadata']['audit_verdict']}")
    print(f"Saved JSON: {out_audit_json}")
    print(f"Saved Text: {out_audit_txt}")

    return 0 if audit_passed else 1

def main():
    parser = argparse.ArgumentParser(description="Scoped Allowlist & Preflight/Postflight Invariance Guard for TERRA Issues.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Preflight parser
    p_pre = subparsers.add_parser("preflight", help="Generate preflight manifest for an issue")
    p_pre.add_argument("--issue", required=True, help="Issue identifier, e.g. issue20")
    p_pre.add_argument("--allowlist", nargs="+", required=True, help="Scoped file path or glob patterns")
    p_pre.add_argument("--baseline", default=DEFAULT_BASELINE, help="Path to baseline manifest JSON")

    # Postflight parser
    p_post = subparsers.add_parser("postflight", help="Audit postflight changes for an issue against allowlist")
    p_post.add_argument("--issue", required=True, help="Issue identifier, e.g. issue20")
    p_post.add_argument("--preflight", default=None, help="Path to preflight manifest JSON")
    p_post.add_argument("--baseline", default=DEFAULT_BASELINE, help="Path to baseline manifest JSON")

    args = parser.parse_args()
    if args.command == "preflight":
        sys.exit(cmd_preflight(args))
    elif args.command == "postflight":
        sys.exit(cmd_postflight(args))

if __name__ == "__main__":
    main()
