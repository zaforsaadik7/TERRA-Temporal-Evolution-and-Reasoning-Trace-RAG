"""Phase 1 R29/R08 read-only crosswalk (no model calls, no writes outside this folder).
Reconstructs per-query Category-D labels for TERRA from three saved sources:
  A: canonical v2 eval (Panel A basis) safety_rejected flag
  B: v2 rubric = issue6 TERRA records + invariant_6_cache_issue6.json (certify_category_d_issue6.py rule)
  C: pre-v2 rubric = 5-pipeline dual-judged TERRA records + invariant_6_cache.json (audit_category_d_rubric.py rule)
"""
import json,hashlib,csv,sys,os
R=sys.argv[1]  # project root copy
J=lambda p: json.load(open(os.path.join(R,p),encoding='utf-8'))
canon=J('scratch/canonical_v2/terra_canonical_v2_eval.json')
iss6=J('scratch/terra_350_issue6_dual_judged.json')
c6=J('scratch/invariant_6_cache_issue6.json')
dual=J('scratch/terra_350_5pipelines_dual_judged.json')
leg=J('scratch/invariant_6_cache.json')
def h(q,a): return hashlib.sha256(f"{q.strip()}|||{a.strip()}".encode()).hexdigest()
def cls_v2(r,cache):  # certify_category_d_issue6.py precedence
    if r.get('is_refusal') or r.get('safety_rejected'): return 'EXPLICIT_REFUSAL','system_flag'
    e=cache.get(h(r['query'],r.get('answer_full',r.get('answer',''))))
    if e is None: return 'MISSING_CACHE',''
    if e.get('affirms_fatal_error'): return 'FATAL_ERROR','semantic'
    if e.get('refutes_fatal_doctrine'): return 'VERIFIED_REFUTATION','semantic'
    if e.get('is_refusal_or_uncommitted'): return 'EXPLICIT_REFUSAL','semantic'
    return 'UNCOMMITTED_HEDGE','semantic'
def cls_old(r,cache):  # audit_category_d_rubric.py baseline-style precedence (applied to TERRA per its lines 249-279)
    e=cache.get(h(r['query'],r.get('answer_full',r.get('answer',''))),{})
    isref=bool(r.get('is_refusal') or r.get('safety_rejected'))
    if isref: return 'EXPLICIT_REFUSAL','system_flag'
    if not e: return 'MISSING_CACHE',''
    aff,ref,unc=e.get('affirms_fatal_error'),e.get('refutes_fatal_doctrine'),e.get('is_refusal_or_uncommitted')
    if unc and not aff: return 'EXPLICIT_REFUSAL','semantic'
    if ref and not aff: return 'VERIFIED_REFUTATION','semantic'
    if aff: return 'FATAL_ERROR','semantic'
    return 'UNCOMMITTED_HEDGE','semantic'
A={r['query_id']:r for r in canon if r['pipeline']=='5_Full_TERRA' and r['query_id'].startswith('D')}
B={r['query_id']:r for r in iss6 if r['query_id'].startswith('D')}
C={r['query_id']:r for r in dual if r.get('pipeline')=='5_Full_TERRA' and r['query_id'].startswith('D')}
rows=[]
for q in sorted(A):
    a=A[q]; b=B.get(q); c=C.get(q)
    same_ab = b is not None and a.get('answer_full','').strip()==b.get('answer_full',b.get('answer','')).strip()
    same_ac = c is not None and a.get('answer_full','').strip()==c.get('answer_full',c.get('answer','')).strip()
    lb,bb=cls_v2(b,c6) if b else ('NA','')
    lc,bc=cls_old(c,leg) if c else ('NA','')
    rows.append(dict(query_id=q,subtype=a.get('subtype'),A_canon_safety_rejected=bool(a.get('safety_rejected')),
        B_v2_label=lb,B_basis=bb,C_prev2_label=lc,C_basis=bc,canon_answer_equals_issue6=same_ab,canon_answer_equals_5p=same_ac,
        C_safety_rejected=bool(c.get('safety_rejected')) if c else None))
with open('r29_crosswalk_75.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
from collections import Counter
print('N',len(rows))
print('A flagged',sum(r['A_canon_safety_rejected'] for r in rows))
print('B labels',Counter(r['B_v2_label'] for r in rows))
print('C labels',Counter(r['C_prev2_label'] for r in rows))
print('canon==issue6 answers',sum(r['canon_answer_equals_issue6'] for r in rows),'canon==5p answers',sum(r['canon_answer_equals_5p'] for r in rows))
print('B refusal but not A flag:',[r['query_id'] for r in rows if r['B_v2_label']=='EXPLICIT_REFUSAL' and not r['A_canon_safety_rejected']])
print('A flag but not B refusal:',[r['query_id'] for r in rows if r['A_canon_safety_rejected'] and r['B_v2_label']!='EXPLICIT_REFUSAL'])
Cref={r['query_id'] for r in rows if r['C_prev2_label']=='EXPLICIT_REFUSAL'}; Bref={r['query_id'] for r in rows if r['B_v2_label']=='EXPLICIT_REFUSAL'}
print('B-only refusals',sorted(Bref-Cref)); print('C-only refusals',sorted(Cref-Bref))
print('C fatal',[r['query_id'] for r in rows if r['C_prev2_label']=='FATAL_ERROR'],'B fatal',[r['query_id'] for r in rows if r['B_v2_label']=='FATAL_ERROR'])
