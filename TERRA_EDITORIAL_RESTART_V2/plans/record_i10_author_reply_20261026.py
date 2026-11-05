from pathlib import Path
import json,hashlib
R=Path('F:/TERRA -Copy');T=R/'TERRA_EDITORIAL_RESTART_V2';P=T/'reviewer_I10_20261026_01';D=P/'author_reply_20261026_01'
assert not D.exists();D.mkdir()
def put(n,v):(D/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
reply={'1':'yes','2':"we are the main authors, there will some people added later. Md. Emam Zafor Saadik 1st author and Muhammad Raihan Molla 2nd author. we are students bubt. again there will be some other people added to this paper, who has advised us or giving us the funding. we don't have information about them for now.",'3':'donno','4':'no idea what are you talking about','5':'mostly yes but give me a description of what you are talking about here later'}
put('USER_REPLY.json',{'date':'2026-10-26','source':'Direct human answer to asynchronous I10author questions','answers':reply})
facts={'target_journal':{'value':'Artificial Intelligence and Law','status':'CONFIRMED_BY_LEAD_AUTHOR'},'known_author_order':[{'position':1,'name':'Md. Emam Zafor Saadik','role':'student','institution_reported':'BUBT'},{'position':2,'name':'Muhammad Raihan Molla','role':'student','institution_reported':'BUBT'}],'second_author_name_correction':{'prior_manuscript':'Md. Raihan Molla','confirmed':'Muhammad Raihan Molla','active_manuscript_edited':False},'full_author_list':{'status':'INCOMPLETE','reason':'User anticipates additional advisers/funders; names and contributions not yet available','automatic_authorship':False},'corresponding_author':None,'funding_and_conflicts':'UNKNOWN','prior_preprint_publication_concurrent_submission':'UNKNOWN','ethics_and_consent_determination':'UNEXPLAINED_TO_AUTHOR_NOT_A_NEGATIVE_ATTESTATION','contribution_and_AI_disclosure_approval':'PROVISIONAL_MOSTLY_YES_EXPLANATION_REQUESTED_NOT_FINAL_ALL_AUTHOR_APPROVAL','sharing_arrangement':'UNCONFIRMED','article_type':'UNCONFIRMED','working_manuscript_changed':False,'I10_complete':False,'status':'PREPARATION_COMPLETE_BLOCKED'}
put('CONFIRMED_AND_PENDING.json',facts)
note='''# Author response update

26October2026. Artificial Intelligence and Law is confirmed by the lead author as the intended journal. Known first author: **Md. Emam Zafor Saadik**. Known second author: **Muhammad Raihan Molla**, correcting the prior manuscript spelling. Both are reported BUBTstudents. Additional proposed authors are not yet identified; full authorship/corresponding contact remain pending. No automatic addition for advice/funding and no affiliation beyond that supplied is invented.

Funding, interests and publication/submission history remain unknown. The ethics question was not understood; no approval, exemption or consent attestation follows. “Mostly yes” is provisional, not final contribution/disclosure approval for all current/futureauthors. The requested explanation is supplied below; no working manuscript or anonymous candidate change is needed for this private update. The original300-entry implementation package manifest remains preserved; this dated addendum has its own manifest.

## Plain-language explanation for the authors

**Ethics/consent:** Did a university or research committee review the assessment exercise, or tell you review was unnecessary? Did the two assessors agree that their ratings and descriptions of their work could be used in the paper? These are separate questions. If neither was discussed, report that fact; do not claim an exemption or formal approval. This is not a request to obtain legal experts.

**Contributions:** Who actually designed the research, built the software, ran experiments, analysed results, did the assessments and wrote/revised the paper? Advice/funding are recorded accurately; neither alone automatically qualifies someone as an author. Final author roles/approval must be agreed with the actual people before submission.

**AI-use description:** Proposed account says Author1read opinions and drafted assessments before using AI to find/interpret/check/rewrite; Author2reviewed and amended AI-proposed ratings/rationales, read opinions, and later participated in unblinded reconciliation. AIalso supported project code, audits and substantive manuscript work. Confirm what is accurate and correct anything inaccurate. The method does not claim independent expert legal validation.

**Sharing:** Which code, benchmark questions, results and supporting files may reviewers access, and how? Public release, anonymous review access and private assessments are different choices. No data will be uploaded or originals shared without the required decision and rights/privacy review.

**Funding/conflicts:** Identify who supplied money or computing/APIcredits and any related financial/nonfinancial interest, if known. Unknown is not the same as none.

Remaining I10gates: full author/contact/declaration facts, rights/access arrangement, confirmed final disclosure, currentjournalstyle/keyword/placement issues and actual outputpeerreview. Journal selection alone does not resolve I9formatting or imply permission to restart Springerconversion.
'''
(D/'AUTHOR_EXPLANATION_AND_UPDATE.md').write_text(note,encoding='utf-8')
put('MANIFEST.json',{'files':[{'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(D.iterdir()) if f.is_file()]})
st=R/'coordination/terra_antigravity/STATUS.json';s=json.loads(st.read_text(encoding='utf-8-sig'));(D/'STATUS_before_update.json').write_bytes(st.read_bytes());s['i10_author_reply']=(D/'CONFIRMED_AND_PENDING.json').relative_to(R).as_posix();s['i10_state']='PREPARATION_COMPLETE_BLOCKED';s['latest_codex_message']='codex_to_antigravity/20261026-codex-0340-i10-author-facts-and-pending-declarations.md';s['current_turn_scope']='I10direct authorreply recorded: targetAIandLawconfirmed; Md.EmamZaforSaadik first/MuhammadRaihanMolla second, bothBUBTstudents; additionalauthors/contact unknown. Funding/conflicts/prior/concurrent unknown; ethicsnotunderstood; AI/contributionapprovalprovisional. Datedaddendum preserves originalpackage/workingbytes; no adviser/funderautomaticauthorship, no exemption/finalconsent/sharing inferred. I10stillblocked; roadmap9/1/3.';st.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('I10 author answers recorded; no manuscript changes; outstanding facts remain explicit.')
