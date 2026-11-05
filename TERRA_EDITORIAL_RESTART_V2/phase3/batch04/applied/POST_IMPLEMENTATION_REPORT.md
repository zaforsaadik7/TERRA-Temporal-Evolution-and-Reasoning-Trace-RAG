# Batch 04 post-implementation report (Claude; not independent)

- **Authorization:** `user_authorizations/20261005T1700Z-user-approves-batch04.md` (all of B4-1 to B4-12; the isolated working source only).
- **Applied:** `main.tex` (CRLF 1,107 and bare LF 16, unchanged) and `tables/table_router_eval.tex` (36 LF, unchanged). Commits used `expectedMtimeMs` guards and none was rejected.
- **Verified after re-staging from the device:** `main.tex` `d9a10dc9…` and `table_router_eval.tex` `71bbb26e…`, both equal to `EXPECTED_POST_HASHES.sha256`. The pre-state snapshots are in `snapshot_pre/`.
- **Device-state build (sandbox XeLaTeX, 3 passes):** 39 pages, 0 undefined references (`device_state_build.pdf/.log`). It matches the dry run.
- **Not done:** no Codex audit (queued), and no Tectonic build on the device. The page count is still 39 against the target of 25. No canonical promotion.
