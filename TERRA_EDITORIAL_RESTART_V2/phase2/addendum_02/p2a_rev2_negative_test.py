"""Negative control for p2a_ledger_rev2.py: perturb 7 frozen values in a scratch copy of the rev1 ledger and
confirm that the strict check no longer grants a source identity. Usage:
  python -X utf8 p2a_rev2_negative_test.py <repo_root> <addendum_01_dir> <scratch_dir>"""
import csv, os, subprocess, sys
ROOT, A1, S = sys.argv[1:4]
os.makedirs(S, exist_ok=True)
r = list(csv.DictReader(open(os.path.join(A1, 'number_provenance_ledger_rev1.csv'), encoding='utf-8')))
alt = {'ObscFullSafeSummary': ('0.8007', '0.8107'), 'ObscKappa': ('0.5746', '0.5747'), 'ClercFlatCiteFOne': ('1.8', '1.9'),
       'ClercTerraBleu': ('1.10', '1.20'), 'IssueTwentyOneAuditTargetConfirmedCI': ('96.9', '97.9'),
       'DirectLLMCatDSafeHandling': ('71/75', '70/75'), 'ObscSecFullVsFlatPRel': ('< 0.001', '= 0.5')}
for x in r:
    if x['macro'] in alt:
        a, b = alt[x['macro']]; x['frozen_value'] = x['frozen_value'].replace(a, b)
w = csv.DictWriter(open(os.path.join(S, 'number_provenance_ledger_rev1.csv'), 'w', newline='', encoding='utf-8'), fieldnames=r[0].keys()); w.writeheader(); w.writerows(r)
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(os.path.dirname(__file__), 'p2a_ledger_rev2.py'), ROOT, S, os.path.join(S, 'out.csv'), os.path.join(S, 's.json')], check=True, capture_output=True)
bad = [x for x in csv.DictReader(open(os.path.join(S, 'out.csv'), encoding='utf-8')) if x['macro'] in alt and x['status_rev2'].startswith('SOURCE_KEYED')]
print('perturbed rows still keyed:', len(bad), '(expected 0)')
sys.exit(1 if bad else 0)
