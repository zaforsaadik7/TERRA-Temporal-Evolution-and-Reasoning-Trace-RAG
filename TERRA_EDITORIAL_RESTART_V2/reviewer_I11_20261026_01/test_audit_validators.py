import json,tempfile,unittest
from pathlib import Path
import validators as v
P=Path(__file__).resolve().parent
class AuditChecks(unittest.TestCase):
 def test_actual_coverage(self):v.coverage(json.loads((P/'READING_COVERAGE.json').read_text(encoding='utf8')))
 def test_missing_page(self):
  a=json.loads((P/'READING_COVERAGE.json').read_text(encoding='utf8'))
  with self.assertRaises(ValueError):v.coverage(a[:-1])
 def test_empty_inspection(self):
  a=json.loads((P/'READING_COVERAGE.json').read_text(encoding='utf8'));a[0]['review_notes']=''
  with self.assertRaises(ValueError):v.coverage(a)
 def test_findings_have_owners(self):
  for x in json.loads((P/'FINDINGS.json').read_text(encoding='utf8')):v.finding(x)
 def test_false_closure(self):
  with self.assertRaises(ValueError):v.finding(dict(id='x',artifact_sha256='a',closure_test='inspect',owner='test',status='RESOLVED_VERIFIED'))
 def test_stale_hash(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'a';p.write_bytes(b'a')
   with self.assertRaises(ValueError):v.pin(p,'0'*64)
 def test_traversal(self):
  with self.assertRaises(ValueError):v.members(['../outside.tex'])
 def test_alias(self):
  with self.assertRaises(ValueError):v.members(['main.tex','MAIN.tex'])
 def test_cross_pdf_destination(self):
  with self.assertRaises(ValueError):v.destination(21,21)
 def test_exception_cannot_be_ready(self):
  with self.assertRaises(ValueError):v.readiness(dict(submission_ready=True,certification_complete=False,open_exceptions=['I9'],peer_review_complete=False))
 def test_actual_archive_members(self):
  import zipfile
  with zipfile.ZipFile(P/'source_package.zip') as z:v.members(z.namelist());self.assertEqual(len(z.namelist()),46)
 def test_no_false_eq_pass(self):
  a=json.loads((P/'PDF_EQUIVALENCE.json').read_text(encoding='utf8'))
  for x in a.values():self.assertTrue(all(x[k] for k in ['all_text_equal','all_rasters_equal','all_links_equal','named_destinations_equal']))
 def test_citation_keys_match_actual_bibliography(self):
  import re
  a=json.loads((P/'CITATION_REGISTER.json').read_text(encoding='utf8'))
  self.assertEqual(a['uncited_entries'],['roig2026scalablereliableevaluationai'])
  for d in ['main','TERRA_SUPPLEMENT']:
   aux=(P/'cleanroom/extracted'/(d+'.aux')).read_text(encoding='utf8')
   self.assertEqual(a['undefined_citekeys'][d],[])
   self.assertEqual(a['cited_counts'][d],len(set(re.findall(r'\\bibcite\{([^}]+)\}',aux))))
if __name__=='__main__':unittest.main(verbosity=2)
