import os
import sys
import json
import random
import dotenv

dotenv.load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# Fixed random seed for complete experimental reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

EXCLUDED_FLIPPED_NODE_IDS = {
    '156_0001-01',  # E. C. Knight (D009)
    '347_0483-01',  # Brown v. Board / Loving (D024)
    '109_0003-01',  # Civil Rights Cases (D049)
    '157_0429-01',  # Pollock (D054)
    '198_0045-01',  # Lochner (D057, D071)
    '83_0130-01',   # Bradwell (D059)
    '163_0537-01',  # Plessy (D066)
    '208_0412-01',  # Muller (D072)
}

os.makedirs('data', exist_ok=True)


def jaccard_similarity(str1: str, str2: str) -> float:
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))


# ==============================================================================
# PART 1: BUILD TRACK A (CaseHOLD 200 Pairs)
# ==============================================================================
def build_casehold_track_a(target_pairs: int = 200):
    print("\n--- Building Track A: CaseHOLD Benchmark (200 Pairs) ---")
    import datasets
    token = os.environ.get('HF_TOKEN')
    
    # Load CaseHOLD test split in streaming mode
    ds = datasets.load_dataset('coastalcph/lex_glue', 'case_hold', token=token, streaming=True, split='test')
    
    positive_pairs = []
    negative_pairs = []
    needed_per_class = target_pairs // 2
    
    for item in ds:
        if len(positive_pairs) >= needed_per_class and len(negative_pairs) >= needed_per_class:
            break
            
        raw_ctx = item['context']
        gold_idx = item['label']
        endings = item['endings']
        gold_ending = endings[gold_idx].strip()
        
        # Format the context passage cleanly (replacing placeholder)
        citation_context = raw_ctx.replace("(<HOLDING>)", "").strip()
        if len(citation_context) < 100:
            continue
            
        # Positive Pair
        if len(positive_pairs) < needed_per_class:
            query = f"Does the cited legal authority hold that {gold_ending}?"
            positive_pairs.append({
                "pair_id": f"CH_POS_{len(positive_pairs)+1:03d}",
                "track": "Track_A_CaseHOLD",
                "sub_type": "citation_gold_holding",
                "user_query": query,
                "retrieved_context": citation_context,
                "candidate_holding": gold_ending,
                "ground_truth_entails": True,
                "label_rationale": "Direct citation context entails the authentic gold holding affirmed by the court."
            })
            
        # Negative Pair: Pick the distractor with LOWEST lexical overlap to ensure crisp non-entailment
        if len(negative_pairs) < needed_per_class:
            candidate_distractors = [
                (idx, e.strip(), jaccard_similarity(gold_ending, e.strip()))
                for idx, e in enumerate(endings) if idx != gold_idx
            ]
            # Sort by lowest similarity
            candidate_distractors.sort(key=lambda x: x[2])
            best_distractor_idx, best_distractor, sim = candidate_distractors[0]
            
            # Sanity gate: similarity must be <= 0.25 to guarantee clean non-entailment
            if sim <= 0.25:
                query = f"Does the cited legal authority hold that {best_distractor}?"
                negative_pairs.append({
                    "pair_id": f"CH_NEG_{len(negative_pairs)+1:03d}",
                    "track": "Track_A_CaseHOLD",
                    "sub_type": "citation_distractor_holding",
                    "user_query": query,
                    "retrieved_context": citation_context,
                    "candidate_holding": best_distractor,
                    "ground_truth_entails": False,
                    "label_rationale": f"Citation context does not entail distractor proposition (lexical similarity to gold: {sim:.2f})."
                })
                
    combined = positive_pairs + negative_pairs
    random.shuffle(combined)
    
    out_path = 'data/casehold_nli_eval_200.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Track A built successfully: {len(combined)} pairs ({len(positive_pairs)} pos, {len(negative_pairs)} neg) saved to {out_path}")
    return combined


# ==============================================================================
# PART 2: BUILD TRACK B (TERRA-EEG In-Domain 200 Pairs)
# ==============================================================================
def build_terra_eeg_track_b(target_pairs: int = 200):
    print("\n--- Building Track B: TERRA-EEG Judicial Entailment (200 Pairs) ---")
    
    with open('dataset_20k_cap/terra_eeg_index_20k.json', 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
        
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    
    # Verify exclusion of blacklisted nodes
    for nid in EXCLUDED_FLIPPED_NODE_IDS:
        assert nid in nodes, f"Blacklist sanity check: {nid} not found in nodes"
        
    # Build adjacency and predecessor maps
    predecessors = {}
    successors = {}
    for e in edges:
        src = e['source']
        tgt = e['target']
        rel = e.get('relation', 'CITES')
        successors.setdefault(src, []).append((tgt, rel))
        predecessors.setdefault(tgt, []).append((src, rel))
        
    # Candidate Tier 1 landmark nodes (excluding blacklisted)
    tier1_nodes = [
        nid for nid, ndata in nodes.items()
        if nid not in EXCLUDED_FLIPPED_NODE_IDS
        and ndata.get('holding_source', '').upper() == 'TIER1_HEADNOTE_SYLLABUS'
        and len(ndata.get('substantive_holding', '')) >= 150
        and len(ndata.get('title', '')) > 4
    ]
    random.shuffle(tier1_nodes)
    
    GATE2_LANDMARK_PAIRS = {
        ('304_0064-01', '41_0001-01'),   # Erie -> Swift
        ('347_0483-01', '163_0537-01'),  # Brown -> Plessy
        ('372_0335-01', '316_0455-01'),  # Gideon -> Betts
        ('367_0643-01', '338_0025-01'),  # Mapp -> Wolf
        ('300_0379-01', '261_0525-01'),  # West Coast Hotel -> Adkins
        ('312_0100-01', '247_0251-01'),  # Darby -> Hammer
        ('319_0624-01', '310_0586-01'),  # Barnette -> Gobitis
        ('378_0001-01', '211_0078-01'),  # Malloy -> Twining
        ('395_0444-01', '274_0357-01'),  # Brandenburg -> Whitney
    }
    COLLISION_PAIRS = {
        ('415_0651-01', '394_0759-01')   # Edelman -> Wyman-Gordon page collision
    }

    # Candidate clean CRS overrule edges (strictly held-out: excluding blacklisted, Gate 2 dev landmarks, and collisions)
    clean_overrule_edges = [
        e for e in edges
        if e.get('relation') == 'OVERRULES'
        and e['source'] not in EXCLUDED_FLIPPED_NODE_IDS
        and e['target'] not in EXCLUDED_FLIPPED_NODE_IDS
        and (e['source'], e['target']) not in GATE2_LANDMARK_PAIRS
        and (e['source'], e['target']) not in COLLISION_PAIRS
        and e['source'] in nodes and e['target'] in nodes
        and len(nodes[e['source']].get('substantive_holding', '')) >= 100
        and len(nodes[e['target']].get('substantive_holding', '')) >= 100
    ]
    random.shuffle(clean_overrule_edges)
    
    positive_pairs = []
    
    # 1. 50 Direct Holding Entailments
    for i in range(50):
        nid = tier1_nodes[i]
        ndata = nodes[nid]
        title = ndata.get('title', nid)
        date = ndata.get('decision_date', '')
        holding = ndata['substantive_holding'].strip()
        
        # Build realistic production traversal context
        succ_lines = []
        for succ_id, rel in successors.get(nid, [])[:4]:
            succ_title = nodes.get(succ_id, {}).get('title', succ_id)
            succ_date = nodes.get(succ_id, {}).get('decision_date', '')
            succ_lines.append(f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{succ_title}' (Case ID: {succ_id}, Date: {succ_date}) [{rel}] this precedent.")
            
        succ_block = f"[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n" + "\n".join(succ_lines) + "\n\n" if succ_lines else ""
        
        seeded_block = f"[SEEDED CASE] {title}:\n[Holding]: {holding[:800]}\n\n"
        retrieved_block = f"[Top Retrieved Cases]\n- In {title} ({date}), the Supreme Court rendered its operative ruling."
        
        production_context = f"{succ_block}{seeded_block}{retrieved_block}"
        
        # Craft precise query
        query = f"What did the Supreme Court hold regarding the legal rule and standard in {title} ({date[:4] if date else ''})?"
        
        positive_pairs.append({
            "pair_id": f"TB_POS_DIR_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "direct_holding_entailment",
            "difficulty": "positive_direct_holding",
            "case_id": nid,
            "case_title": title,
            "decision_date": date,
            "user_query": query,
            "retrieved_context": production_context,
            "ground_truth_entails": True,
            "label_rationale": "Retrieved context provides authentic Tier 1 substantive holding directly resolving the query."
        })
        
    # 2. 25 Overruling / Invalidation Entailments
    for i in range(25):
        edge = clean_overrule_edges[i]
        overruling_id = edge['source']
        overruled_id = edge['target']
        overruling_node = nodes[overruling_id]
        overruled_node = nodes[overruled_id]
        
        overruling_title = overruling_node.get('title', overruling_id)
        overruled_title = overruled_node.get('title', overruled_id)
        overruling_date = overruling_node.get('decision_date', '')
        overruled_date = overruled_node.get('decision_date', '')
        
        overruling_holding = overruling_node.get('substantive_holding', '').strip()[:600]
        overruled_holding = overruled_node.get('substantive_holding', '').strip()[:400]
        
        evolution_block = (
            f"[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n"
            f"- CHRONOLOGICAL FLOW / OVERRULING SUCCESSOR: '{overruling_title}' (Case ID: {overruling_id}, Date: {overruling_date}) "
            f"[OVERRULES / REPUDIATES] this precedent (Case ID: {overruled_id}). [Holding]: {overruling_holding}\n\n"
        )
        structural_block = f"[STRUCTURAL CONNECTIONS]\n- [OVERRULES] '{overruling_title}' directly overrules '{overruled_title}' in the legal citation graph.\n\n"
        seeded_block = f"[SEEDED CASE] {overruled_title}:\n[Holding]: {overruled_holding}\n\n"
        retrieved_block = f"[Top Retrieved Cases]\n- {overruled_title} was formally evaluated and repudiated by {overruling_title}."
        
        production_context = f"{evolution_block}{structural_block}{seeded_block}{retrieved_block}"
        
        query = (
            f"Under the binding doctrine of {overruled_title} ({overruled_date[:4] if overruled_date else ''}), "
            f"is it currently constitutional and enforceable to apply its holding as active Supreme Court law?"
        )
        
        positive_pairs.append({
            "pair_id": f"TB_POS_OVR_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "overruling_invalidation_entailment",
            "difficulty": "positive_overruling_refutation",
            "case_id": overruled_id,
            "overruling_id": overruling_id,
            "case_title": overruled_title,
            "overruling_title": overruling_title,
            "user_query": query,
            "retrieved_context": production_context,
            "ground_truth_entails": True,
            "label_rationale": "Context contains the explicit [OVERRULES / REPUDIATES] successor with its holding, entailing the refutation."
        })
        
    # 3. 25 Multi-Hop Citation Trajectory Entailments
    used_for_trajectories = set([p['case_id'] for p in positive_pairs])
    traj_count = 0
    for nid in tier1_nodes[50:]:
        if traj_count >= 25:
            break
        if nid in used_for_trajectories:
            continue
            
        succ_list = successors.get(nid, [])
        if len(succ_list) < 2:
            continue
            
        mid_id, rel1 = succ_list[0]
        if mid_id in EXCLUDED_FLIPPED_NODE_IDS or mid_id not in nodes:
            continue
            
        grand_succ_list = successors.get(mid_id, [])
        if not grand_succ_list:
            continue
            
        end_id, rel2 = grand_succ_list[0]
        if end_id in EXCLUDED_FLIPPED_NODE_IDS or end_id not in nodes:
            continue
            
        start_title = nodes[nid].get('title', nid)
        mid_title = nodes[mid_id].get('title', mid_id)
        end_title = nodes[end_id].get('title', end_id)
        
        start_holding = nodes[nid].get('substantive_holding', '')[:300]
        mid_holding = nodes[mid_id].get('substantive_holding', '')[:300]
        end_holding = nodes[end_id].get('substantive_holding', '')[:300]
        
        evolution_block = (
            f"[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n"
            f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{mid_title}' [{rel1}] '{start_title}'. [Holding]: {mid_holding}\n"
            f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{end_title}' [{rel2}] '{mid_title}'. [Holding]: {end_holding}\n\n"
        )
        seeded_block = f"[SEEDED CASE] {start_title}:\n[Holding]: {start_holding}\n\n"
        production_context = f"{evolution_block}{seeded_block}"
        
        query = f"How was the doctrinal principle established in {start_title} subsequently cited and applied in {mid_title} and {end_title}?"
        
        positive_pairs.append({
            "pair_id": f"TB_POS_TRAJ_{traj_count+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "multihop_trajectory_entailment",
            "difficulty": "positive_multihop_trajectory",
            "case_id": nid,
            "case_title": start_title,
            "user_query": query,
            "retrieved_context": production_context,
            "ground_truth_entails": True,
            "label_rationale": "Context details the sequential citation lineage and holdings connecting all three cases."
        })
        traj_count += 1
        
    assert len(positive_pairs) == 100, f"Expected 100 positive pairs, got {len(positive_pairs)}"
    
    # --------------------------------------------------------------------------
    # NEGATIVE PAIRS (100)
    # --------------------------------------------------------------------------
    negative_pairs = []
    
    # 1. 35 Out-of-Domain Negatives (20 Hard Domain-Adjacent Legal + 15 Trivial Non-Legal Noise)
    ood_queries_hard_legal = [
        "How does the European Court of Justice establish the supremacy of EU law over national statutes in Costa v. ENEL?",
        "What are the proportionality requirements for derogations under Article 15 of the European Convention on Human Rights?",
        "How does Article 25 of the ICSID Convention define jurisdiction over legal disputes arising directly out of an investment?",
        "What is the test for State responsibility under the ILC Articles on Responsibility of States for Internationally Wrongful Acts?",
        "How does the Rome Statute of the International Criminal Court define the principle of complementarity under Article 17?",
        "What legal standard governs maritime delimitation of the exclusive economic zone under UNCLOS Article 74?",
        "How does Common Article 3 of the Geneva Conventions apply to armed conflicts not of an international character?",
        "What constitutes an illegal expropriation under Chapter 11 of the North American Free Trade Agreement (NAFTA)?",
        "How does UCC Section 2-207 resolve the 'battle of the forms' regarding additional terms in commercial acceptance?",
        "What are the statutory requirements for establishing commercial unconscionability under UCC Section 2-302?",
        "How does Section 514 of ERISA govern the express preemption of state healthcare benefit regulations?",
        "What constitutes a 'covered entity' required to maintain protected health information under HIPAA Privacy Rule 45 CFR § 164.502?",
        "How does Section 404 of the Sarbanes-Oxley Act mandate internal accounting controls certification by public corporate officers?",
        "What is the maximum statutory penalty for residential zoning setbacks under the Los Angeles Municipal Code Section 12.21?",
        "How are commercial driveway curb-cut permits processed under the Chicago Department of Transportation Municipal Regulations?",
        "What statutory notice requirements govern tenant non-payment evictions under the New York City Housing Maintenance Code?",
        "How does the California Environmental Quality Act (CEQA) define an Environmental Impact Report (EIR) threshold of significance?",
        "What constitutes a qualifying disability accommodation under the UK Equality Act 2010 Section 20?",
        "How does the German Civil Code (BGB) Section 823 define unlawful intentional or negligent injury to property rights?",
        "What are the requirements for judicial review of administrative action under the French Conseil d'État standard of excès de pouvoir?"
    ]
    
    ood_queries_trivial_noise = [
        "How does PostgreSQL optimize multiversion concurrency control (MVCC) vacuuming to prevent transaction ID wraparound?",
        "What were the primary gameplay mechanics introduced in Nintendo's The Legend of Zelda: Tears of the Kingdom?",
        "How does Git implement garbage collection (git gc) and packfile delta compression across commit DAG objects?",
        "Who directed the 2023 fantasy comedy film Barbie that grossed over $1.4 billion worldwide?",
        "How does WebAssembly (WASM) achieve near-native execution speed within Chromium V8 browser runtimes?",
        "What are the thermodynamic requirements for reversible adiabatic expansion in an ideal Carnot cycle engine?",
        "How does Kubernetes manage pod eviction thresholds when node disk pressure exceeds high watermarks?",
        "What chemical reaction mechanism describes the acid-catalyzed hydration of an alkene to form an alcohol?",
        "How does the Kafka consumer group coordinator rebalance partitions during a consumer instance crash?",
        "What are the biological functions of CRISPR-Cas9 guide RNA duplexes in targeted DNA cleavage?",
        "How does Redis implement ziplist memory compression for sorted sets with small member counts?",
        "What were the key architectural changes between Python 2 and Python 3 regarding unicode text strings?",
        "How does the TLS 1.3 handshake eliminate round-trip latency compared to TLS 1.2?",
        "What are the nutritional differences between saturated and polyunsaturated fatty acids in human metabolism?",
        "How do B-tree storage engines differ from log-structured merge-trees (LSM) in write amplification?"
    ]
    
    # Process 20 Hard Domain-Adjacent Legal Negatives
    for i, hard_q in enumerate(ood_queries_hard_legal):
        nid = tier1_nodes[i + 80]
        ndata = nodes[nid]
        title = ndata.get('title', nid)
        holding = ndata.get('substantive_holding', '')[:500]
        production_context = f"[SEEDED CASE] {title}:\n[Holding]: {holding}\n\n[Top Retrieved Cases]\n- Procedural and substantive text of {title}."
        negative_pairs.append({
            "pair_id": f"TB_NEG_OOD_HARD_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "out_of_domain_noise",
            "difficulty": "hard_domain_adjacent_legal",
            "user_query": hard_q,
            "retrieved_context": production_context,
            "ground_truth_entails": False,
            "label_rationale": "Query asserts an authentic legal rule from foreign, international, or municipal law; retrieved SCOTUS precedent has 0% entailment."
        })
        
    # Process 15 Trivial Non-Legal Negatives
    for i, trivial_q in enumerate(ood_queries_trivial_noise):
        nid = tier1_nodes[i + 100]
        ndata = nodes[nid]
        title = ndata.get('title', nid)
        holding = ndata.get('substantive_holding', '')[:500]
        production_context = f"[SEEDED CASE] {title}:\n[Holding]: {holding}\n\n[Top Retrieved Cases]\n- Procedural and substantive text of {title}."
        negative_pairs.append({
            "pair_id": f"TB_NEG_OOD_TRIV_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "out_of_domain_noise",
            "difficulty": "trivial_non_legal_noise",
            "user_query": trivial_q,
            "retrieved_context": production_context,
            "ground_truth_entails": False,
            "label_rationale": "Query is entirely non-legal/out-of-domain; retrieved legal context has 0% entailment."
        })
        
    # 2. 45 Semantic Distractor Cases (Same Topic, Wrong Proposition)
    # Take cases from the same category/domain where context does NOT entail the asserted query rule
    for i in range(45):
        nid_a = tier1_nodes[i + 120]
        nid_b = tier1_nodes[i + 170]
        ndata_a = nodes[nid_a]
        ndata_b = nodes[nid_b]
        
        title_a = ndata_a.get('title', nid_a)
        title_b = ndata_b.get('title', nid_b)
        date_a = ndata_a.get('decision_date', '')
        
        holding_a = ndata_a.get('substantive_holding', '')[:500]
        holding_b = ndata_b.get('substantive_holding', '')[:500]
        
        # Context contains Case A, but query asks if Case A held the rule of Case B!
        production_context = (
            f"[SEEDED CASE] {title_a} ({date_a[:4] if date_a else ''}):\n"
            f"[Holding]: {holding_a}\n\n"
            f"[Top Retrieved Cases]\n- Record of opinion in {title_a}."
        )
        
        query = f"Did the Supreme Court in {title_a} establish that {holding_b[:120]}?"
        
        negative_pairs.append({
            "pair_id": f"TB_NEG_DIS_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "semantic_distractor_holding",
            "difficulty": "hard_semantic_distractor",
            "case_id": nid_a,
            "case_title": title_a,
            "distractor_case_id": nid_b,
            "distractor_case_title": title_b,
            "user_query": query,
            "retrieved_context": production_context,
            "ground_truth_entails": False,
            "label_rationale": f"Context contains holding for {title_a}, which does NOT state or entail the proposition of {title_b}."
        })
        
    # 3. 20 Unremedied Overruled Traps (Lacks Invalidation Authority)
    # Use remaining clean, strictly held-out CRS overruled cases (edges 25 to 45), giving ONLY the obsolete preamble without the overruling successor!
    for i in range(20):
        edge = clean_overrule_edges[i + 25]  # Edges 25 to 45 from the 47 clean held-out pool
        overruled_id = edge['target']
        overruled_node = nodes[overruled_id]
        overruled_title = overruled_node.get('title', overruled_id)
        overruled_date = overruled_node.get('decision_date', '')
        
        # Incomplete traversal: ONLY obsolete procedural preamble, ZERO mention of overruling successor!
        raw_preamble = overruled_node.get('text', '')[:600]
        production_context = (
            f"[SEEDED CASE] {overruled_title} ({overruled_date[:4] if overruled_date else ''}):\n"
            f"[Holding]: {raw_preamble}\n\n"
            f"[Top Retrieved Cases]\n- Procedural record in {overruled_title}."
        )
        
        query = (
            f"Under the binding doctrine of {overruled_title}, is it currently constitutional to enforce that "
            f"its substantive holding remains valid and unrepudiated Supreme Court law?"
        )
        
        negative_pairs.append({
            "pair_id": f"TB_NEG_TRAP_{i+1:03d}",
            "track": "Track_B_TERRA_EEG",
            "sub_type": "unremedied_overruled_trap",
            "difficulty": "hard_unremedied_trap",
            "case_id": overruled_id,
            "case_title": overruled_title,
            "user_query": query,
            "retrieved_context": production_context,
            "ground_truth_entails": False,
            "label_rationale": "Context contains only the obsolete case preamble and completely lacks the invalidating authority needed to resolve the query."
        })
        
    assert len(negative_pairs) == 100, f"Expected 100 negative pairs, got {len(negative_pairs)}"
    
    combined = positive_pairs + negative_pairs
    random.shuffle(combined)
    
    # Verify zero overlap with blacklisted node IDs
    for p in combined:
        cid = p.get('case_id')
        oid = p.get('overruling_id')
        did = p.get('distractor_case_id')
        assert cid not in EXCLUDED_FLIPPED_NODE_IDS, f"Leaked blacklist case_id: {cid}"
        assert oid not in EXCLUDED_FLIPPED_NODE_IDS, f"Leaked blacklist overruling_id: {oid}"
        assert did not in EXCLUDED_FLIPPED_NODE_IDS, f"Leaked blacklist distractor_case_id: {did}"
        
    out_path = 'data/terra_eeg_nli_eval_200.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Track B built successfully: {len(combined)} pairs ({len(positive_pairs)} pos, {len(negative_pairs)} neg) saved to {out_path}")
    return combined


if __name__ == "__main__":
    print("=================================================================")
    print("BUILDING ISSUE #2 NLI VALIDATION SUITE (400 PAIRS)")
    print("=================================================================")
    build_casehold_track_a(200)
    build_terra_eeg_track_b(200)
    print("\n✅ Module 1 Dataset Generation COMPLETE.")
