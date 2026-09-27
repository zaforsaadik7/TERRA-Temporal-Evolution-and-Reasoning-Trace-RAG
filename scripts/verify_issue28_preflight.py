import os
import hashlib
import json
import re
import glob

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

PROTECTED_SUBSTRATES = {
    "terra_350_benchmark.json": "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3",
    "dataset_20k_cap/terra_eeg_index_20k.json": "7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json": "c530f9858e9b3372dc9079092178e9d8c2239758eda073c35b9fc7b0c49e1f72",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json": "14071dba780157b767dfce1f11ef8190722ad94ab9a37e8258bb574a0183c3fc",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json": "98d14bfb75d5051429ff4c48c0410300efb5ef7f04112701635f110aff094ddf",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json": "5e2b59ac3fce2b9513c9ceb60b6a1cae0c2323150f4936a0410503fd56689f3c",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json": "606a6ec126bf7c5ac4cbdbac04f37eee52f7bd524d35e5f12d8dc4ebff3e23b5",
    "ask_terra.py": "430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd",
    "data/issue21_preflight.json": "9a26a9e35340111773180cadd9f3c271fcecde1a3863609d6abbd2236ba7a9b2",
    "logs/issue21_preflight.txt": "91d028cd9ce5079d16bf540cba6546bfa825e5688b3283eb5ef226cc8a3d84d8",
    "ask_terra_pre_issue13_backup.py": "bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9"
}

def main():
    log_lines = []
    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=" * 70)
    log("TERRA ISSUE #28 PREFLIGHT VERIFICATION & CAUSAL NOMENCLATURE AUDIT")
    log("=" * 70)

    # 1. Verify protected substrates
    log("\n[STEP 1/3] Verifying Protected Core Substrates Bit-Invariance...")
    substrate_status = {}
    all_substrates_pass = True
    for rel_path, expected_hash in PROTECTED_SUBSTRATES.items():
        if not os.path.exists(rel_path):
            log(f"  [FAIL] Missing substrate: {rel_path}")
            substrate_status[rel_path] = {"status": "MISSING", "expected": expected_hash}
            all_substrates_pass = False
            continue
        actual_hash = sha256_file(rel_path)
        if actual_hash == expected_hash:
            log(f"  [PASS] {rel_path} -> {actual_hash[:16]}... (MATCH)")
            substrate_status[rel_path] = {"status": "PASS", "hash": actual_hash}
        else:
            log(f"  [FAIL] {rel_path} -> Hash mismatch!\n    Actual:   {actual_hash}\n    Expected: {expected_hash}")
            substrate_status[rel_path] = {"status": "MISMATCH", "actual": actual_hash, "expected": expected_hash}
            all_substrates_pass = False

    if not all_substrates_pass:
        log("\n[ABORT] Protected substrates failed bit-invariance!")
        return False

    # 2. Recursively scan all active LaTeX files in Paper/
    log("\n[STEP 2/3] Recursively Scanning All Active Paper/**/*.tex Files...")
    all_tex_files = sorted(glob.glob("Paper/**/*.tex", recursive=True))
    active_tex_files = [
        f for f in all_tex_files
        if not os.path.basename(f).startswith("prev_main")
        and not os.path.basename(f).endswith("_bak.tex")
    ]
    log(f"  Found {len(active_tex_files)} active .tex files across Paper/ directory tree.")

    causal_matches = {}
    for tex_path in active_tex_files:
        with open(tex_path, "r", encoding="utf-8", errors="ignore") as f:
            for lno, line in enumerate(f, 1):
                found = re.findall(r'\bcausal\w*', line, re.IGNORECASE)
                if found:
                    causal_matches.setdefault(tex_path, []).append((lno, line.strip(), found))
                    log(f"  [FOUND] {tex_path}:{lno}: {found} -> {line.strip()[:80]}")

    log(f"\n  Active .tex files with 'causal': {len(causal_matches)}")
    total_found = sum(len(v) for v in causal_matches.values())
    log(f"  Total occurrences in active .tex files: {total_found}")

    # 3. Check specific phrases
    log("\n[STEP 3/3] Checking Key Phrases in Paper/main.tex...")
    with open("Paper/main.tex", "r", encoding="utf-8") as f:
        main_text = f.read()

    phrase_115 = "chronological precedent relationships across \\CorpusTotalOpinions\\ authentic judicial decisions and \\CorpusPrecedentEdges\\ directed citation edges"
    has_phrase_115 = phrase_115 in main_text
    log(f"  Line 115 'chronological precedent relationships': {'[PRESENT - PASS]' if has_phrase_115 else '[MISSING - FAIL]'}")

    zhang_cite = "zhang2025respectingtemporalcausalconsistencyentityevent"
    has_zhang = zhang_cite in main_text
    log(f"  Line 133 Zhang et al. citation key '{zhang_cite}': {'[PRESENT - PASS]' if has_zhang else '[MISSING - FAIL]'}")

    preflight_data = {
        "status": "PASS" if all_substrates_pass and has_phrase_115 and has_zhang else "FAIL",
        "protected_substrates": substrate_status,
        "active_tex_count": len(active_tex_files),
        "causal_matches": {k: [(item[0], item[2]) for item in v] for k, v in causal_matches.items()},
        "has_phrase_115": has_phrase_115,
        "has_zhang_cite": has_zhang
    }

    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    with open("data/issue28_preflight.json", "w", encoding="utf-8") as f:
        json.dump(preflight_data, f, indent=2)
    with open("logs/issue28_preflight.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    log("\n" + "=" * 70)
    log(f"PREFLIGHT SUMMARY: {preflight_data['status']}")
    log("=" * 70)
    return preflight_data["status"] == "PASS"

if __name__ == "__main__":
    main()
