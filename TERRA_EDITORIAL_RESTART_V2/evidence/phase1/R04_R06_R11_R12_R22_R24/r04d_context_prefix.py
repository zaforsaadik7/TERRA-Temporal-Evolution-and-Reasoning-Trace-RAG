"""R04d: in canonical contexts, count trace blocks that are a (possibly truncated) prefix of the single masked template."""
import json,re
T="Step 1: Identify operative legal and constitutional question under <CAT> jurisprudence. Step 2: Scrutinize governing Supreme Court precedent, historical canons, and statutory text. Step 3: Evaluate factual record under binding standards of appellate review. Step 4: Harmonize conflicting doctrines, distinguish non-controlling authority, and resolve claims. Step 5: Pronounce holding, enter judgment, and transmit mandate."
d=json.load(open("/mnt/user-data/uploads/TERRA -Copy/scratch/canonical_v2/terra_canonical_v2_eval.json"))
tot=pref=0; other=[]
for r in d:
    for m in re.finditer(r"Thinking Trace\s*[—-]\s*(.+?)\s*\((\d{4})\)\s*:\s*(.*?)(?=\n|$)",r['context_full']):
        b=re.sub(r'under .+? jurisprudence','under <CAT> jurisprudence',m.group(3)).strip().rstrip('.').rstrip()
        b=b[:-3] if b.endswith('...') else b
        tot+=1
        if T.startswith(b.rstrip('.')) or b.startswith(T[:60]): pref+=1
        else: other.append(b[:150])
print("trace blocks in contexts:",tot,"template-prefix:",pref,"other:",len(other)); print(other[:5])
