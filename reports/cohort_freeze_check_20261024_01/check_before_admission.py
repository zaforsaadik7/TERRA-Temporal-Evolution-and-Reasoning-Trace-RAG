"""Approved closing filesystem check. No imports of project/native/model code.

Writes fresh evidence only. Does not admit source, copy stores or launch a child.
Two future source flags are checked against their HELD bytes; all other pins must
already match the exact approved decision. Any difference stops without repair.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT=Path('F:/TERRA -Copy');OUT=Path(__file__).resolve().parent
DECISION=ROOT/'reports/cohort_decision_20261024_r02'
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True)
def guard(path):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts:raise ValueError('Absolute reviewed path required')
    for current in (path,*path.parents):
        info=current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Reparse inventory path rejected')
    return path
def identity(path):
    path=guard(path);before=path.stat();total=0;digest=hashlib.sha256()
    if not stat.S_ISREG(before.st_mode):raise ValueError('Ordinary inventory file required')
    with path.open('rb') as f:
        opened=os.fstat(f.fileno())
        if (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns)!=(
                before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns):
            raise ValueError('File changed before open')
        for block in iter(lambda:f.read(1024**2),b''):total+=len(block);digest.update(block)
        after=os.fstat(f.fileno())
    final=path.stat();attrs=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if (total!=before.st_size or any(getattr(before,k)!=getattr(final,k) for k in attrs)
            or any(getattr(opened,k)!=getattr(after,k) for k in attrs)):
        raise ValueError('Inventory changed while hashing')
    return dict(path=str(path),size_bytes=total,sha256=digest.hexdigest())
def members(root,excluded=()):
    root=guard(root);found=[];pending=[root]
    while pending:
        directory=pending.pop()
        for path in directory.iterdir():
            guard(path);info=path.lstat()
            if path.parent==root and path.name in excluded:continue
            if stat.S_ISDIR(info.st_mode):pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink!=1:raise ValueError('Hardlink in complete root')
                found.append(path.relative_to(root).as_posix())
            else:raise ValueError('Unexpected member kind')
            if len(found)>100000:raise ValueError('Traversal ceiling')
    return sorted(found)
result=dict(status='STOP',stage='USER_APPROVED_CLOSING_IDENTITY_CHECK',
    started_utc=datetime.now(timezone.utc).isoformat(),source_admission_changed=False,
    actual_attempt_started=False,model_or_job_firewall_operation=False)
try:
    for path,expected in ((ROOT/'reports/cohort_native_integration_20261024_01/regression_r04/manifest.json',
            '956f1deaca485346688fd919f03e2a78ad31b2d3609dbb4ce77e091102e9a14d'),
            (DECISION/'manifest.json','c156517e564a538db9fd708ee3aa26cc47b9a8dc93b2c6fb4b2a42fe177947c2')):
        if identity(path)['sha256']!=expected:raise ValueError('Reviewed manifest identity mismatch')
        manifest=json.loads(path.read_bytes())
        for row in manifest.get('files',[])+([manifest['helper']] if 'helper' in manifest else []):
            if identity(row['path'])!=row:raise ValueError('Reviewed artifact identity mismatch')
    packet_path=DECISION/'execution_packet.UNAPPROVED.json'
    if identity(packet_path)['sha256']!='343b88b51d0c550e547e4336a7129ce4af3af6a972ba377d22b765d9de5cf477':
        raise ValueError('Approved packet identity mismatch')
    packet=json.loads(packet_path.read_bytes());launch=packet['body']['launch'];review=launch['parent']
    special={str(ROOT/'scripts/matched_baseline'/name).casefold():identity(DECISION/(name+'.held'))
        for name in ('offline_cohort_entry.py','offline_cohort_production.py')}
    observations=[]
    for i,pin in enumerate(review['pins'],1):
        row=identity(pin['path']);expected=dict(special.get(pin['path'].casefold(),pin));expected['path']=pin['path']
        if row!=expected:raise ValueError('Closing selected file differs: '+pin['path'])
        observations.append(row)
        if i%5000==0:print('Closing identities verified',i,flush=True)
    for name in ('offline_cohort_anchor.py','launch_offline_cohort_user.ps1'):
        if identity(ROOT/'scripts/matched_baseline'/name)['sha256']!=identity(DECISION/(name+'.held'))['sha256']:
            raise ValueError('External trust-root file no longer HELD')
    for declaration in review['roots']:
        if members(declaration['root'])!=declaration['members']:raise ValueError('Complete-root membership drift')
    roles=dict(launch['artifacts']);base=Path(roles['firewall_image']['path']).parent
    for root,external,excluded in ((ROOT/'scripts/matched_baseline',
            ('offline_cohort_anchor.py','launch_offline_cohort_user.ps1'),()),(base/'Lib',(),('site-packages',))):
        expected=set(external)
        for pin in review['pins']:
            try:relative=Path(pin['path']).relative_to(root).as_posix()
            except ValueError:continue
            if excluded and relative.split('/')[0] in excluded:raise ValueError('Global site packages unexpectedly selected')
            expected.add(relative)
        if set(members(root,excluded))!=expected:raise ValueError('Dependency namespace membership drift')
    expected={Path(pin['path']).name for pin in review['pins'] if Path(pin['path']).parent==base}
    actual=set()
    for path in guard(base).iterdir():
        guard(path)
        if path.is_file():actual.add(path.name)
    if expected!=actual:raise ValueError('Base runtime root file drift')
    for name in ('controller_image','child_image'):
        cfg=Path(roles[name]['path']).parent.parent/'pyvenv.cfg'
        values={line.split('=',1)[0].strip().lower():line.split('=',1)[1].strip().lower()
                for line in cfg.read_text().splitlines() if '=' in line}
        if values.get('include-system-site-packages')!='false':raise ValueError('Global sites not disabled')
    for target in (ROOT/'reports'/launch['run_id'],ROOT/'reports/cohort_controlled_freeze_20261024_01'):
        if target.exists():raise ValueError('New attempt/freeze directory collision')
    save('observations.json',observations)
    result.update(status='PASS',selected_files=len(observations),complete_roots=len(review['roots']),
                  namespace_checks='PROJECT_STDLIB_BASE_ROOT_PASS')
except Exception as exc:
    result['failure_type']=type(exc).__name__;result['failure']=str(exc);raise
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat();save('RESULT.json',result)
print(json.dumps(result),flush=True)
