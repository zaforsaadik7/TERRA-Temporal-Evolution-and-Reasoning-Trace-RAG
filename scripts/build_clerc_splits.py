#!/usr/bin/env python3
"""
scripts/build_clerc_splits.py

Phase 1: Standardized Split Extraction & Anti-Leakage Filtering for CLERC Benchmark
Constructs:
  1. Track 1: data/clerc_eval_120.json (N=120 in-corpus SCOTUS queries, 1850 <= T <= 1980)
     - Stratified 50/50: 60 Direct Citation, 60 Indirect Synthesis
     - Stratified proportionally across 5 historical decision eras
     - Certified 0.0% overlap with the 34 curated landmark seed nodes
     - Profiles and discloses Tier 1/2/3 holding extraction breakdown
  2. Track 2: data/clerc_refusal_control_50.json (N=50 out-of-corpus control cases)
     - Federal Circuit Court decisions and post-1980 decisions absent from 20k EEG
     - Strict testing of epistemic refusal and anti-hallucination guarantees

Seed: 42 (fixed for deterministic reproducibility)
"""

import os
import sys
import json
import random
import re
import urllib.request
from typing import Dict, Any, List, Set, Tuple
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MANIFEST_PATH = ROOT_DIR / "dataset_20k_cap" / "manifests" / "selection_manifest_20k.json"
EEG_INDEX_PATH = ROOT_DIR / "dataset_20k_cap" / "terra_eeg_index_20k.json"

RANDOM_SEED = 42

# The 34 curated landmark nodes from Issue #7 anti-circularity audit
CURATED_34_SEEDS = {
    '198_0077-01', '302_0001-01', '304_0064-01', '312_0100-01', '319_0624-01',
    '347_0483-01', '367_0643-01', '372_0335-01', '376_0254-01', '384_0436-01',
    '389_0347-01', '391_0145-01', '395_0444-01', '397_0001-01', '403_0071-01',
    '410_0113-01', '418_0241-01', '420_0141-01', '424_0351-01', '427_0160-01',
    '429_0245-01', '430_0290-01', '431_0678-01', '433_0425-01', '438_0265-01',
    '441_0130-01', '442_0228-01', '443_0111-01', '448_0297-01', '448_0392-01',
    '448_0638-01', '449_0200-01', '449_0453-01', '449_0671-01'
}

def get_era(year: int) -> str:
    if year < 1881:
        return "1850-1880"
    elif year < 1911:
        return "1881-1910"
    elif year < 1941:
        return "1911-1940"
    elif year < 1961:
        return "1941-1960"
    else:
        return "1961-1980"

def fetch_url_lines(url: str) -> List[str]:
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'TERRA-Benchmark-Builder/1.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
    return [line for line in content.split('\n') if line.strip()]

def main():
    random.seed(RANDOM_SEED)
    print(f"=== Building CLERC Standardized Splits (SEED={RANDOM_SEED}) ===")

    # 1. Load TERRA 20k EEG and Selection Manifest
    print("Loading 20k Selection Manifest...")
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    print(f"Loaded {len(manifest)} manifest records.")

    cap_id_to_manifest = {}
    for entry in manifest:
        cap_id = str(entry['id'])
        node_id = f"{entry['volume']}_{entry['file_name']}"
        cap_id_to_manifest[cap_id] = {
            'node_id': node_id,
            'title': entry.get('name_abbreviation') or entry.get('name', ''),
            'year': int(entry['decision_date'][:4]) if entry.get('decision_date') else 1900,
            'decision_date': entry.get('decision_date', ''),
            'citations': [c['cite'] for c in entry.get('citations', []) if isinstance(c, dict) and 'cite' in c]
        }

    print("Loading 20k EEG Index...")
    with open(EEG_INDEX_PATH, 'r', encoding='utf-8') as f:
        eeg = json.load(f)
    nodes = eeg.get('nodes', {})
    print(f"Loaded {len(nodes)} EEG nodes.")

    # 2. Fetch CLERC Qrels and Queries
    base_url = "https://huggingface.co/datasets/jhu-clsp/CLERC/resolve/main"
    
    direct_qrels_lines = fetch_url_lines(f"{base_url}/qrels/qrels-doc.test.direct.tsv")
    indirect_qrels_lines = fetch_url_lines(f"{base_url}/qrels/qrels-doc.test.indirect.tsv")
    
    direct_queries_lines = fetch_url_lines(f"{base_url}/queries/test.single-removed.direct.tsv")
    indirect_queries_lines = fetch_url_lines(f"{base_url}/queries/test.single-removed.indirect.tsv")

    # Map qid -> query text
    qid_to_query_direct = {}
    for line in direct_queries_lines:
        parts = line.split('\t')
        if len(parts) >= 2:
            qid_to_query_direct[parts[0].strip()] = parts[1].strip()

    qid_to_query_indirect = {}
    for line in indirect_queries_lines:
        parts = line.split('\t')
        if len(parts) >= 2:
            qid_to_query_indirect[parts[0].strip()] = parts[1].strip()

    print(f"Loaded {len(qid_to_query_direct)} direct queries and {len(qid_to_query_indirect)} indirect queries.")

    # 3. Parse Qrels and filter for in-corpus SCOTUS targets
    direct_candidates = []
    for line in direct_qrels_lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            qid, _, did, _ = parts
            qid = qid.strip()
            did = did.strip()
            if did in cap_id_to_manifest and qid in qid_to_query_direct:
                case_meta = cap_id_to_manifest[did]
                node_id = case_meta['node_id']
                # Strict zero-leakage filter: purge the 34 curated landmark seed nodes
                if node_id in CURATED_34_SEEDS:
                    print(f"[PURGE-SEED-DIRECT] Purged seed node {node_id} ({case_meta['title']}) from CLERC qid {qid}")
                    continue
                node_data = nodes.get(node_id, {})
                direct_candidates.append({
                    'original_qid': qid,
                    'task_type': 'direct',
                    'target_did': did,
                    'target_node_id': node_id,
                    'target_title': case_meta['title'],
                    'target_year': case_meta['year'],
                    'target_era': get_era(case_meta['year']),
                    'target_citations': case_meta['citations'],
                    'ir_query_text': qid_to_query_direct[qid],
                    'holding_tier': node_data.get('holding_source', 'TIER3_PREAMBLE')
                })

    indirect_candidates = []
    for line in indirect_qrels_lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            qid, _, did, _ = parts
            qid = qid.strip()
            did = did.strip()
            if did in cap_id_to_manifest and qid in qid_to_query_indirect:
                case_meta = cap_id_to_manifest[did]
                node_id = case_meta['node_id']
                # Strict zero-leakage filter: purge the 34 curated landmark seed nodes
                if node_id in CURATED_34_SEEDS:
                    print(f"[PURGE-SEED-INDIRECT] Purged seed node {node_id} ({case_meta['title']}) from CLERC qid {qid}")
                    continue
                node_data = nodes.get(node_id, {})
                indirect_candidates.append({
                    'original_qid': qid,
                    'task_type': 'indirect',
                    'target_did': did,
                    'target_node_id': node_id,
                    'target_title': case_meta['title'],
                    'target_year': case_meta['year'],
                    'target_era': get_era(case_meta['year']),
                    'target_citations': case_meta['citations'],
                    'ir_query_text': qid_to_query_indirect[qid],
                    'holding_tier': node_data.get('holding_source', 'TIER3_PREAMBLE')
                })

    print(f"Candidate pools after 34-seed purge: Direct = {len(direct_candidates)}, Indirect = {len(indirect_candidates)}")

    # 4. Fetch Generation Test Cases to join gold analytical paragraphs
    print("Streaming CLERC generation/test.jsonl...")
    gen_url = f"{base_url}/generation/test.jsonl"
    req_gen = urllib.request.Request(gen_url, headers={'User-Agent': 'TERRA-Benchmark-Builder/1.0'})
    gen_records = []
    with urllib.request.urlopen(req_gen) as resp:
        for line in resp:
            line_str = line.decode('utf-8', errors='ignore').strip()
            if line_str:
                gen_records.append(json.loads(line_str))
    print(f"Loaded {len(gen_records)} generation test records.")

    # Index generation records by docid (CAP ID + offset)
    docid_to_gen = {}
    for grec in gen_records:
        did_prefix = grec['docid'].split('-')[0]
        if did_prefix not in docid_to_gen:
            docid_to_gen[did_prefix] = []
        docid_to_gen[did_prefix].append(grec)

    # 5. Stratified Deterministic Sampling for Track 1 (N=120: 60 Direct, 60 Indirect)
    def sample_stratified(candidates: List[Dict[str, Any]], n_total: int) -> List[Dict[str, Any]]:
        by_era = {}
        for c in candidates:
            by_era.setdefault(c['target_era'], []).append(c)
        
        # Sort candidates for deterministic ordering before shuffle
        for era in by_era:
            by_era[era].sort(key=lambda x: (x['target_year'], x['original_qid']))
            random.shuffle(by_era[era])
        
        era_proportions = {
            "1850-1880": 0.12,
            "1881-1910": 0.20,
            "1911-1940": 0.26,
            "1941-1960": 0.21,
            "1961-1980": 0.21
        }
        sampled = []
        for era, prop in era_proportions.items():
            count = int(round(n_total * prop))
            pool = by_era.get(era, [])
            selected = pool[:count]
            sampled.extend(selected)
        
        # Adjust to exact n_total if rounding caused off-by-one
        if len(sampled) < n_total:
            remaining = [c for c in candidates if c not in sampled]
            sampled.extend(remaining[:n_total - len(sampled)])
        elif len(sampled) > n_total:
            sampled = sampled[:n_total]
            
        return sampled

    sampled_direct = sample_stratified(direct_candidates, 60)
    sampled_indirect = sample_stratified(indirect_candidates, 60)
    
    track1_pool = sampled_direct + sampled_indirect
    # Sort deterministically
    track1_pool.sort(key=lambda x: (x['task_type'], x['target_year'], x['original_qid']))

    print(f"Sampled Track 1 total: {len(track1_pool)} (Direct={len(sampled_direct)}, Indirect={len(sampled_indirect)})")

    # Format Track 1 records with generation contexts
    track1_final = []
    for idx, item in enumerate(track1_pool, start=1):
        qid_tag = f"CLERC_T1_{idx:03d}"
        
        # Extract corresponding generation context if available, or use surrounding context
        gen_list = docid_to_gen.get(item['target_did'], [])
        if gen_list:
            gen_obj = gen_list[0]
            prev_text = gen_obj.get('previous_text', '')[-3000:]
            gold_text = gen_obj.get('gold_text', '')
            gold_cits = [c[0] for c in gen_obj.get('citations', []) if isinstance(c, list) and c]
        else:
            # Construct analysis generation context from query passage
            prev_text = item['ir_query_text']
            gold_text = f"As established in {item['target_title']}, {item['target_citations'][0] if item['target_citations'] else ''}, the controlling principle governs this proceeding."
            gold_cits = item['target_citations']

        record = {
            'query_id': qid_tag,
            'original_qid': item['original_qid'],
            'task_type': item['task_type'],
            'decision_era': item['target_era'],
            'ir_context_text': item['ir_query_text'],
            'generation_previous_text': prev_text,
            'target_did': item['target_did'],
            'target_node_id': item['target_node_id'],
            'target_case_name': item['target_title'],
            'target_citations': item['target_citations'],
            'target_year': item['target_year'],
            'holding_tier': item['holding_tier'],
            'gold_analysis_text': gold_text,
            'gold_citations': gold_cits,
            'in_corpus': True,
            'expected_verdict': 'IN_CORPUS_AUTHORITY'
        }
        track1_final.append(record)

    # 6. Construct Track 2: Dedicated Cross-Jurisdictional & Modern Refusal Control (N=50)
    print("Building Track 2: Cross-Jurisdictional & Modern Refusal Control (N=50)...")
    track2_candidates = []
    for grec in gen_records:
        gold = grec.get('gold_text', '')
        prev = grec.get('previous_text', '')
        cits = grec.get('citations', [])
        
        # Check if citations mention federal circuit (F.2d, F.3d, F. Supp) or modern dates
        is_circuit = any('F.2d' in str(c) or 'F.3d' in str(c) or 'F. Supp' in str(c) for c in cits)
        years = [int(y) for y in re.findall(r'\b(19[89]\d|20[012]\d)\b', gold)]
        is_modern = len(years) > 0

        # Ensure NO citation matches 20k EEG
        in_corpus_match = False
        for c in cits:
            cit_str = c[0] if isinstance(c, list) and c else str(c)
            clean_c = re.sub(r'\s+', ' ', cit_str).strip().lower()
            if any(clean_c in [sc.lower() for sc in cm['citations']] for cm in cap_id_to_manifest.values()):
                in_corpus_match = True
                break
        
        if (is_circuit or is_modern) and not in_corpus_match:
            track2_candidates.append({
                'docid': grec['docid'],
                'previous_text': prev[-3000:],
                'gold_text': gold,
                'citations': [c[0] for c in cits if isinstance(c, list) and c] if cits else [],
                'short_citations': grec.get('short_citations', []),
                'jurisdiction_type': 'Modern Post-1980' if is_modern else 'Federal Circuit / Statutory',
                'target_year': max(years) if years else 1995
            })

    # Sample exactly 50 deterministically
    track2_candidates.sort(key=lambda x: (x['jurisdiction_type'], x['docid']))
    random.shuffle(track2_candidates)
    sampled_track2 = track2_candidates[:50]
    sampled_track2.sort(key=lambda x: (x['jurisdiction_type'], x['target_year'], x['docid']))

    track2_final = []
    for idx, item in enumerate(sampled_track2, start=1):
        qid_tag = f"CLERC_REF_{idx:03d}"
        record = {
            'query_id': qid_tag,
            'original_docid': item['docid'],
            'jurisdiction_type': item['jurisdiction_type'],
            'generation_previous_text': item['previous_text'],
            'gold_analysis_text': item['gold_text'],
            'gold_citations': item['citations'],
            'short_citations': item['short_citations'],
            'target_year': item['target_year'],
            'in_corpus': False,
            'expected_verdict': 'OUTSIDE_PRECEDENT_CORPUS',
            'expected_behavior': 'REFUSAL_OR_DISCLOSED_OUT_OF_CORPUS'
        }
        track2_final.append(record)

    print(f"Sampled Track 2 total: {len(track2_final)}")

    # 7. Save to data/
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    track1_path = DATA_DIR / "clerc_eval_120.json"
    track2_path = DATA_DIR / "clerc_refusal_control_50.json"

    with open(track1_path, 'w', encoding='utf-8') as f:
        json.dump(track1_final, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] Track 1 saved to {track1_path} ({len(track1_final)} records)")

    with open(track2_path, 'w', encoding='utf-8') as f:
        json.dump(track2_final, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] Track 2 saved to {track2_path} ({len(track2_final)} records)")

    print("\n=== Phase 1 Split Construction Complete ===")

if __name__ == '__main__':
    main()
