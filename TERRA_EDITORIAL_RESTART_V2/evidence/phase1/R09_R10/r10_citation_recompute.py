"""Re-run project citation/link logic (imported, read-only functions) on canonical_v2 and legacy. Prints only."""
import sys, json, ast, numpy as np
R = "/mnt/user-data/uploads/TERRA -Copy"
sys.path.insert(0, R + "/scripts")
from audit_citation_correctness import build_case_lookup_index, extract_case_entities
nodes = json.load(open(f"{R}/dataset_20k_cap/terra_eeg_index_20k.json"))["nodes"]
t2n, a2n = build_case_lookup_index(nodes)
bench = json.load(open(f"{R}/terra_350_benchmark.json"))
catb = [q for q in bench if q["category"] == "B_Evolutionary"]
def tl(x): return x if isinstance(x, list) else ast.literal_eval(x)
def fl(x):
    try: return float(x)
    except: return 0.0
for lab, p in [("v2", f"{R}/scratch/canonical_v2/terra_canonical_v2_eval.json"), ("legacy", f"{R}/terra_baselines_eval_raw.json")]:
    raw = json.load(open(p)); print("=====", lab)
    tr = [r for r in raw if r["pipeline"] == "5_Full_TERRA"]
    tot = val = fid = 0; bad = []
    for r in tr:
        links, _, _ = extract_case_entities(r.get("answer_full", "") or "", "5_Full_TERRA", nodes, t2n, a2n)
        for lk in links:
            tot += 1
            if lk["is_valid"]:
                val += 1; fid += bool(lk["is_fidelity"])
            else: bad.append((r["query_id"], lk["anchor"], lk["target"]))
    print(f"links total={tot} valid={val} ({val/tot*100:.2f}%) fidelity={fid} ({fid/tot*100:.2f}%) broken={len(bad)}"); print(" broken:", bad)
    for pl in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted", "5_Full_TERRA"]:
        recs = {r["query_id"]: r for r in raw if r["pipeline"] == pl and r["category"] == "B_Evolutionary"}
        mr, cep, dep, depg, hits, full = [], [], [], [], 0, 0
        for q in catb:
            t = set(tl(q["target_nodes"])); rec = recs.get(q["query_id"], {})
            _, res, unr = extract_case_entities(rec.get("answer_full", "") or "", pl, nodes, t2n, a2n)
            n = len(res) + len(unr); h = len(res & t); hits += h; mr.append(h/len(t)); full += h == len(t)
            cep.append(len(res)/n if n else 0.0)
            if n:
                ctx = (rec.get("context_full", "") or "").lower()
                g = sum(1 for nid in res if nid in t or nid.lower() in ctx or nodes[nid].get("title", "").lower() in ctx)
                dep.append(g/n*fl(rec.get("faithfulness", 0))); depg.append(g/n)
            else: dep.append(0.0); depg.append(0.0)
        m, d, dg = np.mean(mr)*100, np.mean(dep)*100, np.mean(depg)*100
        f1 = 2*m*d/(m+d) if m+d else 0; f1g = 2*m*dg/(m+dg) if m+dg else 0
        print(f"{pl:20s} macroCR={m:.2f} microCR={hits/342*100:.2f} CEP={np.mean(cep)*100:.2f} DEP(xfaith)={d:.2f} F1={f1:.2f} DEP(grounded)={dg:.2f} F1g={f1g:.2f} full={full}/100")
    for pl in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted", "5_Full_TERRA"]:
        cc = [r for r in raw if r["pipeline"] == pl and r["category"] == "C_OutOfContext"]
        em = [len(extract_case_entities(r.get("answer_full", "") or "", pl, nodes, t2n, a2n)[1]) + len(extract_case_entities(r.get("answer_full", "") or "", pl, nodes, t2n, a2n)[2]) for r in cc]
        print(f"CatC {pl:20s} emitted={sum(em)} clean={sum(e == 0 for e in em)}/{len(cc)}")
