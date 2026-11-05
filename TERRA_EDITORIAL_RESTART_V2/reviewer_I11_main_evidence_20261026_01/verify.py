from pathlib import Path
import json,re,hashlib,unittest,collections
import pymupdf as f
P=Path(__file__).resolve().parent;B=P/'baseline/src';C=P/'candidate/src';D=P/'builds/r01';W=P.parent/'working/src'
def rd(p):return p.read_text(encoding='utf-8-sig')
def load(p):return json.loads(rd(p))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
allowed={'main.tex','matched_comparison_main.tex','tables/table_casefacts_eval.tex','tables/table_clerc_eval.tex','tables/table_obscure_overruled_eval.tex'}
texts={n:'\n'.join(page.get_text() for page in f.open(D/(n+'.pdf'))) for n in ['main','TERRA_SUPPLEMENT']}
class Evidence(unittest.TestCase):
 def test_working_baseline_untouched_before_adoption(self):
  inv=load(P/'BASELINE_MANIFEST.json')['sources'];self.assertTrue(all(sha(W/k)==v['sha256'] for k,v in inv.items()))
 def test_only_declared_edits(self):
  changed={p.relative_to(C).as_posix() for p in C.rglob('*') if p.is_file() and p.read_bytes()!=(B/p.relative_to(C)).read_bytes()};self.assertEqual(changed,allowed)
 def test_full_detail_and_supplement_unchanged(self):
  for p in C.rglob('*'):
   if p.is_file() and ('supplement' in p.relative_to(C).as_posix().lower() or p.name.startswith('generated_')):self.assertEqual(p.read_bytes(),(B/p.relative_to(C)).read_bytes())
 def test_main_scientific_macro_cells_not_removed(self):
  pattern=r'\\((?:Ablation|Cat[A-D]|Combined|Terra|DirectLLM|FlatRAG|GraphRAG|HippoRAG|CaseFacts|Clerc|Obsc)[A-Za-z]+)\b'
  for name in allowed:
   old=collections.Counter(re.findall(pattern,rd(B/name)));new=collections.Counter(re.findall(pattern,rd(C/name)));self.assertFalse(old-new,name)
 def test_all_twelve_main_tables_still_render(self):
  self.assertEqual(re.findall(r'^TABLE ([IVX]+)$',texts['main'],re.M),['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'])
 def test_restored_lexical_columns(self):
  self.assertIn('ROUGE-L P',texts['main']);self.assertIn('ROUGE-L F1',texts['main'])
 def test_restored_statistical_and_external_uncertainty(self):
  self.assertIn('Raw p',texts['main']);self.assertIn('Exact 95% CI',texts['main']);self.assertIn('0.625',texts['main']);self.assertIn('0.092285',texts['main'])
 def test_main_useful_answer_tradeoff_matches_source_record(self):
  s=rd(C/'matched_comparison_main.tex');u=rd(B/'supplement_utility_audit.tex')
  for pair in ['172/272','178/78','77/29','164/116','96/31']:self.assertIn(pair,s)
  self.assertIn('172 & 272',u);self.assertIn('178 & 78',u);self.assertIn('77 & 29',u);self.assertIn('164 & 116',u);self.assertIn('96 & 31',u)
  self.assertIn('not validated correct-answer yield',s)
 def test_page_budget_and_build_integrity(self):
  x=load(D/'BUILD_RESULT.json');self.assertLessEqual(x['main']['pages'],25);self.assertEqual(x['TERRA_SUPPLEMENT']['pages'],34)
  for r in x.values():
   for field in ['overfull_lines','undefined_reference_lines','missing_character_lines']:self.assertFalse(r[field])
   self.assertFalse(any(p['offpage'] for p in r['layout']))
 def test_visual_coverage(self):
  rows=load(P/'VISUAL_REVIEW.json');self.assertEqual(len(rows),58);self.assertFalse(any(x['review']=='NEEDS_INSPECTION' for x in rows))
 def test_cross_document_pdf_links(self):
  docs={n:f.open(D/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']}
  for d in docs.values():
   for page in d:
    for l in page.get_links():
     if l['kind']==f.LINK_GOTO:self.assertTrue(0<=l['page']<len(d))
     if l['kind']==f.LINK_GOTOR:
      target=Path(l['file']).stem;self.assertIn(target,docs)
      if isinstance(l.get('page'),int) and l['page']>=0:self.assertLess(l['page'],len(docs[target]))
 def test_eleven_table_claim_audit_has_source_evidence(self):
  rows=load(P/'CLAIM_TABLE_SOURCE_REVIEW.json');self.assertEqual(len(rows),11)
  for x in rows:self.assertEqual(len(x['active_summary_matches']),1);self.assertTrue(x['main_citing_paragraphs']);self.assertTrue(x['rationale'])
if __name__=='__main__':unittest.main(verbosity=2)
