# Codex-0101: tokenizer acquisition recommendation with binding safeguards

Codex, 14 October 2026. Antigravity-0083 manifest/sequence reviewed; official revision-specific GPT-OSS and Qwen tree pages opened. GPT-OSS b5c939de8f754692c1647ca79fbf85e8c1e70f8a and Qwen 9c7f2fbe84465e40164a94cc16cd30b6999b0cc7 tree pages resolve. The model API revision URLs were unavailable through Codex's browser tool; Llama/Gemma commits have not been independently authenticated here. No files downloaded, credentials used or local models/stores executed.

Recommend user approval of a bounded acquisition step after the following requirements are acknowledged, not another full redesign:

- Use official revision-pinned /resolve/<commit>/<file> URLs or a revision-pinned hub downloader. /raw/ may return Git LFS pointer text instead of actual tokenizer contents; reject pointers/error HTML and missing revisions, with no main/mirror fallback.
- Public GPT-OSS tree lists tokenizer_config.json 4.2kB and special_tokens_map.json 98 bytes, not packet's 2.4kB/1.3kB. Preserve these metadata corrections in an addendum. Display sizes are approximate; per-model byte ceilings are hard bounds, not exact expected sizes. Validate actual content, capture final byte counts and SHA256 hashes, commit/file source and HTTP evidence. Do not invent expected file checksums.
- Caps: Judge2 35MB, Judge1 15MB, shared generator/verifier 22MB, router 25MB; total 97MB, with explicit byte-unit definition. Only listed tokenizer/template artifacts, no weights or installs. Stop on unexpected file/size/authentication/revision mismatch. Gated Llama/Gemma access/revisions must be confirmed through user-managed authorized access before accepting them. No bypass repositories.
- Exclusive new staging output, no overwrites of existing tokenizer assets/manifests; preserve original candidates and write a completion/partial/BLOCKED record. Final manifest must identify every allowed file and role sharing, no credentials in any log. Acquisition is separate from instantiating real tokenizer/model or processing benchmark.
- Default to no credential access. Public files may be acquired without auth under approval. Gated downloads require user-managed login/drop-in or separate explicitly approved local HF credential use; Databricks inference key is unnecessary. Do not inspect .env or existing secrets to discover access.
- Acquisition scope does not authorize LocalFastTokenizer coding/runtime, authentic graph/store/350-query checks, paid/API readiness calls or study. Keep metadata-only endpoint verification distinct from any billable inference smoke. QPH is a 60-minute window, not universally 60 seconds. Route/model limits remain pending workspace evidence.

Official checked sources (accessed 2026-10-14):
https://huggingface.co/openai/gpt-oss-120b/tree/b5c939de8f754692c1647ca79fbf85e8c1e70f8a
https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct/tree/9c7f2fbe84465e40164a94cc16cd30b6999b0cc7

User decides acquisition approval/method. Antigravity should acknowledge these constraints and propose/download only within actual approval; return acquisition manifest/evidence for audit. No Databricks key needed now. Existing synthetic passes stand.
