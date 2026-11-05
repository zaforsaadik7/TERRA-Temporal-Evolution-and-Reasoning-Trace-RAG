# Consolidated native cohort integration — unadmitted source

24 October 2026, Codex implementation self-verification. User requested milestones
1 and 2 together, aiming for an hour. No claim that milestones are complete:
this is the consolidated source/test checkpoint before a fresh real freeze.

## Scope and implemented composition

Nine new implementation sources, five new named synthetic suites. No previous
implementation source changed; receiving checkpoint's nine identities verified.

- CohortJobOwner: one suspended/assigned/resumed Job, direct root wait plus active
  descendant count, required capture observation, external storage counters,
  termination/wait/close ordering. Unknown tree retains Job handles and rule.
- OwnedCohortBoundary: reused ownership/read-back lifecycle with distinct cohort
  namespace. PS boundary source copied byte-for-byte except rule/owner validation.
- Complete controller-attempt body: independent authority check, exclusive lock,
  pre-inventory/free-space checks, protected copies, boundary intent/create/verify,
  worker Job, active monitoring, strict complete 350-query/700-route audit,
  both protected postchecks and terminal evidence. Partial runs cannot pass.
- Extra post-observation/post-telemetry deadline checks prevent late-success.
- Frozen packet: strict typed hydration from an independently pinned byte SHA,
  regenerated-body comparison, separate run digest including native CLI template,
  derived paths, environment and pipeline policy. Older policy/command approvals
  cannot authorize it. Fixture packets require an explicit fixture-only decoder.
- Streaming filesystem identity and full-root memberships, snapshot/cache map,
  bounded metadata counters. Protected full roots reject hardlinks; selected
  system files may have Windows system hardlinks but remain exact-byte pinned.
- Authentic parent/child composition SOURCE: actual API signatures checked, reused
  DLL/PS/Chroma/ONNX adapters chosen behind closed production entry. Fixed temporary
  in-process admission context restores old component flags even on exceptions;
  no old source gate changes. Worker report mode chosen before computation.
- Standalone -I -B source-root bootstrap, closed anchor slot; outer user-paste hash
  must pin launcher + anchor independently to avoid packet/source hash cycles.
- PS5.1 outer watcher: pre-work clock, exclusive lock and bounded async capture,
  complete newline-ended phase records, work-deadline shutdown request and grace,
  full finalization deadline, verified-ID-only controller stop, no rule deletion
  on uncertain termination. No wildcard/image-name process termination/elevation.

## Evidence/limits

All positive native paths in tests use fake kernels/executors/readers. Test
AUTHENTIC-mode report fixtures are deliberately fabricated schema fixtures, NOT
genuine run evidence. PS tests parse the real source and execute ONLY extracted
safe helpers against temporary files and fake process commands, never main body.
No real benchmark/store/cache/graph/tokenizer/model access or inference, native
DLL/Job/firewall operations, API/credentials, manuscript/statistics or promotion.

The outer actor is independently owned PowerShell, not an extra Python controller
that would violate matching-process policy. Its stop is conservative: identity or
descendant ambiguity -> failure/recovery, not proof of complete termination.
Blocking OS/CIM/filesystem methods are not certified hard-interruptible. Storage
growth polling can detect overshoot, not enforce a filesystem quota. Source
quiescence/hash observations are not a source write lock. Native ABI/runtime
behavior of this new composition remains untested until separately authorized.

Native allocation must fund TWO capture reserves, <=16 combined boundary calls
with 1MiB/call ceiling (15 parent + one child image check), plus 8KiB outer
records. Proposed 64MiB parent/64MiB child of 128MiB leaves ~16MiB parent writer;
the earlier 32/96 synthetic example is deliberately rejected for this native
composition. This is a proposal, not live resource approval/calibration.

The anchor and outer launcher must NOT be put in the packet's own hashed closure
after embedding its SHA (cycle). They require independent external pinning.
Fresh whole-runtime/root inventory, packet generation, review, exact final freeze
and user's dated one-attempt approval remain gates. No runnable command supplied.

Peer-0231 prose has incorrect summary hyperlinks/line numbers; actual files and
manifest match. Preserve peer authorship; source identities govern this checkpoint.
