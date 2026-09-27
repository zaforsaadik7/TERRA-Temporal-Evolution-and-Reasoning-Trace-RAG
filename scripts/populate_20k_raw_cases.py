import os
import sys
import json
import time
import requests
import concurrent.futures
from pathlib import Path

print("=== POPULATING 20,000 RAW CASE JSON FILES ===\n")

manifest_path = Path(r"dataset_20k_cap/manifests/selection_manifest_20k.json")
raw_dir_20k = Path(r"dataset_20k_cap/raw_cases")
raw_dir_10k = Path(r"dataset_10k_cap/raw_cases")

raw_dir_20k.mkdir(parents=True, exist_ok=True)

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

total_entries = len(manifest)
print(f"Loaded 20k manifest with {total_entries:,} cases.")

# Step 1: Instant hardlink for existing 10k files
hardlinked_count = 0
already_present = 0
to_download = []

t0 = time.time()
for entry in manifest:
    vol = entry["volume"]
    fname = entry["file_name"]
    target_filename = f"{vol}_{fname}.json"
    target_path = raw_dir_20k / target_filename

    if target_path.exists() and target_path.stat().st_size > 50:
        already_present += 1
        continue

    src_path = raw_dir_10k / target_filename
    if src_path.exists() and src_path.stat().st_size > 50:
        try:
            os.link(src_path, target_path)
            hardlinked_count += 1
            continue
        except Exception:
            pass

    to_download.append(entry)

t_link = time.time() - t0
print(f"Hardlink / Cache check in {t_link:.2f}s:")
print(f"  - Already present: {already_present:,}")
print(f"  - Hardlinked from 10k: {hardlinked_count:,}")
print(f"  - Remaining to download: {len(to_download):,}")

if not to_download:
    print("\nAll 20,000 cases are already populated on disk!")
    sys.exit(0)

# Step 2: Download remaining cases
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=35, pool_maxsize=35, max_retries=3)
session.mount("https://", adapter)
session.mount("http://", adapter)

def download_single(entry):
    vol = entry["volume"]
    fname = entry["file_name"]
    target_filename = f"{vol}_{fname}.json"
    target_path = raw_dir_20k / target_filename

    if target_path.exists() and target_path.stat().st_size > 50:
        return "skipped"

    url = entry["download_url"]
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            with open(target_path, "w", encoding="utf-8") as out:
                out.write(r.text)
            return "downloaded"
        else:
            return f"failed_status_{r.status_code}"
    except Exception as e:
        return f"error_{e}"

print(f"\nStarting multithreaded download of {len(to_download):,} cases (25 workers)...")
sys.stdout.flush()

downloaded_count = 0
skipped_count = 0
failed_count = 0

t_dl = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
    futures = {executor.submit(download_single, entry): entry for entry in to_download}

    for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
        res = future.result()
        if res == "downloaded":
            downloaded_count += 1
        elif res == "skipped":
            skipped_count += 1
        else:
            failed_count += 1

        if i % 1000 == 0 or i == len(to_download):
            elapsed = time.time() - t_dl
            rate = i / elapsed if elapsed > 0 else 0
            print(f"Progress: {i:5d}/{len(to_download)} | Downloaded: {downloaded_count:5d} | Failed: {failed_count:2d} | Rate: {rate:.1f} cases/s")
            sys.stdout.flush()

total_elapsed = time.time() - t0
print(f"\nPopulation Completed in {total_elapsed:.1f} seconds ({total_elapsed/60:.2f} mins).")
print(f"  - Total on disk in {raw_dir_20k}: {len(list(raw_dir_20k.glob('*.json'))):,}")
