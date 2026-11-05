# claude-0068 - peer review of Codex-0030 reviewer-integrated plan
Claude, 2026-10-08. Claude-only, not independent (I authored Batches 1-28 text and audited Batch 1). Read-only; nothing executed or edited. The plan authorizes nothing; the user's approval does.

## Overall
The plan is sound and honest. Agree with: contradictions before edits; one bounded batch at a time; new experiments (I4/I5) only on separate approval; expert evaluation never requested, point 5 reported as partly unfulfilled; original-graph attribution of historical results; no "released" claim without verification. I recommend I1a first, as Codex does.

## Evidence I reproduced for I1a (distance calibration)
Frozen `generated_stats.tex` (build/src) gives in-domain false-refusal counts (N = 200): tau 0.90 = 9/200, 1.00 = 2/200, 1.10 = 1/200, 1.20 = 1/200, 1.25 = 0/200. Main line 210 reports in-domain distance mean 0.365, SD 0.082, max 0.509. With max 0.509, a threshold of 0.90 cannot reject any in-domain query, so 9/200 (and 1/200 up to tau 1.20) cannot come from the same distance and population. Counts are monotone in tau (consistent internally), so the table is self-consistent; the conflict is between the table and the 0.365/0.509 summary. The out-of-domain TPR at 1.30 is 41/75 = 54.67%, also tied to the calibration run. So I1a's premise is right: they are different statistics, populations or distance definitions until query-level records show otherwise. I did not locate the query-level calibration records and make no claim about which side is right.

## Disagreements and additions
1. **I1b (66 vs 62).** I have not reproduced either number; the plan correctly refuses to assume one. Add: record whether 66/100/100 and 62 use the same gold node set (342 landmarks) and the same matching rule (Node ID vs title), since main uses dual-resolution recall.
2. **I1c scope.** Add my open findings explicitly so they are not lost: Supplement Table X net route macros (5,457 / 14,071; 14,071 exceeds the 14,067.48 ms gross route median) and its gross route rows equal to Category A/B medians; stale "no retrieval" caption in that table; router-table 42/31 note; main line 555 interval-overlap rationale (exact McNemar 3 vs 1, p = 0.625, labelled post hoc, n = 8); line 344 temporal "does not record judge identifiers" (every record has judge_model).
3. **I2/I10 release wording.** Main still says the corrected graph "is released in the replication bundle" (my Batch 28 wording). Make narrowing it to "local separately versioned derivative, release pending" an explicit small batch before any submission file is built; it is cheap and does not depend on I1.
4. **I4 matched baseline.** Endpoint and parity design is reasonable. Two cautions: (a) the existing 5 Category D queries / 19 OVERRULES-Category D queries over 9 edges make any subgroup claim there underpowered; pre-specify that Category D is descriptive. (b) User declined new runs on 2026-10-06; I4 correctly stops before running, but the plan should state that point 3 stays unresolved if the user keeps that decision, and the cover response should say so rather than imply a pending fix.
5. **I6 source-check sample by author or AI.** Acceptable only as labelled "nonexpert source-consistency check". I would add: the same Llama 3.3 70B family that generates and grades must not also be the checker, and the sample's sampling frame and seed be fixed before looking at outputs. The checker should be the author reading source text; AI may only locate passages.
6. **I9 page limit.** Agree not to force illegibility. A measured venue-page conversion is needed before any more compression; do not assume 24 IEEE pages fit 25 Springer pages.
7. **I3 title.** The example title direction is fine as a proposal; I would keep "evidence checking" qualified by "LLM-prompted", since the entailment grader is not independently validated.
8. **Process.** Peer review of I1-I2 evidence batches should check scripts against raw data, not only the report; a Claude audit remains not independent for anything involving my earlier edits, and Codex should keep saying so.

## Not verified
I did not read the 10 supplement objects, the reviewer's original letter, journal guidelines (Codex cites them; I did not fetch), or any calibration query records. I did not check the I12/I10 claims about the journal.

## Recommendation
Approve I0 + I1a only (read-only, evidence-first), plus the small release-wording patch if the user wants it. Do not authorize I4/I5 unless the user reverses the no-new-runs decision.
