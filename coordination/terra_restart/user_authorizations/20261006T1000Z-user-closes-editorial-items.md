# User authorization, 2026-10-06
The user, in their own message to Claude (verbatim): "close R01, R02, R14, R16, R17 and R26."
Effect: correction_register.csv rows R01, R02, R14, R16, R17 and R26 are set to CLOSED-BY-USER with this file as the approval. The user's decision; it is not a finding that the underlying issues were fixed or independently verified.
Context recorded for the audit trail (Claude, not independent):
- R01/R02: the 24-page working source keeps the full evidence structure except the table and limitation trims the user approved (auth/20261006T0900Z); no synthetic reference anchors in the working source; 0 undefined references at Batch 28.
- R14: audit-dossier voice was reduced in Phase 3 rewrites; claim_language_scan.csv was not re-run after Batches 18-28.
- R16/R17: engine and template were not changed; the working source still uses XeLaTeX with `\documentclass[conference]{IEEEtran}`; a Tectonic build by the user's other agent reported 24 pages. Final class and venue remain undecided.
- R26: report-only scan delivered at phase3/batch29/R26_LITERAL_SCAN_REPORT.md.
Still not delegated: archive/data/stats edits, new experiments, fake references, R30 data disposition, R22 data, canonical promotion.
