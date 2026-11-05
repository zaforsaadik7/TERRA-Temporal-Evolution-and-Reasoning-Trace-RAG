# Start here — TERRA Claude ↔ Codex collaboration

Created 2026-09-28. This is a shared working foundation, not a manuscript implementation or execution approval.

## Partnership

Claude and Codex coexist as peer collaborators. Either can propose an approach, challenge an assumption, inspect evidence, or suggest a better solution. Claude is the expected implementation lead and Codex the independent auditor; these roles are complementary, not hierarchical. The user retains approval of phases, scope changes, experiments and promotion.

The objective is a scientifically accurate, coherent paper based on the original 39-page manuscript, provisionally targeting 25–26 pages without sacrificing unique information. Verify the actual venue rule: 26 pages is not compliant if the journal imposes 25. Q1 acceptance cannot be guaranteed by writing quality alone.

## Reading order for initial orientation

1. This file and `PROTOCOL.md`.
2. `STATUS.json` for the current coordination state; it is a summary, not proof of user approval.
3. `docs/TERRA_COMPARATIVE_REVIEWER_ASSESSMENT.md` — full scientific/editorial findings, IDs R01–R15.
4. `docs/TERRA_REVIEW_INFORMED_RESTART_PLAN.md` — proposed execution plan, Phases 0–13.
5. `FINDINGS_REGISTER.md` — compact index linking all findings to required evidence.
6. Latest messages in both mailbox directories and genuine user approvals, if any, in `user_authorizations/`.

Paths are relative to `F:\TERRA -Copy` unless specified otherwise. An agent in a different directory or sandbox must verify it sees the same files; a similarly named project is not enough. If folder access is unavailable, disclose that and request the files instead of asserting that they were reviewed.

## Verified source identities

- Original: `CANONICAL_ARCHIVE/src/main.tex`, SHA256 `31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4`.
- Original PDF: `CANONICAL_ARCHIVE/main.pdf`, 39 pages, SHA256 `757ad2ec03a205649cc97ee2bd06e30c06f41bc47dd857ced3019f3a8b7a38f3`.
- Frozen original stats: `CANONICAL_ARCHIVE/src/generated_stats.tex`, SHA256 `e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73`.
- Current diagnostic source: `Paper/main.tex`, SHA256 `5fde9d91fe7fa0a8c7b5ad2b6f68ff796f58eede7dacc14c4eca6998f52a6080`.
- Current diagnostic PDF: `Paper/main.pdf`, 23 pages, SHA256 `5a0468ddc1a7e287832fbae59b09d647280aa612acfb50976da8992c9627c89e`.

These identities were verified in the comparative review. `evidence_manifest.json` also records the full review/plan hashes. Run `venv\Scripts\python.exe coordination\terra_restart\check_foundation.py` to perform a read-only handoff check. A successful check certifies only file/coordination consistency, not scientific quality or execution permission.

## What the review established

The 39-page paper merits major revision; it is the reconstruction record, not an infallible text. The current 23-page revision is not a suitable scientific base: important setup/results are conditionally excluded, tables do not render, and artificial reference records mask absent destinations.

The original itself needs source-backed reconciliation: incorrect graph arithmetic; safety chart/table/caption mismatches; stale limitations and FDR descriptions; cost/operation conflicts; ambiguous metric/run identities; overly strong inference and novelty claims. Detailed findings and uncertainty are in the review, not replaced by this synopsis.

Other problems are genuine research gaps: independent verifier/legal evaluation, method-isolating comparisons under unequal resources, taxonomy quality and broader generalization. Wording cannot manufacture missing evidence. Propose a separately authorized study or narrow the claim and retain the limitation.

## Protected defaults

Preserve `CANONICAL_ARCHIVE/`, current `Paper/`, datasets, raw evaluations, generated statistics, runtime code, bundles and checklist during orientation and isolated editorial work. Do not recompute results or silently fix data. Keep all 23 original table objects, three figures, all 18 limitations, negative findings and numerical scope by default. Any exception needs explicit, evidence-backed disposition and user approval.

Keep 145,363 historical edges distinct from 145,366 active edges = 145,310 CITES + 56 OVERRULES. Preserve Direct-LLM Category-B counter-results, false refusals, D033/D034, curated-annotation dependence, absent independent NLI validation, absent licensed-practitioner evaluation, and distinctions between retrieval, generator/judge scores and legal correctness.

## First exchange — no execution yet

Claude should send a message using `templates/PEER_MESSAGE.md` that states:

- actual documents read and artifact hashes checked;
- interpretation of the findings and proposed plan;
- any disagreement or improved alternative, with evidence;
- unknowns or missing access;
- confirmation that no manuscript/data edits were made;
- requested next user decision.

Write it under `claude_to_codex/` and ask the user to notify Codex unless a direct channel has been verified. Codex will read it, examine the referenced evidence, and answer under `codex_to_claude/`. Either agent can continue a substantive discussion within authorized scope; neither can expand scope by approving itself or the other.

## Communication reality

Shared files are a durable mailbox, not an automatic live connection. A file write does not wake this Codex chat, notify Claude, or interrupt work. No background watcher, automation, external API, hook or permission enforcement was installed.

Claude's running desktop window was discovered, but project context could not be reliably captured; no message was submitted to it. To establish a direct channel later, identify the exact project conversation, confirm same-workspace access and relevant sending authorization, then perform a small handshake before relying on it. Do not send research data to an unidentified conversation.

For Claude Code, project `CLAUDE.md` is a supported memory mechanism; see [official Claude documentation](https://code.claude.com/docs/en/memory). Ordinary Claude Chat/Cowork access and loading must be confirmed, not assumed. The startup prompt below is the reliable explicit handoff.

## Startup prompt to give Claude

> We will work collaboratively with Codex as a peer, not as a controller. The project is F:\TERRA -Copy. Read CLAUDE.md and coordination/terra_restart/START_HERE.md, then the full comparative reviewer assessment and review-informed restart plan it links. Examine the latest peer messages and verify the handoff hashes. Do not begin reconstruction, compression, experiments or promotion: this message authorizes read-only orientation and a discussion response only. Write your acknowledgment, disagreements, proposed improvements and questions to coordination/terra_restart/claude_to_codex/ using the peer-message template. Tell me the message path so I can notify Codex. Wait for explicit phase authorization from me before implementation. If you cannot access the local folder, say so and request the handoff files; do not pretend to have read them.

## Persistence warning

This repository ignores Markdown and JSON, plus `docs/`. These coordination and review files are local filesystem artifacts and are not automatically protected by a normal Git commit/worktree snapshot. No ignore rules or staging were changed. Preserve them in an explicitly approved backup/package when needed; do not assume a code-only checkout contains the handoff.
