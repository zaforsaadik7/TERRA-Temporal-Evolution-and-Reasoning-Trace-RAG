# TERRA Author Assessment Workbook Validation & Audit Report

**Date:** 11 October 2026  
**Status:** AUDIT COMPLETE — AWAITING USER REVIEW & EXACT CORRECTION IDENTIFICATION  
**Protocol Bounds:** Zero workbook modifications; zero rating alterations; zero final study result calculations; zero manuscript edits.  

---

## 1. Executive Summary & File Integrity Hashes

Both completed workbooks were read strictly read-only and audited against the issued originals and `PRIVATE_KEY_MAPPING.json` using the reviewed validator (`scripts/process_author_assessments.py`).

### Cryptographic Hashes (SHA-256)

| File Role | Relative Path | File Size | SHA-256 Hash | Integrity Status |
|---|---|---|---|---|
| **Author 1 Completed** | `COMPLETED/ASSESSMENT_AUTHOR_1_COMPLETED.xlsx` | 123,985 B | `97258970fad47105ee30a754c27e4f9b83422b189e5c36bfa5ac20c372087150` | Intact (read-only) |
| **Author 2 Completed** | `COMPLETED/ASSESSMENT_AUTHOR_2_COMPLETED.xlsx` | 93,619 B | `4f005cc7c2665452b73162b751c094da9e521411046af4d0390666dcc0bc33e8` | Intact (read-only) |
| Author 1 Issued Original | `ASSESSMENT_AUTHOR_1.xlsx` | 66,184 B | `af74f8b6777527bd05ebc0f9035d052dc1c4cad5cd730983e37fbf5f87d9e62b` | Verified match to manifest |
| Author 2 Issued Original | `ASSESSMENT_AUTHOR_2.xlsx` | 72,086 B | `71cd888cc22283a86443a6ac9e2c50c4a26091cd678f794dfbf6d1befb720a0d` | Verified match to manifest |
| Master Private Mapping | `PRIVATE_KEY_MAPPING.json` | 165,356 B | `64ee9128b5f972861a4846b7d097fdf425386c9711c7c266e6d7698c3408e710` | Verified match to manifest |
| Issued Manifest | `EXTRACTION_MANIFEST.json` | 6,501 B | `988eda05a0b5b38283f667eb3190ef33025f6858897efe8c90d3f4343040d408` | Verified match |

---

## 2. Integrity Verification Against Issued Originals

Using `validate_author_records_against_mapping` and exact cell-by-cell comparison against the issued workbooks:

1. **Row Count Alignment:** Both completed workbooks contain exactly 76 assessment rows (77 total rows including header), matching the 76 issued items per author.
2. **Immutable Field Preservation:**
   - All 76 `assessment_id`s match the issued originals and private key mapping with zero additions, deletions, or substitutions.
   - All 76 `cluster_id`s match verbatim.
   - All 76 `as_of_cutoff_year`s match verbatim.
   - All 76 `task_type`s match verbatim.
3. **Cryptographic Query & Model Response Verification:**
   - **Author 1:** 76/76 query texts match expected SHA-256 digests; 76/76 response texts match expected SHA-256 digests; 76/76 composite item digests match.
   - **Author 2:** 76/76 query texts match expected SHA-256 digests; 76/76 response texts match expected SHA-256 digests; 76/76 composite item digests match.
   - **Tampering Status:** `0` instances of text tampering or modifications detected across all 152 items.
4. **Shared Overlap Verification:** All 20 shared overlap pairs were verified to have identical query texts and model response texts across both authors' workbooks.

---

## 3. Validation Audit Summary (Completeness, Allowed Labels, Citations/Rationales)

| Audit Dimension | Author 1 (Md. Emam Zafor Saadik) | Author 2 (Muhammad Raihan Molla) |
|---|---|---|
| **Assessor Identity** | Populated on all 76 rows | Populated on all 76 rows |
| **Timestamps** | Populated on all 76 rows | Populated on all 76 rows |
| **Unpopulated / Missing Fields** | 0 items (0.0%) | 0 items (0.0%) |
| **Semantic Rule Violations** | 0 items (0.0%) | 0 items (0.0%) |
| **Rationales (>= 5 chars)** | Present on all 76 rows (100.0%) | Present on all 76 rows (100.0%) |
| **Required Pinpoint Sources / Excerpts** | Present on all 62 substantive items | Present on all 59 supported/contradicted items |
| **Invalid Enum Formatting** | **6 items (7.9%)** | **0 items (0.0%)** |
| **Overall Validator Verdict** | **FAIL (Needs 6 formatting corrections)** | **PASS (100.0% Valid)** |

---

## 4. Detailed Breakdown of Author 1 Formatting Discrepancies (6 Items)

All 6 issues in Author 1's workbook are strictly enum label syntax/whitespace discrepancies; zero items have missing data or substantive semantic violations:

### Issue Category A: Label `'no citation'` instead of allowed `'no citation/not applicable'` (5 items)
In these 5 items, the assessor entered the shortened phrase `'no citation'` instead of the full enum string `'no citation/not applicable'`:

| Assessment ID | Current Entered Value | Expected Schema Enum | Item Context |
|---|---|---|---|
| `AUTH1-ITEM-002` | `no citation` | `no citation/not applicable` | Refusal / Correctness N/A |
| `AUTH1-ITEM-003` | `no citation` | `no citation/not applicable` | Refusal / Correctness N/A |
| `AUTH1-ITEM-010` | `no citation` | `no citation/not applicable` | Refusal / Correctness N/A |
| `AUTH1-ITEM-023` | `no citation` | `no citation/not applicable` | Substantive Answer / Contradicted (Model lacked citations) |
| `AUTH1-ITEM-025` | `no citation` | `no citation/not applicable` | Refusal / Correctness N/A |

### Issue Category B: Accidental Trailing Newline in Cell (1 item)
In 1 item, an accidental linefeed (`\n`) was included in the spreadsheet cell:

| Assessment ID | Field Name | Current Entered Value | Expected Schema Enum | Diagnostic Note |
|---|---|---|---|---|
| `AUTH1-ITEM-019` | `temporal_leakage` | `'no\n'` (repr: `no\n`) | `no` | Cell contains trailing newline character |

---

## 5. Next Steps for User Review

1. **Review Identified Items:** Please review the 6 identified assessment IDs above (`AUTH1-ITEM-002`, `AUTH1-ITEM-003`, `AUTH1-ITEM-010`, `AUTH1-ITEM-019`, `AUTH1-ITEM-023`, `AUTH1-ITEM-025`).
2. **Authorization / Instructions for Correction:** If you authorize normalizing these 6 entries to their exact schema enum strings (`no citation/not applicable` and `no`), we can apply the correction, verify the updated workbook hash, re-run the validator to confirm 76/76 PASS on both workbooks, and then proceed to inter-assessor agreement checks and statistical analysis under user delegation.

---

## 6. Comprehensive Per-Item Validation Tables

### Author 1 (Md. Emam Zafor Saadik) — All 76 Items

| ID | Status | Correctness | Temporal Leak | Responsiveness | Citation Check | Refusal Just | Cite/Excerpt | Rationale Len | Result |
|---|---|---|---|---|---|---|---|---|---|
| `AUTH1-ITEM-001` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (207B/802B) | 1037 chars | PASS |
| `AUTH1-ITEM-002` | refusal | not applicable | `not applicable` | does not address | `no citation` | potentially unnecessary | Yes (310B/711B) | 909 chars | **FAIL** |
| `AUTH1-ITEM-003` | refusal | not applicable | `not applicable` | does not address | `no citation` | uncertain | Yes (98B/136B) | 790 chars | **FAIL** |
| `AUTH1-ITEM-004` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (188B/240B) | 799 chars | PASS |
| `AUTH1-ITEM-005` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (188B/487B) | 887 chars | PASS |
| `AUTH1-ITEM-006` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (202B/240B) | 1142 chars | PASS |
| `AUTH1-ITEM-007` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (199B/240B) | 1043 chars | PASS |
| `AUTH1-ITEM-008` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (129B/265B) | 627 chars | PASS |
| `AUTH1-ITEM-009` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (202B/856B) | 1345 chars | PASS |
| `AUTH1-ITEM-010` | refusal | not applicable | `not applicable` | does not address | `no citation` | potentially unnecessary | Yes (478B/980B) | 1248 chars | **FAIL** |
| `AUTH1-ITEM-011` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (316B/1128B) | 1085 chars | PASS |
| `AUTH1-ITEM-012` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (167B/582B) | 1445 chars | PASS |
| `AUTH1-ITEM-013` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (157B/485B) | 1093 chars | PASS |
| `AUTH1-ITEM-014` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (157B/485B) | 1093 chars | PASS |
| `AUTH1-ITEM-015` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (241B/422B) | 1755 chars | PASS |
| `AUTH1-ITEM-016` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (94B/974B) | 1654 chars | PASS |
| `AUTH1-ITEM-017` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (308B/973B) | 916 chars | PASS |
| `AUTH1-ITEM-018` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (94B/963B) | 805 chars | PASS |
| `AUTH1-ITEM-019` | substantive answer | contradicted | `'no\n'` | partly addresses | `authentic but misapplied` | not applicable | Yes (94B/974B) | 1519 chars | **FAIL** |
| `AUTH1-ITEM-020` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (210B/173B) | 685 chars | PASS |
| `AUTH1-ITEM-021` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (552B/808B) | 1055 chars | PASS |
| `AUTH1-ITEM-022` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (187B/642B) | 1026 chars | PASS |
| `AUTH1-ITEM-023` | substantive answer | contradicted | `no` | partly addresses | `no citation` | not applicable | Yes (184B/656B) | 1446 chars | **FAIL** |
| `AUTH1-ITEM-024` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (185B/650B) | 1021 chars | PASS |
| `AUTH1-ITEM-025` | refusal | not applicable | `not applicable` | does not address | `no citation` | potentially unnecessary | Yes (185B/652B) | 651 chars | **FAIL** |
| `AUTH1-ITEM-026` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (109B/513B) | 1587 chars | PASS |
| `AUTH1-ITEM-027` | mixed refusal/substantive answer | supported | `no` | partly addresses | `authentic but misapplied` | potentially unnecessary | Yes (109B/513B) | 1535 chars | PASS |
| `AUTH1-ITEM-028` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (370B/513B) | 1255 chars | PASS |
| `AUTH1-ITEM-029` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (109B/513B) | 1027 chars | PASS |
| `AUTH1-ITEM-030` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (218B/398B) | 1629 chars | PASS |
| `AUTH1-ITEM-031` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (316B/1191B) | 1584 chars | PASS |
| `AUTH1-ITEM-032` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (218B/1192B) | 1651 chars | PASS |
| `AUTH1-ITEM-033` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (218B/824B) | 1825 chars | PASS |
| `AUTH1-ITEM-034` | substantive answer | contradicted | `not applicable` | partly addresses | `no citation/not applicable` | not applicable | Yes (308B/332B) | 1136 chars | PASS |
| `AUTH1-ITEM-035` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (608B/742B) | 1425 chars | PASS |
| `AUTH1-ITEM-036` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (316B/643B) | 1217 chars | PASS |
| `AUTH1-ITEM-037` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (274B/975B) | 1176 chars | PASS |
| `AUTH1-ITEM-038` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (309B/864B) | 1058 chars | PASS |
| `AUTH1-ITEM-039` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (228B/451B) | 1136 chars | PASS |
| `AUTH1-ITEM-040` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (227B/218B) | 648 chars | PASS |
| `AUTH1-ITEM-041` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (233B/426B) | 1076 chars | PASS |
| `AUTH1-ITEM-042` | substantive answer | contradicted | `not applicable` | partly addresses | `no citation/not applicable` | not applicable | Yes (307B/306B) | 1477 chars | PASS |
| `AUTH1-ITEM-043` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (244B/748B) | 1087 chars | PASS |
| `AUTH1-ITEM-044` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (432B/1334B) | 1161 chars | PASS |
| `AUTH1-ITEM-045` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (206B/687B) | 1146 chars | PASS |
| `AUTH1-ITEM-046` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (104B/813B) | 1067 chars | PASS |
| `AUTH1-ITEM-047` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (104B/795B) | 1086 chars | PASS |
| `AUTH1-ITEM-048` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (104B/796B) | 1112 chars | PASS |
| `AUTH1-ITEM-049` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (104B/772B) | 1139 chars | PASS |
| `AUTH1-ITEM-050` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (199B/770B) | 1228 chars | PASS |
| `AUTH1-ITEM-051` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (495B/1104B) | 1124 chars | PASS |
| `AUTH1-ITEM-052` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (217B/928B) | 1228 chars | PASS |
| `AUTH1-ITEM-053` | substantive answer | supported | `yes` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (240B/979B) | 1374 chars | PASS |
| `AUTH1-ITEM-054` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (268B/928B) | 1207 chars | PASS |
| `AUTH1-ITEM-055` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (114B/596B) | 1258 chars | PASS |
| `AUTH1-ITEM-056` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (128B/270B) | 712 chars | PASS |
| `AUTH1-ITEM-057` | substantive answer | supported | `not applicable` | addresses requested issue | `no citation/not applicable` | not applicable | Yes (140B/234B) | 863 chars | PASS |
| `AUTH1-ITEM-058` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (170B/512B) | 1263 chars | PASS |
| `AUTH1-ITEM-059` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (370B/903B) | 1416 chars | PASS |
| `AUTH1-ITEM-060` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (578B/1194B) | 1964 chars | PASS |
| `AUTH1-ITEM-061` | substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | potentially unnecessary | Yes (290B/558B) | 1545 chars | PASS |
| `AUTH1-ITEM-062` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (103B/558B) | 1099 chars | PASS |
| `AUTH1-ITEM-063` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (103B/558B) | 1052 chars | PASS |
| `AUTH1-ITEM-064` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (204B/558B) | 1405 chars | PASS |
| `AUTH1-ITEM-065` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (325B/558B) | 1020 chars | PASS |
| `AUTH1-ITEM-066` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (616B/510B) | 1152 chars | PASS |
| `AUTH1-ITEM-067` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (422B/778B) | 1595 chars | PASS |
| `AUTH1-ITEM-068` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (372B/930B) | 1298 chars | PASS |
| `AUTH1-ITEM-069` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (199B/597B) | 1204 chars | PASS |
| `AUTH1-ITEM-070` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (199B/597B) | 1253 chars | PASS |
| `AUTH1-ITEM-071` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (199B/597B) | 1278 chars | PASS |
| `AUTH1-ITEM-072` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (198B/445B) | 1182 chars | PASS |
| `AUTH1-ITEM-073` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (120B/457B) | 1358 chars | PASS |
| `AUTH1-ITEM-074` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (259B/457B) | 1318 chars | PASS |
| `AUTH1-ITEM-075` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (259B/457B) | 1364 chars | PASS |
| `AUTH1-ITEM-076` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (259B/457B) | 1366 chars | PASS |

### Author 2 (Muhammad Raihan Molla) — All 76 Items

| ID | Status | Correctness | Temporal Leak | Responsiveness | Citation Check | Refusal Just | Cite/Excerpt | Rationale Len | Result |
|---|---|---|---|---|---|---|---|---|---|
| `AUTH2-ITEM-001` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (151B/282B) | 383 chars | PASS |
| `AUTH2-ITEM-002` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (151B/282B) | 383 chars | PASS |
| `AUTH2-ITEM-003` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (151B/282B) | 277 chars | PASS |
| `AUTH2-ITEM-004` | mixed refusal/substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | potentially unnecessary | Yes (151B/282B) | 355 chars | PASS |
| `AUTH2-ITEM-005` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (138B/326B) | 477 chars | PASS |
| `AUTH2-ITEM-006` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (138B/326B) | 312 chars | PASS |
| `AUTH2-ITEM-007` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (138B/326B) | 312 chars | PASS |
| `AUTH2-ITEM-008` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (138B/326B) | 302 chars | PASS |
| `AUTH2-ITEM-009` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (209B/214B) | 374 chars | PASS |
| `AUTH2-ITEM-010` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (110B/88B) | 54 chars | PASS |
| `AUTH2-ITEM-011` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (154B/171B) | 258 chars | PASS |
| `AUTH2-ITEM-012` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (129B/213B) | 487 chars | PASS |
| `AUTH2-ITEM-013` | substantive answer | supported | `not applicable` | partly addresses | `authentic and supports proposition` | not applicable | Yes (178B/157B) | 328 chars | PASS |
| `AUTH2-ITEM-014` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (57B/3B) | 166 chars | PASS |
| `AUTH2-ITEM-015` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (90B/242B) | 249 chars | PASS |
| `AUTH2-ITEM-016` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (88B/140B) | 69 chars | PASS |
| `AUTH2-ITEM-017` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (57B/3B) | 83 chars | PASS |
| `AUTH2-ITEM-018` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (57B/3B) | 85 chars | PASS |
| `AUTH2-ITEM-019` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (90B/36B) | 99 chars | PASS |
| `AUTH2-ITEM-020` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (101B/113B) | 283 chars | PASS |
| `AUTH2-ITEM-021` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (101B/113B) | 225 chars | PASS |
| `AUTH2-ITEM-022` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (101B/113B) | 225 chars | PASS |
| `AUTH2-ITEM-023` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (101B/113B) | 116 chars | PASS |
| `AUTH2-ITEM-024` | substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | not applicable | Yes (193B/149B) | 404 chars | PASS |
| `AUTH2-ITEM-025` | substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | not applicable | Yes (193B/149B) | 418 chars | PASS |
| `AUTH2-ITEM-026` | substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | not applicable | Yes (193B/149B) | 387 chars | PASS |
| `AUTH2-ITEM-027` | substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | not applicable | Yes (193B/149B) | 404 chars | PASS |
| `AUTH2-ITEM-028` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (90B/166B) | 467 chars | PASS |
| `AUTH2-ITEM-029` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (90B/166B) | 467 chars | PASS |
| `AUTH2-ITEM-030` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (90B/166B) | 93 chars | PASS |
| `AUTH2-ITEM-031` | mixed refusal/substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | potentially unnecessary | Yes (90B/166B) | 276 chars | PASS |
| `AUTH2-ITEM-032` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (129B/212B) | 372 chars | PASS |
| `AUTH2-ITEM-033` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (246B/157B) | 428 chars | PASS |
| `AUTH2-ITEM-034` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (103B/86B) | 122 chars | PASS |
| `AUTH2-ITEM-035` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (298B/480B) | 610 chars | PASS |
| `AUTH2-ITEM-036` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (298B/480B) | 398 chars | PASS |
| `AUTH2-ITEM-037` | substantive answer | uncertain | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (298B/386B) | 462 chars | PASS |
| `AUTH2-ITEM-038` | substantive answer | uncertain | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (298B/386B) | 462 chars | PASS |
| `AUTH2-ITEM-039` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (102B/84B) | 182 chars | PASS |
| `AUTH2-ITEM-040` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (198B/131B) | 449 chars | PASS |
| `AUTH2-ITEM-041` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (198B/131B) | 277 chars | PASS |
| `AUTH2-ITEM-042` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (198B/131B) | 449 chars | PASS |
| `AUTH2-ITEM-043` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (198B/131B) | 59 chars | PASS |
| `AUTH2-ITEM-044` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (227B/180B) | 283 chars | PASS |
| `AUTH2-ITEM-045` | mixed refusal/substantive answer | supported | `no` | partly addresses | `authentic and supports proposition` | potentially unnecessary | Yes (227B/180B) | 282 chars | PASS |
| `AUTH2-ITEM-046` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (227B/180B) | 520 chars | PASS |
| `AUTH2-ITEM-047` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (227B/180B) | 520 chars | PASS |
| `AUTH2-ITEM-048` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | uncertain | Yes (237B/65B) | 313 chars | PASS |
| `AUTH2-ITEM-049` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | justified | Yes (57B/3B) | 85 chars | PASS |
| `AUTH2-ITEM-050` | mixed refusal/substantive answer | uncertain | `no` | partly addresses | `authentic and supports proposition` | potentially unnecessary | Yes (149B/193B) | 377 chars | PASS |
| `AUTH2-ITEM-051` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (149B/193B) | 341 chars | PASS |
| `AUTH2-ITEM-052` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (295B/170B) | 538 chars | PASS |
| `AUTH2-ITEM-053` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (149B/193B) | 341 chars | PASS |
| `AUTH2-ITEM-054` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (124B/77B) | 96 chars | PASS |
| `AUTH2-ITEM-055` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (93B/189B) | 309 chars | PASS |
| `AUTH2-ITEM-056` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (110B/337B) | 652 chars | PASS |
| `AUTH2-ITEM-057` | mixed refusal/substantive answer | uncertain | `no` | partly addresses | `authentic but misapplied` | potentially unnecessary | Yes (110B/337B) | 322 chars | PASS |
| `AUTH2-ITEM-058` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (110B/337B) | 474 chars | PASS |
| `AUTH2-ITEM-059` | substantive answer | supported | `no` | addresses requested issue | `authentic but misapplied` | not applicable | Yes (110B/337B) | 652 chars | PASS |
| `AUTH2-ITEM-060` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (91B/95B) | 293 chars | PASS |
| `AUTH2-ITEM-061` | substantive answer | supported | `not applicable` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (82B/103B) | 70 chars | PASS |
| `AUTH2-ITEM-062` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (217B/286B) | 506 chars | PASS |
| `AUTH2-ITEM-063` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (172B/134B) | 181 chars | PASS |
| `AUTH2-ITEM-064` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (172B/134B) | 181 chars | PASS |
| `AUTH2-ITEM-065` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (172B/134B) | 54 chars | PASS |
| `AUTH2-ITEM-066` | substantive answer | supported | `no` | addresses requested issue | `authentic and supports proposition` | not applicable | Yes (172B/134B) | 118 chars | PASS |
| `AUTH2-ITEM-067` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (201B/98B) | 331 chars | PASS |
| `AUTH2-ITEM-068` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | uncertain | Yes (162B/233B) | 299 chars | PASS |
| `AUTH2-ITEM-069` | substantive answer | contradicted | `no` | partly addresses | `authentic but misapplied` | not applicable | Yes (213B/265B) | 364 chars | PASS |
| `AUTH2-ITEM-070` | substantive answer | supported | `not applicable` | partly addresses | `authentic and supports proposition` | not applicable | Yes (194B/148B) | 198 chars | PASS |
| `AUTH2-ITEM-071` | substantive answer | supported | `not applicable` | partly addresses | `authentic and supports proposition` | not applicable | Yes (158B/186B) | 381 chars | PASS |
| `AUTH2-ITEM-072` | substantive answer | uncertain | `uncertain` | partly addresses | `authentic but misapplied` | not applicable | Yes (191B/241B) | 562 chars | PASS |
| `AUTH2-ITEM-073` | substantive answer | supported | `not applicable` | partly addresses | `authentic and supports proposition` | not applicable | Yes (273B/175B) | 322 chars | PASS |
| `AUTH2-ITEM-074` | substantive answer | uncertain | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (128B/213B) | 545 chars | PASS |
| `AUTH2-ITEM-075` | refusal | not applicable | `not applicable` | does not address | `no citation/not applicable` | potentially unnecessary | Yes (197B/268B) | 177 chars | PASS |
| `AUTH2-ITEM-076` | substantive answer | contradicted | `not applicable` | partly addresses | `authentic but misapplied` | not applicable | Yes (183B/232B) | 513 chars | PASS |