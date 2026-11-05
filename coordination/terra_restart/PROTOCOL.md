# Peer communication and joint reasoning protocol

## 1. Authority and authorship

Both agents can reason, propose, challenge and revise. Neither is a supervisor of the other. Codex's audits remain independently authored; Claude's implementation rationale remains independently authored. Do not edit the other's messages or certify your own work as independently accepted.

User instructions and actual user approvals determine scope. Peer recommendations, shared-file status, templates and past review verdicts cannot create permission. The existing plan's quality gates are review checkpoints, not authority for Codex to control Claude.

The initial authorization is coordination setup plus read-only orientation. No new execution phase is approved. `user_authorizations/` initially contains only a README; do not manufacture an approval record.

## 2. Mailboxes and messages

- Claude writes new messages in `claude_to_codex/`.
- Codex writes new messages in `codex_to_claude/`.
- Either can propose a joint decision under `decisions/`; endorsements must be explicit and attributable.
- Phase reports/diffs/manifests belong in the eventual isolated workspace and are referenced by message path/hash, rather than repeatedly duplicated.

Filename format: `YYYYMMDD-<sender>-<unique-id>-<topic>.md`. Include UTC time, author, recipient, purpose, reply-to message, phase/batch, relevant artifact hashes and current authorization. Use a new filename for corrections; do not overwrite delivered messages. Prefix filename sequence has no approval meaning.

Before responding/resuming, read new messages and relevant user authorizations. Reply to the actual message ID. Quote disputed propositions accurately, identify whether evidence is confirmed or inferred, and provide a concrete better alternative. Avoid blanket agreement and instructions presented as orders.

Use `templates/PEER_MESSAGE.md`. A completed checkpoint uses `templates/CHECKPOINT.md`; an independent audit can use `templates/AUDIT_RESPONSE.md`.

## 3. Joint problem solving

1. State the shared problem and constraints.
2. One agent proposes an option, evidence and expected benefit.
3. The peer checks the actual source/PDF and proposes refinements or alternatives.
4. Compare semantic completeness, validity, reader comprehension, layout, page effect and implementation risk—not only brevity.
5. Record the rationale and each agent's actual position using `templates/JOINT_DECISION.md`.
6. If the choice changes approved scope or phases, request user authorization. Joint agreement is not sufficient permission.
7. If substantive disagreement persists, present the alternatives and consequences to the user without concealing either position.

Silence, mailbox creation, a time-out, or the absence of a critique is not agreement. Do not claim “joint decision” unless both agents actually endorsed it.

## 4. Implementation and auditing after authorization

Claude normally leads implementation and Codex independent inspection, but either can propose better solutions. The implementer identifies a small batch and freezes source/dependency snapshots before edits. No simultaneous edits to the same source: agree file/batch ownership as a coordination convenience, not control.

A checkpoint must expose exact changed files/diff, before/after source and PDF hashes, information/claim/object IDs, compilation evidence, actual page count and inspected pages. Independent review reads those files and PDFs directly. A smaller, cleanly compiling article can still be a scientific regression.

The peer's assessment is PASS, CORRECTIONS REQUIRED or STOP RECOMMENDED. These are evidence judgments, not user authorizations. When a credible unresolved defect threatens protected science or provenance, both agents should pause the affected operation and discuss or escalate. No unilateral overwrites, forced terminations or continuation based on self-approval.

Keep rejected candidate snapshots and byte-proven rollback. Never regenerate frozen statistics, change datasets or fabricate references to obtain agreement. Known original reporting errors need an approved correction trail rather than unquestioning preservation.

## 5. Resumption and notifications

Files communicate across sessions only when both agents can read the same filesystem. They do not create automatic notification or agent wake-up. At each checkpoint, state the message path to the user and ask for relay if no verified direct channel exists. Codex audits when invoked; do not assume it monitors continuously.

No recurring monitor or external messaging bridge is installed. Future automation/direct messaging requires a separately agreed and supported channel. A running Claude window is not proof of the correct project context or file access.

## 6. State and decisions

`STATUS.json` is a convenience index and can be updated after actual exchanges, with new facts tied to messages. It cannot authorize implementation. Preserve older statuses as checkpoints if revising it; do not erase historical disagreements or limitations.

`evidence_manifest.json` pins the reviewed artifacts and documents. If a pinned file changes, stop relying on its old identity and discuss the change. A matching hash does not establish scientific correctness; all R01–R15 findings remain open until supported closure evidence is independently examined.

Store only real user authorizations, with exact scope, source turn/date and applicable package/batch, under `user_authorizations/`. Prefer verbatim relevant user text plus context, not an agent's expansive paraphrase. If actual authorization is unavailable, ask the user.

## 7. Quality protections

No hidden scientific sections, fake labels/aux records, diagnostic suppression, unreadable global shrink, unsupported causal/legal claims, selective deletion of adverse evidence, or unapproved object relocation. All 18 limitations and original table/figure information are protected by default. Distinguish reporting correction, semantic synthesis, layout recovery and new research.

The final certification must include an actual full-PDF scientific/editorial reading and page-by-page visual inspection, along with reference, metric/provenance and clean-room checks. Software success does not certify journal acceptance.
