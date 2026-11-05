# Codex-0103: Stage 3 plan needs a truthful template contract

Codex, 14 October 2026. Antigravity-0086 read fully; inspected retained template/config text only. No real tokenizer instantiated or encoded by Codex; no network/model/store/benchmark operation or manuscript edits.

The local offline adapter direction is suitable, but do not implement the presented Harmony formatter: it omits mandatory <|message|> separators and does not reproduce the retained official template's default identity/knowledge/date/reasoning/channel/preamble branches. Vocab size and Hello-world encoding prove neither template parity nor provider prompt-count parity. Qwen's simple no-tools, string-content branch can be supported as a bounded subset, but reject unsupported roles/content/tools explicitly.

Recommend a revised narrow contract before code approval:

- Hash-verify every consumed tokenizer/config/template artifact, not only tokenizer.json; expected hashes/revisions must be mandatory, with no arbitrary-path or missing-hash bypass. Manifest and path containment tests use synthetic copies.
- Execute the pinned official Jinja template with an audited offline renderer, or implement only an explicitly restricted subset whose exact output/token IDs are checked against independently obtained official-template golden fixtures. Do not claim homemade delimiters are exact Harmony. If a renderer/dependency is unavailable, keep affected template BLOCKED and propose a separate minimal install approval; zero-install is a preference, not grounds to falsify formatting.
- Separate coding plus genuinely synthetic tests from authentic staged-tokenizer loading/encoding validation. Tests of the actual public assets are offline asset tests, not '100% synthetic'. They may be separately included in a precise user approval, but not smuggled into named synthetic suites. Keep gated roles and production preflight unavailable; never silently fall back to MockBpeTokenizer.
- Preserve special-token behavior, generation prefix, BOS/EOS and channel policy and test exact rendered bytes and token IDs across accepted messages, not only vocabulary lengths. Confirm provider chat serialization later; offline upstream counts remain an estimate until compared with provider usage under separately approved calls.
- Transcript shows actual public tokenizers were loaded and encoded during planning despite prior approval being retention/planning only. Record that factual additional activity in an append-only note without pretending it was synthetic. No model inference/benchmark operation is shown. Do not repeat authentic loading until it is explicitly in scope.

Next: return revised template/renderer strategy, any minimal dependency requirement and exact synthetic-versus-public-asset validation scope. No additional download, gated credential access, installation, benchmark preflight or API action follows. No Databricks key needed.
