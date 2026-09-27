import os
import sys
import json
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
SRC_DIR = ROOT / "dataset_20k_cap" / "vector_db_20k"
DST_DIR = ROOT / "frozen" / "vector_db_20k_snapshot"
SQLITE_PATH = DST_DIR / "chroma.sqlite3"
OUT_LOG = ROOT / "logs" / "chroma_snapshot_fingerprint.txt"

print("--- U6: CHROMA SNAPSHOT & FINGERPRINT AUDIT ---")

# Step 1: Fresh copy without opening original
print(f"1. Copying {SRC_DIR} to {DST_DIR} ...")
if DST_DIR.exists():
    shutil.rmtree(DST_DIR)
shutil.copytree(SRC_DIR, DST_DIR)
print("Copy completed successfully.")

# Step 2: Binary hash before opening
with open(SQLITE_PATH, "rb") as f:
    sqlite_before_bytes = f.read()
sqlite_hash_before = hashlib.sha256(sqlite_before_bytes).hexdigest()
print(f"2. chroma.sqlite3 SHA-256 BEFORE opening: {sqlite_hash_before}")

# Step 3: Run Process 1
print("3. Running Process 1 fingerprint worker ...")
cmd = [sys.executable, str(ROOT / "scripts" / "chroma_fingerprint_worker.py")]
res1 = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
run1 = json.loads(res1.stdout.strip().splitlines()[-1])
print("Process 1 finished:", run1)

# Step 4: Run Process 2
print("4. Running Process 2 fingerprint worker ...")
res2 = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
run2 = json.loads(res2.stdout.strip().splitlines()[-1])
print("Process 2 finished:", run2)

# Step 5: Assert equality across two separate processes
assert run1 == run2, f"Fingerprint mismatch across processes!\nRun 1: {run1}\nRun 2: {run2}"
print("5. Assert equality: MATCHED! Run 1 and Run 2 are identical.")

# Step 6: Binary hash after opening
with open(SQLITE_PATH, "rb") as f:
    sqlite_after_bytes = f.read()
sqlite_hash_after = hashlib.sha256(sqlite_after_bytes).hexdigest()
print(f"6. chroma.sqlite3 SHA-256 AFTER opening:  {sqlite_hash_after}")

# Step 7: Write to logs/chroma_snapshot_fingerprint.txt
log_lines = [
    "=" * 100,
    "U6 CHROMA SNAPSHOT DETERMINISTIC FINGERPRINT AUDIT",
    "=" * 100,
    f"Snapshot Path:            {DST_DIR.resolve()}",
    f"chroma.sqlite3 BEFORE:    {sqlite_hash_before}",
    f"chroma.sqlite3 AFTER:     {sqlite_hash_after}",
    f"Sqlite Modified On Open:  {sqlite_hash_before != sqlite_hash_after}",
    "",
    "PROCESS 1 FINGERPRINT:",
    f"  Count:                  {run1['count']}",
    f"  Sorted IDs SHA-256:     {run1['sha256_sorted_ids']}",
    f"  Concat Docs SHA-256:    {run1['sha256_concat_docs']}",
    f"  Float32 Embeddings SHA: {run1['sha256_embeddings_float32']}",
    "",
    "PROCESS 2 FINGERPRINT:",
    f"  Count:                  {run2['count']}",
    f"  Sorted IDs SHA-256:     {run2['sha256_sorted_ids']}",
    f"  Concat Docs SHA-256:    {run2['sha256_concat_docs']}",
    f"  Float32 Embeddings SHA: {run2['sha256_embeddings_float32']}",
    "",
    f"ACROSS-PROCESS DETERMINISM ASSERTION (Run1 == Run2): PASSED",
    "=" * 100
]

OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")

print(f"Wrote audit log to {OUT_LOG}")
