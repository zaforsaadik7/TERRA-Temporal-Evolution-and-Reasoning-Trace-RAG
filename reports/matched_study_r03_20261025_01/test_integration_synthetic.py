"""Isolated fake-source TeX integration; no actual manuscript/model/provider I/O."""
import unittest,tempfile,json,hashlib,subprocess,sys
from pathlib import Path
SOURCE=Path(__file__).with_name('integrate_working_sources.py')

class IntegrationTests(unittest.TestCase):
    def check_style(self,nl,mixed):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);p=root/'reports/case';p.mkdir(parents=True)
            s=root/'TERRA_EDITORIAL_RESTART_V2/working/src';s.mkdir(parents=True)
            conclusion=('\\section{Conclusion}\nBenchmarking across \\numUniqueQueries\\ queries (\\numTotalEvals\\ evaluations) shows prior results.\n\\begingroup\n\\let\\oldfootnotesize\\footnotesize\n')
            main=('prefix\n\\subsection{Factual Precision, Safety Firewalling, and Adversarial Deception}\n').replace('\n',nl)+conclusion.replace('\n','\n' if mixed else nl)
            original={'main.tex':main.encode(),'TERRA_SUPPLEMENT.tex':('body\n\\bibliographystyle{IEEEtran}\n').replace('\n',nl).encode(),
                'generated_stats.tex':b'% original statistics unchanged\n','supplement_limitations.tex':b'% all18 existing themes preserved\n'}
            rows=[]
            for name,raw in original.items():
                (s/name).write_bytes(raw);rows.append({'path':str(s/name),'relative':name,'sha256':hashlib.sha256(raw).hexdigest()})
            (p/'MANUSCRIPT_BEFORE_MANIFEST.json').write_text(json.dumps({'files':rows}))
            (p/'postrun').mkdir();(p/'postrun/AUDIT_RESULT.json').write_text(json.dumps({'status':'PASS_COMPLETE_350_AUDIT','reserved_calls':5,'reference_cost_nanodollars':10**9}))
            summary={'assigned':100,'eligible_pairs':100,'excluded_pairs':0,'H_paired_mean':.5,'T_paired_mean':.6,
                'paired_mean_difference':.1,'H_refusals':4,'T_refusals':69,'assigned_cohort_worst_case_bounds':[.1,.1],
                'paired_bootstrap_95':[.1,.02,.2],'two_sided_paired_randomization':[.1,.01]}
            analysis={'primary':'B','summaries':{'B':summary},'per_query':[{'query_id':str(i),'category':'B','H':.5,'T':.6,'difference':.1} for i in range(350)]}
            (p/'ANALYSIS_RESULTS.json').write_text(json.dumps(analysis));(p/SOURCE.name).write_bytes(SOURCE.read_bytes())
            run=subprocess.run([sys.executable,'-I','-S','-B',str(p/SOURCE.name)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            self.assertEqual(run.returncode,0,run.stdout.decode())
            text=(s/'main.tex').read_text();supp=(s/'supplement_matched_comparison.tex').read_text()
            self.assertEqual(text.count('\\input{matched_comparison_main}'),1)
            self.assertIn('historical multi-baseline evaluation',text)
            self.assertIn('69/100 verifier-triggered refusals',text)
            self.assertIn(r'\$1.000000',supp)
            self.assertIn(r'95\%',(s/'matched_comparison_main.tex').read_text())
            self.assertEqual((s/'generated_stats.tex').read_bytes(),original['generated_stats.tex'])
            self.assertEqual((s/'supplement_limitations.tex').read_bytes(),original['supplement_limitations.tex'])
            self.assertFalse(json.loads((p/'WORKING_INTEGRATION.json').read_bytes())['pdf_compiled'])
    def test_lf(self):self.check_style('\n',False)
    def test_crlf(self):self.check_style('\r\n',False)
    def test_mixed_newlines(self):self.check_style('\r\n',True)

if __name__=='__main__':unittest.main()
