# Reproducing Phase 2 outputs (read-only)

Run from the repository root `F:\TERRA -Copy`, with `venv\Scripts\python.exe -X utf8`. `P2` = `TERRA_EDITORIAL_RESTART_V2\phase2`, and `P1E` = `TERRA_EDITORIAL_RESTART_V2\evidence\phase1`. None of these scripts writes to a protected path. The two generator replays write only to the scratch directory given as an argument.

```
python -X utf8 %P2%\evidence\p2a_downstream_checks.py . %P2%\evidence\p2a_downstream_checks.csv
python -X utf8 %P2%\evidence\p2a_budget_checks.py . %P2%\evidence\p2a_budget_checks.csv
python -X utf8 %P2%\evidence\p2a_obscure_checks.py . %P2%\evidence\p2a_obscure_checks.csv
python -X utf8 %P2%\evidence\p2a_corpus_replay.py . %TEMP% %P2%\evidence\p2a_corpus_replay.csv
python -X utf8 %P2%\evidence\p2a_build_ledger.py . %P2% %P1E%
python -X utf8 %P2%\evidence\p2a_literal_scan.py . %P2%\ledgers\number_provenance_ledger.csv %P2%\ledgers\manuscript_literal_ledger.csv
python -X utf8 %P2%\evidence\p2a_table_literal_checks.py . %P2%\evidence\p2a_table_literal_checks.csv
python -X utf8 %P2%\evidence\p2b_build_claim_ledger.py %P1E%\R03_R18_R21_R23\claim_matrix.csv %P2%\ledgers\claim_ledger.csv
```

The previously delivered `p2a_macro_emitters.py` and `p2a_regen_compare.py` are packaged unchanged. The regen replay needs a patched copy of `generate_stats_v2.py` whose `ROOT_DIR` points to a sandbox and whose outputs go to /tmp, with the ablation input replaced by a stub. That setup is described in the script header.

**Inputs:**
- canonical v2 `data/terra_canonical_v2_eval.json`, sha `95e775e2…`;
- active graph `7aa6db46…`;
- pre-Issue-6 graph `012c999b…`;
- `ask_terra.py`, sha `0cca5cf4…`;
- working `generated_stats.tex`, sha `e4e369b7…`.
