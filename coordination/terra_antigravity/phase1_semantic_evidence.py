"""Read protected inputs; write review evidence only under phase1/semantic_review.
No provider calls, graph traversal, statistics regeneration or manuscript writes.
"""
from pathlib import Path
import hashlib, json, re, statistics, subprocess, sys
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008'
OUT = BASE/'semantic_review'
OUT.mkdir(exist_ok=True)
inv = json.loads((BASE/'inventory_rev1.json').read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
changed=[]
checks=[]
for x in inv['manifest']+inv['evidence']+inv['pdfs']:
    if not all(k in x for k in ('source','sha256')): continue
    p=ROOT/x['source']
    actual=sha(p) if p.is_file() else None
    frozen=BASE/x['snapshot'] if 'snapshot' in x else None
    snapshot_actual=sha(frozen) if frozen and frozen.is_file() else None
    checks.append({'source':x['source'],'expected':x['sha256'],'actual':actual,
                   'snapshot':x.get('snapshot'),'snapshot_actual':snapshot_actual})
    if actual!=x['sha256']: changed.append(x['source'])
    if frozen and snapshot_actual!=x['sha256']: changed.append(str(frozen))
assert not changed, changed
main=(BASE/'snapshot/working/main.tex').read_text(encoding='utf-8').splitlines()
pdfs={name:pymupdf.open(BASE/'snapshot/pdfs'/file) for name,file in
      [('main','main.pdf'),('supplement','TERRA_supplementary_removed_material.pdf'),('original','archive_main.pdf')]}
for name,doc in pdfs.items():
    (OUT/f'{name}_pages.json').write_text(json.dumps([
        {'page':i+1,'text':p.get_text()} for i,p in enumerate(doc)],ensure_ascii=False,indent=2),encoding='utf-8')
# Theme equivalence is an authored review judgment, not keyword-based certification.
rows=[
('No practitioner / independent verifier validation','219-240; 658','1','Retained','Expert deployment review and unmeasured verifier errors remain explicit.'),
('Refusal masking and answered-subset selection','451-456; 104','1','Retained','Different answered subsets and overlapping overall intervals remain explicit.'),
('Score ceiling and rubric discrimination','658','1','Corrected qualification','Current 880/1750 ceiling replaces the original unsupported claim that Likert scoring resolved the ceiling.'),
('Jurisdiction, dates and live-update limits','161; 249-256; 635; 665','1','Retained','Historical SCOTUS scope and lack of live upsert remain; topology expansion is not streaming validation.'),
('Hosted variability / sensitivity provenance','240; 307; 344','1','Retained with evidence caveat','D066 and differing paths are disclosed; legacy 15-query sensitivity claim is explicitly not reverified in supplement.'),
('Parametric memory and adverse safety results','451-456; 527-529; 658','1-3','Corrected qualification','Direct-LLM counter-result and fatal errors remain. Supplement causal attribution to pretraining must be expressed as hypothesis.'),
('Fixed-hop retrieval and task failure modes','555; 573; 582-599','2-3','Retained','Chimel and analogical mismatch remain; attributing all CLERC errors to depth is not independently isolated.'),
('Oracle labels, bundled ablation and blinding','320; 540-546; 660','3-4','Retained','Thirty-item test, title seeding, relation tag/excerpt confounding and partial blinding remain.'),
('Answerable-query false refusals','451-456; 649','4','Retained','A=2/B=16 remain visible; unisolated causes stay a limitation, not a proven mechanism.'),
('Latency, concurrency and throttling','344; 474; 614-626','4-5','Retained with definition gap','Route versus category populations and gross versus net timing must not be interchanged; Table X needs explicit source reconstruction.'),
('Shared generation / verifier model','339-344; 659','5','Retained','Non-Llama faithfulness judges do not remove Llama Category-D verifier dependence.'),
('Unflagged refusals and label divergence','451-471','5','Retained','Flagged and semantic refusals remain distinct; fatal/refusal coexistence is not suppressed.'),
('Mixed dates, judges and evaluation regimes','344','5','Corrected with contradiction','Current dual-judge disclosures improve original account, but temporal identifiers are incorrectly said to be absent from records.'),
('Length filtering and sampling bias','161','5','Retained across package','Detailed omission/ranking examples reside in supplement; functioning destination is still required.'),
('Citation existence is not endorsement','162-164','5','Retained','Year-order validity and quotation/treatment limits do not establish legal applicability.'),
('Taxonomy truncation / polysemy / precision','249-256','5','Retained across package','Detailed precision and first-4000-character caveats remain in supplement; not replaced by domain accuracy rhetoric.'),
('Fixed parameters / small pilot / optimality','350; 594-599','5','Retained with provenance caveat','No global optimality; chronology and preregistration require evidence, not assertions.'),
('Public doctrinal versus private reasoning','314; 636','5-6','Retained','Public constitutional reasoning is not validation of private deliberative chains.')]
limitations=[]
for old,row in zip(inv['limitations'],rows):
    topic,loc,pages,status,note=row
    limitations.append({**old,'review_topic':topic,'current_main_lines':loc,
        'supplement_pages':pages,'semantic_status':status,'review_judgment':note,
        'scope':'Theme and qualification review; not verification of every numerical cell.'})
assert len(limitations)==18
(OUT/'limitation_coverage.json').write_text(json.dumps(limitations,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# Eighteen-limitation semantic coverage — Codex','',
    'Original text is preserved in `limitation_coverage.json`. Main line numbers refer to the locked working source; supplement pages refer to the delivered six-page PDF. A retained theme is not a clean-reference or all-numbers PASS. No item is authorized for deletion.', '',
    '| ID / original line | Qualification | Main lines | Supplement pages | Judgment |',
    '|---|---|---|---|---|']
for x in limitations:
    md.append(f"| {x['id']} / {x['original_line']} | {x['review_topic']} | {x['current_main_lines']} | {x['supplement_pages']} | {x['semantic_status']}: {x['review_judgment']} |")
(OUT/'LIMITATION_COVERAGE.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
# Preserve exact source paragraphs around review targets for independent checking.
ranges=[(104,129),(145,145),(161,184),(207,240),(249,256),(285,296),(307,353),
        (410,430),(451,474),(499,529),(540,573),(578,599),(614,649),(654,670)]
excerpts=[]
for a,b in ranges:
    excerpts.append({'start':a,'end':b,'lines':[{'line':i,'text':main[i-1]} for i in range(a,b+1)]})
(OUT/'main_source_excerpts.json').write_text(json.dumps(excerpts,ensure_ascii=False,indent=2),encoding='utf-8')
# Direct timing observations only. Do not label them gross/net without the metric's construction rule.
raw=ROOT/'data/terra_canonical_v2_eval.json'
records=json.loads(raw.read_text(encoding='utf-8'))
t=[x for x in records if x['pipeline']=='5_Full_TERRA']
timing={'source':str(raw.relative_to(ROOT)),'sha256':sha(raw),'field':'timing.total_ms',
        'warning':'These are saved-field medians, not an authenticated wall-clock/gross/net definition or new run.',
        'routes':{},'categories':{}}
for route in ['EASY','HARD']:
    a=[x for x in t if x['timing'].get('route_taken')==route]
    timing['routes'][route]={'n':len(a),'median_ms':statistics.median(x['timing']['total_ms'] for x in a)}
for cat in sorted({x['category'] for x in t}):
    a=[x for x in t if x['category']==cat]
    timing['categories'][cat]={'n':len(a),'median_ms':statistics.median(x['timing']['total_ms'] for x in a)}
(OUT/'timing_observations.json').write_text(json.dumps(timing,indent=2),encoding='utf-8')
temporal_command=[sys.executable,str(ROOT/'coordination/terra_antigravity/verify_temporal_handoff.py')]
temporal_run=subprocess.run(temporal_command,capture_output=True,text=True,encoding='utf-8',check=True)
(OUT/'temporal_verification.json').write_text(json.dumps({'command':temporal_command,
    'exit':temporal_run.returncode,'result':json.loads(temporal_run.stdout)},indent=2),encoding='utf-8')
# Fresh readable review renders, not an automated visual PASS.
render=OUT/'render';render.mkdir(exist_ok=True)
for i,p in enumerate(pdfs['supplement']):
    p.get_pixmap(matrix=pymupdf.Matrix(1.7,1.7)).save(render/f'supplement-{i+1:02d}.png')
for i in [3,5,6,11,12,13,16,18,19,20,21,22,23]:
    pdfs['main'][i].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(render/f'main-{i+1:02d}.png')
(OUT/'protected_input_check.json').write_text(json.dumps({'checked':len(checks),'changed':changed,'files':checks},indent=2),encoding='utf-8')
manifest=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
          for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
manifest.append({'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size})
for rel in ['coordination/terra_restart/codex_to_claude/20261008-codex-0026-phase1-semantic-audit-request.md',
            'coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0006-phase1-semantic-complete.md']:
    p=ROOT/rel
    manifest.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'limitations':len(limitations),'protected_inputs_checked':len(checks),'changed':changed,
                  'pdf_pages':{k:len(v) for k,v in pdfs.items()},'timing':timing},indent=2))
