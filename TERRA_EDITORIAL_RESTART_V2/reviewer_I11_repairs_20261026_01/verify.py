from pathlib import Path
import json,re,collections,hashlib,unittest
import pymupdf as f
P=Path(__file__).resolve().parent;C=P/'candidate/src';B=P/'baseline/src';D=P/'builds/r06'
def rd(p):return Path(p).read_text(encoding='utf-8-sig')
def load(p):return json.loads(rd(p))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def body(s):a=s.index(r'\begin{tabular}');return s[a:s.index(r'\end{tabular}',a)]
def original(row):
 s=rd(B/row['original_file'])
 if row['original_file']=='main.tex':
  p=s.index(r'\label{'+row['label']+'}');a=max(s.rfind(r'\begin{table}',0,p),s.rfind(r'\begin{table*}',0,p));s=s[a:s.index(r'\end{table',p)]
 return s
macro_pat=r'\\((?:Ablation|Cat|Clerc|CaseFacts|Issue|Terra|DirectLLM|FlatRAG|GraphRAG|HippoRAG|Combined|Baselines)[A-Za-z]+)\b'
pres=[]
for row in load(P/'FULL_TABLE_PRESERVATION.json'):
 a,b=body(original(row)),body(rd(C/row['supplement_file']))
 x,y=collections.Counter(re.findall(macro_pat,a)),collections.Counter(re.findall(macro_pat,b))
 na,nb=collections.Counter(re.findall(r'\d+(?:\.\d+)?',a)),collections.Counter(re.findall(r'\d+(?:\.\d+)?',b))
 pres.append({'label':row['label'],'scientific_macro_cells_same':x==y,'literal_numeric_tokens_same':na==nb,'macro_missing':dict(x-y),'literal_missing':dict(na-nb),'literal_extra':dict(nb-na),'numeric_token_count':sum(na.values()),'macro_occurrences':sum(x.values())})
(P/'TABLE_VALUE_PRESERVATION_CHECK.json').write_text(json.dumps(pres,indent=2),encoding='utf8')
docs={n:f.open(D/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']}
text={n:re.sub(r'\s+',' ',' '.join(p.get_text() for p in d)) for n,d in docs.items()}
class Repairs(unittest.TestCase):
 def test_page_budget(self):self.assertLessEqual(len(docs['main']),25);self.assertEqual(len(docs['TERRA_SUPPLEMENT']),34)
 def test_no_clipped_content_or_build_errors(self):
  for v in load(D/'BUILD_RESULT.json').values():
   self.assertFalse(v['overfull_lines']);self.assertFalse(v['undefined_reference_lines']);self.assertFalse(v['missing_character_lines']);self.assertFalse(any(x['offpage'] for x in v['layout']))
 def test_clipped_disclosure_recovered(self):
  for s in ['143, 179, 204 and 203','0.6950 raw, 0.7357 clamped','0.82 to 9.25','headline values in this paper are the raw dual-judge means']:self.assertIn(s,text['main'])
 def test_accepted_fdr_reporting(self):self.assertIn('q = 0.0189',text['main']);self.assertIn('q = 0.3865',text['main'])
 def test_no_false_length_cause(self):self.assertNotIn('because TERRA writes longer',rd(C/'main.tex'))
 def test_counts_and_units(self):
  self.assertNotIn('/100/100',text['main']);self.assertIn('13.97',text['main']);self.assertIn('percentage points',text['main']);self.assertNotIn('CatBTerraVsFlatNodeRecallDelta',rd(C/'main.tex'))
 def test_emphasis(self):
  t=rd(C/'supplement_details/i11_detail_tab_overall_summary.tex');self.assertIn(r'\mathbf{\TerraCatAFaithfulness}',t);self.assertNotIn(r'\mathbf{\HippoRAGCatAFaithfulness}',t)
  t=rd(C/'supplement_details/i11_detail_tab_cat_b_performance.tex');self.assertNotIn(r'\mathbf{',t);self.assertIn('Metric cells are descriptive',t)
 def test_distinct_refusal_definitions(self):
  self.assertIn('separately shows system-flagged refusals',rd(C/'main.tex'));self.assertIn('46/75',text['main']);self.assertIn('48/75',text['main'])
 def test_correct_clerc_endpoint(self):
  s=rd(C/'supplement_limitations.tex');self.assertNotIn('gold-precedent omission rate',s);self.assertIn('across 120 completions, OR/AND respectively',s)
 def test_historical_chronology_qualified(self):
  self.assertIn('do not authenticate historical freezing dates',rd(C/'main.tex'));self.assertNotIn('An automated audit verifies chronological precedence',rd(C/'main.tex'));self.assertIn('historical freezing date or execution order',rd(C/'supplement_limitations.tex'))
 def test_no_shrunk_main_summaries(self):
  for row in load(P/'FULL_TABLE_PRESERVATION.json'):
   if row['original_file'].startswith('tables/'):
    self.assertNotIn(r'\resizebox',rd(C/row['original_file']))
 def test_sat_graph(self):
  s=rd(C/'supplement_tables/table_system_comparison.tex');self.assertNotIn('Propositional SAT solver',s);self.assertIn('Deterministic structural/temporal',s)
  self.assertIn('vol. 416',text['main']);self.assertIn('282–287',text['main'])
 def test_summary_obscure_arms(self):
  s=rd(C/'tables/table_obscure_overruled_eval.tex');self.assertIn('TERRA-Unlabeled',s);self.assertEqual(s.count('Direct LLM'),1)
 def test_all_full_table_cells_preserved(self):
  for row in pres:self.assertTrue(row['scientific_macro_cells_same'],row);self.assertTrue(row['literal_numeric_tokens_same'],row)
 def test_frozen_macros_and_new_study_unchanged(self):
  for p in B.rglob('*'):
   if p.is_file() and (p.name.startswith(('generated_','phase3_')) or p.name in ['matched_comparison_main.tex','supplement_matched_comparison.tex','supplement_utility_audit.tex','supplement_assessment.tex']):self.assertEqual(sha(p),sha(C/p.relative_to(B)),p.name)
 def test_all_limitations_and_historical_labels(self):
  self.assertEqual(len(re.findall(r'\\item\b',rd(C/'supplement_limitations.tex'))),18)
  labs=set(re.findall(r'\\label\{([^}]+)\}','\n'.join(rd(p) for p in C.rglob('*.tex'))))
  old=load(P.parent/'reviewer_I0_20261026_03/OBJECT_MAP.json')['objects']
  for o in old:
   if o['id']!='OBJ08':self.assertIn(o['original']['label'],labs)
 def test_links(self):
  for name,d in docs.items():
   for page in d:
    for l in page.get_links():
     if l['kind']==f.LINK_GOTO:self.assertTrue(0<=l['page']<len(d))
     if l['kind']==f.LINK_GOTOR:
      target=Path(l['file']).stem;self.assertIn(target,docs)
      if isinstance(l.get('page'),int) and l['page']>=0:self.assertLess(l['page'],len(docs[target]))
 def test_summary_notes_survive_tex_comments(self):
  for phrase in ['Overall intervals overlap','No safe-handling contrast survives','not independently validated legal correctness','Full cells, methods and notes']:self.assertIn(phrase,text['main']+text['TERRA_SUPPLEMENT'])
 def test_all_original_macro_usage_definition_files_identical(self):
  for name in ['generated_stats.tex','generated_obscure_stats.tex','generated_corpus_stats_20k.tex']:
   self.assertEqual((B/name).read_bytes(),(C/name).read_bytes())
 def test_old_accepted_sources_still_intact_before_adoption(self):
  w=P.parent/'working/src';base=load(P/'BASELINE_MANIFEST.json')
  self.assertTrue(all(sha(w/k)==v['sha256'] for k,v in base['sources'].items()))
if __name__=='__main__':unittest.main(verbosity=2)
