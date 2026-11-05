"""Small independent checks for audit integrity, not scientific-result tests."""
import hashlib,re
from pathlib import PurePosixPath
def require(v,msg):
 if not v:raise ValueError(msg)
def coverage(rows):
 expected={(d,p) for d,n in [('main',25),('TERRA_SUPPLEMENT',21)] for p in range(1,n+1)}
 require(len(rows)==46 and {(x['document'],x['page']) for x in rows}==expected,'page coverage')
 require(all(x['human_reading']=='COMPLETED_BY_CODEX' and x['human_visual']=='COMPLETED_BY_CODEX' and x.get('review_notes') for x in rows),'empty inspection')
def finding(row):
 require(row.get('id') and row.get('artifact_sha256') and row.get('closure_test') and row.get('owner'),'unowned finding')
 if row['status']=='RESOLVED_VERIFIED':require(row.get('closure_evidence'),'unsupported closure')
def pin(path,digest):require(hashlib.sha256(path.read_bytes()).hexdigest()==digest,'stale hash')
def members(names):
 seen=set()
 for name in names:
  p=PurePosixPath(name)
  require(not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name,'unsafe archive name')
  require(str(p).casefold() not in seen,'case collision');seen.add(str(p).casefold())
def destination(page,count):require(isinstance(page,int) and 0<=page<count,'invalid cross PDF target')
def readiness(rec):
 if rec['submission_ready']:require(rec['certification_complete'] and not rec['open_exceptions'] and rec['peer_review_complete'],'false readiness')
