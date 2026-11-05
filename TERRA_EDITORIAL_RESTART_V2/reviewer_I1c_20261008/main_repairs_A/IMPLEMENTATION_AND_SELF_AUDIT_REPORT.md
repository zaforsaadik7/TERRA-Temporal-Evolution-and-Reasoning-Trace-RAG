# I1c-A implementation and bounded self-audit

Authority: user approved I1c-A with “yes”. No I1c-B authority inferred. Codex implemented and audited this batch; this is not an independent peer audit.

## Changes

Only working/src/main.tex changed, in three passages:

1. Corrected graph derivative described as separately versioned and local, public release pending, unused by reported runs. This withdraws the unsupported release claim; it does not claim an exhaustive search of public repositories.
2. Temporal probe identifies databricks-qwen3-next-80b-a3b-instruct and databricks-gpt-oss-120b instead of saying identifiers were absent.
3. CaseFacts Overruled-class diagnostic replaces confidence-interval overlap as a significance rationale with post-hoc exact two-sided McNemar p=0.625 against each baseline, 3 TERRA-only versus 1 baseline-only correct classifications. Explicitly states that this small diagnostic does not establish equivalence.

The eight Overruled query IDs in scratch/casefacts_120_eval_raw.json are CF_INC_012, CF_INC_038, CF_INC_039, CF_INC_043, CF_INC_058, CF_INC_068, CF_INC_103 and CF_INC_102. Correctness compared by query ID and parsed_label against Overruled, for TERRA versus 2_Flat_Vector_RAG and 1_Direct_LLM. Both yield discordance 3:1. Exact calculation: 2*(C(4,0)+C(4,1))/2^4=0.625. Source SHA256: c607d90e3b368dda992efab2dc04665862c59f699c5feb7be29b5c39724e86dd.

Temporal identifiers agree with the previously reviewed 400-row raw-record audit of judge1_evaluation.judge_model and judge2_evaluation.judge_model. No new model evaluation was conducted.

## Preservation and build

Complete 30-file byte-preserved source snapshot: baseline_src/. Incoming PDF preserved as baseline_main.pdf. dependency_hashes.csv records 29 unchanged dependencies and main.tex as the sole changed file. source.diff records the complete three-passage patch. No table, figure, bibliography, frozen macro, dataset, graph or pipeline file edited. No API, model or store execution; no canonical promotion.

- Incoming main SHA256: 1d69b864f774be4492f5c69a58a71960cffff81244fa459e8065557c6b735f14
- Final main SHA256: 56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2
- Incoming PDF SHA256: 080cea09c6d9a4babfac8cefd55f903404b719caa8f25aaea1955957c5d11f91
- Final PDF SHA256: 900bb124e9a1a0a8f21b42f3b15ed6fd22440849e7f3327d0810fa73467ffbeb

Tectonic 0.17.0, only cached dependencies, keep logs/intermediates, build/main.pdf: exit 0, 24 pages (ceiling 25). Compile console retained in build/. No unresolved ?? tokens. Specific log checks found no undefined reference/citation, multiply-defined label or duplicate-destination diagnostics. Existing font-substitution warnings are not undefined references. Overfull boxes remain 2, underfull boxes remain 74.

## Rendered review

Changed extracted page text: 3 and 9–24, reflecting downstream reflow. Rendered pages 3–24 preserved. Contact-sheet visual review covered every changed page; detailed 2200-pixel renders inspected pages 3, 9 and 16 containing all three edited passages. No observed new clipping, overlap, broken float or bibliography collision. This is a bounded batch review, not whole-document high-resolution publication certification. Existing dense/tiny table typography and other previously recorded layout issues are not certified resolved.

## Result and next gate

I1c-A bounded implementation PASS: three approved disclosures corrected, evidence retained, 24 pages. Request Antigravity peer review of source.diff, dependency hashes and rendered PDF. I1c-B supplementary source reconstruction and latency-cell repair remains unimplemented and requires separate approval. No further batch, experiment or promotion follows automatically.
