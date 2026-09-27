#!/usr/bin/env python3
"""
scripts/build_casefacts_splits.py

Phase 2: External Validation Benchmark Split Generation
Builds the standardized CaseFacts evaluation sets:
1. Track 1: In-Corpus Precedent Benchmark (N=120)
   - 67 Supported claims (1850 <= T <= 1980)
   - 45 Refuted claims (1850 <= T <= 1980)
   - 8 Overruled claims (1850 <= T <= 1980, verified chronological overrulings)
2. Track 2: Dedicated Out-of-Corpus Refusal Stress Control (N=50)
   - 50 modern post-1980 claims (T > 1980) to test temporal boundary adherence and refusal
"""

import json
import os
import re
import random

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

CASEFACTS_TEST = os.path.join(ROOT_DIR, 'scratch', 'casefacts_test.json')
CASEFACTS_TRAIN = os.path.join(ROOT_DIR, 'scratch', 'casefacts_train.json')
GRAPH_PATH = os.path.join(ROOT_DIR, 'dataset_20k_cap', 'terra_eeg_index_20k.json')

OUT_INC_PATH = os.path.join(DATA_DIR, 'casefacts_eval_120.json')
OUT_REF_PATH = os.path.join(DATA_DIR, 'casefacts_refusal_control_50.json')

def clean_title(s):
    s = s.lower().replace('&amp;', '&').replace('&#160;', ' ')
    s = re.sub(r'\[\d+\]', '', s)
    s = s.replace('v.', 'v').replace('&', 'and').replace('.', '').strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def build_casefacts_splits():
    print("=" * 80)
    print("PHASE 2: BUILDING CASEFACTS EVALUATION SPLITS")
    print("=" * 80)

    # 1. Load data
    with open(CASEFACTS_TEST, 'r', encoding='utf-8') as f:
        test_claims = json.load(f)
    with open(CASEFACTS_TRAIN, 'r', encoding='utf-8') as f:
        train_claims = json.load(f)
    all_claims = test_claims + train_claims
    print(f"Loaded {len(all_claims)} total CaseFacts claims.")

    with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    nodes = graph['nodes']
    print(f"Loaded {len(nodes)} graph nodes from {GRAPH_PATH}.")

    # Index graph nodes
    exact_title_map = {}
    first_party_map = {}
    for nid, ndata in nodes.items():
        raw_title = ndata.get('title', '')
        t = clean_title(raw_title)
        if not t:
            continue
        yr = int(ndata.get('decision_date', '0000')[:4]) if ndata.get('decision_date') else 0
        node_info = {'nid': nid, 'title': raw_title, 'year': yr, 'decision_date': ndata.get('decision_date', '')}
        exact_title_map[t] = node_info
        if ' v ' in t:
            fp = t.split(' v ')[0].strip()
            if len(fp) >= 4:
                if fp not in first_party_map:
                    first_party_map[fp] = []
                first_party_map[fp].append(node_info)

    def find_case_in_graph(name_str):
        cln = clean_title(name_str)
        if cln in exact_title_map:
            return exact_title_map[cln]
        if ' v ' in cln:
            fp = cln.split(' v ')[0].strip()
            if fp in first_party_map:
                sp = cln.split(' v ')[1].strip()
                for cand in first_party_map[fp]:
                    cand_t = clean_title(cand['title'])
                    if sp in cand_t or (len(sp) > 5 and sp[:5] in cand_t):
                        return cand
        return None

    # Track 1: Match in-corpus claims
    pre_1980_supported = []
    pre_1980_refuted = []
    
    # 8 canonical chronologically verified overrulings
    target_overruled_pairs = [
        ("Wolf v. Colorado", "Mapp v. Ohio"),
        ("Olmstead v. United States", "Katz v. United States"),
        ("Cicenia v. Lagay", "Escobedo v. Illinois"),
        ("Crooker v. California", "Escobedo v. Illinois"),
        ("Plessy v. Ferguson", "Evans v. Newton"),
        ("United States v. Sealy, Inc.", "Continental T. V., Inc. v. GTE Sylvania Inc."),
        ("Schenck v. United States", "Garrison v. Louisiana"),
        ("Chimel v. California", "United States v. Robinson")
    ]

    selected_overruled = []

    for c in all_claims:
        label = c.get('label')
        case_names = c.get('case_name', [])
        if isinstance(case_names, str):
            case_names = [case_names]
        
        target_node = None
        for cn in case_names:
            target_node = find_case_in_graph(cn)
            if target_node:
                break
        
        if not target_node:
            continue
        
        tyear = target_node['year']
        if not (1850 <= tyear <= 1980):
            continue

        item = {
            'claim': c['claim'],
            'case_name': case_names[0] if case_names else target_node['title'],
            'matched_node_id': target_node['nid'],
            'target_node_title': target_node['title'],
            'target_year': tyear,
            'label': label,
            'overruling_case': c.get('overruling_case', '')
        }

        if label == 'Supported':
            pre_1980_supported.append(item)
        elif label == 'Refuted':
            pre_1980_refuted.append(item)
        elif label == 'Overruled':
            # Check if this matches one of our 8 target pairs
            ovr_case = c.get('overruling_case', '')
            for (t_name, o_name) in target_overruled_pairs:
                if (clean_title(t_name) in clean_title(item['case_name']) or clean_title(item['case_name']) in clean_title(t_name)) and \
                   (clean_title(o_name) in clean_title(ovr_case) or clean_title(ovr_case) in clean_title(o_name)):
                    # Check if not already added
                    if not any(x['case_name'] == item['case_name'] for x in selected_overruled):
                        item['overruling_anchor'] = o_name
                        selected_overruled.append(item)
                    break

    print(f"Candidate pools: Supported={len(pre_1980_supported)}, Refuted={len(pre_1980_refuted)}, Overruled={len(selected_overruled)}")
    assert len(selected_overruled) == 8, f"Expected 8 Overruled claims, found {len(selected_overruled)}"

    # Deterministic sampling for Supported (67) and Refuted (45)
    rng = random.Random(42)
    # Deduplicate by claim text
    seen_claims = set(x['claim'] for x in selected_overruled)

    def sample_unique(pool, n):
        unique_pool = []
        for x in pool:
            if x['claim'] not in seen_claims:
                unique_pool.append(x)
                seen_claims.add(x['claim'])
        rng.shuffle(unique_pool)
        return unique_pool[:n]

    sampled_supported = sample_unique(pre_1980_supported, 67)
    sampled_refuted = sample_unique(pre_1980_refuted, 45)

    assert len(sampled_supported) == 67, f"Expected 67 Supported, got {len(sampled_supported)}"
    assert len(sampled_refuted) == 45, f"Expected 45 Refuted, got {len(sampled_refuted)}"

    in_corpus_120 = []
    # Interleave / shuffle deterministically
    combined = sampled_supported + sampled_refuted + selected_overruled
    rng.shuffle(combined)

    for i, item in enumerate(combined):
        in_corpus_120.append({
            'id': f"CF_INC_{i+1:03d}",
            'claim': item['claim'],
            'case_name': item['case_name'],
            'target_node_id': item['matched_node_id'],
            'target_node_title': item['target_node_title'],
            'target_year': item['target_year'],
            'label': item['label'],
            'overruling_case': item.get('overruling_case', ''),
            'overruling_anchor': item.get('overruling_anchor', ''),
            'corpus_status': 'in_corpus_pre_1980'
        })

    with open(OUT_INC_PATH, 'w', encoding='utf-8') as f:
        json.dump(in_corpus_120, f, indent=2)
    print(f"[SUCCESS] Saved Track 1 In-Corpus benchmark to: {OUT_INC_PATH} (N={len(in_corpus_120)})")

    # Track 2: Dedicated Out-of-Corpus Refusal Stress Control (N=50)
    # Filter claims with modern post-1980 cases
    famous_post_1980 = [
        ('District of Columbia v. Heller', 2008),
        ('Citizens United v. Federal Election Commission', 2010),
        ('Shelby County v. Holder', 2013),
        ('Obergefell v. Hodges', 2015),
        ('Carpenter v. United States', 2018),
        ('Ramos v. Louisiana', 2020),
        ('Dobbs v. Jackson Women\'s Health Organization', 2022),
        ('Riley v. California', 2014),
        ('Arizona v. Gant', 2009),
        ('Bostock v. Clayton County', 2020),
        ('Kennedy v. Bremerton School District', 2022),
        ('New York State Rifle & Pistol Association, Inc. v. Bruen', 2022),
        ('United States v. Windsor', 2013),
        ('Lawrence v. Texas', 2003),
        ('Kelo v. City of New London', 2005),
        ('Boumediene v. Bush', 2008),
        ('National Federation of Independent Business v. Sebelius', 2012),
        ('Masterpiece Cakeshop, Ltd. v. Colorado Civil Rights Commission', 2018),
        ('Burwell v. Hobby Lobby Stores, Inc.', 2014),
        ('South Dakota v. Wayfair, Inc.', 2018),
        ('Janus v. AFSCME', 2018),
        ('Timbs v. Indiana', 2019),
        ('Cedar Point Nursery v. Hassid', 2021),
        ('TransUnion LLC v. Ramirez', 2021),
        ('West Virginia v. EPA', 2022),
        ('Lucia v. SEC', 2018),
        ('Seila Law LLC v. CFPB', 2020),
        ('Rucho v. Common Cause', 2019),
        ('Department of Commerce v. New York', 2019),
        ('Lange v. California', 2021),
        ('Fulton v. City of Philadelphia', 2021),
        ('Jones v. Mississippi', 2021),
        ('Epic Systems Corp. v. Lewis', 2018),
        ('Trump v. Hawaii', 2018),
        ('Murphy v. NCAA', 2018),
        ('Jesner v. Arab Bank, PLC', 2018),
        ('Encino Motorcars, LLC v. Navarro', 2018),
        ('Crawford v. Washington', 2004)
    ]

    post_1980_candidates = []
    for c in all_claims:
        c_names = c.get('case_name', [])
        if isinstance(c_names, str):
            c_names = [c_names]
        matched_post = None
        for cn in c_names:
            for (fp_name, fp_yr) in famous_post_1980:
                if fp_name.lower() in cn.lower() or cn.lower() in fp_name.lower():
                    matched_post = (cn, fp_name, fp_yr)
                    break
            if matched_post:
                break
        
        if matched_post:
            post_1980_candidates.append({
                'claim': c['claim'],
                'case_name': matched_post[0],
                'post_1980_anchor': matched_post[1],
                'year': matched_post[2],
                'label': c.get('label', '')
            })

    print(f"Total post-1980 candidate claims: {len(post_1980_candidates)}")
    rng2 = random.Random(42)
    seen_ref_claims = set()
    unique_post = []
    for p in post_1980_candidates:
        if p['claim'] not in seen_ref_claims:
            unique_post.append(p)
            seen_ref_claims.add(p['claim'])

    rng2.shuffle(unique_post)
    sampled_refusal = unique_post[:50]
    assert len(sampled_refusal) == 50, f"Expected 50 refusal claims, got {len(sampled_refusal)}"

    refusal_control_50 = []
    for i, item in enumerate(sampled_refusal):
        refusal_control_50.append({
            'id': f"CF_REF_{i+1:03d}",
            'claim': item['claim'],
            'case_name': item['case_name'],
            'post_1980_anchor': item['post_1980_anchor'],
            'year': item['year'],
            'original_label': item['label'],
            'ground_truth_class': 'Outside Precedent Corpus',
            'corpus_status': 'out_of_corpus_post_1980'
        })

    with open(OUT_REF_PATH, 'w', encoding='utf-8') as f:
        json.dump(refusal_control_50, f, indent=2)
    print(f"[SUCCESS] Saved Track 2 Refusal Control benchmark to: {OUT_REF_PATH} (N={len(refusal_control_50)})")

    # Summary verification
    print("\n--- SUMMARY OF GENERATED BENCHMARK SPLITS ---")
    print(f"Track 1 (In-Corpus Precedent Benchmark N=120):")
    label_counts = {}
    for item in in_corpus_120:
        l = item['label']
        label_counts[l] = label_counts.get(l, 0) + 1
    for l, cnt in sorted(label_counts.items()):
        print(f"  - {l:<10}: {cnt}")
    print(f"Track 2 (Dedicated Out-of-Corpus Refusal Control N=50):")
    print(f"  - Outside Precedent Corpus: {len(refusal_control_50)}")
    print("=" * 80)

if __name__ == '__main__':
    build_casefacts_splits()
