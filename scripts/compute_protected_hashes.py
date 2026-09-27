import os
import sys
import hashlib
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
OUT_FILE = ROOT / "logs" / sys.argv[1]

files_to_hash = [
    ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json",
    ROOT / "dataset_20k_cap" / "vector_db_20k" / "chroma.sqlite3",
    ROOT / "terra_350_benchmark.json",
    ROOT / "terra_baselines_eval_raw.json"
]

raw_cases_dir = ROOT / "dataset_20k_cap" / "raw_cases"
raw_files = sorted(raw_cases_dir.glob("*.json"))

print(f"Hashing 4 main substrate files + {len(raw_files)} raw case files to {OUT_FILE}...")

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

with open(OUT_FILE, "w", encoding="utf-8") as out:
    for f in files_to_hash:
        rel = f.relative_to(ROOT).as_posix()
        digest = hash_file(f)
        out.write(f"{digest}  {rel}\n")
    
    for f in raw_files:
        rel = f.relative_to(ROOT).as_posix()
        digest = hash_file(f)
        out.write(f"{digest}  {rel}\n")

print(f"Wrote {4 + len(raw_files)} hashes to {OUT_FILE}.")
