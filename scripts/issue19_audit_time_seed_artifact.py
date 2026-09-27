"""Issue #19 fresh audit-time production-seed artifact.

This intentionally records a new audit-time run, not historical reconstruction.
The seed rules mirror ask_terra.py's HARD-path exact-title, expansion, and
thinking_traces top-2 retrieval logic. It performs no model calls or writes to
the EEG/Chroma stores.
"""
import hashlib, json, re
from pathlib import Path
import chromadb

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "terra_350_benchmark.json"
EEG = ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json"
CHROMA = ROOT / "dataset_20k_cap" / "vector_db_20k"
OUT = ROOT / "logs"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def main():
    bench=json.loads(BENCH.read_text(encoding="utf-8"))
    eeg=json.loads(EEG.read_text(encoding="utf-8"))
    nodes=eeg["nodes"]
    # Preserve production's benchmark expansion mapping exactly.
    expansion={
      ("separate but equal","desegregation"): ["Plessy v. Ferguson","Brown v. Board of Education"],
      ("1896","1954"): ["Civil Rights Cases","Plessy v. Ferguson","Brown v. Board of Education"],
      ("turning points","civil rights"): ["Civil Rights Cases","Plessy v. Ferguson","Brown v. Board of Education","Heart of Atlanta Motel","Loving v. Virginia"],
      ("voting rights","1927"): ["Nixon v. Herndon","Smith v. Allwright","Terry v. Adams"],
      ("equal protection","1868"): ["Slaughter-House","Plessy v. Ferguson","Brown v. Board of Education","Heart of Atlanta Motel","McLaughlin v. Florida"],
      ("1883","civil rights"): ["Civil Rights Cases","Plessy v. Ferguson","Brown v. Board of Education","Heart of Atlanta Motel"],
      ("slaughterhouse","civil rights"): ["Slaughter-House","Civil Rights Cases","Plessy v. Ferguson","Brown v. Board of Education"],
      ("decade after","1954"): ["Brown v. Board of Education","Cooper v. Aaron","Griffin v. County School Board"],
    }
    client=chromadb.PersistentClient(path=str(CHROMA))
    col=client.get_collection("thinking_traces")
    rows=[]
    for q in bench:
      if q.get("category") != "B_Evolutionary": continue
      text=q["query"]; low=text.lower(); exact=[]; ids=set()
      for n, d in nodes.items():
        title=d.get("title","")
        if title and len(title)>3 and title.lower() in low:
          ids.add(n); exact.append(n)
        elif "slaughter-house" in low and "slaughter-house" in title.lower() and n not in ids:
          ids.add(n); exact.append(n)
      if "slaughter-house" in low and "brown" in low:
        for n,d in nodes.items():
          if "plessy v. ferguson" in d.get("title","").lower() and n not in ids:
            ids.add(n); exact.append(n)
      span=["eighty years","chronological","evolution","over the decades","path of cases","subsequent civil rights litigation","work together to limit","decade after","decade following","years following"]
      if not exact or (len(exact)<=2 and any(x in low for x in span)):
        for kws,titles in expansion.items():
          if all(k in low for k in kws):
            for st in titles:
              for n,d in nodes.items():
                if st.lower() in d.get("title","").lower() and n not in ids:
                  ids.add(n); exact.append(n)
            if exact: break
      vr=col.query(query_texts=[text], n_results=2, where={"category":{"$eq":"civil_rights"}})
      vector=[]
      for m in vr["metadatas"][0]:
        n=m.get("node_id") or m.get("case_id")
        if n not in ids: vector.append(n)
      rows.append({"query_id":q["query_id"],"production_seed_ids":exact+vector,"exact_seed_ids":exact,"vector_seed_ids":vector,"source":"ask_terra.py HARD-path rules; audit-time Chroma query"})
    return rows, {"benchmark_sha256":sha(BENCH),"eeg_sha256":sha(EEG),"chroma_sqlite_sha256":sha(CHROMA/"chroma.sqlite3"),"ask_terra_sha256":sha(ROOT/"ask_terra.py"),"collection":"thinking_traces","collection_count":col.count()}

if __name__=="__main__":
    rows,meta=main(); print(json.dumps({"metadata":meta,"count":len(rows),"rows":rows},ensure_ascii=False))
