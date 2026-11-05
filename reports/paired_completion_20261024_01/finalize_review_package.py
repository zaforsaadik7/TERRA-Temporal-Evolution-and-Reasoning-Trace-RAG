import hashlib,json
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
status_path=ROOT/'coordination/terra_antigravity/STATUS.json'
status=json.loads(status_path.read_bytes())
status['state']='STEP3_TECHNICAL_PREPARATION_COMPLETE_PENDING_PEER_REVIEW_AND_LIVE_AUTHORIZATION'
status['latest_codex_message']='codex_to_antigravity/20261024-codex-0306-paired-preparation-complete-for-review.md'
status['current_turn_scope']='Codex-0306: held full native paid bootstrap implemented; 265 named tests PASS; 350 authentic local query measurements and 1400 hypothetical arm/route envelopes PASS; 30561 input files and five root memberships unchanged. Real harmless timeout race reproduced and repaired/qualified. No new APIs, credentials, firewall, embedding inference, paper/statistics or promotion. Proposed $300 cap and $238.917280 conditional token envelope; R02 null approval, actual source held and anchor null. Read-only peer review requested; paid run not authorized.'
write(status_path,status)
rows=[]
for p in sorted(P.rglob('*')):
    if not p.is_file() or p.name=='manifest.json':continue
    rel=p.relative_to(P)
    if any(x in rel.parts for x in ('snapshot','disposable')):continue
    rows.append(dict(path=str(p),size_bytes=p.stat().st_size,sha256=sha(p.read_bytes())))
memo=ROOT/'coordination/terra_antigravity/codex_to_antigravity/20261024-codex-0306-paired-preparation-complete-for-review.md'
rows.append(dict(path=str(memo),size_bytes=memo.stat().st_size,sha256=sha(memo.read_bytes())))
write(P/'manifest.json',dict(scope='Saved review package, excluding verified database copies and later delivery receipt',files=rows))
for row in rows:assert sha(Path(row['path']).read_bytes())==row['sha256']
print('SEALED',len(rows),'files; manifest SHA256',sha((P/'manifest.json').read_bytes()))
