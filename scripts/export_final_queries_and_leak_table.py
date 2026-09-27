import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren', 
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 
    'can', 'cannot', 'could', 'couldn', 'did', 'didn', 'do', 'does', 'doesn', 'doing', 'don', 'down', 
    'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn', 'has', 'hasn', 'have', 'haven', 
    'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 
    'into', 'is', 'isn', 'it', 'its', 'itself', 'just', 'll', 'm', 'ma', 'me', 'might', 'mightn', 
    'more', 'most', 'must', 'mustn', 'my', 'myself', 'no', 'nor', 'not', 'now', 'o', 'of', 'off', 
    'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 're', 's', 
    'same', 'shan', 'she', 'should', 'shouldn', 'so', 'some', 'such', 't', 'than', 'that', 'the', 
    'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 
    'through', 'to', 'too', 'under', 'until', 'up', 've', 'very', 'was', 'wasn', 'we', 'were', 
    'weren', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 
    'won', 'would', 'wouldn', 'y', 'you', 'your', 'yours', 'yourself', 'yourselves'
}

def tokenize(text):
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return set(w for w in words if w not in STOPWORDS)

bench = json.load(open(ROOT / 'data' / 'obscure_overruled_benchmark.json', encoding='utf-8'))

# Save final 30 queries JSON
queries_30 = [{"query_id": it["query_id"], "target_case": it["target_case"], "query": it["query"]} for it in bench]
out_q = ROOT / 'data' / 'obscure_benchmark_30_queries.json'
with open(out_q, 'w', encoding='utf-8') as f:
    json.dump(queries_30, f, indent=2, ensure_ascii=False)
print(f"Wrote final 30 queries to: {out_q}")

print("=" * 110)
print(f"{'ID':<8} | {'Target Case':<28} | {'|Gold|':<6} | {'|Ovr|':<6} | {'|LeakPool|':<10} | {'Query Leaks':<12} | Status")
print("-" * 110)

for it in bench:
    qid = it['query_id']
    tc = it['target_case']
    q = it['query']
    gold = it['gold_holding']
    ovr = it['overruling_holding']
    q_toks = tokenize(q)
    g_toks = tokenize(gold)
    o_toks = tokenize(ovr)
    leak_tokens = o_toks - g_toks
    leaks = q_toks & leak_tokens
    assert len(leaks) == 0
    print(f"{qid:<8} | {tc[:28]:<28} | {len(g_toks):<6} | {len(o_toks):<6} | {len(leak_tokens):<10} | {sorted(list(leaks))!s:<12} | PASS (0 leaks)")
print("=" * 110)
print("ZERO LEAK TOKENS IN 100% OF BENCHMARK QUERIES.")
