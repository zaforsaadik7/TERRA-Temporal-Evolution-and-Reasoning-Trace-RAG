import os
import zipfile
import hashlib
import json
from datetime import datetime, timezone

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

FILES_TO_PACKAGE = [
    ("Paper/main.pdf", "main.pdf"),
    ("Paper/main.tex", "main.tex"),
    ("Paper/figure_1_system_architecture.tex", "figure_1_system_architecture.tex"),
    ("Paper/generated_stats.tex", "generated_stats.tex"),
    ("Paper/generated_corpus_stats_20k.tex", "generated_corpus_stats_20k.tex"),
    ("Paper/tables/table_retrieval_eval.tex", "tables/table_retrieval_eval.tex"),
    ("Paper/tables/table_citation_eval.tex", "tables/table_citation_eval.tex"),
    ("Paper/tables/table_computational_budget.tex", "tables/table_computational_budget.tex"),
    ("Paper/scripts/check_consistency.py", "scripts/check_consistency.py"),
    ("scripts/verify_issue28_preflight.py", "scripts/verify_issue28_preflight.py"),
    ("data/issue28_preflight.json", "data/issue28_preflight.json"),
    ("logs/issue28_preflight.txt", "logs/issue28_preflight.txt"),
    ("terra_350_benchmark.json", "terra_350_benchmark.json"),
    ("dataset_20k_cap/terra_eeg_index_20k.json", "dataset_20k_cap/terra_eeg_index_20k.json"),
    ("docs/ISSUE28_CAUSAL_LANGUAGE_REMEDIAL_PLAN.md", "docs/ISSUE28_CAUSAL_LANGUAGE_REMEDIAL_PLAN.md"),
    ("logs/issue28_closeout.txt", "logs/issue28_closeout.txt")
]

BUNDLE_PATH = "TERRA_Reproducibility_Bundle.zip"
MANIFEST_PATH = "logs/issue28_reproducibility_manifest.json"

print(f"[REPRO BUNDLE] Building {BUNDLE_PATH} with {len(FILES_TO_PACKAGE)} files...")

file_manifest = []

with zipfile.ZipFile(BUNDLE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for src_path, arc_name in FILES_TO_PACKAGE:
        assert os.path.exists(src_path), f"Missing source file: {src_path}"
        zf.write(src_path, arc_name)
        f_size = os.path.getsize(src_path)
        f_hash = sha256_file(src_path)
        file_manifest.append({
            "archive_path": arc_name,
            "source_path": src_path,
            "size_bytes": f_size,
            "sha256": f_hash
        })
        print(f"  + {arc_name:45s} ({f_size:10,d} bytes, sha256:{f_hash[:8]})")

zip_size = os.path.getsize(BUNDLE_PATH)
zip_hash = sha256_file(BUNDLE_PATH)
closeout_size = os.path.getsize("logs/issue28_closeout.txt")
closeout_hash = sha256_file("logs/issue28_closeout.txt")

manifest_data = {
    "bundle_name": BUNDLE_PATH,
    "issue": "Issue #28: Inappropriate 'Causal' Language for Citation Links",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "zip_size_bytes": zip_size,
    "zip_sha256": zip_hash,
    "closeout_log_sha256": closeout_hash,
    "closeout_log_size_bytes": closeout_size,
    "file_count": len(file_manifest),
    "files": file_manifest
}

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, indent=2)

print(f"\n[REPRO BUNDLE] Successfully generated {BUNDLE_PATH}")
print(f"  Archive Size: {zip_size:,} bytes")
print(f"  SHA256:       {zip_hash}")
print(f"  Manifest:     {MANIFEST_PATH}")
