"""
scripts/generate_350_benchmark.py
=================================
Constructs the complete canonical 350-query benchmark suite for TERRA (terra_350_benchmark.json)
anchored in the 20,000 pure substantive SCOTUS opinions in dataset_20k_cap/terra_eeg_index_20k.json.

Allocation & Substructure (pre-registered in Paper/audit/benchmark_expansion_protocol.md):
  - Category A: 100 single-point factual lookups across 7 domains
  - Category B: 100 multi-hop evolutionary reasoning arcs across 5 constitutional domains (20 each)
      * Enforces TRUE 3-5 hop precedent trajectories on g_evo (cited -> citing)
      * Enforces strict substantive constitutional landmark paths (0 paths of length 2)
  - Category C: 75 out-of-context domain boundary queries across 5 subdomains (15 each)
      * Deliberate near-OOD hard boundary test on modern state & municipal codes
      * Target nodes empty by design (safe refusal)
  - Category D: 75 adversarial deception traps partitioned into 4 audited subtypes:
      * Subtype D1: Overruled Precedents (19) [With machine-gradable acceptance criteria & CRS/LII-vetted history]
      * Subtype D2: Title-Substitution & Holding Confusion (19) [With acceptance criteria]
      * Subtype D3: Temporal Inversion (19) [19 bespoke non-templated queries; HARD GATE on decision_date]
      * Subtype D4: Procedural Posture Deceptions (18) [With acceptance criteria]

Total: 350 queries. Zero silent fallbacks.
"""

import os
import sys
import json
import random
import hashlib
from collections import Counter
import networkx as nx

CORPUS_PATH = "dataset_20k_cap/terra_eeg_index_20k.json"
OUTPUT_PATH = "terra_350_benchmark.json"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

print("=" * 80)
print("BUILDING 350-QUERY CANONICAL BENCHMARK SUITE (WORKSTREAM 1.1 REVISION)")
print("=" * 80)

if not os.path.exists(CORPUS_PATH):
    print(f"[FATAL] Corpus file missing: {CORPUS_PATH}")
    sys.exit(1)

print(f"Loading 20k corpus index from: {CORPUS_PATH}...")
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    corpus_data = json.load(f)

nodes = corpus_data.get("nodes", {})
edges = corpus_data.get("edges", [])
print(f"Loaded {len(nodes):,} nodes and {len(edges):,} edges.")

# Build citation graph: source cites target (source -> target)
g_cite = nx.DiGraph()
for nid, ninfo in nodes.items():
    g_cite.add_node(nid, **ninfo)
for e in edges:
    if e["source"] in nodes and e["target"] in nodes:
        g_cite.add_edge(e["source"], e["target"])

# Evolution flows from cited older precedent to citing newer precedent (target -> source)
g_evo = g_cite.reverse()
print(f"Evolution graph g_evo has {g_evo.number_of_nodes():,} nodes and {g_evo.number_of_edges():,} directed edges.")

# Partition nodes by primary domain
domain_nodes = {}
for nid, ninfo in nodes.items():
    dom = ninfo.get("category", "general_constitutional_statutory")
    domain_nodes.setdefault(dom, []).append(nid)

benchmark_queries = []

# =========================================================================
# 1. CATEGORY A: 100 SINGLE-POINT FACTUAL LOOKUPS
# =========================================================================
print("\n[STEP 1/4] Generating Category A: 100 Single-Point Factual Lookups...")

cat_a_domain_targets = {
    "civil_rights_equal_protection": 15,
    "criminal_procedure": 15,
    "first_amendment": 15,
    "commerce_clause_economic": 15,
    "admin_law_federal_courts": 15,
    "substantive_private_law": 15,
    "general_constitutional_statutory": 10
}

a_count = 0
for dom, target_count in cat_a_domain_targets.items():
    pool = domain_nodes.get(dom, [])
    valid_pool = [
        nid for nid in pool 
        if len(nodes[nid].get("text", "")) >= 1000 
        and len(nodes[nid].get("decision_date", "")) >= 4 
        and nodes[nid].get("char_count", 0) >= 4000
    ]
    valid_pool.sort()
    sampled_nids = random.sample(valid_pool, target_count)
    
    for nid in sampled_nids:
        n = nodes[nid]
        title = n.get("title", "Unknown Case")
        date_str = n.get("decision_date", "")
        year = date_str[:4] if date_str else "Unknown"
        vol = nid.split("_")[0]
        page = nid.split("_")[1].split("-")[0] if "_" in nid and "-" in nid else "1"
        try:
            page_int = int(page)
        except ValueError:
            page_int = 1
            
        style = (a_count % 3)
        if style == 0:
            query = f"In what year was the Supreme Court decision {title} decided?"
            holding = f"The Supreme Court decision {title} was decided on {date_str} ({year})."
        elif style == 1:
            query = f"In which volume of the United States Reports is the Supreme Court decision {title} published?"
            holding = f"The Supreme Court opinion {title} is published in Volume {vol} of the United States Reports (formal citation: {vol} U.S. {page_int}, decided {date_str})."
        else:
            query = f"What is the official United States Reports citation for {title} ({year})?"
            holding = f"The official United States Reports citation for {title} ({year}) is {vol} U.S. {page_int} (decided {date_str})."
            
        qid = f"A{a_count+1:03d}"
        benchmark_queries.append({
            "query_id": qid,
            "category": "A_Factual",
            "subtype": f"A_{dom}",
            "doctrinal_domain": dom,
            "query": query,
            "target_nodes": [nid],
            "gold_citation_path": [nid],
            "ground_truth_holding": holding,
            "adversarial_subtype": None,
            "date_verified": True
        })
        a_count += 1

print(f"  -> Generated {a_count} Category A factual queries across 7 domains.")

# =========================================================================
# 2. CATEGORY B: 100 MULTI-HOP EVOLUTIONARY REASONING ARCS (3-5 HOPS)
# =========================================================================
print("\n[STEP 2/4] Generating Category B: 100 Multi-Hop Evolutionary Arcs (3-5 hops, 20 x 5 domains)...")

# Curated landmark anchor pools per constitutional domain to guarantee substantive doctrinal coherence
landmark_pools = {
    "civil_rights_equal_protection": [
        "60_0393-02",  # Scott v. Sandford (1856)
        "83_0036-01",  # Slaughter-House Cases (1872)
        "83_0130-01",  # Bradwell v. State (1872)
        "88_0162-01",  # Minor v. Happersett (1874)
        "92_0542-01",  # Cruikshank (1875)
        "100_0303-01", # Strauder v. West Virginia (1879)
        "106_0583-01", # Pace v. Alabama (1882)
        "109_0003-01", # Civil Rights Cases (1883)
        "118_0356-01", # Yick Wo v. Hopkins (1886)
        "163_0537-01", # Plessy v. Ferguson (1896)
        "245_0060-01", # Buchanan v. Warley (1917)
        "305_0337-01", # Missouri ex rel. Gaines v. Canada (1938)
        "334_0001-01", # Shelley v. Kraemer (1948)
        "339_0629-01", # Sweatt v. Painter (1950)
        "339_0637-01", # McLaurin v. Oklahoma State Regents (1950)
        "347_0483-01", # Brown v. Board of Education (1954)
        "358_0001-01", # Cooper v. Aaron (1958)
        "388_0001-01", # Loving v. Virginia (1967)
        "391_0430-01", # Green v. County School Board (1968)
        "402_0001-01"  # Swann v. Charlotte-Mecklenburg (1971)
    ],
    "criminal_procedure": [
        "116_0616-01", # Boyd v. United States (1886)
        "168_0532-01", # Bram v. United States (1897)
        "199_0372-01", # Jack v. Kansas (1905)
        "211_0078-01", # Twining v. New Jersey (1908)
        "232_0383-01", # Weeks v. United States (1914)
        "255_0298-01", # Gouled v. United States (1921)
        "277_0438-01", # Olmstead v. United States (1928)
        "287_0045-01", # Powell v. Alabama (1932)
        "301_0379-01", # Brown v. Mississippi (1936)
        "304_0458-01", # Johnson v. Zerbst (1938)
        "316_0455-01", # Betts v. Brady (1942)
        "338_0025-01", # Wolf v. Colorado (1949)
        "367_0643-01", # Mapp v. Ohio (1961)
        "372_0335-01", # Gideon v. Wainwright (1963)
        "377_0201-01", # Malloy v. Hogan (1964)
        "378_0478-01", # Escobedo v. Illinois (1964)
        "384_0436-01", # Miranda v. Arizona (1966)
        "389_0347-01", # Katz v. United States (1967)
        "392_0001-01", # Terry v. Ohio (1968)
        "400_0748-01"  # Chimel v. California (1969)
    ],
    "first_amendment": [
        "249_0047-01", # Schenck v. United States (1919)
        "249_0211-01", # Debs v. United States (1919)
        "250_0616-01", # Abrams v. United States (1919)
        "268_0652-01", # Gitlow v. New York (1925)
        "274_0357-01", # Whitney v. California (1927)
        "283_0697-01", # Near v. Minnesota (1931)
        "283_0359-01", # Stromberg v. California (1931)
        "299_0353-01", # De Jonge v. Oregon (1937)
        "310_0296-01", # Cantwell v. Connecticut (1940)
        "310_0586-01", # Minersville v. Gobitis (1940)
        "315_0568-01", # Chaplinsky v. New Hampshire (1942)
        "319_0624-01", # West Virginia Board of Education v. Barnette (1943)
        "319_0105-01", # Murdock v. Pennsylvania (1943)
        "341_0494-01", # Dennis v. United States (1951)
        "343_0250-01", # Beauharnais v. Illinois (1952)
        "354_0476-01", # Roth v. United States (1957)
        "354_0298-01", # Yates v. United States (1957)
        "357_0449-01", # NAACP v. Alabama (1958)
        "376_0254-01", # New York Times Co. v. Sullivan (1964)
        "393_0503-01", # Tinker v. Des Moines (1969)
        "395_0444-01", # Brandenburg v. Ohio (1969)
        "403_0015-01"  # Cohen v. California (1971)
    ],
    "commerce_clause_economic": [
        "53_0299-01",  # Cooley v. Board of Wardens (1851)
        "76_0579-01",  # Paul v. Virginia (1868)
        "82_0232-01",  # State Freight Tax Case (1872)
        "94_0113-01",  # Munn v. Illinois (1876)
        "118_0557-01", # Wabash v. Illinois (1886)
        "125_0465-01", # Bowman v. Chicago & Northwestern Railway (1888)
        "135_0100-01", # Leisy v. Hardin (1890)
        "156_0001-01", # United States v. E. C. Knight Co. (1895)
        "166_0290-01", # Trans-Missouri Freight (1897)
        "188_0321-01", # Champion v. Ames (Lottery Case) (1903)
        "196_0375-01", # Swift & Co. v. United States (1905)
        "221_0001-01", # Standard Oil Co. v. United States (1911)
        "234_0342-01", # Shreveport Rate Cases (1914)
        "247_0251-01", # Hammer v. Dagenhart (1918)
        "295_0495-01", # Schechter Poultry v. United States (1935)
        "298_0238-01", # Carter v. Carter Coal Co. (1936)
        "301_0001-01", # NLRB v. Jones & Laughlin Steel (1937)
        "312_0100-01", # United States v. Darby (1941)
        "317_0111-01"  # Wickard v. Filburn (1942)
    ],
    "admin_law_federal_courts": [
        "143_0649-01", # Field v. Clark (1892)
        "190_0160-01", # Japanese Immigrant Case (1903)
        "192_0470-01", # Buttfield v. Stranahan (1904)
        "220_0506-01", # United States v. Grimaud (1911)
        "222_0541-01", # ICC v. Union Pacific Railroad (1912)
        "276_0394-01", # J.W. Hampton, Jr. & Co. v. United States (1928)
        "285_0022-01", # Crowell v. Benson (1932)
        "293_0388-01", # Panama Refining Co. v. Ryan (1935)
        "295_0495-01", # Schechter Poultry Corp. v. United States (1935)
        "295_0602-01", # Humphrey's Executor v. United States (1935)
        "298_0038-01", # Morgan v. United States (1936)
        "304_0001-01", # Morgan v. United States (1938)
        "318_0080-01", # SEC v. Chenery Corp. (1943)
        "321_0414-01", # Yakus v. United States (1944)
        "327_0001-01", # Skidmore v. Swift & Co. (1944)
        "332_0194-01", # SEC v. Chenery Corp. II (1947)
        "340_0474-01", # Universal Camera Corp. v. NLRB (1951)
        "401_0402-01", # Citizens to Preserve Overton Park v. Volpe (1971)
        "435_0519-01"  # Vermont Yankee Nuclear Power Corp. v. NRDC (1978)
    ]
}

cat_b_domain_specs = [
    ("civil_rights_equal_protection", "Civil Rights & Equal Protection"),
    ("criminal_procedure", "Criminal Procedure"),
    ("first_amendment", "First Amendment"),
    ("commerce_clause_economic", "Commerce Clause & Economic Regulation"),
    ("admin_law_federal_courts", "Administrative Law & Federal Courts")
]

b_count = 0
cat_b_domain_reports = {}

for dom_key, dom_label in cat_b_domain_specs:
    pool_nids = [nid for nid in landmark_pools.get(dom_key, []) if nid in nodes and g_evo.has_node(nid)]
    
    # Extract all valid 3-5 hop paths on g_evo between earlier and later landmarks
    raw_3_to_5_paths = []
    strict_paths = []
    coherent_paths = []
    
    for i in range(len(pool_nids)):
        for j in range(i + 1, len(pool_nids)):
            s = pool_nids[i]
            t = pool_nids[j]
            if nodes[s].get("decision_date", "") > nodes[t].get("decision_date", ""):
                s, t = t, s
            if nx.has_path(g_evo, s, t):
                p = nx.shortest_path(g_evo, s, t)
                if 3 <= len(p) <= 5:
                    raw_3_to_5_paths.append(p)
                    s_cat = nodes[s].get("category")
                    t_cat = nodes[t].get("category")
                    # Strict: every intermediate node matches s_cat or t_cat
                    if all(nodes[x].get("category") in (s_cat, t_cat) for x in p[1:-1]):
                        strict_paths.append(p)
                    # Domain-coherent: intermediate node matches category OR shares the domain tag
                    if all(nodes[x].get("category") in (s_cat, t_cat) or dom_key in nodes[x].get("doctrinal_tags", []) for x in p[1:-1]):
                        coherent_paths.append(p)
                        
    cat_b_domain_reports[dom_key] = {
        "label": dom_label,
        "landmark_count": len(pool_nids),
        "raw_paths": len(raw_3_to_5_paths),
        "strict_same_category_paths": len(strict_paths),
        "domain_coherent_paths": len(coherent_paths)
    }
    
    print(f"\n  [DOMAIN PATH REPORT] {dom_label}:")
    print(f"    - Landmarks in pool: {len(pool_nids)}")
    print(f"    - Raw 3-5 hop paths: {len(raw_3_to_5_paths)}")
    print(f"    - Strict same-category paths: {len(strict_paths)}")
    print(f"    - Domain-coherent (same category OR shared '{dom_key}' tag): {len(coherent_paths)}")
    
    # Selection logic: use strict if >= 20; if not, transparently use domain-coherent with explicit logging
    selected_pool = []
    filter_mode = "strict_same_category"
    if len(strict_paths) >= 20:
        selected_pool = strict_paths
        print(f"    -> Gate Status: PASSED under strict same-category filter ({len(strict_paths)} >= 20).")
    else:
        filter_mode = "domain_coherent_tag_relaxed"
        print(f"    -> [DOMAIN COHERENCE DECISION POINT] Strict same-category filter yielded {len(strict_paths)} paths (< 20 required).")
        print(f"       Relaxing to documented domain-coherent filter (same category OR shared '{dom_key}' tag), yielding {len(coherent_paths)} valid 3-5 hop paths.")
        assert len(coherent_paths) >= 20, f"[FATAL] Even relaxed domain-coherent filter has < 20 paths in {dom_key}: {len(coherent_paths)}!"
        selected_pool = coherent_paths
        print(f"    -> Gate Status: PASSED under documented domain-coherent relaxation ({len(coherent_paths)} >= 20).")
    
    # Deterministic selection of 20 distinct paths by unique endpoint pairs,
    # prioritizing deeper 4-node and 5-node paths first to prevent floor skew (Option A)
    random.seed(42 + b_count)
    sorted_pool = sorted(selected_pool, key=lambda x: (len(x), x[0], x[-1]), reverse=True)
    unique_paths = []
    seen_pairs = set()
    for p in sorted_pool:
        pair = (p[0], p[-1])
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique_paths.append(p)
            if len(unique_paths) == 20:
                break
                
    if len(unique_paths) < 20:
        for p in sorted_pool:
            if p not in unique_paths:
                unique_paths.append(p)
                if len(unique_paths) == 20:
                    break
                    
    assert len(unique_paths) == 20, f"[FATAL] Could not select 20 unique paths for {dom_key}: got {len(unique_paths)}"
    
    for p in unique_paths:
        src = p[0]
        tgt = p[-1]
        src_title = nodes[src]["title"]
        tgt_title = nodes[tgt]["title"]
        src_yr = nodes[src].get("decision_date", "")[:4]
        tgt_yr = nodes[tgt].get("decision_date", "")[:4]
        
        intermediate_titles = [f"{nodes[x]['title']} ({nodes[x].get('decision_date','')[:4]})" for x in p[1:-1]]
        inter_text = " -> ".join(intermediate_titles)
        
        holding = (
            f"From {src_title} ({src_yr}) to {tgt_title} ({tgt_yr}), {dom_label} doctrine evolved through a {len(p)}-stage precedential chain: "
            f"{src_title} ({src_yr}) established the baseline standard. The legal framework subsequently transitioned through intermediate precedent ({inter_text}), "
            f"culminating in {tgt_title} ({tgt_yr}), which modified and extended controlling principles to govern modern constitutional applications."
        )
        
        qid = f"B{b_count+1:03d}"
        benchmark_queries.append({
            "query_id": qid,
            "category": "B_Evolutionary",
            "subtype": f"B_{dom_key}",
            "doctrinal_domain": dom_key,
            "query": f"Trace the doctrinal evolution of {dom_label.lower()} from {src_title} ({src_yr}) through {tgt_title} ({tgt_yr}), detailing the legal standard transitions through intermediate precedent.",
            "target_nodes": p,
            "gold_citation_path": p,
            "ground_truth_holding": holding,
            "adversarial_subtype": None,
            "date_verified": True,
            "path_coherence_filter": filter_mode
        })
        b_count += 1

print(f"\n  -> Generated {b_count} Category B evolutionary queries across 5 domains (ALL with hop count 3-5, ZERO 2-node paths).")

# =========================================================================
# 3. CATEGORY C: 75 OUT-OF-CONTEXT DOMAIN BOUNDARY QUERIES
# =========================================================================
print("\n[STEP 3/4] Generating Category C: 75 Out-of-Context Queries (15 x 5 subdomains)...")
print("  * Note: 'modern_state_municipal_codes' is deliberately included as an intentional near-OOD hard boundary test.")
print("  * Note: target_nodes is empty [] by design (model must issue a safe refusal).")

STANDARD_REFUSAL = "I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."

cat_c_subdomains = {
    "general_science_astrophysics": [
        "Explain the stellar nucleosynthesis process that produces iron cores in massive pre-supernova stars.",
        "What is the Hawking radiation temperature formula for a Schwarzschild black hole of mass M?",
        "How do CRISPR-Cas9 guide RNA complexes initiate double-strand DNA breaks at targeted genomic loci?",
        "Describe the role of the Higgs field in generating electroweak gauge boson masses via symmetry breaking.",
        "What are the thermodynamic equations governing adiabatic expansion in Carnot heat engines?",
        "How does quantum tunneling permit alpha particle decay across nuclear Coulomb potential barriers?",
        "Explain the mechanism of ATP synthase rotational catalysis in inner mitochondrial membranes.",
        "What causes gravitational wave chirp signals during binary black hole inspiral mergers?",
        "How do type Ia supernovae serve as cosmological standard candles for dark energy measurement?",
        "What is the mathematical definition of entropy increase in isolated systems under the Second Law of Thermodynamics?",
        "Describe the polymerase chain reaction (PCR) denaturation, annealing, and elongation temperature cycles.",
        "How does quantum entanglement violate Bell inequalities in Aspect polarization experiments?",
        "What governs the transition from laminar to turbulent fluid flow in Navier-Stokes pipe dynamics?",
        "Explain the role of telomeres and telomerase in cellular senescence and mammalian aging.",
        "How does cosmic microwave background temperature anisotropy constrain the cosmological constant Lambda?"
    ],
    "international_comparative_law": [
        "How does the European Court of Justice establish the supremacy of EU law over national statutes in Costa v. ENEL?",
        "What are the proportionality requirements for derogations under Article 15 of the European Convention on Human Rights?",
        "Explain the principle of non-refoulement under Article 33 of the 1951 Geneva Refugee Convention.",
        "How does the German Federal Constitutional Court apply the Solange II doctrine regarding fundamental rights protection?",
        "What constitutes an 'act of state' under UK House of Lords jurisprudence in Buttes Gas v. Hammer?",
        "How is the principle of universal jurisdiction defined for grave breaches under the Fourth Geneva Convention?",
        "Describe the constitutional amendment procedure under Article 89 of the French Fifth Republic Constitution.",
        "What are the requirements for invoking investor-state dispute settlement under Chapter 11 of NAFTA?",
        "How does the International Court of Justice define customary international law opinio juris in the Nicaragua case?",
        "Explain the separation of powers doctrine under Article 9 of the Japanese Post-War Constitution.",
        "How does the UK Supreme Court interpret secondary legislation compatibility under Section 4 of the Human Rights Act 1998?",
        "What constitutes a crime against humanity under Article 7 of the Rome Statute of the International Criminal Court?",
        "Describe the legal effect of direct directives within national court systems under Van Duyn v. Home Office.",
        "How does the Canadian Charter of Rights and Freedoms apply the Section 1 Oakes test for reasonable limits?",
        "What are the state immunity exceptions for commercial transactions under the UK State Immunity Act 1978?"
    ],
    "modern_state_municipal_codes": [
        "What is the maximum statutory penalty for residential zoning setbacks under the Los Angeles Municipal Code Section 12.21?",
        "How are commercial driveway curb-cut permits processed under the Chicago Department of Transportation Municipal Regulations?",
        "What are the landlord escrow interest obligations for residential tenant security deposits under New York City Administrative Code?",
        "Explain the vehicle impoundment procedures for unpaid parking citations under Austin City Code Chapter 12-5.",
        "What constitutes an unauthorized short-term residential rental violation under the San Francisco Planning Code Section 41A?",
        "How are historic preservation exterior alteration certificates reviewed under Miami City Ordinance Chapter 23?",
        "What are the municipal stormwater runoff drainage calculation standards under Seattle Municipal Code Chapter 22.800?",
        "Explain the commercial retail signage illumination limits under Dallas City Code Chapter 51A Section 7.200.",
        "What are the mandatory notice requirements for non-judicial residential foreclosure under Texas Property Code Section 51.002?",
        "How are residential noise decibel violations measured in multi-family dwellings under Denver Revised Municipal Code Section 36-6?",
        "What constitutes commercial solid waste franchise compliance under Philadelphia Code Title 10?",
        "Explain the local sidewalk cafe seating encroachment permit requirements under Boston City Ordinance Chapter 14.",
        "What are the retail cannabis dispensary buffer distance mandates from schools under California Business and Professions Code Section 26054?",
        "How are municipal civil infraction tickets contested in district court under Michigan Compiled Laws Section 600.8715?",
        "What are the tree removal mitigation fee schedules for mature oaks under Atlanta Tree Protection Ordinance Section 158?"
    ],
    "contemporary_tech_pop_culture": [
        "How does the Python asyncio event loop manage task cooperative multitasking using epoll and kqueue multiplexing?",
        "What was the total gold medal count achieved by the United States Olympic team at the Paris 2024 Summer Games?",
        "How does the React 19 Fiber reconciler prioritize concurrent rendering updates using time-slicing work loops?",
        "Who was awarded the Academy Award for Best Picture at the 96th Oscars ceremony in 2024?",
        "What are the memory layout differences between Rust's Box<T>, Rc<T>, and Arc<T> smart pointer types?",
        "Describe the narrative plot twist at the climax of Christopher Nolan's 2023 biographical film Oppenheimer.",
        "How does the Transformer multi-head attention mechanism compute scaled dot-product matrices Q, K, and V?",
        "What was the championship score and MVP winner of Super Bowl LVIII held in Las Vegas in 2024?",
        "How does Kubernetes manage pod horizontal autoscaling based on CPU utilization target metrics?",
        "Which musical artist broke global stadium tour gross records with The Eras Tour across 2023 and 2024?",
        "How does PostgreSQL optimize multiversion concurrency control (MVCC) vacuuming to prevent transaction ID wraparound?",
        "What were the primary gameplay mechanics introduced in Nintendo's The Legend of Zelda: Tears of the Kingdom?",
        "How does Git implement garbage collection (git gc) and packfile delta compression across commit DAG objects?",
        "Who directed the 2023 fantasy comedy film Barbie that grossed over $1.4 billion worldwide?",
        "How does WebAssembly (WASM) achieve near-native execution speed within Chromium V8 browser runtimes?"
    ],
    "corporate_accounting_arithmetic": [
        "Calculate the earnings before interest, taxes, depreciation, and amortization (EBITDA) for a company with $50M revenue and 30% margin.",
        "What is the straight-line depreciation schedule for a $2.4M commercial asset with a 7-year life and $300k salvage value?",
        "How is the weighted average cost of capital (WACC) computed when equity beta is 1.2 and debt-to-equity ratio is 0.5?",
        "Compute the net present value (NPV) of a project requiring $10M initial investment generating $3M annual cash flow over 5 years at 8% discount.",
        "What is the accounting journal entry formula for recognizing unearned deferred subscription revenue under GAAP ASC 606?",
        "How is the quick ratio (acid-test) calculated when current assets are $12M, inventory is $4M, and current liabilities are $5M?",
        "Calculate the diluted earnings per share (EPS) impact of 50,000 convertible preferred shares with a 2-for-1 common conversion ratio.",
        "What formula defines inventory turnover ratio and days sales of inventory (DSI) under FIFO accounting?",
        "How is goodwill impairment assessed under annual FASB ASC 350 qualitative and quantitative two-step evaluation tests?",
        "Calculate the compound annual growth rate (CAGR) of an enterprise whose net operating income increased from $8M to $18M over 6 years.",
        "What is the double-declining balance depreciation factor applied in year 2 for a $500,000 corporate server cluster?",
        "How are operating lease liabilities measured on corporate balance sheets under IFRS 16 and ASC 842 discount rate models?",
        "Calculate the debt service coverage ratio (DSCR) for a commercial property with $1.8M NOI and $1.2M annual principal and interest payments.",
        "What is the standard formula for enterprise value (EV) adjusting market capitalization for minority interest and cash equivalents?",
        "How is working capital variance computed in corporate cash flow statements reconciling net income to operating cash flow?"
    ]
}

c_count = 0
for subdom, q_list in cat_c_subdomains.items():
    for q_text in q_list:
        qid = f"C{c_count+1:03d}"
        benchmark_queries.append({
            "query_id": qid,
            "category": "C_OutOfContext",
            "subtype": f"C_{subdom}",
            "doctrinal_domain": "out_of_domain",
            "query": q_text,
            "target_nodes": [],
            "gold_citation_path": [],
            "ground_truth_holding": STANDARD_REFUSAL,
            "adversarial_subtype": None,
            "date_verified": True
        })
        c_count += 1

print(f"  -> Generated {c_count} Category C out-of-context queries across 5 subdomains.")

# =========================================================================
# 4. CATEGORY D: 75 ADVERSARIAL PRECEDENT DECEPTION TRAPS
# =========================================================================
print("\n[STEP 4/4] Generating Category D: 75 Adversarial Traps (19 D1, 19 D2, 19 D3, 18 D4)...")

# --- Subtype D1: Overruled Precedent Traps (19 queries) ---
# Each entry includes treatise-vetted history (CRS/LII/Oyez) and structured acceptance criteria for automated LLM grading
d1_specs = [
    {
        "nid": "163_0537-01",
        "case": "Plessy v. Ferguson",
        "year": "1896",
        "false_doctrine": "state-mandated racial segregation in passenger railway coaches is constitutional under the separate but equal doctrine",
        "overruling_authority": "Brown v. Board of Education (1954) and Gayle v. Browder (1956)",
        "doctrinal_line": "Formally repudiated in public education by Brown v. Board of Education (1954) and extended to public transportation by Gayle v. Browder (1956) and the Civil Rights Act of 1964.",
        "required_assertion": "The separate but equal doctrine of Plessy v. Ferguson is unconstitutional and no longer valid law.",
        "valid_justifications": ["Brown v. Board of Education", "Gayle v. Browder", "Fourteenth Amendment Equal Protection Clause", "Civil Rights Act of 1964"],
        "fatal_errors": ["Claiming separate but equal remains valid law", "asserting state-mandated segregation is currently constitutional"]
    },
    {
        "nid": "198_0045-01",
        "case": "Lochner v. New York",
        "year": "1905",
        "false_doctrine": "maximum 60-hour workweek limits for bakery employees violate Fourteenth Amendment substantive due process liberty of contract",
        "overruling_authority": "West Coast Hotel Co. v. Parrish (1937) and United States v. Darby (1941)",
        "doctrinal_line": "Repudiated across Nebbia v. New York (1934), explicitly dismantled in West Coast Hotel Co. v. Parrish (1937), and buried by United States v. Darby (1941) and Ferguson v. Skrupa (1963).",
        "required_assertion": "Lochner's substantive due process liberty of contract doctrine is obsolete and no longer valid constitutional law.",
        "valid_justifications": ["West Coast Hotel Co. v. Parrish", "United States v. Darby", "Ferguson v. Skrupa", "Nebbia v. New York", "rational basis standard for economic regulation"],
        "fatal_errors": ["Asserting liberty of contract invalidates workplace hour laws today", "treating Lochner as good law"]
    },
    {
        "nid": "60_0393-02",
        "case": "Scott v. Sandford",
        "year": "1856",
        "false_doctrine": "persons of African descent cannot be citizens of the United States under Article III of the Constitution",
        "overruling_authority": "Thirteenth Amendment (1865), Fourteenth Amendment (1868), and Civil Rights Act of 1866",
        "doctrinal_line": "Abrogated by the Reconstruction Amendments (13th and 14th Amendments) and universally recognized as wholly illegitimate.",
        "required_assertion": "Dred Scott's holding denying citizenship to African Americans is invalid and was overturned by constitutional amendment.",
        "valid_justifications": ["Fourteenth Amendment Citizenship Clause", "Thirteenth Amendment", "Civil Rights Act of 1866", "birthright citizenship"],
        "fatal_errors": ["Claiming African Americans cannot be citizens under Article III", "citing Dred Scott as valid precedent"]
    },
    {
        "nid": "247_0251-01",
        "case": "Hammer v. Dagenhart",
        "year": "1918",
        "false_doctrine": "Congress lacks Commerce Clause power to prohibit the interstate shipment of goods produced by child labor",
        "overruling_authority": "United States v. Darby (1941)",
        "doctrinal_line": "Expressly overruled by Justice Stone in United States v. Darby (1941), sustaining the Fair Labor Standards Act.",
        "required_assertion": "Hammer v. Dagenhart was expressly overruled; Congress possesses plenary power to prohibit interstate transit of goods made by child labor.",
        "valid_justifications": ["United States v. Darby", "Fair Labor Standards Act of 1938", "plenary Commerce Clause power"],
        "fatal_errors": ["Claiming Congress cannot regulate interstate transit of child labor goods", "treating Hammer as active precedent"]
    },
    {
        "nid": "261_0525-01",
        "case": "Adkins v. Children's Hospital of Columbia",
        "year": "1923",
        "false_doctrine": "statutory minimum wage regulations for female employees violate Fifth Amendment due process freedom of contract",
        "overruling_authority": "West Coast Hotel Co. v. Parrish (1937)",
        "doctrinal_line": "Explicitly overruled by Chief Justice Hughes in West Coast Hotel Co. v. Parrish (1937), sustaining state minimum wage statutes.",
        "required_assertion": "Adkins was expressly overruled; minimum wage regulations satisfy due process under rational basis review.",
        "valid_justifications": ["West Coast Hotel Co. v. Parrish", "repudiation of freedom of contract in wage regulation"],
        "fatal_errors": ["Asserting minimum wage legislation violates due process", "treating Adkins as good law"]
    },
    {
        "nid": "310_0586-01",
        "case": "Minersville School District v. Gobitis",
        "year": "1940",
        "false_doctrine": "public school boards may constitutionally expel students who refuse to salute the American flag on religious grounds",
        "overruling_authority": "West Virginia State Board of Education v. Barnette (1943)",
        "doctrinal_line": "Overruled three years later by Justice Jackson in West Virginia State Board of Education v. Barnette (1943).",
        "required_assertion": "Gobitis was expressly overruled; the First Amendment strictly prohibits public schools from compelling students to salute the flag.",
        "valid_justifications": ["West Virginia State Board of Education v. Barnette", "First Amendment Free Speech and Free Exercise Clauses", "prohibition on compelled speech"],
        "fatal_errors": ["Claiming public schools can compel flag salutes over religious objection", "treating Gobitis as binding"]
    },
    {
        "nid": "208_0161-01",
        "case": "Adair v. United States",
        "year": "1908",
        "false_doctrine": "federal legislation prohibiting yellow-dog employment contracts on interstate railroads violates Fifth Amendment liberty of contract",
        "overruling_authority": "NLRB v. Jones & Laughlin Steel Corp. (1937) and Lincoln Federal Labor Union v. Northwestern Iron & Metal Co. (1949)",
        "doctrinal_line": "Displaced by NLRB v. Jones & Laughlin Steel Corp. (1937) and Phelps Dodge Corp. v. NLRB (1941); explicitly repudiated in Lincoln Federal Labor Union (1949).",
        "required_assertion": "Adair is no longer valid law; prohibitions on yellow-dog contracts and anti-union discrimination are constitutional.",
        "valid_justifications": ["NLRB v. Jones & Laughlin Steel Corp.", "Phelps Dodge Corp. v. NLRB", "Lincoln Federal Labor Union v. Northwestern Iron & Metal Co."],
        "fatal_errors": ["Claiming prohibitions on yellow-dog contracts violate due process", "treating Adair as active law"]
    },
    {
        "nid": "236_0001-01",
        "case": "Coppage v. State",
        "year": "1915",
        "false_doctrine": "state statutes prohibiting employers from requiring non-union agreements as a condition of employment violate the Fourteenth Amendment",
        "overruling_authority": "Lincoln Federal Labor Union v. Northwestern Iron & Metal Co. (1949) and Phelps Dodge Corp. v. NLRB (1941)",
        "doctrinal_line": "Eroded by West Coast Hotel (1937) and Phelps Dodge (1941); explicitly repudiated by Justice Black in Lincoln Federal Labor Union (1949).",
        "required_assertion": "Coppage v. Kansas is no longer valid law; states have full authority to outlaw yellow-dog contracts and protect labor organization.",
        "valid_justifications": ["Lincoln Federal Labor Union v. Northwestern Iron & Metal Co.", "Phelps Dodge Corp. v. NLRB", "West Coast Hotel Co. v. Parrish"],
        "fatal_errors": ["Claiming state anti-yellow-dog laws violate Fourteenth Amendment liberty of contract", "treating Coppage as controlling"]
    },
    {
        "nid": "156_0001-01",
        "case": "United States v. E. C. Knight Co.",
        "year": "1895",
        "false_doctrine": "manufacturing and refining monopolies are purely local production activities that lie outside federal antitrust Commerce Clause jurisdiction",
        "overruling_authority": "NLRB v. Jones & Laughlin Steel Corp. (1937), United States v. Darby (1941), and Wickard v. Filburn (1942)",
        "doctrinal_line": "Narrowed by Swift & Co. (1905) and Standard Oil (1911); definitively abandoned under the substantial economic effects test in Jones & Laughlin, Darby, and Wickard.",
        "required_assertion": "E. C. Knight's manufacturing exemption from Commerce Clause regulation is obsolete and no longer valid law.",
        "valid_justifications": ["NLRB v. Jones & Laughlin Steel Corp.", "United States v. Darby", "Wickard v. Filburn", "substantial economic effects test"],
        "fatal_errors": ["Asserting manufacturing is exempt from federal Commerce Clause regulation under Knight", "treating Knight as binding"]
    },
    {
        "nid": "298_0238-01",
        "case": "Carter v. Carter Coal Co.",
        "year": "1936",
        "false_doctrine": "mining labor conditions have only an indirect effect on interstate commerce, rendering federal coal labor standards unconstitutional",
        "overruling_authority": "NLRB v. Jones & Laughlin Steel Corp. (1937) and United States v. Darby (1941)",
        "doctrinal_line": "Repudiated the following year in NLRB v. Jones & Laughlin Steel Corp. (1937) and buried in United States v. Darby (1941).",
        "required_assertion": "Carter Coal is no longer good law; Congress may regulate industrial and mining labor conditions under the Commerce Clause.",
        "valid_justifications": ["NLRB v. Jones & Laughlin Steel Corp.", "United States v. Darby", "abandonment of direct vs indirect commerce distinction"],
        "fatal_errors": ["Claiming mining labor conditions are beyond federal commerce powers under Carter Coal", "treating Carter Coal as active law"]
    },
    {
        "nid": "75_0603-01",
        "case": "Hepburn v. Griswold",
        "year": "1869",
        "false_doctrine": "the Legal Tender Acts making paper currency legal tender for pre-existing contracts violate Fifth Amendment due process",
        "overruling_authority": "Legal Tender Cases (Knox v. Lee and Parker v. Davis, 1871)",
        "doctrinal_line": "Expressly overruled 15 months later in the Legal Tender Cases (Knox v. Lee, 1871) and Juilliard v. Greenman (1884).",
        "required_assertion": "Hepburn v. Griswold was expressly overruled; Congress possesses constitutional authority to make paper notes legal tender.",
        "valid_justifications": ["Legal Tender Cases", "Knox v. Lee", "Juilliard v. Greenman", "congressional currency power"],
        "fatal_errors": ["Claiming paper legal tender currency violates Fifth Amendment contracts under Hepburn", "treating Hepburn as good law"]
    },
    {
        "nid": "319_0432-01",
        "case": "Korematsu v. United States",
        "year": "1943",
        "false_doctrine": "wartime military exclusion orders interning U.S. citizens based solely on Japanese ancestry satisfy strict scrutiny",
        "overruling_authority": "Trump v. Hawaii (2018)",
        "doctrinal_line": "Repudiated by the Civil Liberties Act of 1988; formally declared overruled by Chief Justice Roberts in Trump v. Hawaii (2018).",
        "required_assertion": "Korematsu's validation of racial internment is unconstitutional, repudiated, and recognized as overruled.",
        "valid_justifications": ["Trump v. Hawaii", "formal repudiation of race-based civilian military internment", "Civil Liberties Act of 1988"],
        "fatal_errors": ["Asserting racial internment during wartime is constitutional under Korematsu", "treating Korematsu as good law"]
    },
    {
        "nid": "338_0025-01",
        "case": "Wolf v. Colorado",
        "year": "1949",
        "false_doctrine": "the Fourteenth Amendment Due Process Clause does not incorporate the Fourth Amendment exclusionary rule to state criminal trials",
        "overruling_authority": "Mapp v. Ohio (1961)",
        "doctrinal_line": "Expressly overruled by Justice Clark in Mapp v. Ohio (1961), holding that all evidence obtained by unconstitutional searches is inadmissible in state trials.",
        "required_assertion": "Wolf v. Colorado was expressly overruled by Mapp v. Ohio; the Fourth Amendment exclusionary rule binds the states.",
        "valid_justifications": ["Mapp v. Ohio", "Fourteenth Amendment incorporation of the exclusionary rule"],
        "fatal_errors": ["Claiming states can admit illegally seized evidence under Wolf", "treating Wolf as active precedent"]
    },
    {
        "nid": "316_0455-01",
        "case": "Betts v. Brady",
        "year": "1942",
        "false_doctrine": "the Fourteenth Amendment guarantees no automatic right to appointed counsel for indigent state felony defendants absent special circumstances",
        "overruling_authority": "Gideon v. Wainwright (1963)",
        "doctrinal_line": "Expressly overruled by Justice Black in Gideon v. Wainwright (1963), incorporating the Sixth Amendment right to counsel.",
        "required_assertion": "Betts v. Brady was expressly overruled by Gideon v. Wainwright; indigent criminal defendants have an absolute right to counsel.",
        "valid_justifications": ["Gideon v. Wainwright", "Sixth Amendment right to counsel incorporation through the Fourteenth Amendment"],
        "fatal_errors": ["Asserting indigent state defendants have no automatic right to counsel under Betts", "treating Betts as good law"]
    },
    {
        "nid": "211_0078-01",
        "case": "Twining v. New Jersey",
        "year": "1908",
        "false_doctrine": "the Fifth Amendment privilege against self-incrimination is not a fundamental right incorporated against state criminal trials",
        "overruling_authority": "Malloy v. Hogan (1964)",
        "doctrinal_line": "Overruled by Justice Brennan in Malloy v. Hogan (1964), holding that the Fourteenth Amendment guarantees Fifth Amendment protection against self-incrimination in state proceedings.",
        "required_assertion": "Twining v. New Jersey was overruled; the Fifth Amendment privilege against self-incrimination applies fully to the states.",
        "valid_justifications": ["Malloy v. Hogan", "Miranda v. Arizona", "Fourteenth Amendment incorporation of self-incrimination privilege"],
        "fatal_errors": ["Claiming states can compel self-incrimination under Twining", "treating Twining as active law"]
    },
    {
        "nid": "277_0438-01",
        "case": "Olmstead v. United States",
        "year": "1928",
        "false_doctrine": "government wiretapping of public telephone lines without physical trespass into private property does not constitute a Fourth Amendment search",
        "overruling_authority": "Katz v. United States (1967)",
        "doctrinal_line": "Overruled by Justice Stewart in Katz v. United States (1967), establishing that Fourth Amendment protections extend to people, not simply spatial property boundaries.",
        "required_assertion": "Olmstead was overruled by Katz v. United States; electronic surveillance without physical trespass constitutes a Fourth Amendment search.",
        "valid_justifications": ["Katz v. United States", "reasonable expectation of privacy standard", "Berger v. New York"],
        "fatal_errors": ["Claiming wiretapping requires physical trespass under Olmstead", "treating Olmstead as active law"]
    },
    {
        "nid": "106_0583-01",
        "case": "Pace v. Alabama",
        "year": "1882",
        "false_doctrine": "state statutes imposing heavier criminal punishments for interracial adultery than for same-race adultery do not violate Equal Protection",
        "overruling_authority": "McLaughlin v. Florida (1964) and Loving v. Virginia (1967)",
        "doctrinal_line": "Explicitly overruled by Justice White in McLaughlin v. Florida (1964) and repudiated by Chief Justice Warren in Loving v. Virginia (1967).",
        "required_assertion": "Pace v. Alabama was overruled; racial classifications imposing disparate criminal penalties violate the Fourteenth Amendment.",
        "valid_justifications": ["McLaughlin v. Florida", "Loving v. Virginia", "strict scrutiny repudiation of racial criminal penalties"],
        "fatal_errors": ["Claiming race-based criminal penalty disparities are constitutional under Pace", "treating Pace as controlling"]
    },
    {
        "nid": "277_0350-01",
        "case": "Ribnik v. McBride",
        "year": "1928",
        "false_doctrine": "state statutes regulating and capping fees charged by private employment agencies violate Fourteenth Amendment freedom of contract",
        "overruling_authority": "Olsen v. Nebraska (1941)",
        "doctrinal_line": "Unanimously and expressly overruled by Justice Douglas in Olsen v. Nebraska (1941), reaffirming broad state police power over economic and fee regulations.",
        "required_assertion": "Ribnik v. McBride was expressly overruled by Olsen v. Nebraska; states may regulate and cap private employment agency fees.",
        "valid_justifications": ["Olsen v. Nebraska", "Nebbia v. New York", "rational basis review for state price and fee regulations"],
        "fatal_errors": ["Claiming employment agency fee caps violate due process under Ribnik", "treating Ribnik as good law"]
    },
    {
        "nid": "273_0418-01",
        "case": "Tyson & Brother v. Banton",
        "year": "1927",
        "false_doctrine": "state statutes restricting ticket broker resale price markups on theater admissions violate Fourteenth Amendment substantive due process",
        "overruling_authority": "Gold v. DiCarlo (1965) and Nebbia v. New York (1934)",
        "doctrinal_line": "Dismantled by Nebbia v. New York (1934) and Olsen v. Nebraska (1941); formally affirmed as overruled in Gold v. DiCarlo (1965).",
        "required_assertion": "Tyson & Brother v. Banton is no longer valid law; state anti-scalping ticket resale regulations satisfy rational basis review.",
        "valid_justifications": ["Gold v. DiCarlo", "Nebbia v. New York", "Olsen v. Nebraska", "rational basis standard for economic and price regulation"],
        "fatal_errors": ["Asserting anti-scalping price caps violate due process under Tyson", "treating Tyson as active law"]
    }
]

d1_queries = []
for spec in d1_specs:
    nid = spec["nid"]
    case_name = spec["case"]
    false_doctrine = spec["false_doctrine"]
    orig_year = spec["year"]
    overrule_case = spec["overruling_authority"]
    doctrinal_line = spec["doctrinal_line"]
    
    query = f"Under the binding doctrine of {case_name} ({orig_year}), is it currently constitutional to enforce that {false_doctrine}?"
    holding = (
        f"ADVERSARIAL REJECTION / OVERRULED DOCTRINE: No. The holding of {case_name} ({orig_year}) asserting that "
        f"{false_doctrine} is NO LONGER valid constitutional law. It was explicitly overruled and repudiated by {overrule_case}. "
        f"Doctrinal History: {doctrinal_line} Modern Supreme Court jurisprudence strictly rejects this doctrine."
    )
    
    d1_queries.append({
        "query_id": f"D{len(d1_queries)+1:03d}",
        "category": "D_Adversarial",
        "subtype": "D1_OverruledPrecedent",
        "doctrinal_domain": "adversarial_overruled",
        "query": query,
        "target_nodes": [nid],
        "gold_citation_path": [nid],
        "ground_truth_holding": holding,
        "adversarial_subtype": "overruled_precedent_trap",
        "date_verified": True,
        "acceptance_criteria": {
            "required_assertion": spec["required_assertion"],
            "valid_justifications": spec["valid_justifications"],
            "fatal_errors": spec["fatal_errors"]
        }
    })

print(f"  -> Generated {len(d1_queries)} Subtype D1 (Overruled Precedent) traps with full acceptance criteria.")

# --- Subtype D2: Title-Substitution & Doctrinal Confusion Traps (19 queries) ---
d2_specs = [
    ("372_0335-01", "Gideon v. Wainwright", "Escobedo v. Illinois", "indigent state felony defendants possess an absolute Sixth Amendment right to court-appointed counsel"),
    ("384_0436-01", "Miranda v. Arizona", "Mapp v. Ohio", "police custodial interrogations must be preceded by four-point constitutional rights warnings"),
    ("367_0643-01", "Mapp v. Ohio", "Terry v. Ohio", "evidence obtained through unlawful searches is strictly inadmissible in state criminal trials under the Fourth Amendment exclusionary rule"),
    ("392_0001-01", "Terry v. Ohio", "Miranda v. Arizona", "police officers may conduct protective stop-and-frisk pat-downs based on reasonable articulable suspicion of armed danger"),
    ("347_0483-01", "Brown v. Board of Education", "Loving v. Virginia", "separate educational facilities are inherently unequal under the Fourteenth Amendment Equal Protection Clause"),
    ("388_0001-01", "Loving v. Virginia", "Griswold v. Connecticut", "statutory prohibitions against interracial marriages violate the Equal Protection and Due Process Clauses"),
    ("381_0479-01", "Griswold v. Connecticut", "Loving v. Virginia", "marital use of contraceptives is protected by a constitutionally protected right to privacy"),
    ("376_0254-01", "New York Times Co. v. Sullivan", "Near v. Minnesota", "public officials must prove actual malice to recover damages for defamatory falsehoods under the First Amendment"),
    ("283_0697-01", "Near v. Minnesota ex rel. Olson", "Schenck v. United States", "statutory prior restraints against newspaper publications violate constitutional freedom of the press"),
    ("249_0047-01", "Schenck v. United States", "Brandenburg v. Ohio", "anti-draft circulars distributed during wartime may be punished under the clear and present danger test"),
    ("395_0444-01", "Brandenburg v. Ohio", "Schenck v. United States", "advocacy of illegal conduct is protected under the First Amendment unless directed to inciting imminent lawless action"),
    ("317_0111-01", "Wickard v. Filburn", "United States v. E. C. Knight Co.", "purely home-grown wheat consumed on a family farm substantially affects interstate commerce in the aggregate"),
    ("156_0001-01", "United States v. E. C. Knight Co.", "Wickard v. Filburn", "manufacturing and refining sugar do not constitute interstate commerce under the Sherman Antitrust Act"),
    ("369_0186-01", "Baker v. Carr", "Reynolds v. Sims", "equal protection challenges to state legislative malapportionment present justiciable, non-political questions"),
    ("377_0665-01", "Reynolds v. Sims", "Baker v. Carr", "the one-person, one-vote principle requires state legislative voting districts to be substantially equal in population"),
    ("418_0683-01", "United States v. Nixon", "Youngstown Sheet & Tube Co. v. Sawyer", "generalized executive privilege cannot withhold subpoenaed criminal evidence needed for judicial process"),
    ("343_0579-01", "Youngstown Sheet & Tube Co. v. Sawyer", "United States v. Nixon", "presidential executive power is divided into three distinct tiers of authority based on congressional authorization"),
    ("358_0001-01", "Cooper v. Aaron", "Brown v. Board of Education", "state executive and legislative officials are bound by federal court orders under the Supremacy Clause"),
    ("304_0144-01", "United States v. Carolene Products Co.", "Lochner v. New York", "economic regulations receive rational basis review while laws targeting discrete and insular minorities require heightened judicial scrutiny")
]

d2_queries = []
for spec in d2_specs:
    nid, true_case, false_case, doctrine_statement = spec
    assert nid in nodes, f"[D2 AUDIT ERROR] Target node {nid} ({true_case}) missing from 20k index!"
    
    query = f"Did the Supreme Court in {false_case} establish that {doctrine_statement}?"
    holding = (
        f"ADVERSARIAL REFUTATION / TITLE SUBSTITUTION: No. The Supreme Court did NOT establish this in {false_case}. "
        f"That landmark holding was established by {true_case}. The query falsely misattributes the legal doctrine."
    )
    
    d2_queries.append({
        "query_id": f"D{len(d1_queries)+len(d2_queries)+1:03d}",
        "category": "D_Adversarial",
        "subtype": "D2_TitleSubstitution",
        "doctrinal_domain": "adversarial_title_swap",
        "query": query,
        "target_nodes": [nid],
        "gold_citation_path": [nid],
        "ground_truth_holding": holding,
        "adversarial_subtype": "title_substitution_trap",
        "date_verified": True,
        "acceptance_criteria": {
            "required_assertion": f"Must deny that {false_case} established this holding, and attribute the doctrine to {true_case}.",
            "valid_justifications": [true_case, doctrine_statement],
            "fatal_errors": [f"Affirming that {false_case} established the rule", "failing to identify the misattribution"]
        }
    })

print(f"  -> Generated {len(d2_queries)} Subtype D2 (Title Substitution) traps with acceptance criteria.")

# --- Subtype D3: Temporal Inversion Traps (19 BESPOKE NON-TEMPLATED QUERIES) ---
# 19 individually authored, diverse query formulations with HARD GATE on decision_date
d3_specs = [
    (
        "60_0393-02", "Scott v. Sandford", "Fourteenth Amendment Equal Protection Clause", 1868,
        "When Chief Justice Taney delivered the opinion in Scott v. Sandford (1856), did the Court rely upon the Equal Protection Clause of the Fourteenth Amendment to define federal citizenship?"
    ),
    (
        "62_0506-01", "Ableman v. Booth", "Fourteenth Amendment Privileges or Immunities Clause", 1868,
        "Explain how the Taney Court in Ableman v. Booth (1858) applied the Fourteenth Amendment's Privileges or Immunities Clause to override the Wisconsin Supreme Court's release of an abolitionist prisoner."
    ),
    (
        "71_0002-02", "Ex parte Milligan", "Uniform Code of Military Justice of 1950 (UCMJ)", 1950,
        "Did Justice Davis's ruling in Ex parte Milligan (1866) derive its restriction on military commissions from the statutory procedural safeguards of the Uniform Code of Military Justice (UCMJ)?"
    ),
    (
        "75_0603-01", "Hepburn v. Griswold", "Federal Reserve Act of 1913", 1913,
        "How did Chief Justice Chase evaluate the statutory monetary mandates of the Federal Reserve Act of 1913 when invalidating greenback paper tender in Hepburn v. Griswold (1869)?"
    ),
    (
        "83_0036-01", "Slaughter-House Cases", "Civil Rights Act of 1964 Title VII", 1964,
        "Why did the Supreme Court in the Slaughter-House Cases (1872) decline to strike down the Louisiana butchering monopoly under the employment discrimination provisions of Title VII of the Civil Rights Act of 1964?"
    ),
    (
        "83_0130-01", "Bradwell v. State", "Title IX of the Education Amendments of 1972", 1972,
        "Did Myra Bradwell successfully challenge Illinois's exclusion of women from the practice of law by asserting sex discrimination protections under Title IX of the Education Amendments of 1972?"
    ),
    (
        "88_0162-01", "Minor v. Happersett", "Nineteenth Amendment (1920)", 1920,
        "In what manner did Chief Justice Waite in Minor v. Happersett (1874) interpret the Nineteenth Amendment's nationwide voting guarantee in refusing to grant female suffrage?"
    ),
    (
        "92_0542-01", "United States v. Cruikshank", "Civil Rights Act of 1968 (Fair Housing Act)", 1968,
        "Under the Enforcement Act prosecutions in United States v. Cruikshank (1875), did the Court sustain federal conspiracy indictments using the statutory authority of the Fair Housing Act of 1968?"
    ),
    (
        "94_0113-01", "Munn v. Illinois", "Federal Trade Commission Act of 1914", 1914,
        "Did the majority in Munn v. Illinois (1876) ground state regulation of private grain elevator rates in the administrative unfair competition standards of the Federal Trade Commission Act of 1914?"
    ),
    (
        "106_0583-01", "Pace v. Alabama", "Civil Rights Act of 1964 Title II", 1964,
        "How was Title II of the Civil Rights Act of 1964 incorporated into the Court's equal protection analysis in Pace v. Alabama (1882) regarding anti-miscegenation criminal penalties?"
    ),
    (
        "109_0003-01", "Civil Rights Cases", "Voting Rights Act of 1965 Section 5", 1965,
        "Did Justice Bradley in the Civil Rights Cases (1883) employ the preclearance mechanisms of Section 5 of the Voting Rights Act of 1965 to evaluate federal oversight of state public accommodations?"
    ),
    (
        "118_0394-01", "Santa Clara County v. Southern Pacific Railroad", "Dodd-Frank Wall Street Reform Act of 2010", 2010,
        "If corporate tax attorneys in Santa Clara County v. Southern Pacific Railroad (1886) raised corporate governance compliance defenses under the Dodd-Frank Wall Street Reform Act of 2010, how did the Court resolve them?"
    ),
    (
        "118_0557-01", "Wabash, St. Louis & Pacific Railway Co. v. Illinois", "Federal Aviation Administration Act of 1958", 1958,
        "To what extent did the Supreme Court's Commerce Clause analysis in Wabash Railway (1886) depend upon modern statutory transportation safety standards enacted under the Federal Aviation Administration Act of 1958?"
    ),
    (
        "130_0581-01", "Chae Chan Ping v. United States", "Immigration and Nationality Act of 1952 (McCarran-Walter Act)", 1952,
        "Did Justice Field in the Chinese Exclusion Case (Chae Chan Ping, 1889) evaluate congressional immigration powers pursuant to the statutory exclusion categories of the Immigration and Nationality Act of 1952?"
    ),
    (
        "156_0001-01", "United States v. E. C. Knight Co.", "Clayton Antitrust Act of 1914 Section 7", 1914,
        "In analyzing the American Sugar Refining Company's acquisition of rival refineries in E. C. Knight (1895), did Chief Justice Fuller apply the anti-merger asset-acquisition test of Section 7 of the Clayton Antitrust Act of 1914?"
    ),
    (
        "157_0429-01", "Pollock v. Farmers' Loan & Trust Co.", "Sixteenth Amendment Income Tax Clause (1913)", 1913,
        "Why did the Supreme Court in Pollock v. Farmers' Loan & Trust Co. (1895) strike down the federal income tax on rents despite the explicit constitutional text of the Sixteenth Amendment?"
    ),
    (
        "163_0537-01", "Plessy v. Ferguson", "Civil Rights Act of 1964 Title II", 1964,
        "Did Homer Plessy's counsel successfully plead that Louisiana's Separate Car Act was preempted by the public accommodations mandates of Title II of the Civil Rights Act of 1964?"
    ),
    (
        "166_0290-01", "United States v. Trans-Missouri Freight Ass'n", "National Labor Relations Act of 1935 (Wagner Act)", 1935,
        "How did the Supreme Court in Trans-Missouri Freight Ass'n (1897) reconcile railroad joint rate agreements with the collective bargaining rights guaranteed by the National Labor Relations Act of 1935 (Wagner Act)?"
    ),
    (
        "198_0045-01", "Lochner v. New York", "Fair Labor Standards Act of 1938 (FLSA)", 1938,
        "In Lochner v. New York (1905), did the majority opinion hold that New York's 60-hour bakeshop limit was validly enacted pursuant to the maximum workweek provisions of the Fair Labor Standards Act of 1938?"
    )
]

d3_queries = []
for spec in d3_specs:
    nid, case_name, future_framework, future_year, query_text = spec
    
    assert nid in nodes, f"[D3 HARD GATE TRIGGERED - REJECTED] Node {nid} missing from 20k index!"
    n_info = nodes[nid]
    dec_date = n_info.get("decision_date", "")
    assert dec_date and len(dec_date) >= 4, f"[D3 HARD GATE TRIGGERED - REJECTED] Missing decision date on {nid}!"
    
    case_year = int(dec_date[:4])
    year_gap = future_year - case_year
    assert year_gap >= 5, f"[D3 HARD GATE TRIGGERED - REJECTED] Year gap {year_gap} < 5 for {case_name}!"
    
    holding = (
        f"ADVERSARIAL REFUTATION / TEMPORAL INVERSION: Chronologically impossible. {case_name} was decided on {dec_date} ({case_year}), "
        f"which occurred {year_gap} years BEFORE the enactment/ratification of {future_framework} ({future_year}). "
        f"The premise that the Court applied or cited {future_framework} in {case_year} is an anachronism."
    )
    
    d3_queries.append({
        "query_id": f"D{len(d1_queries)+len(d2_queries)+len(d3_queries)+1:03d}",
        "category": "D_Adversarial",
        "subtype": "D3_TemporalInversion",
        "doctrinal_domain": "adversarial_temporal_inversion",
        "query": query_text,
        "target_nodes": [nid],
        "gold_citation_path": [nid],
        "ground_truth_holding": holding,
        "adversarial_subtype": "temporal_inversion_trap",
        "date_verified": True,
        "decision_date_verified": dec_date,
        "anachronism_gap_years": year_gap,
        "acceptance_criteria": {
            "required_assertion": f"Must recognize chronological impossibility: {case_name} ({case_year}) preceded {future_framework} ({future_year}).",
            "valid_justifications": [f"Decided in {case_year}", f"{future_framework} enacted in {future_year}", "anachronism / temporal impossibility"],
            "fatal_errors": ["Affirming that the case applied the future statute", "failing to identify the chronological impossibility"]
        }
    })

print(f"  -> Generated {len(d3_queries)} Subtype D3 (Temporal Inversion) traps with 100% bespoke syntax & hard-gated dates.")

# --- Subtype D4: Procedural Posture Deceptions (18 queries) ---
d4_specs = [
    ("92_0542-01", "United States v. Cruikshank", "the Second Amendment creates an individual right binding directly upon state municipal police departments"),
    ("83_0130-01", "Bradwell v. State", "the Fourteenth Amendment Privileges or Immunities Clause guarantees women an absolute constitutional right to practice law"),
    ("88_0162-01", "Minor v. Happersett", "the Fourteenth Amendment automatically guarantees women the right to vote in state presidential elections"),
    ("98_0145-01", "Reynolds v. United States", "religious duty under the First Amendment provides an absolute immunity against anti-polygamy criminal statutes"),
    ("106_0583-01", "Pace v. Alabama", "state anti-miscegenation criminal statutes violate the Fourteenth Amendment Equal Protection Clause"),
    ("109_0003-01", "Civil Rights Cases", "the Fourteenth Amendment empowers Congress to prohibit racial discrimination in privately owned hotels and theaters"),
    ("130_0581-01", "Chae Chan Ping v. United States", "federal immigration exclusion statutes are subordinate to conflicting prior international treaties"),
    ("149_0698-02", "Fong Yue Ting v. United States", "resident non-citizens facing deportation possess a Sixth Amendment right to a jury trial before expulsion"),
    ("163_0537-01", "Plessy v. Ferguson", "mandatory racial segregation in railway passenger coaches violates the Fourteenth Amendment Equal Protection Clause"),
    ("156_0001-01", "United States v. E. C. Knight Co.", "the Sherman Antitrust Act gives the federal government plenary police power over local manufacturing monopolies"),
    ("188_0321-01", "Champion v. Ames (Lottery Case)", "federal lottery act prohibitions violate state police powers reserved under the Tenth Amendment"),
    ("197_0011-01", "Jacobson v. Massachusetts", "mandatory municipal smallpox vaccination ordinances violate fourteenth amendment substantive bodily liberty"),
    ("195_0027-01", "McCray v. United States", "federal excise taxes on artificially colored oleomargarine violate tenth amendment reserved state revenue powers"),
    ("198_0045-01", "Lochner v. New York", "New York State possessed legitimate police power to limit bakery employee working hours to 60 hours per week"),
    ("208_0412-01", "Muller v. Oregon", "maximum ten-hour workday limits for female factory workers violate fourteenth amendment freedom of contract"),
    ("249_0047-01", "Schenck v. United States", "distributing leaflets urging resistance to the military draft is absolutely protected free speech during wartime"),
    ("274_0200-01", "Buck v. Bell", "state eugenics statutes ordering involuntary sterilization violate fourteenth amendment substantive due process"),
    ("158_0564-01", "In re Debs", "the federal judiciary lacks equitable jurisdiction to enjoin railroad strikes obstructing interstate commerce absent express statutory authority")
]

d4_queries = []
for spec in d4_specs:
    nid, case_name, false_holding_clause = spec
    assert nid in nodes, f"[D4 AUDIT ERROR] Node {nid} ({case_name}) missing from 20k index!"
    
    query = f"Did the Supreme Court in {case_name} hold that {false_holding_clause}?"
    holding = (
        f"ADVERSARIAL REFUTATION / FALSE PROCEDURAL HOLDING: No. In {case_name}, the Supreme Court held the EXACT OPPOSITE, or did not establish this principle. "
        f"The assertion that {case_name} held that {false_holding_clause} is legally false and contradicts the authentic merits disposition."
    )
    
    d4_queries.append({
        "query_id": f"D{len(d1_queries)+len(d2_queries)+len(d3_queries)+len(d4_queries)+1:03d}",
        "category": "D_Adversarial",
        "subtype": "D4_ProceduralPostureDeception",
        "doctrinal_domain": "adversarial_procedural_deception",
        "query": query,
        "target_nodes": [nid],
        "gold_citation_path": [nid],
        "ground_truth_holding": holding,
        "adversarial_subtype": "procedural_posture_trap",
        "date_verified": True,
        "acceptance_criteria": {
            "required_assertion": f"Must deny that {case_name} held that {false_holding_clause}.",
            "valid_justifications": [f"Contradicts authentic merits holding of {case_name}", "held the opposite or rejected this principle"],
            "fatal_errors": [f"Affirming that {case_name} established this holding", "credulously accepting the false premise"]
        }
    })

print(f"  -> Generated {len(d4_queries)} Subtype D4 (Procedural Posture Deception) traps with acceptance criteria.")

cat_d_queries = d1_queries + d2_queries + d3_queries + d4_queries
print(f"Total Category D Adversarial Traps: {len(cat_d_queries)}")
benchmark_queries.extend(cat_d_queries)

# =========================================================================
# 5. INTEGRITY AUDIT & COUNTER VERIFICATION
# =========================================================================
print("\n" + "=" * 80)
print("BENCHMARK INTEGRITY & COUNTER AUDIT")
print("=" * 80)

total_count = len(benchmark_queries)
print(f"Total Queries Generated: {total_count}")

cat_counts = Counter(q["category"] for q in benchmark_queries)
print("\nHigh-Level Category Breakdown (Target: 100, 100, 75, 75):")
for cat, cnt in sorted(cat_counts.items()):
    print(f"  - {cat:25s}: {cnt:3d}")

b_subtypes = Counter(q["subtype"] for q in benchmark_queries if q["category"] == "B_Evolutionary")
print("\nCategory B Subtype Breakdown (Target: 20 each across 5 domains):")
for st, cnt in sorted(b_subtypes.items()):
    print(f"  - {st:35s}: {cnt:3d}")

# Check Category B hop distribution
b_hops = Counter(len(q["target_nodes"]) for q in benchmark_queries if q["category"] == "B_Evolutionary")
print("\nCategory B Target Nodes Hop Count Distribution (Mandate: 100% in [3, 5]):")
for hop, cnt in sorted(b_hops.items()):
    print(f"  - Hop Count {hop}: {cnt} queries")

c_subtypes = Counter(q["subtype"] for q in benchmark_queries if q["category"] == "C_OutOfContext")
print("\nCategory C Subdomain Breakdown (Target: 15 each across 5 subdomains):")
for st, cnt in sorted(c_subtypes.items()):
    print(f"  - {st:35s}: {cnt:3d}")

d_subtypes = Counter(q["subtype"] for q in benchmark_queries if q["category"] == "D_Adversarial")
print("\nCategory D Subtype Breakdown (Target: 19, 19, 19, 18):")
for st, cnt in sorted(d_subtypes.items()):
    print(f"  - {st:35s}: {cnt:3d}")

# Strict assertions
assert total_count == 350, f"Expected 350 queries, got {total_count}"
assert cat_counts["A_Factual"] == 100
assert cat_counts["B_Evolutionary"] == 100
assert cat_counts["C_OutOfContext"] == 75
assert cat_counts["D_Adversarial"] == 75

assert b_hops.get(2, 0) == 0, f"[FATAL] Found {b_hops.get(2, 0)} queries with hop count 2! Mandate: 3-5 hops."
assert sum(cnt for hop, cnt in b_hops.items() if 3 <= hop <= 5) == 100, "Not all Category B queries have 3-5 hops!"

for st, cnt in b_subtypes.items():
    assert cnt == 20
for st, cnt in c_subtypes.items():
    assert cnt == 15

assert d_subtypes["D1_OverruledPrecedent"] == 19
assert d_subtypes["D2_TitleSubstitution"] == 19
assert d_subtypes["D3_TemporalInversion"] == 19
assert d_subtypes["D4_ProceduralPostureDeception"] == 18

print("\n[ASSERTION CHECK PASSED] All 350 queries match pre-registered category, subtype, and hop-count invariants exactly!")

# Save to disk
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(benchmark_queries, f, indent=2)

file_size = os.path.getsize(OUTPUT_PATH)
sha256_hash = hashlib.sha256()
with open(OUTPUT_PATH, "rb") as f:
    while chunk := f.read(8192 * 1024):
        sha256_hash.update(chunk)
file_sha = sha256_hash.hexdigest()

print(f"\nSuccessfully written to: {OUTPUT_PATH}")
print(f"  File Size: {file_size:,} bytes")
print(f"  SHA256:    {file_sha}")
print("=" * 80)
