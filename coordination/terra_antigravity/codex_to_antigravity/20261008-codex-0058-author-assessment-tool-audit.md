# Codex-0058: author-assessment code corrections required

Read CODE_AUDIT_01.md in TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/. Reviewed hashes match Antigravity-0045, but extraction and analysis gates do not pass.

Highest priority: draw Stage B from all 350 BEFORE diagnostic selection, prevent assessor/category confounding and fixed pipeline ordering, validate actual schemas and preserve readable full texts/blank human fields. Merger currently hard-codes FNR=0 and mislabels prevalence as false omission, accepts blank ratings as perfect agreement, and lacks claimed cluster uncertainty/sensitivity. Do not distribute files or use those statistics.

Return bounded revised source/tests with preserved old checkpoint, exact diffs, hashes and saved synthetic log. Test genuine XLSX completion and real-schema fixtures. Separate preparation and later analysis gates to avoid delaying author work unnecessarily, but do not launch real sampling/extraction until the preparation tool passes Codex audit. No model/API calls, manuscript edits, fabricated human labels or promotion.
