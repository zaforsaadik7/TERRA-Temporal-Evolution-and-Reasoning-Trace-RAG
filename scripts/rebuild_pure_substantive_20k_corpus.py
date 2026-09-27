import os
import sys
import json
import time
import random
import requests
import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock
from collections import defaultdict, Counter

# 1. Suppress eyecite and library warnings & mock fast_diff_match_patch
import logging, warnings
warnings.filterwarnings("ignore")
logging.getLogger("eyecite").setLevel(logging.CRITICAL)
sys.modules['fast_diff_match_patch'] = MagicMock()
import eyecite

import chromadb
import networkx as nx

print("=== REBUILDING PURE SUBSTANTIVE 20,000-CASE CORPUS & EEG GRAPH ===\n")

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

cache_dir = Path("dataset_20k_cap/volume_metadata_cache")
raw_dir = Path("dataset_20k_cap/raw_cases")
manifest_path = Path("dataset_20k_cap/manifests/selection_manifest_20k.json")
output_index_path = Path("dataset_20k_cap/terra_eeg_index_20k.json")
vector_db_path = Path("dataset_20k_cap/vector_db_20k")

# Doctrinal classification lexicons
DOCTRINAL_LEXICONS = {
    "first_amendment": [
        "first amendment", "free speech", "freedom of speech", "freedom of the press",
        "establishment clause", "free exercise", "censorship", "obscenity", "libel", "defamation", "religion"
    ],
    "criminal_procedure": [
        "fourth amendment", "search and seizure", "warrant", "probable cause",
        "fifth amendment", "self-incrimination", "double jeopardy", "sixth amendment",
        "right to counsel", "habeas corpus", "miranda", "confession", "jury trial"
    ],
    "commerce_clause_economic": [
        "commerce clause", "interstate commerce", "sherman act", "antitrust", "monopoly",
        "clayton act", "trade regulation", "fair labor", "nlrb", "labor relations",
        "interstate commerce commission", "icc"
    ],
    "admin_law_federal_courts": [
        "administrative", "statutory interpretation", "jurisdiction", "standing",
        "exhaustion", "agency", "judicial review", "mandamus", "sovereign immunity",
        "federal question", "diversity of citizenship"
    ],
    "substantive_private_law": [
        "patent", "copyright", "trademark", "admiralty", "maritime", "internal revenue",
        "income tax", "taxation", "bankruptcy", "contract"
    ]
}

CIVIL_RIGHTS_KW = [
    "equal", "civil", "rights", "segregat", "fourteenth", "14th", "amendment",
    "due process", "discrimination", "school", "negro", "race", "racial", "state", "board"
]

def classify_doctrine(title, full_text):
    text_lower = (title + " " + full_text[:4000]).lower()
    
    # Check civil rights / 14th Amendment first
    tags = []
    if any(kw in text_lower for kw in CIVIL_RIGHTS_KW):
        tags.append("civil_rights_equal_protection")
        
    for domain, kws in DOCTRINAL_LEXICONS.items():
        if any(kw in text_lower for kw in kws):
            tags.append(domain)
            
    if not tags:
        tags.append("general_constitutional_statutory")
        
    # Primary category
    primary = tags[0]
    return primary, tags

def build_structured_trace(title, date, primary_cat):
    d_str = date[:4] if date and len(date) >= 4 else "Historical"
    cat_label = primary_cat.replace("_", " ").title()
    return (
        f"Thinking Trace — {title} ({d_str}): "
        f"Step 1: Identify operative legal and constitutional question under {cat_label} jurisprudence. "
        f"Step 2: Scrutinize governing Supreme Court precedent, historical canons, and statutory text. "
        f"Step 3: Evaluate factual record under binding standards of appellate review. "
        f"Step 4: Harmonize conflicting doctrines, distinguish non-controlling authority, and resolve claims. "
        f"Step 5: Pronounce holding, enter judgment, and transmit mandate."
    )

def parse_case_citations(node_id, full_text, cite_to_node):
    extracted = []
    if not full_text:
        return extracted
    try:
        cites = eyecite.get_citations(full_text)
        for c in cites:
            matched = (c.corrected_citation() if hasattr(c, 'corrected_citation') else c.matched_text()).strip()
            if matched in cite_to_node:
                target_id = cite_to_node[matched]
                if target_id != node_id:
                    extracted.append((node_id, target_id))
    except Exception:
        pass
    return extracted

def main():
    t0 = time.time()
    
    # 1. Gather all candidates across volumes 50-448
    vols = sorted([int(f.stem.split('_')[1]) for f in cache_dir.glob("vol_*.json")])
    print(f"Scanning candidate metadata across {len(vols)} volumes...")
    
    civil_candidates = []
    other_substantive_candidates = []
    
    for v in vols:
        with open(cache_dir / f"vol_{v}.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
        for c in cases:
            fname = c.get("file_name")
            char_cnt = c.get("analysis", {}).get("char_count", 0)
            if char_cnt < 4000:
                continue # STRICTLY EXCLUDE ALL PROCEDURAL CERT-DENIAL ENTRIES (<4000 chars)
                
            node_id = f"{v}_{fname}"
            c_name = (c.get("name", "") + " " + c.get("name_abbreviation", "")).lower()
            
            entry = {
                "id": c.get("id"),
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
            
            if any(kw in c_name for kw in CIVIL_RIGHTS_KW):
                civil_candidates.append(entry)
            else:
                other_substantive_candidates.append(entry)
                
    print(f"Total Substantive Candidates Found (char_count >= 4000):")
    print(f"  - Civil Rights: {len(civil_candidates):,}")
    print(f"  - Other Substantive: {len(other_substantive_candidates):,}")
    print(f"  - Total Available: {len(civil_candidates) + len(other_substantive_candidates):,}")
    
    # Selection: All 5,972 civil rights + 14,028 other substantive = Exactly 20,000 substantive opinions
    selected_civil = list(civil_candidates)
    needed_other = 20000 - len(selected_civil)
    print(f"\nSelecting all {len(selected_civil):,} civil rights opinions and sampling {needed_other:,} other substantive opinions...")
    selected_other = random.sample(other_substantive_candidates, needed_other)
    
    final_cases = selected_civil + selected_other
    assert len(final_cases) == 20000, f"Expected 20,000 cases, got {len(final_cases)}"
    print(f"Total Selected 100% Substantive Opinions: {len(final_cases):,}")
    
    # 2. Download missing cases
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=35, pool_maxsize=35, max_retries=3)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    to_download = []
    for c in final_cases:
        target_path = raw_dir / f"{c['node_id']}.json"
        if not (target_path.exists() and target_path.stat().st_size > 50):
            to_download.append(c)
            
    print(f"\nCases to download: {len(to_download):,}")
    if to_download:
        def dl_worker(entry):
            target_path = raw_dir / f"{entry['node_id']}.json"
            try:
                r = session.get(entry["download_url"], timeout=15)
                if r.status_code == 200:
                    with open(target_path, "w", encoding="utf-8") as out:
                        out.write(r.text)
                    return True
            except Exception:
                pass
            return False
            
        t_dl = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as ex:
            results = list(ex.map(dl_worker, to_download))
        print(f"Downloaded {sum(results):,}/{len(to_download):,} cases in {time.time() - t_dl:.1f}s.")
        
    # 3. Build Citation Lookup Table & Node Metadata
    print("\nBuilding citation lookup table and classifying doctrinal domains...")
    cite_to_node = {}
    node_date_map = {}
    nodes = {}
    cases_for_eyecite = []
    manifest_entries = []
    
    for c in final_cases:
        nid = c["node_id"]
        node_date_map[nid] = c.get("decision_date") or ""
        for cit in c.get("citations", []):
            if isinstance(cit, dict) and cit.get("cite"):
                cite_to_node[cit["cite"].strip()] = nid
            elif isinstance(cit, str):
                cite_to_node[cit.strip()] = nid

    print(f"Indexed {len(cite_to_node):,} official citations.")
    
    # Process opinions and classify
    domain_counts = defaultdict(int)
    
    for c in final_cases:
        nid = c["node_id"]
        raw_path = raw_dir / f"{nid}.json"
        if not raw_path.exists():
            continue
            
        with open(raw_path, "r", encoding="utf-8") as rf:
            cdata = json.load(rf)
            
        title = cdata.get("name_abbreviation") or cdata.get("name") or c.get("name_abbreviation") or "Unknown Case"
        date = cdata.get("decision_date") or c.get("decision_date") or ""
        court = cdata.get("court", {}).get("name", "U.S. Supreme Court")
        
        cbody = cdata.get("casebody", {})
        opinions = cbody.get("opinions", []) if isinstance(cbody, dict) and isinstance(cbody.get("opinions"), list) else []
        full_text = "\n\n".join([op.get("text", "") for op in opinions if op.get("text")]).strip()
        
        # Classify doctrine
        primary_cat, doctrinal_tags = classify_doctrine(title, full_text)
        domain_counts[primary_cat] += 1
        
        trace_text = build_structured_trace(title, date, primary_cat)
        cits = [cit.get("cite") for cit in c.get("citations", []) if isinstance(cit, dict)]
        
        node_info = {
            "node_id": nid,
            "title": title,
            "decision_date": date,
            "court": court,
            "category": primary_cat,
            "doctrinal_tags": doctrinal_tags,
            "char_count": c.get("char_count", len(full_text)),
            "thinking_trace": trace_text,
            "citations": cits,
            "edges_count": 0,
            "text": full_text[:3000] if full_text else title
        }
        nodes[nid] = node_info
        cases_for_eyecite.append((nid, full_text, date))
        
        # Manifest entry
        man_entry = dict(c)
        if "node_id" in man_entry:
            del man_entry["node_id"]
        man_entry["category"] = primary_cat
        man_entry["doctrinal_tags"] = doctrinal_tags
        manifest_entries.append(man_entry)
        
    print(f"\nCompiled {len(nodes):,} 100% substantive nodes.")
    print("Persisted Doctrinal Distribution (Primary Categories):")
    for dom, cnt in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  - {dom:35s}: {cnt:5,d} ({cnt/len(nodes)*100:5.1f}%)")
        
    # Write updated manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)
    print(f"Manifest written to: {manifest_path}")

    # 4. Extract Citation Edges
    print(f"\nExtracting citation edges across all {len(cases_for_eyecite):,} substantive cases (20 workers)...")
    def worker(item):
        nid, txt, dt = item
        return parse_case_citations(nid, txt, cite_to_node)
        
    t_cite = time.time()
    raw_edges = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for idx, edges_list in enumerate(executor.map(worker, cases_for_eyecite), 1):
            raw_edges.extend(edges_list)
            if idx % 5000 == 0 or idx == len(cases_for_eyecite):
                print(f"  Processed {idx:5d}/{len(cases_for_eyecite)} cases | Raw edges: {len(raw_edges):,}")
    print(f"Citation parsing finished in {time.time() - t_cite:.1f}s. Total raw citation mentions: {len(raw_edges):,}")

    # 5. Deduplicate and Filter Edges (Preserving Temporal Directionality)
    print("\nDeduplicating unique directed pairs and enforcing temporal directionality...")
    unique_edges = set()
    temporal_reversals = 0

    for src, tgt in raw_edges:
        if src not in nodes or tgt not in nodes or src == tgt:
            continue
        d_src = node_date_map.get(src, "")
        d_tgt = node_date_map.get(tgt, "")
        if d_src and d_tgt and len(d_src) >= 4 and len(d_tgt) >= 4:
            y_src = int(d_src[:4])
            y_tgt = int(d_tgt[:4])
            if y_src < y_tgt:
                temporal_reversals += 1
                continue
        unique_edges.add((src, tgt))

    print(f"Raw citation mentions: {len(raw_edges):,}")
    print(f"Deduplicated unique directed edges: {len(unique_edges):,} (Filtered {temporal_reversals:,} temporal reversals)")

    formatted_edges = [{"source": s, "target": t, "relation": "CITES"} for s, t in sorted(unique_edges)]

    # Update edge counts on nodes
    edge_counts = Counter()
    for s, t in unique_edges:
        edge_counts[s] += 1
        edge_counts[t] += 1
    for nid, ninfo in nodes.items():
        ninfo["edges_count"] = edge_counts[nid]

    # 6. Graph Topology Metrics
    print("\nComputing Graph Topology Metrics (NetworkX)...")
    G = nx.DiGraph()
    for nid in nodes:
        G.add_node(nid)
    for s, t in unique_edges:
        G.add_edge(s, t)

    total_opinions = G.number_of_nodes()
    total_edges = G.number_of_edges()
    density = nx.density(G)
    avg_degree = total_edges / total_opinions if total_opinions else 0.0

    wcc = list(nx.weakly_connected_components(G))
    largest_wcc = max(len(c) for c in wcc) if wcc else 0
    largest_wcc_pct = (largest_wcc / total_opinions * 100.0) if total_opinions else 0.0

    scc = list(nx.strongly_connected_components(G))
    largest_scc = max(len(c) for c in scc) if scc else 0

    G_undir = G.to_undirected()
    degrees = dict(G_undir.degree())
    mean_deg = sum(degrees.values()) / total_opinions if total_opinions else 0.0
    max_node = max(degrees, key=degrees.get)
    max_deg = degrees[max_node]
    max_title = nodes.get(max_node, {}).get("title", "")

    print(f"\nFinal Substantive Graph Topology Summary:")
    print(f"  - Total Opinions (Nodes): {total_opinions:,}")
    print(f"  - Unique Directed Precedent Edges: {total_edges:,}")
    print(f"  - Graph Density: {density:.6f}")
    print(f"  - Average In/Out Degree: {avg_degree:.4f}")
    print(f"  - Mean Undirected Degree: {mean_deg:.2f}")
    print(f"  - Max Degree Hub Node: {max_deg} ({max_title})")
    print(f"  - Weakly Connected Components: {len(wcc):,}")
    print(f"  - Largest WCC: {largest_wcc:,} ({largest_wcc_pct:.2f}%)")
    print(f"  - Strongly Connected Components: {len(scc):,}")
    print(f"  - Largest SCC: {largest_scc:,}")

    # 7. Write out EEG Index
    index_data = {
        "nodes": nodes,
        "edges": formatted_edges,
        "total_nodes": len(nodes),
        "total_edges": len(formatted_edges),
        "graph_density": density,
        "average_degree": avg_degree,
        "largest_wcc_size": largest_wcc,
        "largest_wcc_pct": round(largest_wcc_pct, 2),
        "largest_scc_size": largest_scc,
        "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
    with open(output_index_path, "w", encoding="utf-8") as out:
        json.dump(index_data, out, indent=2)
    print(f"\nEEG Index successfully written to: {output_index_path}")

    # 8. Rebuild ChromaDB Vector Store
    print(f"\nConnecting to ChromaDB at: {vector_db_path}...")
    chroma_client = chromadb.PersistentClient(path=str(vector_db_path))
    try:
        chroma_client.delete_collection(name="thinking_traces")
    except Exception:
        pass
    collection = chroma_client.create_collection(name="thinking_traces")

    print(f"Populating ChromaDB with {len(nodes):,} pure substantive thinking traces...")
    batch_size = 500
    all_node_items = list(nodes.items())
    for b_idx in range(0, len(all_node_items), batch_size):
        batch = all_node_items[b_idx:b_idx + batch_size]
        docs, metas, ids = [], [], []
        for nid, ninfo in batch:
            title = ninfo.get("title", "Case")
            date = ninfo.get("decision_date", "")
            d_str = date[:4] if date else "Historical"
            trace = ninfo.get("thinking_trace", "")
            text_snip = ninfo.get("text", "")[:1000]

            doc_text = f"{title} ({d_str})\nThinking Trace: {trace}\nOpinion Snippet: {text_snip}"
            docs.append(doc_text)
            metas.append({
                "node_id": nid,
                "title": title,
                "date": date,
                "category": ninfo.get("category", "substantive"),
                "primary_domain": ninfo.get("category", "substantive"),
                "doctrinal_tags": ",".join(ninfo.get("doctrinal_tags", [])),
                "char_count": ninfo.get("char_count", 0)
            })
            ids.append(nid)

        collection.upsert(documents=docs, metadatas=metas, ids=ids)
        if (b_idx + len(batch)) % 5000 == 0 or (b_idx + len(batch)) == len(all_node_items):
            print(f"  ChromaDB Upserted: {b_idx + len(batch):5d}/{len(all_node_items):5d} documents")

    print(f"ChromaDB Collection count: {collection.count():,}")
    print(f"\n=== PURE SUBSTANTIVE 20,000 CORPUS REBUILD COMPLETED IN {time.time() - t0:.1f}s ===")

if __name__ == "__main__":
    main()
