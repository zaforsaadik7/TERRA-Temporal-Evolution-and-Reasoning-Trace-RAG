# Approved I1c offline evidence export — completion report

Codex, 8 October 2026. User approved the evidence export and then said “okay then start with it”. Scope: saved JSON arithmetic only, no manuscript adoption. One invocation completed, exit 0; no retry.

## Pinned execution

Interpreter: `C:/Users/zafor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Command: `scripts/verify_i1c_route_latency.py --input [workspace]/data/terra_canonical_v2_eval.json --output-dir [workspace]/TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01 --expected-hash 95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`. All paths were supplied absolutely. Console and real child exit code retained in `export_execution_01/`. Version metadata retained in exported summary.

Checker before/after SHA256: `8c54d533c01f88b12820c8e33d580ce27cc2b84c7f2b0471481bcb07d5981fee`. Input before/after and recorded final hashes all match the pinned canonical hash above. No API/model/vector-store/firewall operation occurred.

## Output verification

Read all 350 CSV rows and checked each ID, category, route, gross, sleep and net against canonical input. All 350 IDs unique; no mismatches. Independently calculated all 126 raw summary fields across 14 cohorts using standard-library statistics and explicit linear percentile interpolation rather than calling the exported checker functions. All agree (comparison tolerance rel=1e-12, abs=1e-8). Manifest hashes agree. Completion JSON is valid, reports SUCCESS, and all three source hashes match the measured input hash.

Route medians, milliseconds: EASY N=110 gross/net 5464.955; HARD N=240 gross/net 14067.480. Category gross medians: A 5828.080, B 17938.505, C 2212.530, D 10144.640. Overall N=350: gross 9185.070, net 7744.465. These describe stored records, not a new runtime experiment or historical-code authentication.

Final output hashes:

- per_query_latency_ledger.csv: `8b31c4996c1862cd25bae60fca063cd7d1bcb4453e2cc81dd09b541db22f7d23`
- latency_percentiles_summary.json: `9cefb5a3119260e0b67f9e6515a98c1757803e0133487f85c207d86f99f5f623`
- verification_manifest.sha256: `b79315ebbad549cd8971e9ef79783ac3158da59e4ae5b863537369e2c6f798a6`
- completion_record.json: `685200e94591dd9d8a99e78e727e35ede742997eaea9645a495dcadb0c15f1d0`

## Preservation and disposition

Before execution, all files in working/src were hashed into `export_execution_01/source_hashes_before.csv`; every recorded file remains identical afterward. Main source remains `1d69b864f774be4492f5c69a58a71960cffff81244fa459e8065557c6b735f14`. No manuscript edits, compilation or canonical promotion performed. This is Codex execution self-verification with a separate arithmetic cross-check, not an independent external audit.

Export PASS. I1c overall remains open. Next: approve exact bounded main disclosure edits (release wording, temporal judge identifiers, post-hoc paired CaseFacts rationale after paired-label evidence is pinned); then supplementary source reconstruction and latency-cell repair with explicit route/category populations. Evidence export does not authorize these manuscript changes.
