"""AST-extract pure source rules; never execute the CLI's dataset reads."""
import ast,hashlib,html,unittest,unicodedata
from pathlib import Path
tree=ast.parse(Path(__file__).with_name('source_check.py').read_text(encoding='utf-8'))
env={'html':html,'unicodedata':unicodedata,'hashlib':hashlib}
nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['norm','sections','span_result']]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'pure_source_rules','exec'),env)
norm,span=env['norm'],env['span_result']
def doc(text,kind='majority'):return {'casebody':{'head_matter':'Reporter statement','opinions':[{'type':kind,'text':text}]}}
class SourceTests(unittest.TestCase):
 def test_whitespace_typography(self):self.assertEqual(span('A “quoted”\nstatement',doc('A "quoted" statement'))['status'],'LOCATED_NORMALIZED_SPAN')
 def test_paraphrase_not_exact_source(self):self.assertEqual(span('A reworded proposition',doc('A different proposition'))['status'],'NOT_LOCATED_NORMALIZED_SPAN')
 def test_dissent_not_majority(self):self.assertEqual(span('An opinion statement',doc('An opinion statement','dissent'))['locations'][0]['section_type'],'dissent')
 def test_reporter_headnote_not_holding(self):self.assertEqual(span('Reporter statement',doc('Majority body'))['locations'][0]['section_type'],'head_matter_reporter')
 def test_no_empty_span_success(self):self.assertEqual(span('',doc('Body'))['status'],'NO_SPAN')
 def test_different_opinions_not_concatenated(self):self.assertEqual(span('alpha beta',{'casebody':{'opinions':[{'type':'majority','text':'alpha'},{'type':'dissent','text':'beta'}]}})['status'],'NOT_LOCATED_NORMALIZED_SPAN')
 def test_source_location_does_not_certify_law(self):self.assertIn('answer correctness',span('Body',doc('Body'))['not_certified'])
if __name__=='__main__':unittest.main()
