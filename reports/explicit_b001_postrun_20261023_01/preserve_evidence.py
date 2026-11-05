"""Read saved evidence only. No runtime imports, database/model or native calls."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
E=R/'reports/authentic_smoke_explicit_candidate_20261023_01/evidence'
W=R/'reports/explicit_user_b001_freeze_20261023_01/wrapper_evidence'
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
rows=[ident(p) for folder in (E,W) for p in sorted(folder.iterdir()) if p.is_file()]
save('evidence_manifest.json',(json.dumps(rows,indent=2)+'\n').encode())
for name in ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1'):
    live=(R/'scripts/matched_baseline'/name).read_bytes()
    assert live==(R/'reports/explicit_user_b001_freeze_20261023_01'/(name+'.final')).read_bytes()
    save(name+'.executed',live)
save('STATUS.incoming.json',(R/'coordination/terra_antigravity/STATUS.json').read_bytes())
before=(E/'file_pins_before.json').read_bytes();after=(E/'file_pins_after.json').read_bytes()
assert before==after
terminal=json.loads((E/'terminal.json').read_bytes())
summary={'outcome':terminal,'wrapper_terminal':json.loads((W/'terminal.json').read_bytes()),
 'before_after_saved_pins_byte_equal':True,'pin_record':ident(E/'file_pins_before.json'),
 'pin_summary':json.loads(before).get('__manifest_verification__'),
 'child_report_bytes':(E/'child_report.json').stat().st_size,
 'child_output':(E/'child_output.log').read_text(),
 'boundary_records':[{'path':str(p),'mtime_ns':p.stat().st_mtime_ns,'value':json.loads(p.read_bytes())}
     for p in sorted(E.glob('boundary_*.stdout'),key=lambda p:p.stat().st_mtime_ns)],
 'limitations':['No independent fresh source-store/cache rehash or firewall query performed in this audit.',
 'Successful one-query feasibility report, not provider certification or full-benchmark results.',
 'Hypothetical EASY/HARD routes and synthetic judge-answer placeholder are not live model responses.'],
 'retry_authorized':False}

report=json.loads((E/'child_report.json').read_bytes())
assert terminal['status']=='OFFLINE_FEASIBILITY_SUCCESS' and terminal['child_exit']==0 and terminal['failures']==[]
assert summary['wrapper_terminal']['parent_exit']==0 and summary['wrapper_terminal']['failures']==[]
assert report['mode']=='AUTHENTIC_OFFLINE_FEASIBILITY' and report['query_id']=='B001'
assert report['query_text_sha256']=='55ae112d6bf9526988d3a7e412255200f5d684779724c4c83f3cb8d6d87c6723'
assert report['documents']==20000 and report['graph_audit']['schema_valid'] is True
assert len(report['dense_candidate_ids'])==len(set(report['dense_candidate_ids']))==100
assert report['graph_seed_ids']==report['dense_candidate_ids'][:2]
assert set(report['hypothetical_route_metrics'])=={'EASY','HARD'}
assert all(v['all_roles_passed'] is True for v in report['hypothetical_route_metrics'].values())
assert report['execution_facts']['live_api_calls']==0
assert report['execution_facts']['provider_certified'] is False
assert report['execution_facts']['judge_answer']=='SYNTHETIC_PLACEHOLDER'
capture=terminal['child_capture'];output_id=ident(E/'child_output.log')
assert (capture['size_bytes'],capture['sha256'])==(output_id['size_bytes'],output_id['sha256'])
assert capture['limit_exceeded'] is False
assert ident(E/'console_transcript.txt')['sha256']==terminal['transcript_sha256']
assert ident(W/'console.txt')['sha256']==summary['wrapper_terminal']['transcript_sha256']
summary['child_report']=report
summary['capture_and_transcripts_verified']=True

save('AUDIT_FACTS.json',(json.dumps(summary,indent=2)+'\n').encode())
print(json.dumps({'status':'SAVED_EVIDENCE_PRESERVED','evidence_files':len(rows),'saved_pin_records_equal':True,
                  'unique_members':summary['pin_summary']['verified_unique_members']}))
