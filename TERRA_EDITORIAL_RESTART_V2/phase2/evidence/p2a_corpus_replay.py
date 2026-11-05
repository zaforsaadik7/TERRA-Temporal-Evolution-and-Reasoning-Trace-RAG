"""Phase 2A: replay Paper/scripts/generate_corpus_stats.py with --out pointing to a scratch path and compare with
the frozen generated_corpus_stats_20k.tex. Read-only for protected files.
Usage: python -X utf8 p2a_corpus_replay.py <repo_root> <scratch_dir> <out_csv>
"""
import csv, os, re, subprocess, sys
ROOT, SCR, OUT = sys.argv[1:4]
tmp = os.path.join(SCR, 'corpus_replay.tex')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'Paper', 'scripts', 'generate_corpus_stats.py'),
                '--corpus', os.path.join(ROOT, 'dataset_20k_cap', 'terra_eeg_index_20k.json'), '--out', tmp], check=True)


def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        m = re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}', l.strip())
        if m:
            d[m.group(1)] = m.group(2)
    return d


a = load(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'generated_corpus_stats_20k.tex')); b = load(tmp)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['macro', 'frozen_value', 'replay_value', 'status'])
    for k in a:
        w.writerow([k, a[k], b.get(k), 'MATCH' if a[k] == b.get(k) else 'MISMATCH'])
print(sum(a[k] == b.get(k) for k in a), '/', len(a), 'match')
