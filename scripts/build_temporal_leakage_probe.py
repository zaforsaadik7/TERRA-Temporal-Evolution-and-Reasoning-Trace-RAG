#!/usr/bin/env python3
"""
scripts/build_temporal_leakage_probe.py

Phase 1 Probe Construction & Preregistration Script for Issue #3
Generates:
1. data/temporal_leakage_probe_50.json (N=50 benchmark queries)
2. data/temporal_leakage_verifier_controls_10.json (N=10 paired verifier proposition controls)

Enforces:
- Dynamic percentile verification against dataset_20k_cap/terra_eeg_index_20k.json (p90>=18, p50<=4)
- Exclusion of intermediate degree range (5 <= deg <= 17)
- Prominence x Depth balanced allocation matrix (High: 13 D1, 12 D2; Lower: 12 D1, 13 D2)
- Cutoff balance (10 queries per cutoff across 1890, 1930, 1950, 1970, 1980)
- Doctrinal balance across 7 domains (8, 7, 7, 7, 7, 7, 7 summing to 50)
- Hard pre-execution sanitization invariants:
    query_lower ∩ future_case_names == ∅
    query_years ∩ future_years == ∅
    query_lower ∩ future_doctrinal_concepts == ∅
    target_case_year <= cutoff_year
"""

import json
import os
import re
import sys
import numpy as np

EEG_INDEX_PATH = 'dataset_20k_cap/terra_eeg_index_20k.json'
PROBE_OUTPUT_PATH = 'data/temporal_leakage_probe_50.json'
VERIFIER_OUTPUT_PATH = 'data/temporal_leakage_verifier_controls_10.json'

def load_eeg_index(path):
    print(f"[Phase 1] Loading EEG index from {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    nodes = data['nodes']
    edges = data['edges']
    in_degrees = {k: 0 for k in nodes}
    for e in edges:
        tgt = e.get('target')
        if tgt in in_degrees:
            in_degrees[tgt] += 1
    deg_vals = list(in_degrees.values())
    p90 = float(np.percentile(deg_vals, 90))
    p50 = float(np.percentile(deg_vals, 50))
    print(f"[Phase 1] EEG Index Loaded: {len(nodes):,} nodes, {len(edges):,} edges")
    print(f"[Phase 1] Citation Distribution: p90 = {p90:.1f} (in-degree >= 18), p50 = {p50:.1f} (in-degree <= 4)")
    assert p90 >= 18.0, f"EEG index p90 {p90} < 18.0"
    assert p50 <= 4.0, f"EEG index p50 {p50} > 4.0"
    return nodes, in_degrees, p90, p50

def get_probe_definitions():
    """
    Returns the 50 probe query definitions across the 5 cutoffs.
    """
    probes = [
        # =========================================================================
        # CUTOFF T1 = 1890 (Queries TLP-01 to TLP-10)
        # =========================================================================
        {
            "query_id": "TLP-01",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "109_0003-01",
            "target_case_name": "Civil Rights Cases",
            "target_case_citation": "109 U.S. 3 (1883)",
            "target_case_year": 1883,
            "query_text": "Under United States constitutional law as of 1890, does Section 5 of the Fourteenth Amendment grant Congress the authority to enact penal statutes prohibiting racial discrimination by private operators of inns, public conveyances, and theaters?",
            "ground_truth_holding": "Section 5 of the Fourteenth Amendment empowers Congress to enforce the prohibition against state action, but does not authorize direct federal legislation punishing individual private acts of discrimination by private citizens or business operators.",
            "required_historical_elements": [
                "state action requirement",
                "fourteenth amendment section 5 enforcement power",
                "inapplicable to purely private discrimination",
                "individual invasion of individual rights"
            ],
            "forbidden_future_elements": [
                "civil rights act of 1964",
                "commerce clause authority for public accommodations",
                "heart of atlanta motel",
                "katzenbach v. mcclung",
                "public accommodations non-discrimination mandate"
            ],
            "future_case_names": ["heart of atlanta motel", "katzenbach v. mcclung", "jones v. alfred h. mayer", "shelley v. kraemer"],
            "future_years": ["1948", "1964", "1968"],
            "future_doctrinal_concepts": ["commerce clause civil rights", "substantial effects on commerce doctrine", "public accommodations under commerce clause"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-02",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "128_0001-01",
            "target_case_name": "Kidd v. Pearson",
            "target_case_citation": "128 U.S. 1 (1888)",
            "target_case_year": 1888,
            "query_text": "As of 1890, does a state statute prohibiting the manufacture of intoxicating liquors within state borders violate the Commerce Clause when the manufacturer intends the goods exclusively for export to other states?",
            "ground_truth_holding": "State police power legitimately reaches local manufacturing even if manufactured goods are intended for interstate export, because manufacture is distinct from commerce and precedes it.",
            "required_historical_elements": [
                "manufacture is not commerce",
                "police power of the state",
                "local manufacturing distinction",
                "intent to export does not strip state authority"
            ],
            "forbidden_future_elements": [
                "substantial effects test",
                "wickard aggregation principle",
                "stream of commerce doctrine",
                "interstate commerce encompasses manufacture"
            ],
            "future_case_names": ["wickard v. filburn", "national labor relations board v. jones & laughlin", "united states v. darby", "united states v. lopez"],
            "future_years": ["1937", "1941", "1942", "1995"],
            "future_doctrinal_concepts": ["substantial effects on interstate commerce", "aggregation principle", "affecting commerce doctrine"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-03",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "110_0516-01",
            "target_case_name": "Hurtado v. California",
            "target_case_citation": "110 U.S. 516 (1884)",
            "target_case_year": 1884,
            "query_text": "As of 1890, does the Due Process Clause of the Fourteenth Amendment require state criminal prosecutions for capital felonies to proceed exclusively upon a grand jury indictment?",
            "ground_truth_holding": "The Due Process Clause of the Fourteenth Amendment does not require a grand jury indictment in state prosecutions for capital crimes; proceeding by information after examination and commitment by a magistrate satisfies due process.",
            "required_historical_elements": [
                "due process does not incorporate grand jury requirement",
                "prosecution by information is permissible",
                "fifth amendment grand jury clause applies only to federal government",
                "procedural due process satisfied by judicial examination"
            ],
            "forbidden_future_elements": [
                "total incorporation doctrine",
                "selective incorporation of grand jury clause",
                "fundamental fairness incorporation standard"
            ],
            "future_case_names": ["duncan v. louisiana", "benton v. maryland", "malloy v. hogan", "gitlow v. new york"],
            "future_years": ["1925", "1964", "1968", "1969"],
            "future_doctrinal_concepts": ["selective incorporation", "total incorporation doctrine", "penumbral incorporation"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-04",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "123_0623-01",
            "target_case_name": "Mugler v. Kansas",
            "target_case_citation": "123 U.S. 623 (1887)",
            "target_case_year": 1887,
            "query_text": "Tracing constitutional doctrine through 1890, does a state legislative enactment prohibiting the brewing and sale of beer without compensating existing brewery owners for the destruction of their property value constitute a deprivation of property without due process of law?",
            "ground_truth_holding": "A state's exercise of police power to protect public health, safety, and morals by prohibiting liquor manufacture does not constitute a taking or deprivation of property without due process, and requires no compensation even if brewery value is destroyed.",
            "required_historical_elements": [
                "valid exercise of state police power",
                "protection of public health and morals",
                "prohibition of noxious use is not a taking",
                "no compensation required under fourteenth amendment"
            ],
            "forbidden_future_elements": [
                "regulatory taking requiring just compensation",
                "penn central balancing test",
                "lucas categorical wipeout rule",
                "lochner liberty of contract restriction"
            ],
            "future_case_names": ["lucas v. south carolina coastal council", "penn central transportation co. v. new york city", "lochner v. new york"],
            "future_years": ["1905", "1978", "1992"],
            "future_doctrinal_concepts": ["regulatory takings doctrine", "penn central balancing", "total regulatory taking rule", "lochner economic due process"],
            "evolutionary_arc_cases": [
                {"case": "Bartemeyer v. Iowa", "year": 1873, "citation": "85 U.S. 129"},
                {"case": "Beer Co. v. Massachusetts", "year": 1877, "citation": "97 U.S. 25"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-05",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "77_0557-01",
            "target_case_name": "The Daniel Ball",
            "target_case_citation": "77 U.S. 557 (1870)",
            "target_case_year": 1870,
            "query_text": "Under federal admiralty and commerce jurisprudence through 1890, what legal standard determines whether an inland river constitutes navigable water of the United States subject to federal regulatory and admiralty jurisdiction?",
            "ground_truth_holding": "Rivers are navigable waters of the United States when they form in their ordinary condition by themselves, or by uniting with other waters, a continued highway over which commerce is or may be carried on with other states or foreign countries (navigable in fact test, rejecting the English tidal ebb-and-flow limit).",
            "required_historical_elements": [
                "navigable in fact",
                "continued highway for interstate commerce",
                "rejection of English tidal ebb and flow rule",
                "admiralty and commerce clause authority over navigable waters"
            ],
            "forbidden_future_elements": [
                "clean water act jurisdictional tests",
                "significant nexus standard",
                "continuous surface connection test",
                "adjacent non-navigable wetland regulation"
            ],
            "future_case_names": ["raapanos v. united states", "solid waste agency of northern cook county", "sackett v. epa"],
            "future_years": ["1972", "2001", "2006", "2023"],
            "future_doctrinal_concepts": ["significant nexus test", "clean water act jurisdiction", "adjacent wetlands jurisdiction", "waters of the united states rule"],
            "evolutionary_arc_cases": [
                {"case": "The Genesee Chief", "year": 1851, "citation": "53 U.S. 443"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-06",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "87_0201-01",
            "target_case_name": "The Lottawanna",
            "target_case_citation": "87 U.S. 201 (1873)",
            "target_case_year": 1873,
            "query_text": "As of 1890, does general federal maritime law recognize a maritime lien in favor of materialmen who furnish repairs or supplies to a domestic vessel in her home port in the absence of a state statute?",
            "ground_truth_holding": "The general maritime law of the United States does not create a maritime lien for repairs and supplies furnished to a vessel in her home port, though states possess constitutional power to create such liens by local statute enforceable in federal admiralty courts.",
            "required_historical_elements": [
                "no general maritime lien in home port",
                "distinction between foreign and domestic vessels",
                "state statutes may create enforceable home port liens",
                "materialmen rights under general maritime law"
            ],
            "forbidden_future_elements": [
                "federal maritime lien act of 1910",
                "commercial instruments and maritime liens act",
                "uniform federal statutory home port lien"
            ],
            "future_case_names": ["the thomas barlum", "piedmont & georges creek coal co. v. seaboard fisheries co."],
            "future_years": ["1910", "1920", "1934"],
            "future_doctrinal_concepts": ["federal maritime lien act", "commercial instruments and maritime liens act", "elimination of home port doctrine"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-07",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "135_0576-01",
            "target_case_name": "Des Moines & Fort Dodge Railroad v. Wabash, St. Louis & Pacific Railway Co.",
            "target_case_citation": "135 U.S. 576 (1890)",
            "target_case_year": 1890,
            "query_text": "Under federal equity practice as of 1890, does an operating agreement between two connecting railroad corporations obligating one to deliver all traffic to the other create an equitable lien or covenant running with the railroad property enforceable against a subsequent purchaser at foreclosure?",
            "ground_truth_holding": "A traffic and operating agreement between railroad companies is purely a personal contract; it does not constitute a covenant running with the property or an equitable lien binding a purchaser at foreclosure sale who takes the property unburdened by the contract.",
            "required_historical_elements": [
                "personal contract rather than property covenant",
                "no equitable lien created on railroad property",
                "foreclosure purchaser takes free of traffic agreement",
                "privity of contract required"
            ],
            "forbidden_future_elements": [
                "interstate commerce act consolidation oversight",
                "mandatory trackage rights under modern staggers act",
                "surface transportation board common carrier conditions"
            ],
            "future_case_names": ["penn-central merger cases", "northern securities co. v. united states"],
            "future_years": ["1904", "1968", "1980"],
            "future_doctrinal_concepts": ["clayton act section 7 railroad review", "surface transportation board public interest standard"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-08",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "67_0448-01",
            "target_case_name": "Trustees of the Wabash & Erie Canal Co. v. Beers",
            "target_case_citation": "67 U.S. 448 (1862)",
            "target_case_year": 1862,
            "query_text": "In federal jurisprudence through 1890, when a state legislature pledges the revenues and lands of a public canal system to secure construction bonds, can the state subsequently divert those pledged revenues to finance subordinate canal completion without impairing contractual obligations?",
            "ground_truth_holding": "A state legislative act pledging specific public canal revenues and tolls to bondholders creates a binding contract, and any subsequent legislative enactment subordinating or diverting those pledged revenues impairs the obligation of contract in violation of Article I, Section 10.",
            "required_historical_elements": [
                "contract clause violation",
                "legislative pledge of canal revenues is binding",
                "subsequent legislative diversion impairs obligation",
                "vested rights of public bondholders"
            ],
            "forbidden_future_elements": [
                "home building & loan ass'n v. blaisdell emergency exception",
                "modern contract clause balancing test",
                "united states trust co. reasonable and necessary standard"
            ],
            "future_case_names": ["home building & loan ass'n v. blaisdell", "united states trust co. v. new jersey", "energy reserves group v. kansas power & light"],
            "future_years": ["1934", "1977", "1983"],
            "future_doctrinal_concepts": ["blaisdell emergency doctrine", "reasonable and necessary contract modification standard", "contract clause balancing test"],
            "evolutionary_arc_cases": [
                {"case": "Dartmouth College v. Woodward", "year": 1819, "citation": "17 U.S. 518"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-09",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "61_0543-01",
            "target_case_name": "Snow v. Hill",
            "target_case_citation": "61 U.S. 543 (1857)",
            "target_case_year": 1857,
            "query_text": "Under federal navigation rules through 1890, what liability rule governs when a steam vessel descending a river with the current collides with an ascending vessel that has properly stopped and yielded the channel?",
            "ground_truth_holding": "A descending steamer having the current in its favor is liable for a collision if it fails to use proper precaution and steer clear of an ascending vessel that had properly stopped its headway along the river bank.",
            "required_historical_elements": [
                "descending steamer duty of precaution",
                "current in vessel's favor requires vigilance",
                "ascending vessel stopped along bank",
                "sole fault on navigating vessel"
            ],
            "forbidden_future_elements": [
                "proportional comparative fault in admiralty",
                "reliable transfer rule",
                "abolition of divided damages rule"
            ],
            "future_case_names": ["united states v. reliable transfer co."],
            "future_years": ["1975"],
            "future_doctrinal_concepts": ["pure comparative fault in admiralty", "proportional liability in maritime collisions"],
            "evolutionary_arc_cases": [
                {"case": "Fretz v. Bull", "year": 1851, "citation": "53 U.S. 466"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-10",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "66_0484-01",
            "target_case_name": "United States v. Jackalow",
            "target_case_citation": "66 U.S. 484 (1861)",
            "target_case_year": 1861,
            "query_text": "Under early federal constitutional procedure through 1890, when a criminal offense is committed on a vessel in coastal waters near state shores, does the judge or the jury determine whether the locus of the crime lies within the territorial boundary of a state?",
            "ground_truth_holding": "The maritime boundary of a state and whether an offense occurred within its territorial jurisdiction is a question of fact that must be submitted to and found by the jury under proper legal instructions, rather than decided by the court as a pure matter of law.",
            "required_historical_elements": [
                "territorial boundary is a question of fact for the jury",
                "sixth amendment jury trial requirement",
                "court cannot determine geographic boundary as pure law",
                "jurisdiction locus submitted under special instructions"
            ],
            "forbidden_future_elements": [
                "judicial notice of federal maritime territorial jurisdiction",
                "judge-determined jurisdictional elements under modern federal rules",
                "apprendi line of authority"
            ],
            "future_case_names": ["apprendi v. new jersey", "united states v. gaudin"],
            "future_years": ["1995", "2000"],
            "future_doctrinal_concepts": ["apprendi rule", "gaudin materiality submission requirement"],
            "evolutionary_arc_cases": [
                {"case": "United States v. Bevans", "year": 1818, "citation": "16 U.S. 336"}
            ],
            "metadata_sanitization_verified": True
        },

        # =========================================================================
        # CUTOFF T2 = 1930 (Queries TLP-11 to TLP-20)
        # =========================================================================
        {
            "query_id": "TLP-11",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "261_0525-01",
            "target_case_name": "Adkins v. Children's Hospital",
            "target_case_citation": "261 U.S. 525 (1923)",
            "target_case_year": 1923,
            "query_text": "Under United States constitutional law as of 1930, does an act of Congress fixing minimum wages for adult women employed in private occupations violate the Due Process Clause of the Fifth Amendment?",
            "ground_truth_holding": "An act of Congress prescribing minimum wages for women infringes the freedom of contract protected by the Due Process Clause of the Fifth Amendment, as wage-fixing is an arbitrary interference with private bargaining.",
            "required_historical_elements": [
                "liberty of contract under fifth amendment due process",
                "statutory minimum wage for women is unconstitutional",
                "freedom of contract is the general rule",
                "arbitrary interference with private employment bargaining"
            ],
            "forbidden_future_elements": [
                "west coast hotel v. parrish",
                "repudiation of freedom of contract in minimum wage",
                "rational basis review for economic regulation",
                "fair labor standards act validity"
            ],
            "future_case_names": ["west coast hotel co. v. parrish", "united states v. darby", "nebbia v. new york"],
            "future_years": ["1934", "1937", "1941"],
            "future_doctrinal_concepts": ["demise of substantive economic due process", "rational basis economic review", "parrish repudiation of adkins"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-12",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "247_0251-01",
            "target_case_name": "Hammer v. Dagenhart",
            "target_case_citation": "247 U.S. 251 (1918)",
            "target_case_year": 1918,
            "query_text": "As of 1930, does the Commerce Clause authorize Congress to prohibit the transportation in interstate commerce of manufactured goods produced in factories that employ child labor?",
            "ground_truth_holding": "Congress exceeds its Commerce Clause powers by prohibiting the interstate shipment of goods made by child labor, because the production of goods is a purely local activity reserved to the states under the Tenth Amendment.",
            "required_historical_elements": [
                "production and manufacture are purely local activities",
                "commerce clause does not extend to regulating factory labor conditions",
                "tenth amendment reservation of state police power",
                "goods themselves are harmless in transit"
            ],
            "forbidden_future_elements": [
                "united states v. darby overruling hammer",
                "fair labor standards act commerce power",
                "tenth amendment as a mere truism",
                "substantial effects test"
            ],
            "future_case_names": ["united states v. darby", "wickard v. filburn", "national labor relations board v. jones & laughlin"],
            "future_years": ["1937", "1941", "1942"],
            "future_doctrinal_concepts": ["tenth amendment truism", "modern commerce clause labor standards", "substantial effect doctrine"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-13",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "277_0438-01",
            "target_case_name": "Olmstead v. United States",
            "target_case_citation": "277 U.S. 438 (1928)",
            "target_case_year": 1928,
            "query_text": "Under Fourth Amendment jurisprudence through 1930, does the clandestine interception of telephone conversations by federal agents tapping telephone wires outside a suspect's premises constitute an unconstitutional search and seizure?",
            "ground_truth_holding": "Electronic wiretapping without physical trespass into a defendant's house or office does not violate the Fourth Amendment, which protects only persons, houses, papers, and effects against physical search or seizure of tangible material.",
            "required_historical_elements": [
                "fourth amendment requires physical trespass",
                "wiretapping outside premises is not a search",
                "intangible telephone conversations not protected items",
                "protection limited to persons, houses, papers, and effects"
            ],
            "forbidden_future_elements": [
                "katz reasonable expectation of privacy test",
                "fourth amendment protects people not places",
                "electronic surveillance requires warrant without trespass",
                "title iii omnibus crime control act"
            ],
            "future_case_names": ["katz v. united states", "berger v. new york", "silverman v. united states"],
            "future_years": ["1961", "1967", "1968"],
            "future_doctrinal_concepts": ["reasonable expectation of privacy test", "katz two-prong test", "trespass-free fourth amendment violation"],
            "evolutionary_arc_cases": [
                {"case": "Boyd v. United States", "year": 1886, "citation": "116 U.S. 616"},
                {"case": "Weeks v. United States", "year": 1914, "citation": "232 U.S. 383"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-14",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "221_0001-01",
            "target_case_name": "Standard Oil Co. of New Jersey v. United States",
            "target_case_citation": "221 U.S. 1 (1911)",
            "target_case_year": 1911,
            "query_text": "Tracing federal antitrust doctrine through 1930, what legal standard governs whether a commercial contract, combination, or conspiracy violates Section 1 of the Sherman Antitrust Act?",
            "ground_truth_holding": "Section 1 of the Sherman Act prohibits only contracts, combinations, or agreements that result in an unreasonable or undue restraint of trade, establishing the standard of the Rule of Reason.",
            "required_historical_elements": [
                "rule of reason standard",
                "prohibition of unreasonable or undue restraints",
                "common law standard of restraint of trade",
                "intent and market effect evaluation"
            ],
            "forbidden_future_elements": [
                "per se illegality expansion of socony-vacuum",
                "horizontal territorial allocation per se rule under topco",
                "hart-scott-rodino premerger review"
            ],
            "future_case_names": ["united states v. socony-vacuum oil co.", "united states v. topco associates", "continental t.v. v. gte sylvania"],
            "future_years": ["1940", "1972", "1976", "1977"],
            "future_doctrinal_concepts": ["socony per se price-fixing doctrine", "quick look rule of reason", "modern market power screens"],
            "evolutionary_arc_cases": [
                {"case": "United States v. Trans-Missouri Freight Ass'n", "year": 1897, "citation": "166 U.S. 290"},
                {"case": "United States v. Joint Traffic Ass'n", "year": 1898, "citation": "171 U.S. 505"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-15",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "252_0189-01",
            "target_case_name": "Eisner v. Macomber",
            "target_case_citation": "252 U.S. 189 (1920)",
            "target_case_year": 1920,
            "query_text": "Under federal income tax jurisprudence through 1930, does a bona fide pro-rata stock dividend paid by a corporation in its own stock constitute taxable income to the shareholder under the Sixteenth Amendment?",
            "ground_truth_holding": "A true stock dividend is not taxable income under the Sixteenth Amendment because it does not sever profits from capital or result in realization of gain by the stockholder; it merely increases the number of share certificates representing identical underlying equity.",
            "required_historical_elements": [
                "stock dividend is not income under sixteenth amendment",
                "requirement of realization and severance from capital",
                "shareholder receives no cash or separate property",
                "capital value remains corporate investment"
            ],
            "forbidden_future_elements": [
                "commissioner v. glenshaw glass accession to wealth standard",
                "undeniable accessions to wealth clearly realized",
                "internal revenue code of 1954 section 305 treatment"
            ],
            "future_case_names": ["commissioner v. glenshaw glass co.", "helvering v. griffiths"],
            "future_years": ["1943", "1954", "1955"],
            "future_doctrinal_concepts": ["glenshaw glass accession to wealth definition", "modern corporate distribution tax rules"],
            "evolutionary_arc_cases": [
                {"case": "Pollock v. Farmers' Loan & Trust Co.", "year": 1895, "citation": "158 U.S. 601"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-16",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "180_0486-01",
            "target_case_name": "Li Sing v. United States",
            "target_case_citation": "180 U.S. 486 (1901)",
            "target_case_year": 1901,
            "query_text": "As of 1930, under federal immigration and exclusion statutes, does a decision of a collector of customs denying an alien entry into the United States preclude a judicial commissioner in subsequent deportation proceedings from re-examining the alien's right to remain?",
            "ground_truth_holding": "A customs collector's decision denying entry does not bind or preclude a United States commissioner in subsequent deportation proceedings from examining de novo whether the person is a merchant lawfully entitled to remain.",
            "required_historical_elements": [
                "collector exclusion order not conclusive in deportation proceeding",
                "commissioner has jurisdiction to determine right to remain",
                "statutory distinction between exclusion at port and expulsion from territory",
                "burden of proof on Chinese laborer"
            ],
            "forbidden_future_elements": [
                "administrative procedure act judicial review",
                "modern plenary power doctrine evolution",
                "board of immigration appeals exclusive jurisdiction"
            ],
            "future_case_names": ["shaughnessy v. united states ex rel. mezei", "fiallo v. bell"],
            "future_years": ["1953", "1977"],
            "future_doctrinal_concepts": ["administrative procedure act immigration review", "consular nonreviewability modern doctrine"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-17",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "181_0029-01",
            "target_case_name": "Interstate Commerce Commission v. Clyde Steamship Co.",
            "target_case_citation": "181 U.S. 29 (1901)",
            "target_case_year": 1901,
            "query_text": "Under the Interstate Commerce Act as interpreted through 1930, can the Interstate Commerce Commission find a violation of the Fourth Section long-and-short-haul prohibition without considering substantial competition between carriers at competitive terminal points?",
            "ground_truth_holding": "The Interstate Commerce Commission must take into account carrier and market competition at terminal points, and cannot treat competition as an irrelevant factor when evaluating whether conditions are substantially similar under Section 4.",
            "required_historical_elements": [
                "competition must be considered under section 4",
                "substantially similar circumstances and conditions",
                "long and short haul clause application",
                "railroad and water carrier competitive conditions"
            ],
            "forbidden_future_elements": [
                "transportation act of 1940 fourth section revisions",
                "staggers rail act of 1980 railroad deregulation",
                "icc termination act of 1995 abolition of interstate commerce commission",
                "surface transportation board market dominance test"
            ],
            "future_case_names": [
                "interstate commerce commission v. j-t transport co.",
                "american trucking associations v. united states"
            ],
            "future_years": ["1940", "1980", "1995"],
            "future_doctrinal_concepts": [
                "market dominance standard under staggers rail act",
                "complete administrative rail rate deregulation",
                "surface transportation board transfer of regulatory authority"
            ],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-18",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "186_0126-01",
            "target_case_name": "Felsenheld v. United States",
            "target_case_citation": "186 U.S. 126 (1902)",
            "target_case_year": 1902,
            "query_text": "As of 1930, does the federal excise tax power authorize Congress to prescribe packaging restrictions that prohibit inserting promotional coupons or tickets into taxable tobacco packages?",
            "ground_truth_holding": "Congress possesses constitutional power under the taxing clause to prescribe how taxable articles shall be packaged and to prohibit inserting non-tobacco articles or coupons to facilitate tax collection and prevent fraud.",
            "required_historical_elements": [
                "congressional power to regulate packaging under excise authority",
                "prevention of tax evasion and fraud",
                "prohibition of non-taxed enclosures in tobacco packages",
                "necessary and proper exercise of taxing power"
            ],
            "forbidden_future_elements": [
                "modern commercial speech first amendment scrutiny",
                "central hudson test for commercial promotions",
                "four-part commercial speech intermediate scrutiny"
            ],
            "future_case_names": ["central hudson gas & electric corp. v. public service commission", "virginia state board of pharmacy v. virginia citizens consumer council"],
            "future_years": ["1976", "1980"],
            "future_doctrinal_concepts": ["central hudson commercial speech test", "intermediate scrutiny for commercial promotional enclosures"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-19",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "183_0591-01",
            "target_case_name": "United States Repair & Guarantee Co. v. Assyrian Asphalt Co.",
            "target_case_citation": "183 U.S. 591 (1902)",
            "target_case_year": 1902,
            "query_text": "Under federal patent law through 1930, what standard determines whether an asphalt repair process patent is invalidated when the patentee claims as novel an application of direct heat to melt asphalt that was already disclosed in prior published patents?",
            "ground_truth_holding": "A process patent claiming the application of heat to repair asphalt pavement is invalid for lack of patentable invention when the identical application of heat to soften old asphalt was disclosed in prior art and public use.",
            "required_historical_elements": [
                "anticipation by prior public use and published patents",
                "lack of patentable invention",
                "application of known heat process to asphalt repair",
                "mere mechanical adaptation"
            ],
            "forbidden_future_elements": [
                "patent act of 1952 non-obviousness standard under section 103",
                "graham v. john deere factual inquiries",
                "secondary considerations of non-obviousness"
            ],
            "future_case_names": ["graham v. john deere co.", "khe technology v. teleflex"],
            "future_years": ["1952", "1966", "2007"],
            "future_doctrinal_concepts": ["35 u.s.c. 103 non-obviousness", "graham factors", "secondary considerations of nonobviousness"],
            "evolutionary_arc_cases": [
                {"case": "Smith v. Nichols", "year": 1874, "citation": "88 U.S. 112"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-20",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "199_0048-01",
            "target_case_name": "New York ex rel. Brooklyn City Railroad v. New York State Board of Tax Commissioners",
            "target_case_citation": "199 U.S. 48 (1905)",
            "target_case_year": 1905,
            "query_text": "Tracing Contract Clause doctrine through 1930, does a state statute imposing a special franchise tax on a street railway corporation's tracks in public streets violate its corporate charter when the municipal franchise required prior annual payments?",
            "ground_truth_holding": "A state tax upon a special franchise does not impair the contract contained in the municipal franchise grant; surrender of the sovereign taxing power is never presumed and must be expressed in clear, unambiguous terms.",
            "required_historical_elements": [
                "taxing power is never surrendered by implication",
                "contract clause does not bar franchise taxation",
                "annual license payment is not an exemption from general taxation",
                "strict construction of legislative tax exemptions"
            ],
            "forbidden_future_elements": [
                "complete auto transit four-prong commerce tax test",
                "modern dormant commerce clause nexus requirement",
                "fair apportionment test"
            ],
            "future_case_names": ["complete auto transit, inc. v. brady", "department of revenue of washington v. association of washington stevedoring cos."],
            "future_years": ["1977", "1978"],
            "future_doctrinal_concepts": ["complete auto transit four-part test", "dormant commerce clause substantial nexus"],
            "evolutionary_arc_cases": [
                {"case": "Providence Bank v. Billings", "year": 1830, "citation": "29 U.S. 514"}
            ],
            "metadata_sanitization_verified": True
        },

        # =========================================================================
        # CUTOFF T3 = 1950 (Queries TLP-21 to TLP-30)
        # =========================================================================
        {
            "query_id": "TLP-21",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "334_0001-01",
            "target_case_name": "Shelley v. Kraemer",
            "target_case_citation": "334 U.S. 1 (1948)",
            "target_case_year": 1948,
            "query_text": "As of 1950, does judicial enforcement by state courts of private racially restrictive real estate covenants violate the Equal Protection Clause of the Fourteenth Amendment?",
            "ground_truth_holding": "Judicial enforcement by state courts of private racial restrictive covenants constitutes state action in violation of the Equal Protection Clause of the Fourteenth Amendment, even though the private agreements themselves are not unconstitutional.",
            "required_historical_elements": [
                "state judicial enforcement constitutes state action",
                "fourteenth amendment equal protection violation",
                "private covenants themselves not barred without court enforcement",
                "state coercive power denying property rights on basis of race"
            ],
            "forbidden_future_elements": [
                "fair housing act of 1968 private covenant ban",
                "42 u.s.c. 3604 statutory prohibition on private discrimination",
                "jones v. alfred h. mayer thirteenth amendment reach"
            ],
            "future_case_names": ["jones v. alfred h. mayer co.", "trafficante v. metropolitan life insurance co."],
            "future_years": ["1968", "1972"],
            "future_doctrinal_concepts": ["fair housing act private covenant invalidity", "thirteenth amendment badging of slavery in private housing"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-22",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "317_0111-01",
            "target_case_name": "Wickard v. Filburn",
            "target_case_citation": "317 U.S. 111 (1942)",
            "target_case_year": 1942,
            "query_text": "As of 1950, does the Commerce Clause authorize Congress to regulate wheat grown purely for home consumption on an individual farm under federal agricultural marketing quotas?",
            "ground_truth_holding": "Congress possesses Commerce Clause authority to regulate wheat grown solely for on-farm home consumption because that home-grown wheat, when aggregated across many farmers, exerts a substantial economic effect on interstate commerce.",
            "required_historical_elements": [
                "substantial economic effect on interstate commerce",
                "aggregation principle across individual producers",
                "home consumption wheat overhangs and affects market price",
                "commerce power extends to activities exerting substantial economic impact"
            ],
            "forbidden_future_elements": [
                "united states v. lopez commercial versus non-commercial distinction",
                "united states v. morrison non-economic aggregation limits",
                "national federation of independent business v. sebelius activity versus inactivity"
            ],
            "future_case_names": ["united states v. lopez", "united states v. morrison", "national federation of independent business v. sebelius"],
            "future_years": ["1995", "2000", "2012"],
            "future_doctrinal_concepts": ["commercial activity requirement for aggregation", "traditional state sovereignty areas commerce barrier", "inactivity mandate limitation"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-23",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "316_0455-01",
            "target_case_name": "Betts v. Brady",
            "target_case_citation": "316 U.S. 455 (1942)",
            "target_case_year": 1942,
            "query_text": "Under United States constitutional law as of 1950, does the Due Process Clause of the Fourteenth Amendment require a state court to appoint counsel for an indigent defendant in every non-capital felony prosecution?",
            "ground_truth_holding": "The Due Process Clause of the Fourteenth Amendment does not require appointment of counsel for indigent felony defendants in all state non-capital prosecutions; appointment is required only where special circumstances demonstrate that lack of counsel results in fundamental unfairness.",
            "required_historical_elements": [
                "fourteenth amendment does not incorporate sixth amendment counsel guarantee",
                "no absolute right to counsel in non-capital state cases",
                "special circumstances test",
                "case-by-case totality of circumstances evaluation"
            ],
            "forbidden_future_elements": [
                "gideon v. wainwright automatic appointment rule",
                "sixteenth amendment counsel incorporated against states",
                "fundamental right to counsel in all felony cases"
            ],
            "future_case_names": ["gideon v. wainwright", "argersinger v. hamlin"],
            "future_years": ["1963", "1972"],
            "future_doctrinal_concepts": ["universal right to counsel in felony prosecutions", "gideon overruling of betts", "counsel requirement for actual imprisonment"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-24",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "310_0150-01",
            "target_case_name": "United States v. Socony-Vacuum Oil Co.",
            "target_case_citation": "310 U.S. 150 (1940)",
            "target_case_year": 1940,
            "query_text": "Tracing Sherman Act Section 1 jurisprudence through 1950, what legal standard governs an agreement among competing oil refiners to purchase surplus gasoline from independent distress refiners to stabilize market prices?",
            "ground_truth_holding": "Any combination or agreement formed for the purpose and with the effect of raising, depressing, fixing, pegging, or stabilizing market prices is illegal per se under Section 1 of the Sherman Act, regardless of reasonableness or economic distress.",
            "required_historical_elements": [
                "per se illegality of horizontal price-fixing",
                "price stabilization is illegal price-fixing",
                "reasonableness of price is no defense",
                "economic distress or ruinous competition does not justify agreement"
            ],
            "forbidden_future_elements": [
                "broadcast music, inc. v. cbs blanket license rule of reason",
                "ncaa v. board of regents quick look exception",
                "procompetitive price coordination analysis"
            ],
            "future_case_names": ["broadcast music, inc. v. columbia broadcasting system", "national collegiate athletic ass'n v. board of regents of university of oklahoma", "california dental ass'n v. ftc"],
            "future_years": ["1979", "1984", "1999"],
            "future_doctrinal_concepts": ["bmi integration exception to per se rule", "quick look analysis in sports associations", "procompetitive justification for joint pricing"],
            "evolutionary_arc_cases": [
                {"case": "United States v. Trenton Potteries Co.", "year": 1927, "citation": "273 U.S. 392"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-25",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "338_0025-01",
            "target_case_name": "Wolf v. Colorado",
            "target_case_citation": "338 U.S. 25 (1949)",
            "target_case_year": 1949,
            "query_text": "Under constitutional criminal procedure through 1950, does the Fourteenth Amendment Due Process Clause forbid a state court from admitting evidence obtained in an unreasonable search and seizure conducted by state police?",
            "ground_truth_holding": "Although the security of one's privacy against arbitrary intrusion by state police is implicit in ordered liberty under the Fourteenth Amendment, the federal exclusionary rule is not a departure requirement imposed upon the states, leaving states free to adopt other remedies.",
            "required_historical_elements": [
                "fourteenth amendment does not impose exclusionary rule on state courts",
                "exclusionary rule is a judicially created remedy for federal courts",
                "states may rely on tort remedies or police discipline",
                "core privacy protected but remedy not incorporated"
            ],
            "forbidden_future_elements": [
                "mapp v. ohio mandatory incorporation of exclusionary rule",
                "fourteenth amendment requires suppression of unconstitutionally seized evidence in state court",
                "deterrence rationale requiring nationwide suppression"
            ],
            "future_case_names": ["mapp v. ohio", "linkletter v. walker"],
            "future_years": ["1961", "1965"],
            "future_doctrinal_concepts": ["mapp mandatory state exclusionary rule", "total incorporation of exclusionary rule"],
            "evolutionary_arc_cases": [
                {"case": "Weeks v. United States", "year": 1914, "citation": "232 U.S. 383"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-26",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "339_0605-01",
            "target_case_name": "Graver Tank & Mfg. Co. v. Linde Air Products Co.",
            "target_case_citation": "339 U.S. 605 (1950)",
            "target_case_year": 1950,
            "query_text": "Under federal patent jurisprudence as of 1950, what legal doctrine permits a patentee to recover for infringement when an accused welding composition does not fall within the literal terms of the patent claim but performs substantially the same function in substantially the same way?",
            "ground_truth_holding": "The doctrine of equivalents allows a finding of patent infringement when an accused composition performs substantially the same function in substantially the same way to achieve the same result as the patented invention, preventing an infringer from making unimportant substitutions to escape liability.",
            "required_historical_elements": [
                "doctrine of equivalents",
                "substantially the same function in substantially the same way to achieve the same result",
                "equating known interchangeable elements",
                "finding of equivalence is a question of fact"
            ],
            "forbidden_future_elements": [
                "warner-jenkinson all-elements rule",
                "festo prosecution history estoppel presumption",
                "doctrine of equivalents limited to element-by-element analysis"
            ],
            "future_case_names": ["warner-jenkinson co. v. hilton davis chemical co.", "festo corp. v. shoketsu kinzoku kogyo kabushiki co."],
            "future_years": ["1997", "2002"],
            "future_doctrinal_concepts": ["all elements rule for doctrine of equivalents", "festo complete bar presumption", "prosecution history estoppel rebuttal standards"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-27",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "282_0270-01",
            "target_case_name": "Stange v. United States",
            "target_case_citation": "282 U.S. 270 (1931)",
            "target_case_year": 1931,
            "query_text": "Under federal revenue statutes as of 1950, is a taxpayer's written waiver extending the statutory assessment period for income tax valid when executed after the statutory limitations period has already expired?",
            "ground_truth_holding": "A taxpayer's written waiver consenting to determination and assessment of income taxes after expiration of the statutory period is valid and enforceable, as a tax waiver is not a contract requiring mutual consideration but a statutory relinquishment of a defense.",
            "required_historical_elements": [
                "tax assessment waiver valid even after limitation period expired",
                "waiver is not a contract requiring fresh consideration",
                "statutory relinquishment of bar to collection",
                "congressional authority to permit waivers"
            ],
            "forbidden_future_elements": [
                "internal revenue code of 1954 section 6501 limitation",
                "internal revenue service restructuring and reform act waiver advisement requirements"
            ],
            "future_case_names": [],
            "future_years": ["1954", "1998"],
            "future_doctrinal_concepts": ["mandatory taxpayer notification of rights to refuse waiver", "irc 6501 strict pre-expiration execution rules"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-28",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "287_0129-01",
            "target_case_name": "United States ex rel. Stapf v. Corsi",
            "target_case_citation": "287 U.S. 129 (1932)",
            "target_case_year": 1932,
            "query_text": "Tracing statutory immigration jurisprudence through 1950, does an alien seaman who previously resided in the United States and briefly ships out on a foreign vessel re-enter the country as a new arrival subject to contemporary statutory deportation bars upon return?",
            "ground_truth_holding": "An alien seaman who departs the United States on a foreign vessel and returns makes a new entry into the United States, and is subject to the deportation provisions of the immigration statutes in effect at the time of that re-entry.",
            "required_historical_elements": [
                "re-entry doctrine applies to alien seamen",
                "departure on foreign vessel constitutes departure from territory",
                "return is a new entry subject to prevailing statutory grounds",
                "statutory limitations run from date of last entry"
            ],
            "forbidden_future_elements": [
                "rosenberg v. fleuti brief casual and innocent absence exception",
                "immigration and nationality act illegal immigration reform and immigrant responsibility act of 1996 admission standard",
                "fleuti doctrine"
            ],
            "future_case_names": ["rosenberg v. fleuti", "landon v. plasencia"],
            "future_years": ["1963", "1982", "1996"],
            "future_doctrinal_concepts": ["fleuti brief casual and innocent absence rule", "iirira admission definition replacing entry doctrine"],
            "evolutionary_arc_cases": [
                {"case": "United States ex rel. Claussen v. Day", "year": 1929, "citation": "279 U.S. 398"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-29",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "263_0403-01",
            "target_case_name": "National Ass'n of Window Glass Manufacturers v. United States",
            "target_case_citation": "263 U.S. 403 (1923)",
            "target_case_year": 1923,
            "query_text": "Tracing antitrust jurisprudence through 1950, does an agreement between handblown glass manufacturers and a national labor union dividing scarce workers between two sets of factories operating at alternating periods of the year violate Section 1 of the Sherman Act as an unlawful restraint of trade?",
            "ground_truth_holding": "An agreement between manufacturers and a union dividing the scarce labor supply between two sets of factories operating at alternating periods, necessitated by an acute labor shortage caused by machine competition, does not violate Section 1 of the Sherman Act when evaluated under the rule of reason, as it regulates the employment of labor in production rather than commercial market prices or sales distribution.",
            "required_historical_elements": [
                "rule of reason analysis under sherman act section 1",
                "agreement regulating employment of union labor in production",
                "justified by acute labor shortage and machine competition",
                "does not fix commercial prices or restrain sales distribution"
            ],
            "forbidden_future_elements": [
                "per se horizontal market division under topco",
                "modern statutory labor exemption balancing under connecticut v. harlan",
                "quick-look rule of reason framework"
            ],
            "future_case_names": ["united states v. topco associates, inc.", "broadcasting music, inc. v. columbia broadcasting system", "ftc v. superior court trial lawyers ass'n"],
            "future_years": ["1972", "1979", "1990"],
            "future_doctrinal_concepts": ["per se horizontal market allocation standard", "quick-look rule of reason analysis", "statutory labor antitrust exemption balancing"],
            "evolutionary_arc_cases": [
                {"case": "Board of Trade of Chicago v. United States", "year": 1918, "citation": "246 U.S. 231"},
                {"case": "United Mine Workers of America v. Coronado Coal Co.", "year": 1922, "citation": "259 U.S. 344"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-30",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "300_0105-01",
            "target_case_name": "Hill v. United States ex rel. Weiner",
            "target_case_citation": "300 U.S. 105 (1937)",
            "target_case_year": 1937,
            "query_text": "Tracing statutory criminal contempt and habeas corpus jurisprudence through 1950, does the six-month statutory limitation on imprisonment for contempt under Section 22 of the Clayton Act apply to a defendant sentenced for criminal contempt arising from the violation of an injunction entered in a suit brought by the United States?",
            "ground_truth_holding": "Under Section 24 of the Clayton Act, the six-month limitation on imprisonment prescribed in Section 22 does not apply to criminal contempts committed in disobedience of any decree entered in a suit brought or prosecuted on behalf of the United States; such contempts may be punished under the court's general authority.",
            "required_historical_elements": [
                "clayton act section 24 exception for united states suits",
                "six-month limitation of section 22 inapplicable",
                "contempt of decree entered in government enforcement action",
                "court retains power to impose sentence beyond statutory six months"
            ],
            "forbidden_future_elements": [
                "bloom v. illinois constitutional right to jury trial for serious criminal contempt",
                "codispoti v. pennsylvania jury trial aggregation rule",
                "cheff v. schnackenberg six-month petty offense boundary"
            ],
            "future_case_names": ["bloom v. illinois", "cheff v. schnackenberg", "codispoti v. pennsylvania"],
            "future_years": ["1966", "1968", "1974"],
            "future_doctrinal_concepts": ["bloom constitutional jury trial requirement for criminal contempt", "six-month penalty threshold for petty criminal contempt", "fourteenth amendment jury trial right in state contempt proceedings"],
            "evolutionary_arc_cases": [
                {"case": "United States v. Goldman", "year": 1928, "citation": "277 U.S. 229"}
            ],
            "metadata_sanitization_verified": True
        },

        # =========================================================================
        # CUTOFF T4 = 1970 (Queries TLP-31 to TLP-40)
        # =========================================================================
        {
            "query_id": "TLP-31",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "347_0483-01",
            "target_case_name": "Brown v. Board of Education",
            "target_case_citation": "347 U.S. 483 (1954)",
            "target_case_year": 1954,
            "query_text": "As of 1970, does racial segregation of children in public schools pursuant to state statutes violate the Equal Protection Clause of the Fourteenth Amendment even if physical facilities are equal?",
            "ground_truth_holding": "Racial segregation of children in public schools deprives minority children of equal educational opportunities and violates the Equal Protection Clause of the Fourteenth Amendment; separate educational facilities are inherently unequal.",
            "required_historical_elements": [
                "separate educational facilities are inherently unequal",
                "fourteenth amendment equal protection clause violation",
                "deprivation of equal educational opportunity",
                "repudiation of separate but equal doctrine in public education"
            ],
            "forbidden_future_elements": [
                "milliken v. bradley cross-district busing prohibition",
                "parents involved voluntary integration strict scrutiny limits",
                "affirmative action university admissions quotas"
            ],
            "future_case_names": ["milliken v. bradley", "regents of university of california v. bakke", "parents involved in community schools v. seattle school district no. 1"],
            "future_years": ["1974", "1978", "2007"],
            "future_doctrinal_concepts": ["interdistrict desegregation remedies barrier", "strict scrutiny for race-conscious school assignment"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-32",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "384_0436-01",
            "target_case_name": "Miranda v. Arizona",
            "target_case_citation": "384 U.S. 436 (1966)",
            "target_case_year": 1966,
            "query_text": "Under Fifth Amendment jurisprudence as of 1970, what procedural warnings must law enforcement officers administer before conducting custodial interrogation of a suspect to permit admission of resulting statements in a criminal prosecution?",
            "ground_truth_holding": "Prior to custodial interrogation, a suspect must be warned that they have the right to remain silent, that any statement made may be used against them in court, that they have the right to the presence of an attorney, and that an attorney will be appointed if indigent.",
            "required_historical_elements": [
                "right to remain silent warning",
                "warning that statements may be used against suspect",
                "right to presence of counsel during questioning",
                "right to appointed counsel if indigent"
            ],
            "forbidden_future_elements": [
                "dickerson v. united states constitutionalization debate",
                "berghuis v. thompkins explicit invocation requirement",
                "harris v. new york impeachment exception",
                "new york v. quarles public safety exception"
            ],
            "future_case_names": ["harris v. new york", "new york v. quarles", "dickerson v. united states", "berghuis v. thompkins"],
            "future_years": ["1971", "1984", "2000", "2010"],
            "future_doctrinal_concepts": ["public safety exception to miranda", "impeachment exception to miranda", "unambiguous invocation of right to silence"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-33",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "381_0479-01",
            "target_case_name": "Griswold v. Connecticut",
            "target_case_citation": "381 U.S. 479 (1965)",
            "target_case_year": 1965,
            "query_text": "Tracing constitutional privacy doctrine through 1970, does a state statute prohibiting the use of contraceptives by married couples violate the United States Constitution?",
            "ground_truth_holding": "A state statute forbidding the use of contraceptives by married persons violates the constitutional right of marital privacy, which is protected within the penumbras and emanations of the Bill of Rights (First, Third, Fourth, Fifth, and Ninth Amendments).",
            "required_historical_elements": [
                "right of marital privacy",
                "penumbras and emanations of specific bill of rights guarantees",
                "statute forbidding contraceptive use is an unconstitutional invasion",
                "intrusive policing of marital bedroom is intolerable"
            ],
            "forbidden_future_elements": [
                "eisenstadt v. baird unmarried individual privacy extension",
                "roe v. wade constitutional right to abortion",
                "dobbs v. jackson women's health organization overruling",
                "trimester framework"
            ],
            "future_case_names": ["eisenstadt v. baird", "roe v. wade", "planned parenthood of southeastern pennsylvania v. casey", "dobbs v. jackson women's health organization"],
            "future_years": ["1972", "1973", "1992", "2022"],
            "future_doctrinal_concepts": ["individual right to contraception outside marriage", "trimester abortion framework", "viability standard", "undue burden standard"],
            "evolutionary_arc_cases": [
                {"case": "Meyer v. Nebraska", "year": 1923, "citation": "262 U.S. 390"},
                {"case": "Pierce v. Society of Sisters", "year": 1925, "citation": "268 U.S. 510"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-34",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "392_0001-01",
            "target_case_name": "Terry v. Ohio",
            "target_case_citation": "392 U.S. 1 (1968)",
            "target_case_year": 1968,
            "query_text": "Tracing Fourth Amendment jurisprudence through 1970, what standard authorizes a police officer on the street to stop a person and conduct a protective pat-down search for weapons in the absence of probable cause for arrest?",
            "ground_truth_holding": "A police officer may conduct a brief investigatory stop and a limited pat-down frisk of outer clothing for weapons if the officer possesses reasonable, articulable suspicion based on specific facts that criminal activity is afoot and the person may be armed and dangerous.",
            "required_historical_elements": [
                "reasonable articulable suspicion standard",
                "specific and articulable facts, not inchoate hunches",
                "limited protective pat-down for weapons",
                "distinction between brief investigative stop and formal arrest"
            ],
            "forbidden_future_elements": [
                "illinois v. wardlow unprovoked flight in high crime area rule",
                "whren v. united states pretextual stop doctrine",
                "minnesota v. dickerson plain feel doctrine"
            ],
            "future_case_names": ["whren v. united states", "minnesota v. dickerson", "illinois v. wardlow"],
            "future_years": ["1993", "1996", "2000"],
            "future_doctrinal_concepts": ["plain feel doctrine for non-weapons", "pretextual traffic stop objective reasonableness test", "unprovoked flight high crime area rule"],
            "evolutionary_arc_cases": [
                {"case": "Carroll v. United States", "year": 1925, "citation": "267 U.S. 132"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-35",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "377_0665-01",
            "target_case_name": "Reynolds v. Sims",
            "target_case_citation": "377 U.S. 533 (1964)",
            "target_case_year": 1964,
            "query_text": "Tracing voting rights doctrine through 1970, does the Equal Protection Clause of the Fourteenth Amendment require state legislative apportionment to construct districts of substantially equal population in both houses of a bicameral state legislature?",
            "ground_truth_holding": "The Equal Protection Clause requires both houses of a bicameral state legislature to be apportioned substantially on a population basis, ensuring that as nearly as practicable each citizen's vote is debased or diluted (the one person, one vote rule).",
            "required_historical_elements": [
                "one person, one vote principle",
                "both houses of bicameral legislature must be based on population",
                "vote dilution violates fourteenth amendment equal protection",
                "rejection of federal senate analogy for state legislatures"
            ],
            "forbidden_future_elements": [
                "voting rights act of 1982 section 2 results test",
                "thornburg v. gingles majority-minority redistricting rules",
                "rucho v. common cause non-justiciability of partisan gerrymandering"
            ],
            "future_case_names": ["thornburg v. gingles", "shaw v. reno", "rucho v. common cause"],
            "future_years": ["1982", "1986", "1993", "2019"],
            "future_doctrinal_concepts": ["gingles three-prong minority vote dilution test", "shaw racial gerrymandering strict scrutiny", "rucho partisan gerrymandering non-justiciability"],
            "evolutionary_arc_cases": [
                {"case": "Baker v. Carr", "year": 1962, "citation": "369 U.S. 186"},
                {"case": "Gray v. Sanders", "year": 1963, "citation": "372 U.S. 368"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-36",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "362_0145-01",
            "target_case_name": "Flora v. United States",
            "target_case_citation": "362 U.S. 145 (1960)",
            "target_case_year": 1960,
            "query_text": "Under federal tax refund jurisdictional statutes as of 1970, can a taxpayer maintain a tax refund suit in federal district court under 28 U.S.C. Section 1346(a)(1) after paying only a partial payment of the assessed income tax deficiency?",
            "ground_truth_holding": "A federal district court lacks jurisdiction over a taxpayer's tax refund suit under 28 U.S.C. 1346(a)(1) unless the taxpayer has fully paid the entire assessed tax deficiency before commencing the action (the full payment rule).",
            "required_historical_elements": [
                "full payment rule for tax refund jurisdiction",
                "28 u.s.c. 1346(a)(1) requires complete payment of assessment",
                "partial payment does not confer district court jurisdiction",
                "tax court is available forum for pre-payment challenges"
            ],
            "forbidden_future_elements": [
                "internal revenue service restructuring and reform act exceptions",
                "equitable recoupment expansion under modern precedents"
            ],
            "future_case_names": ["united states v. dalm"],
            "future_years": ["1990", "1998"],
            "future_doctrinal_concepts": ["qualified offer rule for litigation fees", "statutory exceptions to full payment rule in collection due process"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-37",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "370_0460-01",
            "target_case_name": "United States v. Borden Co.",
            "target_case_citation": "370 U.S. 460 (1962)",
            "target_case_year": 1962,
            "query_text": "Under the Robinson-Patman Act as interpreted through 1970, can a seller establish a valid cost-justification defense for charging different prices to customer classes based on broad average cost grouping across customers?",
            "ground_truth_holding": "A seller claiming a cost-justification defense under Robinson-Patman Section 2(a) cannot rely on arbitrary or overly broad customer groupings; cost justification requires that customer classes be composed of members of such self-sameness as to make average cost representative of individual members.",
            "required_historical_elements": [
                "cost-justification defense requirements",
                "customer groupings must show true cost self-sameness",
                "arbitrary customer classifications invalid",
                "robinson-patman act section 2(a) strict defense scrutiny"
            ],
            "forbidden_future_elements": [
                "brooke group predatory pricing price-cost test",
                "modern economic critique of robinson-patman act enforcement"
            ],
            "future_case_names": ["brooke group ltd. v. brown & williamson tobacco corp.", "volvo trucks north america, inc. v. reeder-simco gmc, inc."],
            "future_years": ["1993", "2006"],
            "future_doctrinal_concepts": ["brooke group price-cost test", "recoupment requirement for predatory pricing", "secondary line competitive injury revision"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-38",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "342_0371-01",
            "target_case_name": "United States v. New Wrinkle, Inc.",
            "target_case_citation": "342 U.S. 371 (1952)",
            "target_case_year": 1952,
            "query_text": "As of 1970, does the patent monopoly shield a patent-holding company and its manufacturing licensees from Sherman Act Section 1 liability when competing patent holders pool patents and require all industry licensees to adhere to minimum price schedules?",
            "ground_truth_holding": "Patentees cannot pool competing patents in a holding corporation and license the entire industry subject to mandatory uniform minimum prices; such price-fixing agreements across an industry exceed patent rights and violate Section 1 of the Sherman Act.",
            "required_historical_elements": [
                "patent pool cannot fix industry-wide prices",
                "exceeds scope of patent monopoly",
                "sherman act section 1 violation",
                "patent rights cannot shield industry-wide price fixing"
            ],
            "forbidden_future_elements": [
                "doj/ftc antitrust guidelines for licensing of intellectual property",
                "modern patent pool rule of reason analysis",
                "standard essential patent fair reasonable and non-discriminatory commitments"
            ],
            "future_case_names": ["ftc v. actavis, inc."],
            "future_years": ["1995", "2013"],
            "future_doctrinal_concepts": ["actavis reverse payment antitrust standard", "frand royalty licensing framework", "safe harbor for cross-licensing packages"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-39",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "366_0169-01",
            "target_case_name": "Brotherhood of Maintenance of Way Employes v. United States",
            "target_case_citation": "366 U.S. 169 (1961)",
            "target_case_year": 1961,
            "query_text": "Tracing railroad regulatory jurisprudence through 1970, does Section 5(2)(f) of the Interstate Commerce Act require the Interstate Commerce Commission to mandate that a merging railroad company retain all employees in active service throughout a 4-year statutory protection period?",
            "ground_truth_holding": "Section 5(2)(f) of the Interstate Commerce Act does not require the mandatory preservation of active employment positions on merging railroads; its requirement that employees not be left in a worse position is satisfied by financial compensation for displaced workers.",
            "required_historical_elements": [
                "interstate commerce act section 5(2)(f)",
                "active employment retention not mandatory",
                "financial compensation satisfies protective standard",
                "merging carrier efficiency versus employee protection"
            ],
            "forbidden_future_elements": [
                "regional rail reorganization act of 1973 conrail labor protection",
                "surface transportation board modern labor protective conditions",
                "new york dock conditions"
            ],
            "future_case_names": ["norfolk & western railway co. v. american train dispatchers' ass'n"],
            "future_years": ["1973", "1979", "1991"],
            "future_doctrinal_concepts": ["new york dock arbitration requirements", "staggers act merger labor conditions"],
            "evolutionary_arc_cases": [
                {"case": "United States v. Lowden", "year": 1939, "citation": "308 U.S. 225"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-40",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "388_0350-01",
            "target_case_name": "United States v. Sealy, Inc.",
            "target_case_citation": "388 U.S. 350 (1967)",
            "target_case_year": 1967,
            "query_text": "Under Section 1 of the Sherman Act as interpreted through 1970, does an arrangement by which licensee-manufacturers who own and control a trademark licensing company agree to assign mutually exclusive territorial sales markets to each manufacturer constitute an unlawful per se restraint of trade?",
            "ground_truth_holding": "An arrangement under which mattress manufacturers owning substantially all stock in a trademark licensing company agree to allocate mutually exclusive territorial sales markets among themselves is a horizontal restraint of trade that constitutes a per se violation of Section 1 of the Sherman Act without inquiry into its business reasonableness.",
            "required_historical_elements": [
                "horizontal territorial market allocation",
                "licensee control of trademark licensing entity",
                "per se illegality under sherman act section 1",
                "mutually exclusive sales territories among competitors"
            ],
            "forbidden_future_elements": [
                "continental t.v. v. gte sylvania rule of reason for non-price restrictions",
                "united states v. topco associates extension to grocery cooperatives",
                "broadcast music v. cbs rule of reason integration",
                "business electronics corp. sharp electronics interbrand competition"
            ],
            "future_case_names": [
                "united states v. topco associates, inc.",
                "continental t.v., inc. v. gte sylvania inc.",
                "broadcast music, inc. v. columbia broadcasting system, inc.",
                "business electronics corp. v. sharp electronics corp."
            ],
            "future_years": ["1972", "1977", "1979", "1988"],
            "future_doctrinal_concepts": [
                "gte sylvania economic efficiency and interbrand competition standard",
                "vertical non-price territorial restrictions governed by rule of reason",
                "topco strict horizontal allocation per se ban extension"
            ],
            "evolutionary_arc_cases": [
                {"case": "Timken Roller Bearing Co. v. United States", "year": 1951, "citation": "341 U.S. 593"},
                {"case": "Addyston Pipe & Steel Co. v. United States", "year": 1899, "citation": "175 U.S. 211"}
            ],
            "metadata_sanitization_verified": True
        },

        # =========================================================================
        # CUTOFF T5 = 1980 (Queries TLP-41 to TLP-50)
        # =========================================================================
        {
            "query_id": "TLP-41",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "410_0113-01",
            "target_case_name": "Roe v. Wade",
            "target_case_citation": "410 U.S. 113 (1973)",
            "target_case_year": 1973,
            "query_text": "Under United States constitutional law as of 1980, does the Fourteenth Amendment Due Process Clause protect a pregnant woman's fundamental right to terminate a pregnancy prior to fetal viability?",
            "ground_truth_holding": "The constitutional right of personal privacy grounded in the Fourteenth Amendment Due Process Clause encompasses a woman's qualified right to terminate her pregnancy; states may regulate abortion only pursuant to compelling state interests under the trimester framework, and may prohibit abortion after fetal viability except when necessary to preserve the life or health of the mother.",
            "required_historical_elements": [
                "fourteenth amendment due process privacy protects abortion",
                "trimester framework",
                "compelling state interest standard",
                "fetal viability threshold for state prohibition"
            ],
            "forbidden_future_elements": [
                "dobbs v. jackson women's health organization overruling roe",
                "elimination of federal constitutional right to abortion",
                "planned parenthood v. casey undue burden standard",
                "rational basis review for state abortion bans"
            ],
            "future_case_names": ["planned parenthood of southeastern pennsylvania v. casey", "dobbs v. jackson women's health organization"],
            "future_years": ["1992", "2022"],
            "future_doctrinal_concepts": ["undue burden standard", "dobbs repudiation of constitutional abortion right", "state constitutional history history-and-tradition standard"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-42",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case_node_id": "426_0833-01",
            "target_case_name": "National League of Cities v. Usery",
            "target_case_citation": "426 U.S. 833 (1976)",
            "target_case_year": 1976,
            "query_text": "As of 1980, does the Tenth Amendment prohibit Congress from applying the minimum wage and overtime provisions of the Fair Labor Standards Act to state and municipal employees engaged in traditional governmental functions?",
            "ground_truth_holding": "The Tenth Amendment and structural principles of federalism limit the Commerce Clause power by barring Congress from applying federal minimum wage and overtime requirements to states in areas of traditional governmental functions.",
            "required_historical_elements": [
                "tenth amendment limits commerce clause reach over states",
                "traditional governmental functions immunity",
                "state sovereignty barrier against federal wage mandates",
                "flsa amendments unconstitutional as applied to state sovereign functions"
            ],
            "forbidden_future_elements": [
                "garcia v. san antonio metropolitan transit authority overruling",
                "procedural safeguards of federalism replacing traditional functions test",
                "flsa fully applicable to state and municipal employees"
            ],
            "future_case_names": ["garcia v. san antonio metropolitan transit authority", "new york v. united states", "printz v. united states"],
            "future_years": ["1985", "1992", "1997"],
            "future_doctrinal_concepts": ["garcia procedural federalism doctrine", "anti-commandeering doctrine", "traditional governmental functions unworkability"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-43",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Constitutional Law & Civil Rights",
            "target_case_node_id": "429_0190-01",
            "target_case_name": "Craig v. Boren",
            "target_case_citation": "429 U.S. 190 (1976)",
            "target_case_year": 1976,
            "query_text": "As of 1980, what standard of equal protection review applies under the Fourteenth Amendment to state statutes that draw explicit regulatory distinctions on the basis of sex?",
            "ground_truth_holding": "Classifications based on gender must serve important governmental objectives and must be substantially related to the achievement of those objectives to withstand scrutiny under the Equal Protection Clause (intermediate scrutiny).",
            "required_historical_elements": [
                "intermediate scrutiny standard for gender classifications",
                "important governmental objectives requirement",
                "substantially related means requirement",
                "rejection of mere rational basis review for gender distinctions"
            ],
            "forbidden_future_elements": [
                "united states v. virginia exceedingly persuasive justification standard",
                "strict scrutiny for all sex classifications",
                "equal rights amendment ratification"
            ],
            "future_case_names": ["united states v. virginia", "rostker v. goldberg", "mississippi university for women v. hogan"],
            "future_years": ["1981", "1982", "1996"],
            "future_doctrinal_concepts": ["exceedingly persuasive justification standard", "heightened intermediate scrutiny"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-44",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case_node_id": "413_0015-01",
            "target_case_name": "Miller v. California",
            "target_case_citation": "413 U.S. 15 (1973)",
            "target_case_year": 1973,
            "query_text": "Tracing First Amendment jurisprudence through 1980, what three-prong legal test determines whether expressive sexual materials constitute obscenity unprotected by constitutional speech guarantees?",
            "ground_truth_holding": "Material is obscene if: (a) the average person applying contemporary community standards would find the work taken as a whole appeals to the prurient interest; (b) the work depicts in a patently offensive way sexual conduct specifically defined by applicable state law; and (c) the work taken as a whole lacks serious literary, artistic, political, or scientific value.",
            "required_historical_elements": [
                "contemporary community standards prurient interest test",
                "patently offensive depiction of sexual conduct defined by statute",
                "lacks serious literary, artistic, political, or scientific value (slaps test)",
                "rejection of utterly without redeeming social value standard"
            ],
            "forbidden_future_elements": [
                "reno v. aclu internet communications decency act standard",
                "ashcroft v. free speech coalition virtual depiction protection",
                "child internet protection act filtering standard"
            ],
            "future_case_names": ["reno v. aclu", "ashcroft v. free speech coalition", "pope v. illinois"],
            "future_years": ["1987", "1997", "2002"],
            "future_doctrinal_concepts": ["national reasonable person standard for value prong", "internet obscenity application under cda"],
            "evolutionary_arc_cases": [
                {"case": "Roth v. United States", "year": 1957, "citation": "354 U.S. 476"},
                {"case": "Memoirs v. Massachusetts", "year": 1966, "citation": "383 U.S. 413"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-45",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case_node_id": "428_0153-01",
            "target_case_name": "Gregg v. Georgia",
            "target_case_citation": "428 U.S. 153 (1976)",
            "target_case_year": 1976,
            "query_text": "Tracing Eighth Amendment capital punishment jurisprudence through 1980, what statutory sentencing framework is required to impose the death penalty for murder without violating the prohibition against cruel and unusual punishments?",
            "ground_truth_holding": "The death penalty does not invariably violate the Eighth Amendment if imposed under a bifurcated trial procedure with guided discretion, where the sentencing authority must find specific statutory aggravating circumstances and consider individualized mitigating circumstances.",
            "required_historical_elements": [
                "death penalty is not per se cruel and unusual punishment",
                "bifurcated guilt and sentencing phases",
                "guided discretion through statutory aggravating circumstances",
                "sentencer consideration of individualized mitigating factors"
            ],
            "forbidden_future_elements": [
                "atkins v. virginia intellectual disability capital ban",
                "roper v. simmons juvenile capital ban",
                "kennedy v. louisiana non-homicide capital ban"
            ],
            "future_case_names": ["atkins v. virginia", "roper v. simmons", "kennedy v. louisiana"],
            "future_years": ["2002", "2005", "2008"],
            "future_doctrinal_concepts": ["categorical ban on execution of intellectually disabled offenders", "categorical ban on juvenile offenders", "non-homicide capital ban"],
            "evolutionary_arc_cases": [
                {"case": "Furman v. Georgia", "year": 1972, "citation": "408 U.S. 238"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-46",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "435_0561-01",
            "target_case_name": "Frank Lyon Co. v. United States",
            "target_case_citation": "435 U.S. 561 (1978)",
            "target_case_year": 1978,
            "query_text": "Under federal income tax law as of 1980, what legal standard determines whether a three-party sale-and-leaseback of commercial real estate will be respected as a genuine transaction entitling the lessor to depreciation deductions rather than treated as a financing loan?",
            "ground_truth_holding": "Where there is a genuine multiple-party transaction with economic substance that is compelled or encouraged by business or regulatory realities, is imbued with tax-independent considerations, and is not shaped solely by tax avoidance, the lessor is respected as the owner entitled to statutory tax deductions.",
            "required_historical_elements": [
                "economic substance standard for sale leaseback",
                "business realities independent of tax avoidance",
                "multi-party transaction regulatory and commercial motives",
                "lessor entitled to depreciation and interest deductions"
            ],
            "forbidden_future_elements": [
                "codified economic substance doctrine under 26 u.s.c. section 7701(o)",
                "strict two-prong objective and subjective economic substance test"
            ],
            "future_case_names": ["coltec industries, inc. v. united states"],
            "future_years": ["2006", "2010"],
            "future_doctrinal_concepts": ["codified section 7701(o) economic substance rules", "strict conjunction economic substance test"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-47",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 1,
            "reasoning_depth_type": "Direct Holding Lookup",
            "domain": "Antitrust & Corporate Law",
            "target_case_node_id": "431_0720-01",
            "target_case_name": "Illinois Brick Co. v. Illinois",
            "target_case_citation": "431 U.S. 720 (1977)",
            "target_case_year": 1977,
            "query_text": "Under Section 4 of the Clayton Act as interpreted through 1980, can indirect purchasers who bought price-fixed goods through intermediary distributors maintain a federal treble damages action against the price-fixing manufacturer?",
            "ground_truth_holding": "Only direct purchasers from an antitrust violator may sue for treble damages under Section 4 of the Clayton Act; indirect purchasers down the supply chain are barred from asserting passed-on overcharges (the indirect purchaser rule).",
            "required_historical_elements": [
                "direct purchaser standing rule",
                "indirect purchasers barred from asserting pass-on theories",
                "clayton act section 4 treble damages limitation",
                "avoidance of complex damages apportionment"
            ],
            "forbidden_future_elements": [
                "california v. arc america corp. state indirect purchaser statutes",
                "apple inc. v. pepper app store purchaser exception",
                "state illinois brick repealer statutes"
            ],
            "future_case_names": ["california v. arc america corp.", "apple inc. v. pepper"],
            "future_years": ["1989", "2019"],
            "future_doctrinal_concepts": ["illinois brick repealer statutes under state antitrust law", "app store platform direct purchaser classification"],
            "evolutionary_arc_cases": [],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-48",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "448_0176-01",
            "target_case_name": "Dawson Chemical Co. v. Rohm & Haas Co.",
            "target_case_citation": "448 U.S. 176 (1980)",
            "target_case_year": 1980,
            "query_text": "Tracing patent misuse doctrine through 1980, does a patentee who holds a process patent for applying an unpatented, non-staple chemical herbicide commit patent misuse by selling the unpatented chemical and refusing to license competitors who sell the same non-staple chemical?",
            "ground_truth_holding": "Under 35 U.S.C. Section 271(d), a patentee does not commit patent misuse by selling an unpatented chemical that constitutes a non-staple article of commerce having no substantial non-infringing use, and may enjoin competitors from contributory infringement.",
            "required_historical_elements": [
                "35 u.s.c. section 271(d) patent misuse statutory exception",
                "non-staple article of commerce with no substantial non-infringing use",
                "contributory infringement protection",
                "patentee may exploit process by selling non-staple chemical"
            ],
            "forbidden_future_elements": [
                "patent misuse reform act of 1988 market power requirement",
                "statutory market power presumption elimination under section 271(d)(5)",
                "illinois tool works v. independent ink"
            ],
            "future_case_names": ["illinois tool works inc. v. independent ink, inc."],
            "future_years": ["1988", "2006"],
            "future_doctrinal_concepts": ["patent misuse market power requirement", "elimination of market power presumption in tying"],
            "evolutionary_arc_cases": [
                {"case": "Mercoid Corp. v. Mid-Continent Investment Co.", "year": 1944, "citation": "320 U.S. 661"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-49",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case_node_id": "434_0077-01",
            "target_case_name": "Commissioner v. Kowalski",
            "target_case_citation": "434 U.S. 77 (1977)",
            "target_case_year": 1977,
            "query_text": "Tracing gross income definitions through 1980, does cash meal allowance money paid to state police officers in lieu of meals furnished on business premises qualify for exclusion from gross income under federal income tax statutes?",
            "ground_truth_holding": "Cash meal allowances paid to state troopers are not excludable from gross income under Internal Revenue Code Section 119, which permits exclusion only for meals furnished in kind on the business premises of the employer.",
            "required_historical_elements": [
                "internal revenue code section 119 in kind requirement",
                "cash meal allowances constitute taxable gross income",
                "exclusion limited to meals furnished on business premises",
                "section 61 comprehensive gross income sweep"
            ],
            "forbidden_future_elements": [
                "statutory retroactive relief acts for state troopers",
                "qualified employee discounts under section 132"
            ],
            "future_case_names": [],
            "future_years": ["1984", "1986"],
            "future_doctrinal_concepts": ["internal revenue code section 132 fringe benefit exclusions", "de minimis fringe benefit rules"],
            "evolutionary_arc_cases": [
                {"case": "Commissioner v. Glenshaw Glass Co.", "year": 1955, "citation": "348 U.S. 426"}
            ],
            "metadata_sanitization_verified": True
        },
        {
            "query_id": "TLP-50",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "reasoning_depth": 2,
            "reasoning_depth_type": "Evolutionary Precedent Arc",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case_node_id": "421_0397-01",
            "target_case_name": "United States v. Reliable Transfer Co.",
            "target_case_citation": "421 U.S. 397 (1975)",
            "target_case_year": 1975,
            "query_text": "Tracing American maritime and admiralty jurisprudence through 1980, does federal admiralty law continue to require that property damages in a maritime vessel collision or stranding be divided equally between joint tortfeasors regardless of the comparative degree of fault attributable to each party?",
            "ground_truth_holding": "The Supreme Court overruled the traditional equal divided damages rule, holding that liability for property damage in a maritime collision or stranding must be allocated among the parties proportionately to the comparative degree of their fault, and divided equally only when fault is equal or cannot be fairly measured.",
            "required_historical_elements": [
                "proportional fault allocation based on comparative negligence",
                "equal division of damages rule overruled",
                "maritime collision and stranding property damages",
                "liability allocated equally only where fault is equal or cannot be measured"
            ],
            "forbidden_future_elements": [
                "oil pollution act of 1990 strict statutory liability",
                "exxon shipping co. v. baker punitive damages limitation",
                "maritime punitive damages ratio under exxon valdez"
            ],
            "future_case_names": [
                "exxon shipping co. v. baker",
                "miles v. apex marine corp.",
                "norfolk southern railway co. v. kirby"
            ],
            "future_years": [
                "1990",
                "2004",
                "2008"
            ],
            "future_doctrinal_concepts": [
                "oil pollution act statutory maritime liability regime",
                "one to one punitive damages ratio in maritime law",
                "miles non-pecuniary damages bar under general maritime law"
            ],
            "evolutionary_arc_cases": [
                {"case": "The \"North Star\"", "year": 1882, "citation": "106 U.S. 17"},
                {"case": "The Max Morris", "year": 1890, "citation": "137 U.S. 1"}
            ],
            "metadata_sanitization_verified": True
        }
    ]
    return probes

def get_verifier_controls():
    """
    Returns the 10 paired verifier proposition controls from implementation plan table lines 68-81.
    """
    controls = [
        {
            "pair_id": "VP-01",
            "cutoff_year": 1890,
            "stratum": "High-Prominence",
            "domain": "Commerce Clause & Economic Regulation",
            "target_case": "Kidd v. Pearson (1888)",
            "topic": "Local Manufacture vs Interstate Commerce",
            "proposition_claim": "State police power legitimately reaches local manufacturing even if manufactured goods are intended for interstate export.",
            "negative_context": "The power of Congress over interstate commerce is complete and exclusive. Once articles enter the channels of trade between states, state authority yields entirely to the supreme federal authority established in Gibbons v. Ogden. State regulations that restrict or burden the flow of articles intended for trade across state lines infringe upon the national commerce power.",
            "positive_context": "We held in Kidd v. Pearson, 128 U.S. 1 (1888), that a state has the right to prohibit the manufacture of intoxicating liquors within its limits, even though such liquors are intended for export to other states. Manufacture is distinct from commerce. The police power of a state to regulate or prohibit manufacturing within its borders is not surrendered because the manufacturer contemplates sending the finished product into other states.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-02",
            "cutoff_year": 1890,
            "stratum": "Lower-Prominence",
            "domain": "Federal Taxation & Fiscal Powers",
            "target_case": "New Jersey v. Yard (1877)",
            "topic": "Corporate Legislative Charter Tax Exemption",
            "proposition_claim": "A tax exemption contractually granted in a corporate legislative charter is protected against subsequent repeal by the Contract Clause.",
            "negative_context": "The power of taxation is an essential prerogative of state sovereignty. Statutes granting exemptions from public burdens are strictly construed against the grantee. Unless an exemption is expressed in terms that admit of no other construction, it is treated as a revocable legislative privilege that may be altered or repealed at the pleasure of the state legislature.",
            "positive_context": "In New Jersey v. Yard, 95 U.S. 104 (1877), this court ruled that when a state legislature amends a corporate charter by statute stipulating that the corporation shall pay a fixed annual tax which shall be in lieu of all other taxes, and the corporation accepts the act, a contract is created. The Contract Clause protects this charter tax exemption from subsequent legislative repeal or unilateral tax increases.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-03",
            "cutoff_year": 1930,
            "stratum": "High-Prominence",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case": "Adkins v. Children's Hospital (1923)",
            "topic": "Freedom of Contract and Minimum Wage Legislation",
            "proposition_claim": "A congressional statute fixing minimum wages for women infringes the liberty of contract guaranteed by the Fifth Amendment.",
            "negative_context": "In Muller v. Oregon, 208 U.S. 412, we affirmed that the physical differences between men and women justify protective labor legislation regulating maximum working hours for women. The state may properly exercise its police power to safeguard women from excessive industrial burdens in the interest of public health, and such hours restrictions do not violate constitutional due process.",
            "positive_context": "Under the controlling authority of Adkins v. Children's Hospital, 261 U.S. 525 (1923), an act of Congress fixing minimum wages for adult women in the District of Columbia is an unconstitutional interference with the freedom of contract guaranteed by the Due Process Clause of the Fifth Amendment. Freedom of contract is the general rule and cannot be abridged by compulsory wage rates.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-04",
            "cutoff_year": 1930,
            "stratum": "Lower-Prominence",
            "domain": "Constitutional Law & Civil Rights",
            "target_case": "Black & White Taxicab (1928)",
            "topic": "General Commercial Common Law Independence",
            "proposition_claim": "Federal courts exercising diversity jurisdiction are not bound by state court decisions on questions of general commercial common law.",
            "negative_context": "Federal courts sitting in diversity jurisdiction must faithfully adhere to state statutory enactments and local real property rules established by state judicial decisions. In matters governed by local statutes and property titles, the determinations of the highest state court constitute rules of decision binding upon federal tribunals.",
            "positive_context": "Applying the doctrine of Swift v. Tyson in Black & White Taxicab & Transfer Co. v. Brown & Yellow Taxicab & Transfer Co., 276 U.S. 518 (1928), federal courts exercising diversity jurisdiction are not bound to follow decisions of the state courts on questions of general commercial common law, such as the validity of exclusive railroad terminal carrier contracts.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-05",
            "cutoff_year": 1950,
            "stratum": "High-Prominence",
            "domain": "Constitutional Law & Civil Rights",
            "target_case": "Sweatt v. Painter (1950)",
            "topic": "Legal Education Segregation and Tangible Opportunities",
            "proposition_claim": "A state must admit qualified Black applicants to its flagship law school when segregated alternatives lack substantially equal educational opportunities.",
            "negative_context": "Under Plessy v. Ferguson, 163 U.S. 537, and Cumming v. Richmond County Board of Education, the establishment of separate public educational facilities for white and colored citizens satisfies constitutional standards where the state provides equal educational facilities under the law. Formal separation itself does not violate the Fourteenth Amendment.",
            "positive_context": "In Sweatt v. Painter, 339 U.S. 629 (1950), the Supreme Court unanimously ordered that a Black student must be admitted to the University of Texas Law School, holding that a newly created segregated state law school for Negroes lacked substantial equality in faculty size, library volume, reputation, and alumni prestige, thereby violating the Equal Protection Clause.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-06",
            "cutoff_year": 1950,
            "stratum": "Lower-Prominence",
            "domain": "Criminal Law & Constitutional Procedure",
            "target_case": "Wolf v. Colorado (1949)",
            "topic": "State Search & Exclusionary Rule Non-Incorporation",
            "proposition_claim": "In a prosecution in a state court for a state crime, the Fourteenth Amendment does not forbid the admission of evidence obtained by an unreasonable search and seizure.",
            "negative_context": "In Weeks v. United States, 232 U.S. 383, this court established that papers and property seized in violation of the Fourth Amendment must be excluded from evidence upon timely objection. The preservation of constitutional guarantees against unlawful searches requires that federal courts refuse to sanction convictions obtained through evidence seized in violation of supreme law.",
            "positive_context": "In Wolf v. Colorado, 338 U.S. 25 (1949), Mr. Justice Frankfurter concluded that in a prosecution in a state court for a state crime the Fourteenth Amendment does not forbid the admission of evidence obtained by an unreasonable search and seizure. While the core of privacy is protected, the federal exclusionary rule of Weeks is not an essential ingredient of due process imposed upon the states.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-07",
            "cutoff_year": 1970,
            "stratum": "High-Prominence",
            "domain": "Due Process, Privacy & Substantive Rights",
            "target_case": "Griswold v. Connecticut (1965)",
            "topic": "Marital Privacy Under Penumbras of Bill of Rights",
            "proposition_claim": "A state statute forbidding the use of contraceptives violates the constitutional right of marital privacy created by penumbras of the Bill of Rights.",
            "negative_context": "Economic and social welfare legislation is accorded wide deference under modern due process review. States possess broad police powers to regulate health, safety, and morals without judicial interference unless arbitrary. In economic regulation, the courts will not substitute their social judgment for legislative enactments.",
            "positive_context": "In Griswold v. Connecticut, 381 U.S. 479 (1965), the court struck down a state law banning contraceptive use, holding that specific guarantees in the Bill of Rights have penumbras formed by emanations from those guarantees that give them life and substance. These penumbras create zones of privacy, including a constitutional right of marital privacy that invalidates intrusions into the marital relationship.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-08",
            "cutoff_year": 1970,
            "stratum": "Lower-Prominence",
            "domain": "Constitutional Law & Civil Rights",
            "target_case": "Trop v. Dulles (1958)",
            "topic": "Eighth Amendment Evolving Standards of Decency",
            "proposition_claim": "Use of denationalization as a punishment for military desertion violates the Eighth Amendment's evolving standards of decency.",
            "negative_context": "Congress possesses broad war powers to govern military forces and punish desertion in time of war. The Articles of War and congressional enactments defining military discipline and forfeitures are given full effect by civilian courts, which will not interfere with military penalties enacted by the national legislature.",
            "positive_context": "In Trop v. Dulles, 356 U.S. 86 (1958), Chief Justice Warren held that stripping a native-born American citizen of their citizenship as a punishment for wartime desertion violates the Eighth Amendment. The words of the Eighth Amendment are not static, but must draw their meaning from the evolving standards of decency that mark the progress of a maturing society.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-09",
            "cutoff_year": 1980,
            "stratum": "High-Prominence",
            "domain": "Constitutional Law & Civil Rights",
            "target_case": "Regents of Univ. of California v. Bakke (1978)",
            "topic": "Affirmative Action Quotas vs Plus Factors",
            "proposition_claim": "A rigid quota reserving a fixed number of university seats solely for minority applicants violates the Equal Protection Clause.",
            "negative_context": "Title VI of the Civil Rights Act of 1964 and the Fourteenth Amendment prohibit racial discrimination by programs receiving federal financial assistance. Remedial programs intended to eliminate societal discrimination may consider group disadvantages to ensure broad participation in educational institutions receiving public funds.",
            "positive_context": "In Regents of the University of California v. Bakke, 438 U.S. 265 (1978), Justice Powell announced the judgment of the court, concluding that the state university's rigid special admissions program reserving 16 out of 100 seats solely for disadvantaged minority applicants violated the Equal Protection Clause. While race may be considered as a plus factor in competitive admissions, rigid racial quotas are unconstitutional.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        },
        {
            "pair_id": "VP-10",
            "cutoff_year": 1980,
            "stratum": "Lower-Prominence",
            "domain": "Intellectual Property, Patents & Admiralty",
            "target_case": "United States v. Reliable Transfer Co. (1975)",
            "topic": "Proportional Fault in Maritime Collision Damages",
            "proposition_claim": "Under federal maritime law, property damages resulting from a maritime collision or stranding must be allocated among the parties proportionately to the comparative degree of their fault rather than divided equally.",
            "negative_context": "Under the traditional American admiralty rule established in The Schooner Catharine v. Dickinson, 17 How. 170, when both vessels are at fault in a maritime collision, the mutual damages must be divided equally between them, regardless of the relative disparity or disproportion in the respective degrees of negligence contributing to the collision.",
            "positive_context": "In United States v. Reliable Transfer Co., 421 U.S. 397 (1975), the Supreme Court overruled the century-old divided damages rule of The Schooner Catharine, holding that when two or more parties contribute by their fault to property damage in a maritime collision or stranding, liability is to be allocated proportionately to the comparative degree of their fault.",
            "expected_negative_label": "NOT ENTAILED",
            "expected_positive_label": "ENTAILED"
        }
    ]
    return controls

def validate_probes(probes, nodes, in_degrees, p90, p50):
    print(f"\n[Phase 1 Validation] Validating {len(probes)} probe queries against rigorous invariants...")
    assert len(probes) == 50, f"Expected 50 probe queries, found {len(probes)}"

    # Check Cutoff counts
    cutoff_counts = {}
    for p in probes:
        cutoff_counts[p['cutoff_year']] = cutoff_counts.get(p['cutoff_year'], 0) + 1
    assert cutoff_counts == {1890: 10, 1930: 10, 1950: 10, 1970: 10, 1980: 10}, f"Cutoff balance failed: {cutoff_counts}"

    # Check Stratum counts
    stratum_counts = {}
    for p in probes:
        stratum_counts[p['stratum']] = stratum_counts.get(p['stratum'], 0) + 1
    assert stratum_counts == {"High-Prominence": 25, "Lower-Prominence": 25}, f"Stratum balance failed: {stratum_counts}"

    # Check Depth counts
    depth_counts = {}
    for p in probes:
        depth_counts[p['reasoning_depth']] = depth_counts.get(p['reasoning_depth'], 0) + 1
    assert depth_counts == {1: 25, 2: 25}, f"Depth balance failed: {depth_counts}"

    # Check Cell Matrix balance (13/12, 12/13)
    cell_counts = {
        ("High-Prominence", 1): 0,
        ("High-Prominence", 2): 0,
        ("Lower-Prominence", 1): 0,
        ("Lower-Prominence", 2): 0
    }
    for p in probes:
        cell_counts[(p['stratum'], p['reasoning_depth'])] += 1
    assert cell_counts[("High-Prominence", 1)] == 13, f"High D1 expected 13, got {cell_counts[('High-Prominence', 1)]}"
    assert cell_counts[("High-Prominence", 2)] == 12, f"High D2 expected 12, got {cell_counts[('High-Prominence', 2)]}"
    assert cell_counts[("Lower-Prominence", 1)] == 12, f"Lower D1 expected 12, got {cell_counts[('Lower-Prominence', 1)]}"
    assert cell_counts[("Lower-Prominence", 2)] == 13, f"Lower D2 expected 13, got {cell_counts[('Lower-Prominence', 2)]}"

    # Check Domain counts (8, 7, 7, 7, 7, 7, 7)
    domain_counts = {}
    for p in probes:
        domain_counts[p['domain']] = domain_counts.get(p['domain'], 0) + 1
    assert domain_counts.get("Constitutional Law & Civil Rights") == 8, f"Const domain count: {domain_counts.get('Constitutional Law & Civil Rights')}"
    for dom in [
        "Commerce Clause & Economic Regulation",
        "Due Process, Privacy & Substantive Rights",
        "Federal Taxation & Fiscal Powers",
        "Antitrust & Corporate Law",
        "Criminal Law & Constitutional Procedure",
        "Intellectual Property, Patents & Admiralty"
    ]:
        assert domain_counts.get(dom) == 7, f"Domain {dom} expected 7, got {domain_counts.get(dom)}"
    assert sum(domain_counts.values()) == 50

    # Validate each query
    for p in probes:
        qid = p['query_id']
        nid = p['target_case_node_id']
        assert nid in nodes, f"[{qid}] Target node {nid} not found in EEG index"
        node = nodes[nid]
        deg = in_degrees[nid]
        p['target_case_in_degree'] = deg

        # Verify year
        m = re.search(r'(\d{4})', node.get('decision_date', ''))
        yr = int(m.group(1)) if m else 0
        assert yr <= p['cutoff_year'], f"[{qid}] Target case year {yr} > cutoff {p['cutoff_year']}"

        # Verify Stratum and Exclusion of intermediate range [5, 17]
        assert not (5 <= deg <= 17), f"[{qid}] Node {nid} has intermediate degree {deg} (forbidden range 5-17)"
        if p['stratum'] == "High-Prominence":
            assert deg >= p90, f"[{qid}] High stratum node {nid} degree {deg} < p90 ({p90})"
        elif p['stratum'] == "Lower-Prominence":
            assert deg <= p50, f"[{qid}] Lower stratum node {nid} degree {deg} > p50 ({p50})"

        # Verify Query-level Sanitization
        query_text = p['query_text']
        query_lower = query_text.lower()

        # 1. Future case names disjoint
        for fcase in p['future_case_names']:
            assert fcase.lower() not in query_lower, f"[{qid}] Future case '{fcase}' leaked in query: {query_text}"

        # 2. Future years disjoint (no years > cutoff_year)
        years_in_query = [int(y) for y in re.findall(r'\b(1[89]\d\d|20\d\d)\b', query_text)]
        for y in years_in_query:
            assert y <= p['cutoff_year'], f"[{qid}] Future year {y} > cutoff {p['cutoff_year']} found in query: {query_text}"
        for fyear in p['future_years']:
            assert str(fyear) not in query_text, f"[{qid}] Forbidden future year '{fyear}' found in query: {query_text}"

        # 3. Future doctrinal concepts disjoint
        for fconcept in p['future_doctrinal_concepts']:
            assert fconcept.lower() not in query_lower, f"[{qid}] Future concept '{fconcept}' found in query: {query_text}"

        # 5. Citation format and node citation consistency
        cite_regex = re.compile(r'^\d+\s+U\.S\.\s+\d+\s+\(\d{4}\)$')
        assert cite_regex.match(p['target_case_citation']), f"[{qid}] Malformed citation: {p['target_case_citation']}"
        vol_page = p['target_case_citation'].split(' (')[0].strip()
        node_cites = node.get('citations', [])
        assert any(vol_page in c or c in vol_page for c in node_cites), (
            f"[{qid}] Citation mismatch: '{vol_page}' not in node {nid} citations {node_cites}"
        )

        # 6. Evolutionary arc validation
        if p['reasoning_depth'] == 2:
            assert len(p.get('evolutionary_arc_cases', [])) > 0, f"[{qid}] Depth 2 query has empty evolutionary_arc_cases"
            for arc in p['evolutionary_arc_cases']:
                assert arc['year'] <= p['cutoff_year'], f"[{qid}] Arc case year {arc['year']} > cutoff {p['cutoff_year']}"
        else:
            assert len(p.get('evolutionary_arc_cases', [])) == 0, f"[{qid}] Depth 1 query has evolutionary_arc_cases"

    print("[Phase 1 Validation] All 50 probe queries passed ALL structural, statistical, and sanitization tests!")

def main():
    nodes, in_degrees, p90, p50 = load_eeg_index(EEG_INDEX_PATH)
    probes = get_probe_definitions()
    controls = get_verifier_controls()

    validate_probes(probes, nodes, in_degrees, p90, p50)

    # Validate verifier controls
    print(f"\n[Phase 1 Validation] Validating {len(controls)} verifier controls...")
    assert len(controls) == 10, f"Expected 10 verifier controls, got {len(controls)}"
    for c in controls:
        assert c['expected_negative_label'] == "NOT ENTAILED"
        assert c['expected_positive_label'] == "ENTAILED"
        assert len(c['negative_context']) > 50
        assert len(c['positive_context']) > 50
        assert len(c['proposition_claim']) > 20
    print("[Phase 1 Validation] All 10 verifier controls verified.")

    # Save outputs
    os.makedirs(os.path.dirname(PROBE_OUTPUT_PATH), exist_ok=True)
    with open(PROBE_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(probes, f, indent=2, ensure_ascii=False)
    print(f"[Phase 1 Output] Successfully wrote 50 probe queries to {PROBE_OUTPUT_PATH}")

    with open(VERIFIER_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(controls, f, indent=2, ensure_ascii=False)
    print(f"[Phase 1 Output] Successfully wrote 10 verifier controls to {VERIFIER_OUTPUT_PATH}")

if __name__ == '__main__':
    main()
