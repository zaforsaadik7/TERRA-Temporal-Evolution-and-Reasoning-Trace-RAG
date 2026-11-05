# Diagnostics B001 failed: home-directory binding omitted

23 October 2026, Asia/Dhaka. Codex implementation self-audit of the authorized user-window attempt. No rerun or real-worker reproduction was performed. All executed source bytes and46 saved parent/wrapper files were preserved before closing live admission constants.

## Cause identified from the new traceback and pinned source

Child exit1, parent exit1, FAIL. Captured stage LOCAL_COMPUTATION, RuntimeError. The traceback's innermost frames identify Chroma's onnx_mini_lm_l6_v2.py class definition line39 calling pathlib.Path.home, with the failure at pathlib/__init__.py home line1261. The captured log is1,452 bytes; child_report.json is empty. Locals, exception strings and source text were intentionally omitted by the logger, but the exact failing source line is now recoverable.

The installed Chroma class assigns `DOWNLOAD_PATH = Path.home() / ".cache" / "chroma" / "onnx_models" / MODEL_NAME` while importing the module. The pinned Python Path.home source calls os.path.expanduser("~") and raises RuntimeError("Could not determine home directory.") if expansion returns "~". Its Windows ntpath.expanduser implementation relies on USERPROFILE, or HOMEPATH with optional HOMEDRIVE; without either home location it returns the input unchanged.

The executed packet's runtime_environment contains only PATH, SYSTEMROOT and WINDIR. Saved child_environment_policy.json confirms the cleaned inherited keys include offline flags but neither USERPROFILE nor HOMEPATH. The wrapper clears inherited process variables, and the child receives only the explicit cleaned environment plus its independent context digest. Thus our clean-environment construction omitted the profile location needed by an import-time Chroma dependency. This is an environment-binding defect, not evidence of bad query answers, manuscript results, missing model weights or inadequate PC resources.

The exception occurred inside `import chromadb`, before the following `chromadb.PersistentClient(...)` call could execute. The traceback follows corpus extraction -> get_collection -> get_client -> authentic factory import. Prior worker assembly had returned and local computation had begun; its disposable SQLite schema check and graph/role setup precede that point in the inspected source. Do not generalize this to successful corpus extraction, dense retrieval, MiniLM inference or end-to-end feasibility: those results were not produced. This trace identifies the current attempt's cause; the prior class-only RuntimeError cannot independently be assigned the same cause retrospectively.

## Cleanup and integrity

Rule TERRA_Smoke_20261023_diagnostics01 was created and read back with matching outbound Block/Profile Any/program/owner properties. Saved owned-remove output is followed by null query responses. Terminal failures contain only execution failure, no cleanup/integrity/transcript failure. Under the reviewed lifecycle this implies termination was confirmed before teardown/postchecks; this audit did not independently query current processes or firewall state. Property read-back does not prove actual network isolation.

Pre/post file-pin records are byte-identical, SHA-256 99eac34b298fdb5a32d2d21a44ee3928be1f71687a78da988b54dadd85fc7967, reporting30,555 unique members. Source/cache/snapshot postchecks completed without recorded error. These are saved run records, not a new independent hash sweep. Child capture size/hash match its metadata, with no output-limit excess. No resource-limit failure is recorded; absence of a measured peak does not certify broad resource margins.

Process visibility uncertainty remains: parent observations21/18 unreadable, child18. Parent PID19968 and child PID1420 are the verified matching processes shown in the child-side check, not unrelated competitors. Both current attempt locks and all prior attempt evidence/locks remain preserved. No deletion or recovery action is indicated by the saved cleanup records.

## Containment and proposed repair

After preserving executed bytes matching the freeze .final snapshots, only live admission constants were restored closed: ENTRY_ADMITTED=False, packet anchors None, wrapper admission false/record anchors null. The frozen approval/packet/launch record and used locks are unchanged. The consumed permission does not permit a retry.

Proposed next scope, requiring user approval: provide one explicit reviewed USERPROFILE path through the existing cleaned-environment binding, with validation and synthetic regression tests for home resolution/import-like behavior. Do not inherit the whole environment, add credentials or weaken offline/firewall/process gates. No real Chroma import, client, model or run is necessary to build the synthetic regression. No implementation of that repair or new attempt occurred in this audit.
