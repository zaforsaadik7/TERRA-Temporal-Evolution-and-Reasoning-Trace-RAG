# TERRA_EDITORIAL_RESTART_V2 — isolated workspace

Created in Phase 0 (user authorization: `coordination/terra_restart/user_authorizations/20260927T2338Z-user-authorizes-phase0.md`).

| Folder | Role | Permitted mutation |
|---|---|---|
| `archive_snapshot/` | Byte copy of `CANONICAL_ARCHIVE/` (main.pdf, canonical_manifest.json, src/**). Historical bundles excluded, since they are not build inputs. | **Never.** Read-only reference. |
| `working/src/` | Future editing source. At Phase 0 it is byte-identical to `archive_snapshot/src/`. | Only in an approved phase, one batch at a time, with a snapshot taken before each batch. |
| `builds/phase0/` | Diagnostic builds B1–B4, each with PDF, log, blg and `source_change.diff` against `working/src/main.tex`. | Append only. |
| `ledgers/` | Tracking registers: object, limitations, correction, macro values, rendered numbers, section budget, claim-language scan, information, claim, semantic-change, build/visual. | Append/update only, with a change note. |
| `reports/` | Phase reports and the venue shortlist. | Append only. |
| `manifests/` | Per-file SHA256 manifests per phase. | Append only (a new file per phase). |

Rules:
- **Do not execute `working/src/scripts/*.py`.** `generate_stats.py` and `check_consistency.py` have hardcoded `Paper/` paths and can write protected files.
- `generated_stats.tex`, `generated_obscure_stats.tex` and `generated_corpus_stats_20k.tex` stay byte-identical in every phase. Corrections go only through the registered and validated overlay agreed in claude-0003/0004, after item-level user approval.
- Deterministic builds use `SOURCE_DATE_EPOCH=1790467200 FORCE_SOURCE_DATE=1`.
