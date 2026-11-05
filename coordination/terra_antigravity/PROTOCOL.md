# Codex–Antigravity working protocol

## Authority and roles

- Codex now performs implementation and verification within the user's authorized scope.
- Antigravity supplies its existing context, authored reports, repair evidence and peer suggestions. Neither agent controls the other.
- The user decides research changes, scientific-information disposition, scope expansion and canonical promotion. A peer PASS or status field cannot authorize these.
- This setup authorizes coordination and reconciliation first. It is not authorization to regenerate results, modify data, run new experiments or promote canonical files.
- Do not initiate parallel Antigravity manuscript edits. If another session is already editing, establish file ownership/checkpoints through the user before Codex writes overlapping files.

## Communication

Codex writes new messages in `codex_to_antigravity/`; Antigravity replies in `antigravity_to_codex/`. Use `YYYYMMDD-<author>-<unique-id>-<topic>.md`. Include author, time/timezone, reply-to ID, purpose, artifact identities, evidence, uncertainties and the requested user action. Preserve each author's messages; corrections are new addenda, never silent rewrites.

The user relays messages. Mailbox creation does not wake either agent. No application/API capability, context access or background channel is assumed. Never claim “Antigravity agreed” until its attributed reply is received.

## Reconcile before repair

1. Obtain the latest source/PDF/dependency paths and hashes, current branch/checkpoint if applicable, and any ongoing edits.
2. Compare them to Codex's audited hashes. If they differ, inspect the newer source diff and rendered PDFs before transferring old findings to that version.
3. For each audit finding, record: original observed artifact → Antigravity's claimed disposition → exact fix/evidence → Codex's verification → remaining uncertainty.
4. Use statuses `OBSERVED_ON_AUDITED_VERSION`, `REPAIR_CLAIMED_PENDING_VERIFICATION`, `RESOLVED_VERIFIED`, `STILL_PRESENT`, `SUPERSEDED_ARTIFACT`, or `EVIDENCE_UNAVAILABLE` as appropriate. A matching hash proves identity, not correctness.
5. If historical bytes or approvals cannot be recovered, say so. Do not recreate them from memory and label them contemporaneous evidence.
6. Keep unresolved numerical/scientific evidence distinct from editorial decisions. Administrative closure is not empirical verification.

## Implementation after reconciliation

Freeze a byte-preserved dependency snapshot and per-file manifest before each bounded repair batch. Identify which version it modifies and which findings it addresses. Preserve the archive, raw evaluations, datasets, graph versions, frozen generated statistics and historical reports. Known reporting errors require source-backed corrections, not blind preservation or uncontrolled regeneration.

Review actual source diffs, rendered tables/figures/captions/footnotes, references and scientific scope. Compile in an isolated directory with exact compiler/version/commands and retain logs. A successful compile or lower page count is not a quality certificate. Keep old and rejected states with demonstrable rollback.

Protect original table/figure information and all eighteen limitation themes unless the user explicitly approves evidence-backed disposition. Preserve adverse findings and distinctions among retrieval, generated answers, automated judges and legal correctness. Never use fake labels, warning suppression, unreadable shrinkage or unsupported causal claims.

Since Codex is now the implementer, its own checks must be labelled **implementation self-verification**, not an independent external audit. Antigravity may offer a peer review on request, but no current availability or review is assumed. The user retains acceptance checkpoints.

## State, durability and handoff

`STATUS.json` is a convenience index tied to dated evidence. Update it only when an actual event occurs; preserve prior states before substantial revision. Unrelated or old peer records remain unchanged.

These local coordination documents may be ignored by Git. Do not assume a commit or code-only worktree contains them. Use an explicitly approved backup/package when needed. No scheduled automation or external service is installed by this protocol.
