# Codex-0107: tokenizer audit 02 — focused initialization/path corrections

Codex, 14 October 2026. Entire revised source and synthetic cases reviewed. Four named suites independently pass 134 tests in 4.315 s. Hashes match source dbe3ff01d05ae025b815e67c02751860d163be00c2fb2b96b58329d139d34e1d and tests f2539149d0af227e457d55973fe7fe67ea8fe833a18bac1b3771d5fa81b98ac3. No package installed, authentic tokenizer/template executed, real store/model/benchmark or API accessed.

Accepted: canonical manifest lookup replaces fallback; explicit base required; duplicate/nonhex/escaping manifest paths rejected; authentic mode rejects engine/renderer injection; integrity skip removed; sandbox class named; per-role/tool message restrictions expanded. Preserve these repairs.

Remaining focused initialization/path issues:

1. Import the sandbox submodule explicitly. Constructor only imports jinja2, builder then expects getattr(jinja2,'sandbox'). Python package import does not guarantee loading submodules. Synthetic top-level-only Jinja stub reproduces ConfigurationError 'jinja2.sandbox module is unavailable'; current builder fixture pre-populates .sandbox so hides this contract. Use explicit jinja2.sandbox.ImmutableSandboxedEnvironment import/injected sandbox class; no downgrade to mutable sandbox. Add constructor-level synthetic import test, plus real dependency test after approved install.
2. Inspect original lexical paths and parent hierarchy before resolve. Current verify_role_artifacts resolves role_dir/base then checks only resolved hierarchy, hiding a directory symlink/junction alias that points into canonical role. Validate manifest path too: require the canonical base/assets/tokenizers/tokenizer_manifest.sha256, no arbitrary manifest override. lstat failures currently suppressed; fail closed for existing inaccessible paths. Add existing alias/escape and altered manifest-location cases using synthetic filesystem/injected lstat, explicitly skip unavailable platform privileges rather than claiming they passed.

Carry-forward template controls: model_identity/reasoning_effort remain caller-overridable defaults, not immutable policies; record allowed explicit overrides in configuration, reject unknown kwargs/builtin_tools, and validate approved message fields. Full official-template byte/token-ID parity and sandbox escape tests remain blocked until dependency installed. Do not call mock environment formatting HF fidelity.

Return bounded source diff/checkpoint, hashes and named test logs. No installs/downloads/authentic-asset runs under this repair. After this source gate, propose exact two-wheel acquisition/install permission separately. No Databricks key needed; all real-data/live gates closed.
