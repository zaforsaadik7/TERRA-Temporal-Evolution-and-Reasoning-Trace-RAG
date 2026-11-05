# Codex-0284 — native integration R02 namespace closure

From Codex, 24 October 2026 (Asia/Dhaka). Follow-up to Codex-0283.
User-relayed peer review request; implementation self-verification only.

Operative source checkpoint:
reports/cohort_native_integration_20261024_01/regression_r02/manifest.json
SHA256804053ff1071679ba032ed4f69b1f1650d7e69face40b7987cc852b386d27ded.
All32 entries reverified.749 tests/49 named suites,747 passed/two skipped,
zero failures/errors,116.396seconds. The initial33-entry checkpoint is preserved;
four active-source rows are now superseded: filesystem,packet,production,packet
tests. All other source and immutable historical snapshots remain unchanged.

R02 closes the namespace gap called out in0283:
- Complete project module-directory membership, except exactly two externally
  pinned trust-root files: offline_cohort_anchor.py and launch_offline_cohort_user.ps1.
- Complete stdlib membership except global base site-packages; explicit pinned
  venv configuration must say include-system-site-packages=false for both roles.
- Complete base-runtime top-level file membership; existing full-root declarations
  still cover store/cache/tokenizers/base DLLs/venv installed environment.
- Parent before/after and child pre-model checks perform these namespace checks.
- Packet run digest now includes the explicit namespace policy. Any older digest
  or approval cannot authorize this amended source.

One extra focused test exercises the actual namespace checker on generated
temporary trees, including excluded global package fixture and unpinned-module
rejection. Full production-shaped tests mock these observations honestly; they
do NOT claim physical authentic closure or native behavior.

Filesystem preparation R01 was interrupted because its base-Lib traversal
included the global installed packages. Preserved STOP note in
reports/cohort_readiness_20261024_01/PREPARATION_STOP.md. No real cohort/DB/model
or attempt retry happened. R02 helper is now filesystem-only and excludes that
global subtree, with all actual selected identities refreshed twice and immutable
scientific inputs checked against prior pins. This helper is NOT in the sealed
source-test manifest; its results are separate preparation evidence and confer
no authority. A CIM query was denied; the owned helper was stopped using exact
Get-Process path/start identity without elevation. No unrelated process touched.

All production/entry/launcher holds remain closed; anchor null; actual attempt
directory absent. Please review operative R02 plus0283 scope/limits, not just
initial active rows. No actual permission or runnable command requested yet.
