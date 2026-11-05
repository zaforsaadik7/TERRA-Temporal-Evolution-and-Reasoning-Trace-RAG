# Claude post-run audit of the authorized diagnostic run (claude-0097)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static read of saved evidence plus arithmetic recomputation from the saved ledger. I did not run the runbook, wrapper, diagnostic or any test, did not query the firewall or processes, and did not open any Chroma store. I have not seen the user's screenshots; I audited the saved files. I did not re-hash the large store files; I rely on the run's own recorded hashes where noted. Coordination is user-relayed.

## 1. Evidence read (my SHA-256)

| File | SHA-256 |
| --- | --- |
| runbook_20261008T050457Z_11984_b20d5802/runbook_console_transcript.txt (7,434 B) | d711e037ad97d2be12802f89ee2fbb2522196ccde32fb48ec8e173251275cb03 |
| .../runbook_pre_execution_record.json (4,942 B) | aba0e69de5bbbdc74004f7292bacce73971e65bf0e720f3ceb2964beecd6568a |
| .../runbook_terminal_record.json (7,895 B) | b270d75aeb94bb5dc413bd3e0d29f23eac258e01437867a9990e1270e46e60cf |
| addendum_01/runs/harness_run_1791435903_11152_5c6ba953/console_output.log | 439ee89c9caa7f618794fd9eb7e3f7844f7319d04d11e6720eb5ebca3e9d81b0 |
| .../execution_metadata.json | 6cc48cc16bfc476bd9e5e0dd1ec841f07e6260aa15107ca10cd6252de1866f00 |
| .../exit_code.txt (value 0) | 13bf7b3039c63bf5a50491fa3cfd8eb4e699d1ba1436315aef9cbe5711530354 |
| addendum_01/runs/run_1791435903_17576_69cd01c5/contemporary_distance_diagnostic_...json (135,236 B) | 2b6a9b556cf6183c985ec44444bd5c22093aacde80256f6fba551e982a88e9a9 |
| addendum_01/runs/.single_run_lock | 9be42d57018a7d6d716d63ea93c978b6e822c309e2b26e2a046345eb056c466d |
| pre_run_snapshot_20k/budget_and_gate_summary.json (saved summary) | b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f |
| execution_package/runbook_operational_metadata_correction.json | b4d45a32ea983d98648a7fa87e969226edb4411e53de45f36643505a692ced29 |

The report hash and the console-log hash equal the values recorded inside execution_metadata.json. The saved summary hash equals the pinned b5c49847.

## 2. Runbook record: consistent and complete

- One production run, ID 20261008T050457Z_11984_b20d5802, Windows PowerShell 5.1.19041.7725 Desktop, exact reviewed command line, parameterless, elevation passed (the earlier attempt 042842Z in its own folder is unchanged).
- Steps 1-7 all PASS in the transcript. Pre-execution record exists (INITIALIZED, six pre-hashes equal expected), then terminal record: SUCCESS, rule_created_by_this_run true, rule facts Name/DisplayName TERRA_Offline_Diagnostic_20261008, Outbound, Block, Enabled, Profile Any, Program = pinned python.exe; native exit 0 (05:05:00 to 05:05:26 UTC); teardown_verified true; six post-hashes equal expected; transcript closed cleanly; errors empty.
- The "TerminatingError(Get-NetFirewallRule) ... No MSFT_NetFirewallRule objects found" lines appear twice in the transcript (collision check and removal check). They are the designed ObjectNotFound probe; the PASS lines follow. They are noise to a reader, not failures.
- Zero other known processes using the pinned interpreter; 16 processes could not be inspected (recorded uncertainty in pre and terminal records, as the runbook is designed). That means the concurrency check was not exhaustive, not that it failed.
- The pre-execution record's transcript_closed_cleanly false is expected at that point in the run.
- Rule effectiveness remains unprovable: the record shows the rule existed and was verified, not that it blocked anything. The wrapper's own caveat says so.

## 3. Wrapper and diagnostic: consistent

- exit_code.txt = 0; metadata success true, wrapper 0, child 0, failure_reasons empty, elapsed 21.97 s.
- Pinned facts: interpreter 3adbbf2a..., diagnostic c37ddaa7..., chromadb 1.5.9, numpy 2.5.1, onnxruntime 1.27.0; ONNX cache six files with hashes recorded and post-run match.
- Benchmark validation: 350 unique IDs (A100/B100/C75/D75); legacy 40 unique identifiers (all source field id, matching the earlier finding that Benchmark 175 uses id).
- Post-run invariants: all_invariants_passed true; all 11 vector-store files and the snapshot assets, diagnostic, interpreter and ONNX files recorded as matching. The single-run lock exists, so a second wrapper run would be refused.
- Diagnostic JSON: status SUCCESS, no errors, 10 stages, all six integrity checks true, space l2, collection thinking_traces dimension 384, schema not migrated, WAL/SHM absent, historical script hash ad6f26e8... equals reference. The report records Python 3.14.5, which resolves the earlier "peer-reported" version item.
- Disposable snapshot: analysis copy stayed at scratch/diagnostics/run_1791435903_17576_69cd01c5/vector_db_20k. It is still on disk; keep or remove is the user's decision.

## 4. Independent recomputation from the per-query ledger (my arithmetic)

From the 350-row ledger I recomputed: 350 unique IDs with category counts 100/100/75/75; all anomaly flags "none"; all distances finite; sqrt column squares back to raw within 2.2e-16. With in-domain = A+B (200) and out-of-domain = C (75), AUROC = 0.9901333333333333, identical to the diagnostic and the saved summary. The eight-threshold grid recomputed by me (false positives among in-domain; true positives among OOD) is identical to both the diagnostic grid and the saved summary: tau 0.90 9/72; 1.00 2/62; 1.10 1/54; 1.20 1/47; 1.25 0/44; 1.30 0/41; 1.35 0/35; 1.40 0/32. At tau 1.30 that is 0/200 and 41/75 = 54.67%, as Table XII Panel B and main line 210 state. Ties do not matter here (">" and ">=" give identical counts).

I also verified the legacy sample (40 rows): sample_in_20 mean 0.716, sample_out_20 mean 1.005 (raw squared).

## 5. What the result does and does not establish

Establishes (contemporary only): the current store, current model weights and current libraries reproduce the saved AUROC and the whole threshold grid exactly, and the Table XII counts and the 0/200 and 41/75 statements at tau 1.30 are reproducible now. The run left the protected files unchanged according to the recorded hashes.

Does NOT establish:
1. **Historical provenance.** The diagnostic and wrapper both say so. A contemporary match cannot show how the historical numbers were produced.
2. **Why the saved summary matches.** Exact concordance is what one expects if the saved summary came from this same data and model; it is reassuring about determinism, not independent confirmation.
3. **That the line 210 descriptive statistics are right. They are not reproduced.** Main line 210 says in-domain distances have "mean 0.365±0.082, max 0.509". The contemporary in-domain (A+B, n=200) raw squared distances have mean 0.712, SD 0.122, max 1.244 (Euclidean sqrt: mean 0.841, SD 0.073, max 1.115). Per category: A 0.690/0.152/1.244, B 0.734/0.076/0.890. I also tried halving (cosine-style): mean 0.356, SD 0.061, max 0.622, and the legacy 20-in sample (0.716/0.196/1.131). None gives 0.365/0.082/0.509. So the grid and the 0/200, 41/75 counts agree with the paper, but the descriptive statistics in the same sentence do not match anything the diagnostic computed. The sentence's numbers remain unexplained; they should not be left as is, but no replacement is authorized and I make no manuscript edit. This is the real finding of the run for I1a, and it is more specific than "historical calibration is open". I did not search the generating scripts/macros for the origin of 0.365/0.082/0.509 in this round.
4. **Offline enforcement.** The declared label, in-process guards, negative control and rule verification are layers of evidence; none proves the firewall blocked traffic, and the 16 uninspected processes are recorded uncertainty.
5. Equivalence of dataset_20k_cap to the historical environment (see item 1).

## 6. Minor notes (not blockers)

- Record field naming (`actual_*`, `teardown_attempted`) still means "attempted"; here the verified facts agree.
- Stage 10 and Final Stage print no PASS line in the console; their results are in the report's integrity_checks (all true).
- Addendum fcb4d2a8 is still the original; the size correction is the separate metadata-correction file (b4d45a32). I read the correction and it agrees with the 38,481 / 30,160 bytes I reported.
- The user's screenshots are consistent with the saved files as far as the user described them; I did not view them.

## 7. Verdict

The authorized single run is a clean, internally consistent SUCCESS at the recorded level. Evidence supports: exact contemporary concordance with the saved grid (independently recomputed), unchanged protected files per recorded hashes, rule created and removed with verification. Calibration of line 210 stays OPEN: its grid claims reproduce, its mean/SD/max do not, and provenance is unestablished. Nothing here authorizes a manuscript change.

## 8. Boundaries

No rerun (the lock forbids it and the user said not to), no 10k run, no API call, no threshold change, no manuscript edit. Whether and how to correct the line 210 statistics (use the contemporary numbers with a disclosed provenance, narrow the sentence, or locate the old figure's source) is a decision for the user and the coordinating agents. Relaying this to Codex or Antigravity is the user's.
