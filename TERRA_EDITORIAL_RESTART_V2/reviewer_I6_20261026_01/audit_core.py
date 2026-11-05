"""Pure I6 analysis rules. No provider, database, experiment or model imports."""
import hashlib,json
from fractions import Fraction
LABELS={'SUBSTANTIVE_ANSWER':'full_substantive','MIXED_OR_UNCERTAIN':'partial_or_mixed','PREMISE_REFUTATION':'premise_refutation','EXPLICIT_ABSTENTION':'explicit_abstention'}
def unique(rows,keys):
 seen=set()
 for r in rows:
  k=tuple(r[x] for x in keys)
  if k in seen:raise ValueError('Duplicate analysis unit: '+str(k))
  seen.add(k)
 return seen
def fraction(n,d):
 if not 0<=n<=d:raise ValueError('Invalid numerator/denominator')
 return {'numerator':n,'denominator':d,'fraction':None if d==0 else n/d}
def consensus_status(labels):
 if len(labels)!=2 or any(l not in LABELS for l in labels):raise ValueError('Invalid judge outcome')
 return LABELS[labels[0]] if labels[0]==labels[1] else 'unclassifiable'
def judge_proxy_bounds(labels):
 """Bounds for each judge's SUBSTANTIVE label, not true semantic coverage."""
 if len(labels)!=2 or any(l not in LABELS for l in labels):raise ValueError('Invalid judge outcome')
 return int(all(l=='SUBSTANTIVE_ANSWER' for l in labels)),int(any(l=='SUBSTANTIVE_ANSWER' for l in labels))
def positive_weight(n,N):
 if not 0<n<=N:raise ValueError('Invalid sample size')
 return Fraction(n,N),Fraction(N,n)
def verify_request(raw,expected_sha):
 b=raw.encode('utf-8')
 if hashlib.sha256(b).hexdigest()!=expected_sha:raise ValueError('Request byte identity failed')
 d=json.loads(raw)
 if not isinstance(d.get('messages'),list):raise ValueError('Missing messages')
 user=[m['content'] for m in d['messages'] if m.get('role')=='user']
 if len(user)!=1:raise ValueError('Ambiguous user message')
 body=json.loads(user[0])
 if not isinstance(body.get('evidence'),str) or not isinstance(body.get('query'),str):raise ValueError('Invalid verifier payload')
 return body
def verifier_rates(cases):
 cm={'true_acceptance':0,'false_rejection':0,'false_acceptance':0,'true_rejection':0};unavailable=0
 for c in cases:
  if not c.get('input_verified') or c.get('reference') not in ['sufficient','insufficient'] or c.get('reference_basis') not in ['independent_reference']:
   unavailable+=1;continue
  if type(c.get('passed')) is not bool:raise ValueError('Invalid decision')
  key=('true_acceptance' if c['passed'] else 'false_rejection') if c['reference']=='sufficient' else ('false_acceptance' if c['passed'] else 'true_rejection')
  cm[key]+=1
 ns=cm['true_acceptance']+cm['false_rejection'];ni=cm['true_rejection']+cm['false_acceptance']
 return {'confusion_matrix':cm if ns+ni else None,'false_rejection_rate':fraction(cm['false_rejection'],ns),'false_acceptance_rate':fraction(cm['false_acceptance'],ni),'unavailable_reference_or_input':unavailable,'eligible':ns+ni}
def author_counts(rows):
 valid={'substantive answer','mixed refusal/substantive answer','refusal'}
 if any(r['response_status'] not in valid for r in rows):raise ValueError('Unknown historical author label')
 non=[r for r in rows if r['response_status']!='refusal']
 supported=sum(r['source_correctness']=='supported' for r in non);wrong=sum(r['source_correctness']=='contradicted' for r in non);uncertain=sum(r['source_correctness']=='uncertain' for r in non)
 if supported+wrong+uncertain!=len(non):raise ValueError('Unreconciled non-refusal support labels')
 return {'assigned':len(rows),'non_refusal':fraction(len(non),len(rows)),'supported_answer_proxy':fraction(supported,len(rows)),'contradicted_among_non_refusals':fraction(wrong,len(non)),'uncertain_non_refusals':uncertain,'contradiction_proxy_bounds':[fraction(wrong,len(non)),fraction(wrong+uncertain,len(non))]}
