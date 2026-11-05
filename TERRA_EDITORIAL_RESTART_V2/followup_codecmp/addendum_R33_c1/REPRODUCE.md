# How to reproduce R33/R34 (append-only note, following codex-0016)

## Always run Python in UTF-8 mode

On Windows the default text encoding raises `UnicodeDecodeError` when reading the evaluation JSON. Use `-X utf8`, or set `PYTHONUTF8=1`. This does not change any count.

## Commands

Run both from the repository root, `F:\TERRA -Copy`:

```
venv\Scripts\python.exe -X utf8 TERRA_EDITORIAL_RESTART_V2\followup_codecmp\addendum_R33\r33_holding_provenance_v2.py ask_terra.py dataset_20k_cap\terra_eeg_index_20k.json scratch\canonical_v2\terra_canonical_v2_eval.json dataset_20k_cap\terra_eeg_index_20k_pre_issue6_backup.json <outdir>

venv\Scripts\python.exe -X utf8 TERRA_EDITORIAL_RESTART_V2\followup_codecmp\addendum_R33_c1\r34_profile_v2.py dataset_20k_cap\terra_eeg_index_20k.json scratch\canonical_v2\terra_canonical_v2_eval.json TERRA_EDITORIAL_RESTART_V2\followup_codecmp\addendum_R33\r33_items.csv <outdir>
```

## Precision notes, for any future manuscript wording

- **The 82 "neither" items.** The selected 60-character fragment (`obs_head[20:80]`) was not found verbatim in either field of the later graph. This neither proves a different source for the full excerpt nor dates any change.
- **The 18 Category D rows marked NONE** are unclassified. They are not evidence of Category B settings.
