# Authorized author-assessment preparation

Codex, 9 October 2026 (Asia/Dhaka). User approved preparation and inspection with “yes” after Codex-0063.

Executed reviewed preparation script once in production mode with bundled Python, explicit absolute pinned inputs and seed 20261008. Exit 0. Output destination was fresh. No model/API call, statistical scoring, manuscript edit or promotion performed.

Command: bundled `C:/Users/zafor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, `scripts/prepare_author_assessment_workbooks.py --temporal-input "F:/TERRA -Copy/data/temporal_leakage_dual_judged.json" --canonical-input "F:/TERRA -Copy/data/terra_canonical_v2_eval.json" --output-dir "F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/issued_20261009_01" --seed 20261008`.

Final extraction manifest: COMPLETED_AND_VERIFIED, production certification true. Independently checked every output-file hash against manifest. Original dataset, preparation script and working main hashes remain unchanged.

Actual allocation: 76 records per author; 132 unique responses; 20 shared responses; primary samples 80 temporal, 40 canonical, 12 targeted diagnostics. Diagnostics must not be pooled into probability estimates.

Read every issued workbook record through the reviewed loader; verified immutable fields and text hashes against private mapping. All G–Q judgment/evidence fields blank; no spreadsheet formula cells. All 76 query/response pairs per author occur verbatim in corresponding TXT and HTML companions (HTML-escaped representation checked).

Visual QA: imported workbooks with Artifact Tool and viewed representative rendered ranges on all three sheets for both authors: instruction opening, judgment headers/blank fields, and initial full-reading cards. These render legibly. This is representative visual QA, not inspection of every row in native Excel or a browser-rendered HTML inspection. Full-text integrity was checked across all records. Excel views are previews; the unrestricted HTML/TXT companions remain the complete reading route. No dropdown behavior is claimed.

The render helper had an initial URL-encoding path error; correcting fileURLToPath resolved it. This affected QA only, not extraction; the preparation script was not rerun or modified.

Separate author-only delivery packages contain each author's XLSX, matching HTML/TXT and common instructions. Private mapping, extraction metadata, TSV alternatives and QA files are excluded from delivery. Do not share the root issued directory or the other assessor's package. Returned XLSX files will be preserved before analysis. No author judgments exist yet.
