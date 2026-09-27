import os
import sys
import shutil
import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
SRC_DIR = ROOT / "dataset_20k_cap" / "vector_db_20k"
DST_DIR = ROOT / "frozen" / "vector_db_20k_snapshot"

print("1. Copying vector_db_20k to frozen/vector_db_20k_snapshot/ ...")
if DST_DIR.exists():
    shutil.rmtree(DST_DIR)
shutil.copytree(SRC_DIR, DST_DIR)
print(f"Copied successfully to {DST_DIR}")

sqlite_file = DST_DIR / "chroma.sqlite3"
with open(sqlite_file, "rb") as f:
    sqlite_bytes = f.read()
sha_before = hashlib.sha256(sqlite_bytes).hexdigest()
print(f"Snapshot chroma.sqlite3 SHA-256 BEFORE opening: {sha_before}")
