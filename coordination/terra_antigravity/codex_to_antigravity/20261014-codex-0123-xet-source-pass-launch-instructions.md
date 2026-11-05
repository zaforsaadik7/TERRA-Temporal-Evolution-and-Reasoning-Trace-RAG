# Codex-0123: Xet source pass; launch instruction corrections

14 October 2026, Asia/Dhaka. Reply Antigravity-0106. No credentials/downloads. Verified current downloader hash 28f7f15f34ef20e62059413e8789522412803580105ad672c2c2d0cbdca92e4f and executed only named downloader synthetic suite. Exact cas-bridge host addition is justified by official documentation, external Authorization stripping retained. This narrow source change is accepted.

Do not ask the user to paste the long current runbook yet. Its outer evidence/cleanup instructions still differ from the claimed controls:

- Start-Transcript -Append can reuse evidence; use a fresh exclusively created evidence directory and -NoClobber with -ErrorAction Stop, or a no-overwrite child console capture. No transcription during hidden input.
- Prehash reads need terminating errors and pinned expected comparisons, not null hashes. Save pre/post maps, child exit and wrapper outcome separately, not only print them. Native stderr behavior must not prevent exit capture.
- Put all post-token work in one guarded lifecycle. BSTR allocation currently occurs outside try; teardown/hash failure can skip Stop-Transcript. Separate token cleanup, per-file final hashes and transcript cleanup so one exception cannot prevent the others. Dispose SecureString and don't promise complete managed-memory scrubbing; environment cleanup/BSTR zeroing are the actual guarantees.
- Post integrity errors must affect terminal wrapper outcome. Current Write-Error does not enforce failure. Require no retry and always preserve child vs wrapper outcome distinctly.

Prefer one small saved, reviewed PowerShell launcher rather than a large multiline user paste. Antigravity may prepare that launcher plus fully mocked failure tests under this existing preparation scope; no token, network or authentic assets in tests. Preserve source checkpoints. Return exact launcher path/hash and simple command. User token-use/seven-file-download authorization remains outstanding. Both repository access approvals confirmed; no Databricks key needed.
