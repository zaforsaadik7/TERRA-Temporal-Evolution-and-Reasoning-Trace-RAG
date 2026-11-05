# Codex subagent source reviews and repair record

24 October 2026. Separate Codex subagents performed read-only source reviews. They did not edit files, execute tests, inspect credentials, use network/models or review authentic input data. These are additional Codex code reviews, not an Antigravity acknowledgment or independent external scientific audit. Test execution and repairs are the implementation lead's self-verification.

## Review 1: existing accounting/workflow/run-control components

Planck found four concrete issues:

1. Settlement fsync failure could cause a duplicate sequence append. Repaired by a permanent persistence-failed latch prohibiting further journal writes, preserving the ambiguous tail. Session-level settlement-fsync regression added; in-flight exposure remains unresolved and no resume is authorized.
2. Skeletal result dictionaries could satisfy run completion. Repaired with full ArmResult/PairedResult schema validation and linkage to workflow/HTTP request-response evidence. Missing answers, scores or unbound result content cannot issue completion.
3. A long completed-ID list could exceed terminal reserve. Repaired with bounded count/digest summaries, tested with 350 maximum-length IDs.
4. Equal-token retained text mutation could reuse an unrelated prompt hash. Repaired by checking reconstructed evidence bytes inside the serializer-produced prompt as well as the stored prompt hash, with a same-token-length substitution regression. Authentic source identity still requires its separately reviewed input receipt; these tests do not certify real data provenance.

## Review 2: integrated runner

Schrodinger confirmed the journal latch and earlier manifest-before-terminal changes, then identified:

1. A terminal fsync failure could leave a success-shaped committed marker. Repaired using separate exclusive success/failure pending files, fsync before publish and rename only afterward. Injected success-terminal fsync failure preserves the pending artifact and commits FAIL, never authoritative SYNTHETIC_COMPLETE. Directory durability across sudden power loss is not universally proven.
2. Windows reserved names, control names and case aliases could collide. Repaired by validating the entire query filename namespace before creating the run root; regressions cover terminal, artifact_manifest, device names and case-only duplicates.
3. Final aggregate accounting omitted terminal space after the manifest. Repaired by reserving manifest bytes plus an additional 4 KiB terminal allowance before either success publish step.
4. Result token/evidence/category/order fields could be consistently modified in the final trace. Repaired by deriving/checking these fields from earlier query contract, EVIDENCE and REQUEST records, with coordinated mutation regressions.

## Review 3: request binding

Pasteur found that earlier workflow requests/local token counts were not yet bound to persisted HTTP request bytes. Repaired by verifying request SHA256, exact message equality, recomputing synthetic rendered token counts, checking prompt-contract identity and reconstructing generator/verifier/judge messages from the actual query, common evidence and candidate answer. Added a coordinated trace-token/result mutation regression.

Pasteur's follow-up verdict: bounded concurrence, no new concrete blocker identified in the request-binding repair. It did not independently run tests or inspect the subsequent counter-based aggregate performance refinement. The 148-test result remains parent self-verification. See FINAL_CODEX_SUBAGENT_VERDICT.md; no Antigravity availability or verdict is assumed.

## Test execution scope

Final combined named suite: 148 PASS, 24.960 seconds, no errors/failures/skips. Full synthetic 350-query/3,150-call composition uses static HTTP responses and stubs os.fsync while asserting barrier invocations; it does not prove 3,150 real durable physical provider transactions. Smaller runs use ordinary filesystem barriers and explicit injected fsync/manifest/terminal failures. No real sockets, TLS factory, keys, stores, authentic tokenizers or benchmark queries were used.

Three earlier in-progress synthetic suite runs were deliberately stopped while source-review fixes and scan-performance changes were being integrated. No outcome from those interrupted runs is counted as PASS. They were synthetic test processes, not additional offline diagnostic attempts. A read-only CIM process-inventory query was denied by the environment; no matching process was killed through inventory. Test cancellation used the owned tool session. Final tests were started after the stopped sessions exited.
