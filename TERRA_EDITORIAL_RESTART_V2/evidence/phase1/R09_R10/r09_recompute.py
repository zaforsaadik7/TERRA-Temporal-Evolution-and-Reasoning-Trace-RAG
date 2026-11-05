"""R09 read-only recomputation from staged CLERC / CaseFacts raw files. Prints only."""
import json
from collections import Counter
S = "/mnt/user-data/uploads/TERRA -Copy/scratch"
def b(x): return x is True or str(x).lower() == "true"
P = ["1_Direct_LLM", "2_Flat_Vector_RAG", "5_Full_TERRA"]
print("=== CLERC")
for tr, f in [("T1", "clerc_120_eval_raw.json"), ("T2", "clerc_50_refusal_eval_raw.json")]:
    d = json.load(open(f"{S}/{f}"))
    for p in P:
        rs = [r for r in d if r["pipeline"] == p]; n = len(rs)
        q = lambda r: b(r.get("eval_qwen", {}).get("hallucination_detected")); g = lambda r: b(r.get("eval_gpt_oss", {}).get("hallucination_detected"))
        OR = sum(q(r) or g(r) for r in rs); AND = sum(q(r) and g(r) for r in rs)
        sc = [r for r in rs if b(r["generation"].get("refusal_short_circuit"))]; gen = [r for r in rs if not b(r["generation"].get("refusal_short_circuit"))]
        OR_gen = sum(q(r) or g(r) for r in gen); AND_gen = sum(q(r) and g(r) for r in gen); OR_sc = sum(q(r) or g(r) for r in sc)
        fb = sum(b(r.get("eval_qwen", {}).get("_judge_fallback_contaminated")) or b(r.get("eval_gpt_oss", {}).get("_judge_fallback_contaminated")) for r in rs)
        rs_q = Counter(r["eval_qwen"].get("refusal_status") for r in rs)
        print(f"{tr} {p:18s} n={n} OR={OR} ({OR/n*100:.1f}%) AND={AND} ({AND/n*100:.1f}%) short_circuit={len(sc)} OR_among_generated={OR_gen}/{len(gen)} AND_among_generated={AND_gen}/{len(gen)} OR_among_shortcircuit={OR_sc} fallback={fb} qwen_status={dict(rs_q)}")
        if tr == "T1" and p != "1_Direct_LLM":
            ev = [r["retrieval_evaluation"] for r in rs]
            print("   hits@10 flat", sum(b(e["flat_hit_top10"]) for e in ev), "terra", sum(b(e["terra_hit_top10"]) for e in ev))
print("=== CaseFacts T1")
d = json.load(open(f"{S}/casefacts_120_eval_raw.json")); L = ["Supported", "Refuted", "Overruled"]
for p in P:
    rs = [r for r in d if r["pipeline"] == p]
    tp = {l: sum(r["ground_truth"] == l and r["parsed_label"] == l for r in rs) for l in L}
    pred = {l: sum(r["parsed_label"] == l for r in rs) for l in L}; sup = {l: sum(r["ground_truth"] == l for r in rs) for l in L}
    f1 = {}
    for l in L:
        pr = tp[l]/pred[l] if pred[l] else 0; rc = tp[l]/sup[l]; f1[l] = 2*pr*rc/(pr+rc)*100 if pr+rc else 0
    TP = sum(tp.values()); npred = sum(pred.values()); ooc = sum(r["parsed_label"] == "Outside Precedent Corpus" for r in rs)
    mP, mR = TP/npred, TP/len(rs); mF = 2*mP*mR/(mP+mR)*100
    conc = sum(r["judge_qwen"]["predicted_label"].lower() == r["judge_gpt_oss"]["predicted_label"].lower() for r in rs)
    pl_vs_j = sum(r["parsed_label"].lower() == r["judge_qwen"]["predicted_label"].lower() for r in rs)
    print(f"{p:18s} macroF1(3cls)={sum(f1.values())/3:.2f} macroF1(Supp+Ref only)={(f1['Supported']+f1['Refuted'])/2:.2f} accuracy(=script 'micro')={mR*100:.2f} trueMicroF1(OOC as abstain)={mF:.2f} OOC_preds={ooc} F1={ {k: round(v,2) for k,v in f1.items()} } judge_concord={conc}/{len(rs)} parsed==qwen={pl_vs_j}/{len(rs)}")
print("=== CaseFacts T2")
d = json.load(open(f"{S}/casefacts_50_refusal_eval_raw.json"))
for p in P:
    rs = [r for r in d if r["pipeline"] == p]
    print(p, "parsed_label", dict(Counter(r["parsed_label"] for r in rs)), "direct_match", sum(b(r["direct_match"]) for r in rs), "consensus_correct", sum(b(r["consensus_correct"]) for r in rs),
          "refused(script rule)", sum(r["parsed_label"] == "Outside Precedent Corpus" or b(r["direct_match"]) or b(r["consensus_correct"]) for r in rs),
          "ctx_len0", sum(str(r.get("context_len")) == "0" for r in rs), "answer_startswith_apolog", sum((r.get("answer") or "").strip().lower().startswith("i apolog") for r in rs))
