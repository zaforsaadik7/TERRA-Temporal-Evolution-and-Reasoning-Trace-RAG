"""Read saved evidence only. No runtime imports, database/model or native calls."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
E=R/'reports/authentic_smoke_profile_candidate_20261023_01/evidence'
W=R/'reports/profile_user_b001_freeze_20261023_01/wrapper_evidence'
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
rows=[ident(p) for folder in (E,W) for p in sorted(folder.iterdir()) if p.is_file()]
save('evidence_manifest.json',(json.dumps(rows,indent=2)+'\n').encode())
for name in ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1'):
    live=(R/'scripts/matched_baseline'/name).read_bytes()
    assert live==(R/'reports/profile_user_b001_freeze_20261023_01'/(name+'.final')).read_bytes()
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
 'Structured traceback identifies validate_embedding_function_conflict_on_get; raw exception message intentionally omitted.',
 'No successful retrieval result; Chroma client construction succeeded but get_collection rejected the embedding function binding.'],
 'retry_authorized':False}
save('AUDIT_FACTS.json',(json.dumps(summary,indent=2)+'\n').encode())
print(json.dumps({'status':'SAVED_EVIDENCE_PRESERVED','evidence_files':len(rows),'saved_pin_records_equal':True,
                  'unique_members':summary['pin_summary']['verified_unique_members']}))
