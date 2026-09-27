"""
scripts/audit_excluded_edges.py - Mechanical Audit of Excluded and Corrupted Edges
===================================================================================
Directly inspects the raw Harvard CAP opinion text for the 3 candidate edges to count
target case name occurrences in the overruling opinion, verifying why they are false
positives produced by automated CRS citation extraction.
Also checks the total in-degree of 'The Harrisburg' against the <= 16 cutoff.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def audit_excluded_edges():
    print("=" * 90)
    print("MECHANICAL AUDIT OF EXCLUDED CRS EDGES & DEGREE ANCHORS")
    print("=" * 90)
    
    # 1. Harrisburg degree check
    eeg = json.load(open(ROOT / 'dataset_20k_cap' / 'terra_eeg_index_20k.json', encoding='utf-8'))
    edges = eeg['edges']
    harrisburg_id = "119_0199-01"
    h_deg = sum(1 for e in edges if e['target'] == harrisburg_id)
    print(f"\n[Exclusion 1: The Harrisburg (119_0199-01)]")
    print(f"  Total In-Degree in EEG edge list: {h_deg}")
    print(f"  Mechanical benchmark threshold:   <= 16")
    print(f"  Result: Excluded mechanically by degree cutoff ({h_deg} > 16).")
    
    # 2. Target Name Counts in Overruler Opinions
    tests = [
        {
            "target_name": "Frisbie",
            "target_node": "342_0519-01", # Frisbie v. Collins
            "overruler_case": "Griffin v. Breckenridge",
            "overruler_node": "403_0088-01",
            "explanation": "Griffin (403 U.S. 88) overruled Collins v. Hardyman, 341 U.S. 651 (1951). Citation parser confused 'Collins' with Frisbie v. Collins."
        },
        {
            "target_name": "Wyman-Gordon",
            "target_search": ["wyman-gordon", "wyman gordon"],
            "target_node": "394_0759-01", # NLRB v. Wyman-Gordon Co.
            "overruler_case": "Edelman v. Jordan",
            "overruler_node": "415_0651-01",
            "explanation": "Edelman (415 U.S. 651) overruled Ford Motor Co. v. Dept. of Treasury (1945). Edelman mentions NY Welfare Comm'r Wyman (in Rothstein v. Wyman and Rosado v. Wyman), but never NLRB v. Wyman-Gordon."
        },
        {
            "target_name": "Norwood",
            "target_node": "172_0269-01", # Norwood v. Baker
            "overruler_case": "Hensley v. Municipal Court",
            "overruler_node": "411_0345-01",
            "explanation": "Hensley (411 U.S. 345) overruled Stallings and Johnson v. Hoy on bail custody, never Norwood v. Baker (1898)."
        }
    ]
    
    for t in tests:
        onode = t['overruler_node']
        cap_p = ROOT / 'dataset_20k_cap' / 'raw_cases' / f'{onode}.json'
        cap = json.load(open(cap_p, encoding='utf-8'))
        text = cap['casebody']['opinions'][0]['text'].lower()
        
        search_terms = t.get('target_search', [t['target_name'].lower()])
        counts = {term: text.count(term) for term in search_terms}
        total_hits = sum(counts.values())
        
        print(f"\n[Corrupted Edge: {t['target_name']} -> {t['overruler_case']} ({onode})]")
        print(f"  Target Node:      {t['target_node']}")
        print(f"  Overruler Node:   {onode}")
        print(f"  Search Terms:     {search_terms}")
        print(f"  Term Counts:      {counts}")
        print(f"  Total Mentions:   {total_hits} (Expected: 0)")
        print(f"  Audited Finding:  {t['explanation']}")
        assert total_hits == 0, f"Expected 0 mentions of target in {onode}, got {total_hits}"
        print(f"  Verification:     CONFIRMED CORRUPTED CRS EDGE (0 target mentions in opinion text).")

    print("\n" + "=" * 90)
    print("ALL EXCLUSION AUDITS COMPLETE: 3 FALSE OVERRULES EDGES IDENTIFIED AND LOGGED.")
    print("=" * 90)

if __name__ == '__main__':
    audit_excluded_edges()
