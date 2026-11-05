# Codex-0220 — Child command integration

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification.

Connected argument parsing to saved-request execution through execute_injected_cli. It accepts exactly one --request path, requires exact agreement with an independently supplied absolute frozen path, and receives expected request digest, reviewed context and fake worker loader independently. Duplicate options, abbreviations and mode/policy overrides are rejected before file access. It does not read environment settings or infer authority from request contents. Production use rejects before argument handling; main remains unconditionally blocked.

Updated supervised-dispatch integration to pass its frozen command's child arguments through this CLI function on the fake backend's resume hook, then generate and validate the saved report. No subprocess or native API executes. Added four tests covering command-to-worker/report success, malformed/override rejection, frozen-path mismatch and pre-argument production rejection.

265 tests passed across the existing 20 named synthetic suites in 6.942 seconds, exit 0. No wildcard discovery; ledger collision output is an expected temporary-fixture test.

Preserved source/test copies in reports/codex_child_cli_20261015_01/:

- offline_smoke_child_entry.py: 8bcdb1596045a78f33a9215f53aa4bf3b416b21e0126e87e35124beb2b0c63a4
- test_offline_smoke_child_entry_synthetic.py: b2eb891668bfe4f5b703b9d1aa53d9ce6b62a5e61cff4acd0b40724d93d56a8c
- test_offline_smoke_dispatch_synthetic.py: 288c8e78f0d3b70486ff447fa0cfdee032d8aa3117092d8b121fd660f376b58d

This is tested command parsing and handoff, not an admitted production CLI. Authentic-worker construction, genuine DLL/executor loading, transport of independent parent context to a genuine child, parent CLI and final constituent/approval packet remain unfinished. No real store, graph, model/tokenizer, Windows Job/firewall, credential, network/API or manuscript activity. No API key needed. Existing code-only approval remains sufficient for further implementation; peer review may be batched rather than requiring another approval round.
