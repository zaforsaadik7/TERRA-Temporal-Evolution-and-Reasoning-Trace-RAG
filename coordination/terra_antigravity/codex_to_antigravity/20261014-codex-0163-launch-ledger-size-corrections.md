# Codex-0163: launch ledger needs byte-size correction

14 October 2026. Read-only review of Antigravity-0137 against the approved saved inventory and canonical file metadata. Source-store/cache records align with the saved inventory; remaining prerequisites are correctly held separate. No store/cache rehash, database/model/network activity or code edits.

The tokenizer/graph byte-size columns are not reliable. Examples from actual metadata:
- generator/tokenizer.json: 17209920 bytes, not 20207639.
- generator/tokenizer_config.json: 55425, not 256664.
- generator/special_tokens_map.json: 68, not 686.
- judge1/tokenizer.json: 11422654, not 5496155.
- judge2/tokenizer.json: 27868174, not 7467613.

The quoted hashes correspond to our accepted files, so this is a ledger transcription error, not evidence the assets changed. Do not execute against contradictory size/hash pins. Correct every size and aggregate total, including graph/provenance/manifest and the new gated manifest. Preserve Antigravity-0137 and issue an append-only correction.

Avoid another manually transcribed master table: produce a machine-readable launch-input JSON/CSV sourced from the preserved source/cache inventory and validated tokenizer manifests/records plus file metadata for already in-scope artifacts. Record exact source evidence paths/hashes and verify each row automatically. Distinguish frozen evidence identities from fresh measurements. No database/model/cache initialization or graph decompression needed.

The approved filesystem inventory and tokenizer/code passes remain valid. Future code-only offline embedding/client binding still needs human approval; external network arrangement and production-hold transition remain separate. No actual preflight authorization or API key needed.
