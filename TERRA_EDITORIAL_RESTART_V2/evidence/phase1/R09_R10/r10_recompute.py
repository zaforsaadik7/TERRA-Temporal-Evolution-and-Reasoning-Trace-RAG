"""R10 read-only recomputation. Writes only r10_recompute_out.json next to this script."""
import json, re, os, ast, hashlib
import numpy as np
from scipy.stats import beta
R = "/mnt/user-data/uploads/TERRA -Copy"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "r10_recompute_out.json")
def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else beta.ppf(a/2, k, n-k+1)
    hi = 1.0 if k == n else beta.ppf(1-a/2, k+1, n-k)
    return [round(lo*100, 2), round(hi*100, 2)]
res = {"clopper_pearson": {f"{k}/5": cp(k, 5) for k in range(6)}}
res["clopper_pearson"].update({f"{k}/8": cp(k, 8) for k in (2, 4)})
res["clopper_pearson"]["16/32"] = cp(16, 32); res["clopper_pearson"]["20/32"] = cp(20, 32)
res["ratios"] = {"TERRA/Flat CiteF1 16.02/21.15": round(16.02/21.15, 4), "TERRA/Hippo 16.02/15.02": round(16.02/15.02, 4),
                 "TERRA/Direct 16.02/12.17": round(16.02/12.17, 4), "path 66/1": 66, "path 66/21": round(66/21, 3)}
eeg = json.load(open(f"{R}/dataset_20k_cap/terra_eeg_index_20k.json"))
nodes = eeg.get("nodes", {})
def match(tid, ctx):
    c = ctx.lower()
    if tid.lower() in c: return True
    t = nodes.get(tid, {}).get("title", "")
    if t:
        tc = t.split(" v. ")[0].strip().lower() if " v. " in t else t.lower()
        if len(tc) > 4 and tc in c: return True
    return False
def tolist(x): return x if isinstance(x, list) else ast.literal_eval(x)
bench = {q["query_id"]: q for q in json.load(open(f"{R}/terra_350_benchmark.json"))}
LINK = re.compile(r"\]\((/case/[^)\s]+)\)")
def analyse(rows, label):
    out = {}
    for p in ["2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted", "5_Full_TERRA"]:
        recs = {r["query_id"]: r for r in rows if r["pipeline"] == p and r["category"] == "B_Evolutionary"}
        nr, tg, tf, full = [], 0, 0, 0; bl = {3: [0, 0, 0, 0], 4: [0, 0, 0, 0], 5: [0, 0, 0, 0]}
        for qid, q in bench.items():
            if q["category"] != "B_Evolutionary": continue
            t = tolist(q["target_nodes"]); ctx = recs.get(qid, {}).get("context_full", "") or ""
            f = sum(match(x, ctx) for x in t); nr.append(f/len(t)); tg += len(t); tf += f
            isf = f == len(t); full += isf; b = bl[len(t)]; b[0] += 1; b[1] += isf; b[2] += len(t); b[3] += f
        out[p] = {"macro": round(np.mean(nr)*100, 2), "micro": round(tf/tg*100, 2), "full": full, "gold": tg,
                  "by_len": {L: {"n": v[0], "full": v[1], "node_recall": round(v[3]/v[2]*100, 2)} for L, v in bl.items()}}
    links = []
    for r in rows:
        if r["pipeline"] == "5_Full_TERRA":
            for u in LINK.findall(r.get("answer_full", "") or ""): links.append((r["query_id"], u))
    tgt = [u.split("/case/")[1] for _, u in links]
    resolved = sum(t in nodes for t in tgt)
    out["terra_links"] = {"total": len(links), "resolved_exact_id": resolved,
                          "unresolved": [(q, u) for q, u in links if u.split('/case/')[1] not in nodes]}
    res[label] = out
v2p = f"{R}/scratch/canonical_v2/terra_canonical_v2_eval.json"
analyse(json.load(open(v2p)), "canonical_v2")
analyse(json.load(open(f"{R}/terra_baselines_eval_raw.json")), "raw_eval_legacy")
json.dump(res, open(OUT, "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:6000])
