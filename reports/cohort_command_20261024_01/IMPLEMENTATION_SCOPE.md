# Prospective controller command contract

24 October 2026. Code-only implementation self-verification, not independent audit.

New immutable ControllerCommand combines the prior launch-policy digest with
exact controller argv, Windows list2cmdline rendering, explicit cwd, and four-key
environment (PATH, SYSTEMROOT, WINDIR, USERPROFILE). No ambient environment is
read or inherited. Uses pinned controller image/entry and derived context/approval
paths. -I -B are fixed. No shell, subprocess, native library or real input operation.

The new digest is distinct from the old policy digest. Existing approval validation
is NOT upgraded or wired to this new digest. No prior approval authorizes it.
The old command_contract remains UNRENDERED in the preserved policy module;
this separate prospective extension is not an admitted executable packet.

Still pending: receiving CLI/parser/bootstrap (including isolated Python import
strategy), independent controller observer, native process/image mapping, child
command/receipt transport, Job/capture/cleanup integration, fresh inventory and
dated run permission. Environment paths are lexical bindings, not filesystem
identity observations. No claim of endpoint, inference or 350-query execution.

Initial focused run: 16 tests, one test failure because its temporary path had no
spaces. No implementation failure: fixture corrected to declare a spaced entry
path and assert its exact quoting. Full named rerun recorded separately.

All old source checkpoints remain unchanged; new command gate False/main 2.
