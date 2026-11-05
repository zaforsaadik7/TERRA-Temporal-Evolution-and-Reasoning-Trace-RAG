# R28 Amendment 3: post-hoc correction of Amendment 1

- **Written:** 2026-09-28, **after** all computations. It is labelled post-hoc because of that.
- **Trigger:** Codex audit `codex_to_claude/20260928-codex-0010-phase1-audit.md`, item 1.
- `R28_FROZEN_METHOD.md` is left unmodified (append-only).

## What Amendment 1 got wrong

- Amendment 1 compared the current 10k index's **listed** edge count (48,599) with the **unique** edge count in `terra_graph_metrics.json` (37,918).
- On that basis it concluded that the pre-backfill 10k file was the correct validation target.
- The comparison was invalid, because listed and unique counts are different quantities.

## Correct provenance (from the stored outputs; nothing was recomputed)

| File | SHA256 | Listed edges | Unique directed edges | Nodes | Largest WCC | Diameter | ASPL |
|---|---|---|---|---|---|---|---|
| `terra_eeg_index_10k.json` (current) | `a6da204e…` | 48,599 | **37,918** | 10,009 | **7,983** | **15** | **4.7131** |
| `terra_eeg_index_10k_pre_backfill_backup.json` | `7463b5ad…` | 48,516 | 37,835 | 10,000 | 7,973 | 15 | 4.7153 |

- The **current** 10k file matches `terra_graph_metrics.json` exactly: 37,918 edges, largest WCC 7,983, diameter 15, ASPL 4.713.
- It is therefore the file that validates the method (M4).
- The pre-backfill file does not match; its ASPL rounds to 4.715.

## Effect

- **M4 validation passes** against the correct target. The method is unchanged.
- **The 20k results are unchanged:** diameter 13, ASPL 4.305 (Σd = 1,482,541,170 over 344,380,806 ordered pairs, largest WCC 18,558).
- **Precondition for the paper:** before any Table III value is replaced, the paper must state the graph definition: undirected projection, largest weakly connected component, all ordered pairs.
