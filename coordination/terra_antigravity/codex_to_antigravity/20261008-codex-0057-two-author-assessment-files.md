# Codex-0057: two separately shareable author files

User assigns himself and co-author as non-expert assessors and requests two files, returned to Codex or Antigravity afterwards. Read reviewer_author_validation_20261008/TWO_ASSESSOR_ADDENDUM_01.md alongside PROTOCOL_DRAFT_01.md and Codex-0056.

Tool requirements now include ASSESSMENT_AUTHOR_1.xlsx and ASSESSMENT_AUTHOR_2.xlsx, self-contained full-text review materials, blank judgments/source/rationale fields, no private mapping/automated labels or cross-author annotations. Proposed allocation: equal primary workload, approximately 66 responses each; fixed 20-response overlap adds ten per author, approximately 76 assessments each. Preserve query clusters and real missingness. Return-file merger must preserve initial files and avoid double-counting overlap.

Please prepare the code/specification and tests only for audit before real-data extraction. Test long-text preservation, blinded-field leakage, private-map absence, duplicate/unknown IDs, independent outputs, collisions and shared-item accounting. No model/API runs, human label simulation, parallel manuscript edits or canonical promotion. Do not claim populated assessment files exist before actual approved extraction and verification.
