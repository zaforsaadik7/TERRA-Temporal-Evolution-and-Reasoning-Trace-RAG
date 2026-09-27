import os
import json
import random
from pathlib import Path

# Fix random seed for exact reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

cache_dir = Path("dataset_20k_cap/volume_metadata_cache")
vols = sorted([int(f.stem.split('_')[1]) for f in cache_dir.glob("vol_*.json")])

total_cases = 0
civil_rights_kw = [
    "equal", "civil", "rights", "segregat", "fourteenth", "14th", "amendment",
    "due process", "discrimination", "school", "negro", "race", "racial", "state", "board"
]

civil_cases = []
other_full = []
proc_cases = []

# Load existing 10k manifest to preserve all 10,000 cases
manifest_10k_path = Path("dataset_10k_cap/manifests/selection_manifest.json")
with open(manifest_10k_path, "r", encoding="utf-8") as f:
    existing_10k = json.load(f)

existing_ids = set()
for c in existing_10k:
    v = c.get("volume")
    fn = c.get("file_name")
    existing_ids.add(f"{v}_{fn}")

print(f"Loaded existing 10k manifest: {len(existing_10k):,} entries (unique IDs: {len(existing_ids):,})")

for v in vols:
    with open(cache_dir / f"vol_{v}.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    for c in cases:
        total_cases += 1
        cid = c.get("id")
        fname = c.get("file_name")
        node_id = f"{v}_{fname}"
        char_cnt = c.get("analysis", {}).get("char_count", 0)
        c_name = (c.get("name", "") + " " + c.get("name_abbreviation", "")).lower()

        entry = {
            "id": cid,
            "volume": v,
            "file_name": fname,
            "node_id": node_id,
            "name": c.get("name"),
            "name_abbreviation": c.get("name_abbreviation"),
            "decision_date": c.get("decision_date"),
            "char_count": char_cnt,
            "citations": c.get("citations", []),
            "download_url": f"https://static.case.law/us/{v}/cases/{fname}.json"
        }

        if char_cnt >= 4000:
            if any(kw in c_name for kw in civil_rights_kw):
                entry["category"] = "civil_rights"
                civil_cases.append(entry)
            else:
                entry["category"] = "other_subject"
                other_full.append(entry)
        else:
            entry["category"] = "procedural"
            proc_cases.append(entry)

print(f"\nTotal cases scanned across {len(vols)} volumes (50–448): {total_cases:,}")
print(f"  - Civil Rights Candidates (>=4k): {len(civil_cases):,}")
print(f"  - Other Full Opinions (>=4k):     {len(other_full):,}")
print(f"  - Short Procedural (<4k):         {len(proc_cases):,}")

unselected_civil = [c for c in civil_cases if c["node_id"] not in existing_ids]
unselected_other = [c for c in other_full if c["node_id"] not in existing_ids]
unselected_proc = [c for c in proc_cases if c["node_id"] not in existing_ids]

print(f"\nUnselected Candidates Pool:")
print(f"  - Unselected Civil Rights: {len(unselected_civil):,}")
print(f"  - Unselected Other Full:   {len(unselected_other):,}")
print(f"  - Unselected Procedural:   {len(unselected_proc):,}")

# Target: Expand to 20,000 cases
# 1. Keep all 10,000 existing cases intact
# 2. Add any newly found civil rights cases (if any)
# 3. Add sampled other_subject full opinions to reach high doctrinal diversity
# 4. Add sampled procedural entries to match balance

TARGET_TOTAL = 20000
needed = TARGET_TOTAL - len(existing_10k)
print(f"\nExpanding by: {needed:,} cases to reach {TARGET_TOTAL:,}")

# Sample from unselected
# E.g. take all unselected civil (if any), then ~85% other full, ~15% procedural
new_civil = list(unselected_civil)
remaining_needed = needed - len(new_civil)

num_other_needed = int(remaining_needed * 0.85)
num_proc_needed = remaining_needed - num_other_needed

selected_new_other = random.sample(unselected_other, min(num_other_needed, len(unselected_other)))
remaining_after_other = remaining_needed - len(selected_new_other)
selected_new_proc = random.sample(unselected_proc, min(remaining_after_other, len(unselected_proc)))

newly_selected = new_civil + selected_new_other + selected_new_proc
print(f"\nNewly Selected Breakdown ({len(newly_selected):,} cases):")
print(f"  - Additional Civil Rights: {len(new_civil):,}")
print(f"  - Additional Other Full:   {len(selected_new_other):,}")
print(f"  - Additional Procedural:   {len(selected_new_proc):,}")

# Combine existing 10k + newly selected 10k
combined_manifest = list(existing_10k)
# Strip 'node_id' helper key from new entries before saving to match exact schema
for entry in newly_selected:
    entry_clean = dict(entry)
    if "node_id" in entry_clean:
        del entry_clean["node_id"]
    combined_manifest.append(entry_clean)

# Verification
assert len(combined_manifest) == TARGET_TOTAL, f"Expected {TARGET_TOTAL}, got {len(combined_manifest)}"
unique_combined_ids = {f"{c['volume']}_{c['file_name']}" for c in combined_manifest}
assert len(unique_combined_ids) == TARGET_TOTAL, f"Duplicate cases detected! Unique: {len(unique_combined_ids)}"

# Category breakdown of 20k
cat_counts = {}
for c in combined_manifest:
    cat = c.get("category", "unknown")
    cat_counts[cat] = cat_counts.get(cat, 0) + 1

print(f"\nFinal 20k Manifest Breakdown:")
for cat, count in sorted(cat_counts.items()):
    pct = (count / TARGET_TOTAL) * 100
    print(f"  - {cat:20s}: {count:6,d} ({pct:5.2f}%)")

# Write out manifest
out_manifest_dir = Path("dataset_20k_cap/manifests")
out_manifest_dir.mkdir(parents=True, exist_ok=True)
out_manifest_path = out_manifest_dir / "selection_manifest_20k.json"

with open(out_manifest_path, "w", encoding="utf-8") as f:
    json.dump(combined_manifest, f, indent=2)

print(f"\nManifest successfully written to: {out_manifest_path}")
print(f"File size: {out_manifest_path.stat().st_size:,} bytes")
