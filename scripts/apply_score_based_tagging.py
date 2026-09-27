import json
import time
from collections import Counter
from pathlib import Path

GRAPH_PATH = Path("dataset_20k_cap/terra_eeg_index_20k.json")
MANIFEST_PATH = Path("dataset_20k_cap/manifests/selection_manifest_20k.json")

print("=== APPLYING SCORE-BASED PERSISTENT DOCTRINAL CLASSIFICATION ===")

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
    "civil_rights_equal_protection": [
        "equal protection", "civil rights", "fourteenth amendment", "14th amendment",
        "racial discrimination", "segregat", "desegregat", "separate but equal",
        "thirteenth amendment", "fifteenth amendment", "voting rights", "disenfranchise"
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

def get_accurate_domain(title, text):
    t_lower = (title + " " + text[:4000]).lower()
    scores = {}
    for dom, kws in DOCTRINAL_LEXICONS.items():
        score = sum(t_lower.count(kw) for kw in kws)
        if score > 0:
            scores[dom] = score
    if not scores:
        return "general_constitutional_statutory", ["general_constitutional_statutory"]
    best_dom = max(scores, key=scores.get)
    all_tags = sorted(scores.keys(), key=lambda x: -scores[x])
    return best_dom, all_tags

with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    graph_data = json.load(f)

nodes = graph_data.get("nodes", {})
print(f"Loaded {len(nodes):,} nodes from {GRAPH_PATH}.")

primary_counts = Counter()
tag_counts = Counter()

for nid, ninfo in nodes.items():
    title = ninfo.get("title", "")
    text = ninfo.get("text", "")
    p_dom, tags = get_accurate_domain(title, text)
    
    ninfo["category"] = p_dom
    ninfo["primary_domain"] = p_dom
    ninfo["doctrinal_tags"] = tags
    
    primary_counts[p_dom] += 1
    for t in tags:
        tag_counts[t] += 1

with open(GRAPH_PATH, "w", encoding="utf-8") as f:
    json.dump(graph_data, f, indent=2)

print(f"\nUpdated {GRAPH_PATH} with score-based doctrinal classification.")
print("Primary Categories Distribution:")
for dom, cnt in primary_counts.most_common():
    print(f"  - {dom:35s}: {cnt:5,d} ({cnt/len(nodes)*100:5.1f}%)")

# Update manifest
if MANIFEST_PATH.exists():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for entry in manifest:
        nid = f"{entry['volume']}_{entry['file_name']}"
        if nid in nodes:
            entry["category"] = nodes[nid]["category"]
            entry["primary_domain"] = nodes[nid]["primary_domain"]
            entry["doctrinal_tags"] = nodes[nid]["doctrinal_tags"]
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Updated {MANIFEST_PATH} with matching persisted doctrinal tags.")

print("=== PERSISTENT DOCTRINAL TAGGING COMPLETE ===")
