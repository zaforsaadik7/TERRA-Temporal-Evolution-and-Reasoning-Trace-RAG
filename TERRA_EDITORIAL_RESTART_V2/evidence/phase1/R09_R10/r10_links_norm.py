"""Page-padding-normalised link resolution for TERRA answers (v2 and legacy). Read-only; prints only."""
import json, re
R = "/mnt/user-data/uploads/TERRA -Copy"
nodes = json.load(open(f"{R}/dataset_20k_cap/terra_eeg_index_20k.json"))["nodes"]
LINK = re.compile(r"\]\((/case/[^)\s]+)\)")
def norm(t):
    m = re.match(r"^(\d+)_(\d+)-(\d+)$", t)
    return f"{m.group(1)}_{int(m.group(2)):04d}-{m.group(3)}" if m else t
for lab, p in [("v2", f"{R}/scratch/canonical_v2/terra_canonical_v2_eval.json"), ("legacy", f"{R}/terra_baselines_eval_raw.json")]:
    rows = [r for r in json.load(open(p)) if r["pipeline"] == "5_Full_TERRA"]
    L = [(r["query_id"], u.split("/case/")[1]) for r in rows for u in LINK.findall(r.get("answer_full") or "")]
    exact = sum(t in nodes for _, t in L); normd = sum(norm(t) in nodes for _, t in L)
    other_pipes = 0
    print(lab, "total", len(L), "exact", exact, "padding-normalised", normd,
          "still unresolved", [(q, t) for q, t in L if norm(t) not in nodes])
    allrows = json.load(open(p))
    print(lab, "baseline links:", {pp: sum(len(LINK.findall(r.get('answer_full') or '')) for r in allrows if r['pipeline'] == pp) for pp in sorted({r['pipeline'] for r in allrows})})
