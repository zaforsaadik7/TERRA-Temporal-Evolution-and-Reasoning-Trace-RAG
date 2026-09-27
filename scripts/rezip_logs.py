import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT_DIR / "logs"
W_OUT_V2_DIR = ROOT_DIR / "scratch" / "w_out_v2"
CANONICAL_V2_DIR = ROOT_DIR / "scratch" / "canonical_v2"
ZIP_OUT = ROOT_DIR / "logs.zip"

print(f"Creating fresh logs.zip...")

with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    # 1. Add all files in logs/
    for root, dirs, files in os.walk(LOGS_DIR):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(LOGS_DIR)
            zf.write(full_path, arcname=f"logs/{rel_path.as_posix()}")

    # 2. Add scratch/w_out_v2/
    if W_OUT_V2_DIR.exists():
        for root, dirs, files in os.walk(W_OUT_V2_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(ROOT_DIR)
                zf.write(full_path, arcname=rel_path.as_posix())

    # 2b. Add scratch/w_out_v2b/
    W_OUT_V2B_DIR = ROOT_DIR / "scratch" / "w_out_v2b"
    if W_OUT_V2B_DIR.exists():
        for root, dirs, files in os.walk(W_OUT_V2B_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(ROOT_DIR)
                zf.write(full_path, arcname=rel_path.as_posix())

    # 3. Add scratch/canonical_v2/
    if CANONICAL_V2_DIR.exists():
        for root, dirs, files in os.walk(CANONICAL_V2_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(ROOT_DIR)
                zf.write(full_path, arcname=rel_path.as_posix())

    # Also include builder/runner scripts for complete auditability
    v2_scripts = [
        "scripts/generate_stats_v2.py",
        "scripts/run_v2_harness.py",
        "scripts/build_v2_macro_ledger.py",
        "scripts/sweep_claims.py",
        "scripts/log_v2_latency.py",
        "scripts/run_v2b_downstream_audit.py",
        "scripts/run_w2_original_redirect_harness.py",
        "scripts/log_v2_policy_and_route.py",
        "scripts/log_v2_fdr_effects.py",
        "scripts/log_v2_judge_effect.py",
        "scripts/rezip_logs.py"
    ]
    for s in v2_scripts:
        sp = ROOT_DIR / s
        if sp.exists():
            zf.write(sp, arcname=s)

file_count = len(zf.namelist())
zip_size = os.path.getsize(ZIP_OUT)
print(f"Successfully created {ZIP_OUT} with {file_count} entries ({zip_size} bytes / {zip_size / (1024*1024):.2f} MB).")
