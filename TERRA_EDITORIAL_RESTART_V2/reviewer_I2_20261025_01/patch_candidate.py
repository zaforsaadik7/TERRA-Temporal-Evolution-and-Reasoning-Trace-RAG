from pathlib import Path
import difflib,json
P=Path(__file__).resolve().parent;S=P/'candidate/src';B=P/'baseline/src'
changes=[]
def replace(file,old,new,reason):
 p=S/file; t=p.read_text(encoding='utf-8');assert t.count(old)==1,(file,old[:80],t.count(old))
 with p.open('w',encoding='utf-8',newline='') as f:f.write(t.replace(old,new))
 changes.append({'file':file,'before':old,'after':new,'reason':reason})
replace('main.tex','if entailment fails across two expansion attempts, generation ends in a deterministic safety refusal','if the permitted evidence checks fail, generation ends in a deterministic safety refusal','Do not give EASY the HARD retry policy or imply two fallback expansions')
replace('main.tex','If entailment still fails after two expansions, the \\textbf{Safety Refusal Firewall} halts generation with a deterministic refusal:',
 'The recovered HARD path permits two attempts in total (initial retrieval plus one fallback), not two retries; EASY has no expansion retry. Historical logs do not record intermediate retry transitions. If the permitted checks fail, the \\textbf{Safety Refusal Firewall} halts generation with a deterministic refusal:',
 'Current source range(2) and EASY branch; distinguish historical logging from capability')
replace('main.tex','Retrieved evidence is checked before generation, with refusal on empty context or failed evidence checks.}',
 'Retrieved evidence is checked before generation, with refusal on empty context or failed evidence checks. Retry arrows describe recovered code, not authenticated historical transitions.}',
 'Caption must not certify all historical runs against recovered source')
replace('figure_1_system_architecture.tex','\\textbf{\\small Self-Correction Loop}','\\textbf{\\small HARD Retrieval Retry}','EASY has no graph expansion fallback')
replace('figure_1_system_architecture.tex','Expand Search Radius','One Fallback After Initial Attempt','Distinguish total attempts from retries')
replace('figure_1_system_architecture.tex','Verified Citation Links','Indexed Citation Links','Known imperfect link fidelity cannot support categorical verified-link claim')
replace('figure_1_system_architecture.tex','{No} (expansion);','{No (HARD)} (expansion);','Do not route EASY failure into HARD retry')
replace('figure_1_system_architecture.tex','(expansion) -| (bfs);','(expansion.west) -| (retrieval.north);','Changed k must re-query vector seeds before BFS')
replace('figure_1_system_architecture.tex','{Failed $2\\times$} (refusal);','{Checks failed} (refusal);','EASY failure does not require two HARD attempts')

# Keep the existing table and source placements; qualify units rather than redesign.
replace('supplement_tables/table_run_provenance.tex','\\textbf{$N$}','\\textbf{$N$ (unit)}','Heterogeneous units must be explicit')
file='supplement_tables/table_run_provenance.tex'
for old,new in [('      1,400 \\\\','      1,400 outputs \\\\'),('      350 \\\\','      350 queries \\\\'),('      1,750 \\\\','      1,750 outputs \\\\'),(' & 35 \\\\',' & 35 queries \\\\'),(' & 400 \\\\',' & 400 records \\\\'),(' & 75 \\\\',' & 75 queries \\\\'),('      120 \\\\','      120 outputs \\\\'),('      76 \\\\','      76 outputs \\\\')]:
 replace(file,old,new,'Label population unit without changing value')
# Two identical external-question counts are both intentional.
p=S/file;t=p.read_text(encoding='utf-8');old=' & 170 \\\\';assert t.count(old)==2
t=t.replace(old,' & 170 queries \\\\');p.write_text(t,encoding='utf-8',newline='');changes.append({'file':file,'before':old,'after':' & 170 queries \\\\','occurrences':2,'reason':'External question count differs from510arm records'})
extra=r'''    \addlinespace
    Stored-context sensitivity & historical dates unverified &
      Canonical: 66/100; legacy: 62/100 complete target sets; separate bounded engine: 61/100 & 100 queries \\
    \addlinespace
    Distance-only diagnostic & 8 Oct.\ 2026\newline (run record) &
      MiniLM squared-L2; benchmark text only, not Title Match & 350 queries \\
    \addlinespace
    Temporal-update topology & 23 Sept.\ 2026\newline (recorded timestamp) &
      BFS stability; 106 pair observations, not generated answers & 82 queries \\
    \addlinespace
    Corpus / taxonomy audits & historical dates unverified &
      Original graph properties and automated classification audits; no blanket historical run linkage & 20,000 nodes \\
'''
replace(file,'    \\bottomrule',extra+'    \\bottomrule','Give distinct sensitivity/diagnostic/topology populations explicit representation')
replace(file,'File modification dates elsewhere are not execution dates.',
 'File modification dates elsewhere are not execution dates. In the recovered source, degree greater than 50 activates hub handling with directional budgets of 75 incoming and 25 outgoing neighbors; these are simultaneous controls, not conflicting cap versions. Current source does not authenticate historical settings. Recorded generator identifiers also reflect different logging paths (requested model arguments versus returned identifiers), not proof of identical backend weights.',
 'Preserve settled threshold/budget distinction and model-identifier limits')
diff=''
for f in sorted(S.rglob('*')):
 if f.is_file():
  rel=f.relative_to(S);a=(B/rel).read_text(encoding='utf-8');b=f.read_text(encoding='utf-8')
  if a!=b:diff+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='baseline/'+rel.as_posix(),tofile='candidate/'+rel.as_posix()))
(P/'source.diff').write_text(diff,encoding='utf-8')
(P/'ledgers/PATCH_DISPOSITIONS.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'patches':len(changes),'changed_files':sorted(set(x['file'] for x in changes))}))
