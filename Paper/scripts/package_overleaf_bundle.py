import os
import zipfile
import hashlib

paper_dir = os.path.abspath("Paper")
output_zip = os.path.join(paper_dir, "overleaf_bundle.zip")

files_to_package = [
    "main.tex",
    "ref.bib",
    "generated_stats.tex",
    "generated_obscure_stats.tex",
    "generated_corpus_stats_20k.tex",
    "figure_1_system_architecture.tex",
    "figure_2_hub_centrality.tex",
    "figure_3_safety_rejection.tex",
    os.path.join("tables", "table_sensitivity_raw_vs_clamped.tex"),
    os.path.join("tables", "table_refusal_breakdown.tex"),
    os.path.join("tables", "table_full_fdr_family.tex"),
    os.path.join("tables", "table_system_comparison.tex"),
    os.path.join("tables", "table_temporal_leakage_probe.tex"),
    os.path.join("tables", "table_casefacts_eval.tex"),
    os.path.join("tables", "table_clerc_eval.tex"),
    os.path.join("tables", "table_retrieval_eval.tex"),
    os.path.join("tables", "table_computational_budget.tex"),
    os.path.join("tables", "table_router_eval.tex"),
    os.path.join("tables", "table_citation_eval.tex"),
    os.path.join("tables", "table_obscure_overruled_eval.tex"),
    os.path.join("tables", "table_temporal_update_stability.tex"),
    os.path.join("tables", "table_baseline_specifications.tex"),
]

print(f"[OVERLEAF BUNDLE] Creating {output_zip}...")
with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for relpath in files_to_package:
        fullpath = os.path.join(paper_dir, relpath)
        if not os.path.exists(fullpath):
            print(f"  [ERROR] Missing required file: {fullpath}")
            continue
        arcname = relpath.replace("\\", "/")
        zf.write(fullpath, arcname=arcname)
        file_size = os.path.getsize(fullpath)
        with open(fullpath, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:8]
        print(f"  + {arcname:<45} ({file_size:>6} bytes, sha256:{file_hash})")

zip_size = os.path.getsize(output_zip)
with open(output_zip, "rb") as f:
    zip_sha = hashlib.sha256(f.read()).hexdigest()
print(f"[OVERLEAF BUNDLE] Successfully generated {output_zip}")
print(f"  Total archive size: {zip_size:,} bytes")
print(f"  SHA256: {zip_sha}")

import shutil
root_zip = os.path.abspath(os.path.join(paper_dir, "..", "TERRA_Overleaf_Bundle.zip"))
shutil.copy2(output_zip, root_zip)
print(f"[OVERLEAF BUNDLE] Synchronized to root: {root_zip}")
