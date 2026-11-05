from pathlib import Path
import json,re,csv,hashlib
from decimal import Decimal,ROUND_HALF_UP
base=Path(__file__).parent; root=Path('F:/TERRA -Copy'); src=base/'candidate_src'
summary_path=root/'TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01/latency_percentiles_summary.json'
if hashlib.sha256(summary_path.read_bytes()).hexdigest()!='9cefb5a3119260e0b67f9e6515a98c1757803e0133487f85c207d86f99f5f623':raise RuntimeError('Latency evidence changed')
data=json.loads(summary_path.read_text(encoding='utf-8'))['cohort_summary']
fmt=lambda v:str(Decimal(str(v)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
lines=['% Supplement-only overrides from audited export_approved_01.', '% Milliseconds; linear percentiles; sample SD ddof=1; decimal half-up rounding to 2 places.']
checks=[]
for stem,cohort in [('TerraFastPathLatency','EASY_gross'),('TerraHardPathLatency','HARD_gross'),('TerraFastPathNetLatency','EASY_net'),('TerraHardPathNetLatency','HARD_net'),('TerraLatency','ALL_gross'),('TerraCatALatency','CatA_gross'),('TerraCatBLatency','CatB_gross')]:
    raw=data[cohort]['raw']
    for suffix,key in [('PTwentyFiveMs','p25'),('MedianMs','median'),('PSeventyFiveMs','p75'),('PNinetyFiveMs','p95')]:
        if cohort.startswith('Cat') and key=='p75': continue # original table omits these cells
        macro=stem+suffix; value=fmt(raw[key]); lines.append('\\renewcommand{\\'+macro+'}{'+value+'}'); checks.append({'macro':macro,'cohort':cohort,'field':key,'value':value})
    value=fmt(raw['mean'])+r' \pm '+fmt(raw['sample_sd_ddof1'])
    macro=stem+'MeanAndStdMs'; lines.append('\\renewcommand{\\'+macro+'}{'+value+'}'); checks.append({'macro':macro,'cohort':cohort,'field':'mean/sample_sd_ddof1','value':value})
for macro,key in [('TerraNetLatencyMedianMs','median'),('TerraNetLatencyPNinetyFiveMs','p95')]:
    value=fmt(data['ALL_net']['raw'][key]); lines.append('\\renewcommand{\\'+macro+'}{'+value+'}'); checks.append({'macro':macro,'cohort':'ALL_net','field':key,'value':value})
(src/'supplement_latency_corrections.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
with (base/'latency_cell_check.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['macro','cohort','field','value']);w.writeheader();w.writerows(checks)
limits=(src/'supplement_limitations.tex').read_text(encoding='utf-8')
labels=[]
for p in (src/'supplement_tables').glob('*.tex'):labels+=re.findall(r'\\label\{([^}]+)\}',p.read_text(encoding='utf-8'))
if len(labels)!=10 or len(set(labels))!=10 or len(re.findall(r'\\item\b',limits))!=18:raise RuntimeError('Object/limitation count mismatch')
assessment=(src/'supplement_assessment.tex').read_text(encoding='utf-8')
for value in ['40/76 (52.6','47/76 (61.8','22/62 (35.5','12/65 (18.5']:
    if value not in assessment:raise RuntimeError('Assessment value missing')
(base/'object_and_value_checks.json').write_text(json.dumps({'tables':labels,'limitation_entries':18,'latency_overrides_traced':len(checks),'sample_sd':True,'assessment_values':'matched approved report; no pipeline attribution'},indent=2),encoding='utf-8')
print('10 tables, 18 limitation entries,',len(checks),'latency overrides traced')
