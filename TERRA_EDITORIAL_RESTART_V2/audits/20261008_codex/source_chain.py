from pathlib import Path
import hashlib,re,json
R=Path('F:/TERRA -Copy'); A=Path(__file__).parent; B=R/'TERRA_EDITORIAL_RESTART_V2/phase3'
state=(B/'batch02/applied/snapshot_pre/main.tex').read_bytes()
rows=[]
for i in range(2,14):
    b=B/f'batch{i:02}'
    dp=b/'rev1/batch02_rev1.diff' if i==2 else b/'applied/apply_diff.diff'
    lines=dp.read_text(encoding='utf8').splitlines()
    start=next(k for k,l in enumerate(lines) if l.startswith('--- ') and l.endswith('main.tex'))
    stop=next((k for k in range(start+1,len(lines)) if lines[k].startswith('--- ')),len(lines))
    patch=lines[start+2:stop]; old=state.decode('utf8').splitlines(); new=[]; pos=0; k=0
    try:
        while k<len(patch):
            m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',patch[k])
            if not m: k+=1;continue
            at=int(m[1])-1;new.extend(old[pos:at]);pos=at;k+=1
            while k<len(patch) and not patch[k].startswith('@@ '):
                l=patch[k];k+=1
                if not l or l.startswith('\\'):continue
                if l[0] in ' -':
                    if pos>=len(old) or old[pos]!=l[1:]:raise ValueError(f'context mismatch at original line {pos+1}')
                    pos+=1
                if l[0] in ' +':new.append(l[1:])
        new.extend(old[pos:]);nl='\r\n' if b'\r\n' in state else '\n';state=(nl.join(new)+nl).encode('utf8')
        sha=hashlib.sha256(state).hexdigest()
        mf=next(b.rglob('EXPECTED_POST_HASHES.sha256'))
        expected=next(l.split()[0] for l in mf.read_text().splitlines() if l.rstrip().endswith('main.tex'))
        rows.append({'batch':i,'replayed_main_sha256':sha,'expected':expected,'match':sha==expected})
        (A/f'replayed_batch{i:02}_main.tex').write_bytes(state)
        if i==2:
            actual=(B/'batch03/applied/snapshot_pre/main.tex').read_bytes()
            rows[-1]['surviving_post_snapshot_sha256']=hashlib.sha256(actual).hexdigest()
            rows[-1]['newline_normalized_match']=state.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n')
            state=actual
    except Exception as e:
        rows.append({'batch':i,'error':str(e)});break
(A/'source_chain.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print(json.dumps(rows,indent=2))
