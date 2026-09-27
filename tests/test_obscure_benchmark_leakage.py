"""
tests/test_obscure_benchmark_leakage.py - Strict Dual-Pool Zero-Leakage Unit Test
=================================================================================
Evaluates all 30 benchmark queries against two independent leak target pools:
  Pool 1: Author-Written Doctrinal Holding Pool:
          words(query) & (words(overruling_holding) - words(gold_holding))
  Pool 2: Authentic Corpus-Grounded Overruling Sentence Pool:
          words(query) & (words(raw_overruling_sentence) - words(raw_target_holding) - words(target_case_caption))

Invariants Asserted:
  - Zero leak tokens across all 30 queries in Pool 1 (0/30).
  - Zero leak tokens across all 30 queries in Pool 2 (0/30).
"""

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
    'into', 'is', 'isn', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no',
    'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves',
    'out', 'over', 'own', 'same', 'she', 'should', 'shouldn', 'so', 'some', 'such', 'than', 'that',
    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those',
    'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn', 'we', 'were', 'weren',
    'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'wouldn', 'you',
    'your', 'yours', 'yourself', 'yourselves',
    # General legal/procedural stopwords common to both target and overruling opinions
    'court', 'supreme', 'decision', 'united', 'states', 'case', 'holding', 'held', 'under', 'rule',
    'doctrine', 'clause', 'amendment', 'constitution', 'constitutional', 'unconstitutional', 'act',
    'section', 'statute', 'federal', 'state', 'law', 'may', 'shall', 'u', 's', 'c', 'v'
}

def tokenize(text: str) -> set:
    if not text:
        return set()
    words = set(re.findall(r'[a-zA-Z]{3,}', text.lower()))
    return words - STOPWORDS

def test_dual_pool_zero_leakage():
    bench_path = ROOT / 'data' / 'obscure_overruled_benchmark.json'
    with open(bench_path, 'r', encoding='utf-8') as f:
        bench = json.load(f)
        
    print("=" * 95)
    print("STRICT DUAL-POOL BENCHMARK ZERO-LEAKAGE AUDIT (N=30)")
    print(f"Benchmark File: {bench_path}")
    print("=" * 95)
    print(f"{'Query ID':<10} | {'Pool 1 Leaks (Summary)':<35} | {'Pool 2 Leaks (Corpus Sentence)':<35}")
    print("-" * 95)
    
    total_p1_leaks = 0
    total_p2_leaks = 0
    
    for it in bench:
        qid = it['query_id']
        query = it.get('query', '')
        q_words = tokenize(query)
        
        # Target caption tokens (petitioner/respondent names)
        t_caption_words = tokenize(it['target_case'])
        
        # Pool 1: Summary holding differential
        gold_words = tokenize(it.get('gold_holding', ''))
        ovr_words = tokenize(it.get('overruling_holding', ''))
        p1_candidates = ovr_words - gold_words
        p1_leaks = q_words & p1_candidates
        
        # Pool 2: Raw corpus opinion sentence differential
        raw_tgt = it.get('grounding_target_holding', {}).get('sentence', '')
        raw_ovr = it.get('grounding_overruling_sentence', {}).get('sentence', '')
        raw_tgt_words = tokenize(raw_tgt)
        raw_ovr_words = tokenize(raw_ovr)
        
        p2_candidates = raw_ovr_words - raw_tgt_words - t_caption_words
        p2_leaks = q_words & p2_candidates
        
        p1_str = str(sorted(list(p1_leaks))) if p1_leaks else "0 (PASS)"
        p2_str = str(sorted(list(p2_leaks))) if p2_leaks else "0 (PASS)"
        
        print(f"{qid:<10} | {p1_str:<35} | {p2_str:<35}")
        
        assert len(p1_leaks) == 0, f"[{qid}] Failed Pool 1 Leak Test: leaked tokens {p1_leaks}"
        assert len(p2_leaks) == 0, f"[{qid}] Failed Pool 2 Leak Test: leaked tokens {p2_leaks}"
        
        total_p1_leaks += len(p1_leaks)
        total_p2_leaks += len(p2_leaks)
        
    print("-" * 95)
    print(f"AUDIT RESULT: ZERO LEAKS DETECTED ACROSS ALL 30 QUERIES IN BOTH POOLS!")
    print(f"Pool 1 Leaks: {total_p1_leaks}/30 | Pool 2 Leaks: {total_p2_leaks}/30")
    print("=" * 95)

if __name__ == '__main__':
    test_dual_pool_zero_leakage()
