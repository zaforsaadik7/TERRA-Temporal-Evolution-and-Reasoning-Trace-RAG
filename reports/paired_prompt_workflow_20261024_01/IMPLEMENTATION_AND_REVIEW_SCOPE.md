# Paired prompt workflow: synthetic implementation checkpoint

Codex implementation self-verification, 24 October 2026. No network, credentials, real model/tokenizer operations, store queries, scientific results, manuscript edits or promotion.

## Completed component

New paired_prompt_workflow.py composes provider_accounting contracts with concrete R01 prompt builders and strict router/verifier/judge parsers. It calls one shared query-only router, selects supplied prepacked EASY/HARD fixture evidence for both arms, calls a verifier per arm, generates only when sufficient, then evaluates the final answer or abstention with both judges. This is synthetic-only composition over prepacked fixtures, not a real retrieval integration or ready live study runner.

The generator remains plain text. Router output has one EASY/HARD field; verifier has a strict boolean plus nonempty explanation. Judges return normalized support score or null, outcome classification and rationale. Same judge instruction and data field layout for both judges and arms. No reference answers, benchmark categories, query IDs or arm labels enter model prompts. Query ID controls paired execution order and accounting only. Case text is shared through existing format_evidence_item, including explicit procedural-scaffold labeling. Same case ID with unequal retained case information across fixtures is rejected before any call. Selected evidence text/hash and omitted IDs are preserved.

Common proposed evidence ceiling 6,000 synthetic tokens, generator/verifier prompt ceiling 7,000, router ceiling 1,000; provider role config further bounds requests. Token counts in this test runner use only MockBpeTokenizer and are not provider measurements. Caller supplies all four prepacked route/arm fixtures; no real retrieval or authentic packing occurs. For future real execution, original ranked candidates must be preserved directly, rather than inferring interleaved ranking from retained/dropped partitions as this fixture adapter does.

Every request and charged provider response is written to an exclusive bounded pair trace, including content before schema/rubric parsing. The separate accounting journal still reserves/settles before interpreting scores. On failure, trace records failed call and completed response stages, leaves partial evidence and halts further journal dispatch. No retry/resume. Exclusive trace collision stops before calls. A verifier abstention skips generator but retains two judge scores; it is not automatically given a favorable score. Null judge scores produce missing composite/difference with full-denominator sensitivity support via the existing ScoringAnalyzer. Judge outcome disagreement becomes MIXED_OR_UNCERTAIN; agreement is still model-reported classification, not human legal validation.

The established ArmResult/PairedResult schemas are used with an explicit evaluation-only category map (B_Evolutionary -> B and equivalent A/C/D). Fixture timing is unavailable, represented as zero with trace timing_available false; timestamp is an explicit fixture zero, not a real observation. Existing provider accounting, matched harness, serializer and analyzer source bytes remain unchanged.

## Scientific review checkpoint

R01 prompts/rubric are PROPOSED and require review and user acceptance before any live study. They are not a claim to reproduce exact historical prompts. Judge faithfulness concerns supplied-evidence support, including evidence-based justification of abstention; no claim of independent legal correctness. Intermediate normalized scores are allowed; null means unassessable, not zero or API failure. Refusal scoring is consequential and must be accepted before freeze, not chosen after results. The prompt digest covers fixed system texts/version; full source identity additionally binds message layout, parsers and outcome rules. The seed-based hashed query-ID arm ordering is prospective and repeatable, not the historical ordering.

Provider availability, rates, accepted response identities, exact output/reasoning controls, independent real judge families, rate scheduling, complete study-level persistence and actual transport remain unresolved. No live_admitted switch opened; run_live_pair unconditionally raises. No historic offline gates changed.

## Validation

Final named command: venv/Scripts/python.exe -B -m unittest tests.test_paired_prompt_workflow_synthetic tests.test_provider_accounting_synthetic tests.test_matched_baseline_synthetic

97 tests in 0.776 seconds: all PASS, no skips/errors/failures. Includes 25 new workflow tests, 31 provider-accounting tests and 41 prior matched baseline tests. Earlier iterations passed at 91 and 95 tests before information-parity, budget and analysis assertions were completed. Fixtures use synthetic case text/HTTP envelopes, synthetic.invalid endpoint descriptors, temporary traces and journals. No broad discovery.

Meaningful cases include nine-call paired success, one shared router, equal prompt bytes for identical evidence, no arm/gold leakage, abstention eight-call path with both judges, null scores and sensitivity bounds, malformed output after charging, timeout failure distinct from refusal, full/partial evidence preservation, exact serving identity parity, changed case content rejection, exclusive collisions, role/token limits and deterministic arm order. Analysis bridge checks retain omitted-query denominators.

Next: peer-review R01 prompts and this source, then implement separately held provider transport and full paired-run persistence/rate controls. No API key needed for that code-only preparation.
