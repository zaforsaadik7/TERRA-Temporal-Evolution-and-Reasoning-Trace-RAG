# Named pin binding repair — implementation self-verification

23 October 2026, Asia/Dhaka. User authorized bounded binding implementation and synthetic checks. No human execution authority was created.

## Source and artifact changes

Added `scripts/matched_baseline/offline_smoke_bindings.py` and `tests/test_offline_smoke_bindings_synthetic.py`. No existing runtime source was edited. Final byte-preserved copies are beside this report. The helper is preparation-only and uses pure dictionaries/JSON/hashes; it performs no file/database/client/model operations itself.

Eight named roles are bound explicitly. Interpreter is the venv launcher; driver is offline_smoke_production.py; benchmark and graph are their exact reviewed input files. Store/cache roles reuse the original manifest declarations including full member verification. Tokenizer role has a selected 17-file manifest and explicit member scope. Original partition manifests remain present; overlaps do not waive constituent checks. New preparation source is additionally directly pinned.

snapshot_manifest pins an expected-copy artifact with 11 relative file identities. Its file SHA-256 is `a42c3f96036043bf6c2e59101c7ed9a6edc1141f4479664845c09b76469ec1d6`. Its separate expected receipt aggregate is `7fd9d9a99f8383c17e963eb1f9916bb52d7ac3203166e26b161e572484dda4d7`, computed using the same sorted `relative_path:size:sha256\n` convention as the lifecycle source. The artifact explicitly says NOT_ISSUED_RECEIPT. It is not a proof that real copies were made. Future production integrity.source_manifest must use these same relative entries and actual receipt validation/parity must still execute.

Built `packet.bound.proposal.json` from preserved approved inventory JSON, not a new source/model/store read. It is 14,348 bytes, SHA-256 `eb6404cb4e3912e652c1026408d69ccecac3d194f2170563e6237dc2dce56618`. All required names are present. This remains intentionally non-production with null launch authority. This evidence reuse is not a new source freshness certificate. Old candidate and prior reports remain unchanged.

## Tests actually run

Initial focused run counted 12 cases because importing a fixture TestCase also exposed its four tests to unittest. After switching to a module import, focused run is exactly 9 tests, all passed in 0.260 seconds. No non-synthetic modules or wildcard discovery were used.

Final named command: project venv Python `-B -m unittest` with the exact 25 modules from `reports/compact_manifest_repair_20261023_01/regression_modules.txt`, followed by `tests.test_offline_smoke_bindings_synthetic`. Result: **515 tests in 20.402 seconds; OK (skipped=2)**, exit 0 (513 passed). Collision/error diagnostics printed by deliberate negative fixtures are expected; there were no unittest failures/errors.

New tests cover nonmutation/member-check retention, direct-file substitution, inventory tamper, missing member checks, outside-source entries, duplicate source entries, role collision, actual request/context serializers, and complete synthetic packet decoding with matching config/request pins. Packet decoding uses existing fictional temp fixtures; it does not claim authentic file-verifier/Windows execution. Existing regression suites retain their separate mocked/full-byte/temp-fixture coverage. Synthetic scale wire output remained 5377/1476/1675 bytes and is not this real candidate's production-wire measurement.

## Remaining boundary

All execution admission flags and root anchor unchanged. No models, tokenizer execution, real database connections/copies, native/firewall operations, downloads/APIs, or manuscript changes. Tests read repository code and temp synthetic files only, not authentic store/model assets. Preparation builder reads saved approved inventory evidence and helper source only.

Peer review of helper, tests, actual artifacts and snapshot semantics is next. Final approved production packet shape, exact runtime request/context bytes, resource/native decision, fresh constituent checks at launch and separate one-attempt permission still remain. Do not treat a small proposal or passing synthetic decoder as actual permission, real-copy parity or a native feasibility result.
