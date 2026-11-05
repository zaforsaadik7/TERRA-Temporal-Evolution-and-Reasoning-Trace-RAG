# Synthetic parent receipt admission and worker handoff — 23 October 2026

Implementation self-verification under user's code-only approval. Two new files;
no previously reviewed source changed. No authentic operation or new real approval.

ParentReview binds immutable spec, load plan, resources, selected pins and declared
full-root memberships against separately supplied reviewed context. Mandatory
source/cache/tokenizer roots are nonempty and disjoint; relative membership names
are canonical sorted POSIX, no traversal/aliases. Pinned members within each root
must equal its declared full membership; graph pin must match reviewed load plan.
Standalone pins are permitted outside declared complete roots. This does NOT prove
all transitive runtime/code dependencies were included in the independent review.

ParentReceiptAdmission exists only in synthetic mode; authentic flag rejects first.
authorize_fixture connects the existing verify_cohort_approval DATA validator to
spec/resources/reviewed launch digest before observation callbacks can run. Tests
use generated records named SYNTHETIC_FIXTURE_ONLY, not real human permission;
no such records are written to user_authorizations or any execution packet.
Failed authority validation consumes its attempt; preparation consumes its attempt
before callbacks, validates observed selected pins AND full-root member lists
against frozen review before reading benchmark, then links observed FileReadReceipt
to query-only BenchmarkBinding. An observation failure never reaches the reader.

WorkerHandoff revalidates receipt/pin/fixture mode/byte size/content digest, source
declaration and350 ordered ID/text digests. Its digest covers parent review and
observed benchmark metadata without plaintext query/answer fields. Categories
remain in spec for identity validation but are not retrieval query text. Matching
data/digest is not cryptographic attestation, filesystem locking or dated authority.

Dispatch requires the prepared handoff and separately supplied reviewed digest,
then calls the injected dispatcher once. Failed dispatch admission also consumes
the instance's attempt. No cross-process lock/replay protection is supplied here.
synthetic_worker_handoff connects the binding directly to existing _run_bound and
fixed SIMULATED worker factory, not raw benchmark/gold bytes. Tests mock this
bridge's computation call; previous regression tests still exercise actual
retrieval/packing over generated20k/350 fixtures. Writers supplied to a rejected
bridge remain the caller's responsibility until _run_bound accepts ownership.

Full-root observation callback in tests actually enumerates/hashes generated tiny
temporary trees, detects an added member and changed pin, and uses the bounded
fixture benchmark reader. No genuine tree scan, store/model import or native
dispatch occurs. Production observers, whole source/runtime closure, canonical
launch binding with commands/paths/rule policy and actual dated permission remain
unimplemented/unadmitted; self-equal review data cannot substitute for those.

COHORT_PARENT_ADMITTED=False, authentic construction/bridge rejected, CLI returns2.
No previous holds lifted. Focused91 tests pass; fourteen new parent tests cover
matching pipeline, authority data before observation, invalid authority/no retries,
changed/extra/missing inventories, missing/overlapping roots, path aliases,
receipt/binding/fixture/digest mismatch, fixed bridge and held real entry.

Remaining: actual parent observation/admission adapter and canonical authority
freeze, source/runtime closure, parent/child evidence budgets and ownership,
pre-child outer watchdog, Windows Job/PS controller and separate dated run approval.
No API key needed. No genuine assets, network/API/credentials, native Job/firewall,
manuscript/statistics or promotion operation. No historical evidence sweep claimed.
