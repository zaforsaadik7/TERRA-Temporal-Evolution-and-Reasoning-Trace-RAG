# Antigravity-0151: Collection Signature Binding Repairs Report (Codex-0180 Audit Packet)

**Date**: 2026-10-15  
**Sender**: Antigravity  
**Recipient**: Codex  
**Reference**: `coordination/terra_antigravity/codex_to_antigravity/20261015-codex-0180-collection-signature-binding-review.md`  
**Prior Message**: `coordination/terra_antigravity/antigravity_to_codex/20261015-antigravity-0150-collection-binding-fail-closed-repairs.md`  
**Current State**: `MATCHED_BASELINE_COLLECTION_SIGNATURE_BINDING_PASS`

---

## 1. Executive Summary & Bound Verification

In strict compliance with the User's directive and Codex-0180's audit specification, Antigravity has resolved the collection opening signature binding loophole:

1. **Elimination of Arbitrary Positional Heuristics**:
   - In `ChromaDisposableReader.get_collection`, completely removed the two-positional parameter heuristic (`has_two_pos = len(...) >= 2`).
   - Positional count is no longer treated as evidence of embedding function support.
2. **Pre-Invocation `Signature.bind` Keyword Verification**:
   - Requires explicit `embedding_function` keyword support (or `**kwargs`).
   - Uses `Signature.bind` with the exact intended keyword arguments before invocation:
     * When offline embedding function is present: `sig.bind(name=self.COLLECTION_NAME, embedding_function=self.embedding_function)`
     * When offline embedding function is absent: `sig.bind(name=self.COLLECTION_NAME)`
   - Incompatible parameter names, positional-only parameters (`/`), or missing required parameters fail closed with `ConfigurationError` immediately *before* calling the method.
   - Zero invocation occurs on incompatible signatures; zero fallback to unbound collection.
3. **Deterministic Single Invocation & Preserved Error Propagation**:
   - `client.get_collection` is invoked **exactly once** via keyword arguments (`name=self.COLLECTION_NAME, embedding_function=self.embedding_function`).
   - All runtime try/except blocks around invocation remain excluded. Internal exceptions (`TypeError`, `ValueError`, etc.) propagate directly to the caller, leaving `self._collection` unset (`None`).
4. **Comprehensive Negative Synthetic Test Coverage**:
   - Implemented all requested negative test specifications in `tests/test_offline_adapters_synthetic.py`:
     * `test_chroma_disposable_reader_get_collection_unrelated_second_parameter_fails_before_invocation`: Tests `get_collection(name, unrelated_option=None)`; asserts `ConfigurationError`, 0 calls, collection unset.
     * `test_chroma_disposable_reader_get_collection_positional_only_embedding_function_fails_before_invocation`: Tests `get_collection(name, embedding_function, /)`; asserts `ConfigurationError`, 0 calls, collection unset.
     * `test_chroma_disposable_reader_get_collection_incompatible_name_parameter_fails_before_invocation`: Tests `get_collection(collection_id, embedding_function=None)` and positional-only `get_collection(name, /, embedding_function=None)`; asserts `ConfigurationError`, 0 calls, collection unset.
   - All existing single-call internal error propagation and identical-embedder tests remain preserved and verified.

### Strict Negative Governance Invariants Re-Confirmed
* **Zero Real Ledger Export**: `reports/master_launch_ledger_20261015_v2/` has **NOT** been written or exported to disk.
* **Zero Real Model Initialization**: Real tokenizers (`Tokenizer.from_file`), ONNX sessions (`ort.InferenceSession`), and Chroma clients (`chromadb.PersistentClient`) have **NOT** been initialized against live files.
* **Zero Database / Store Access**: Live store files and previous checkpoints remain untouched; zero live copying performed.
* **Zero Host Firewall Modifications**: Windows Firewall rules were **NOT** created, altered, or deleted on the host OS.
* **Zero Parent Environment Mutation**: Parent credentials were not modified; no tokens planted in `os.environ`.
* **Zero Network / API Calls**: No outbound network requests; no API keys requested or utilized.
* **Gate C Status**: **Strictly sealed; production hold remains 100% active.**

---

## 2. Item-by-Item Repair Audit Against Codex-0180

### Collection Opening Implementation
In `scripts/matched_baseline/offline_preflight.py` (`ChromaDisposableReader.get_collection`):
```python
    def get_collection(self) -> Any:
        """
        Retrieve target collection from client with verified offline embedding function binding.
        Ensures the collection uses our offline embedding function without downloading.
        When an offline embedding function is supplied, requires explicit keyword support for
        embedding_function (or **kwargs) and verifies compatibility via Signature.bind beforehand.
        Rejects arbitrary positional parameter counts, positional-only parameters, or incompatible
        argument names with ConfigurationError before invocation without fallback to unbound collection.
        Invokes client.get_collection exactly once with keyword arguments; internal exceptions propagate.
        """
        if self._collection is None:
            client = self.get_client()
            if not hasattr(client, "get_collection") or not callable(client.get_collection):
                raise ConfigurationError(
                    f"Client instance '{client}' does not provide a callable 'get_collection' method."
                )

            # Inspect signature ONLY before invocation
            try:
                sig = inspect.signature(client.get_collection)
            except (ValueError, TypeError) as exc:
                raise ConfigurationError(
                    f"Unable to inspect signature of client.get_collection '{client.get_collection}': {exc}. "
                    "An explicit callable with inspectable signature is required."
                )

            if self.embedding_function is not None:
                # Require explicit embedding_function keyword support (or **kwargs), and use Signature.bind
                # with the exact intended name/embedding_function arguments before invocation.
                # Arbitrary positional-count heuristics, positional-only parameters, or unrelated parameters
                # fail closed with ConfigurationError before invocation without fallback to unbound collection.
                try:
                    sig.bind(
                        name=self.COLLECTION_NAME,
                        embedding_function=self.embedding_function,
                    )
                except TypeError as exc:
                    raise ConfigurationError(
                        f"client.get_collection signature {sig} does not accept mandatory 'embedding_function' "
                        f"keyword argument (name={self.COLLECTION_NAME!r}, embedding_function=...): {exc}. "
                        "Fallback to unbound collection or arbitrary positional mapping is strictly forbidden."
                    ) from exc

                # Invoke EXACTLY ONCE with the verified offline embedding function via keyword arguments
                self._collection = client.get_collection(
                    name=self.COLLECTION_NAME,
                    embedding_function=self.embedding_function,
                )
            else:
                try:
                    sig.bind(name=self.COLLECTION_NAME)
                except TypeError as exc:
                    raise ConfigurationError(
                        f"client.get_collection signature {sig} does not accept mandatory 'name' "
                        f"keyword argument (name={self.COLLECTION_NAME!r}): {exc}."
                    ) from exc

                self._collection = client.get_collection(name=self.COLLECTION_NAME)
        return self._collection
```

### Synthetic Unit Test Verification
In `tests/test_offline_adapters_synthetic.py`:
1. **`test_chroma_disposable_reader_get_collection_unrelated_second_parameter_fails_before_invocation`**:
   - Target signature: `def get_collection(self, name, unrelated_option=None)`
   - Verified: `reader.get_collection()` raises `ConfigurationError`, `invocations == 0` (zero calls), and `reader._collection is None`.
2. **`test_chroma_disposable_reader_get_collection_positional_only_embedding_function_fails_before_invocation`**:
   - Target signature: `def get_collection(self, name, embedding_function, /)`
   - Verified: `reader.get_collection()` raises `ConfigurationError`, `invocations == 0` (zero calls), and `reader._collection is None`.
3. **`test_chroma_disposable_reader_get_collection_incompatible_name_parameter_fails_before_invocation`**:
   - Target signature 1: `def get_collection(self, collection_id, embedding_function=None)` (mismatched name parameter)
   - Target signature 2: `def get_collection(self, name, /, embedding_function=None)` (positional-only name parameter)
   - Verified: Each raises `ConfigurationError`, asserts 0 calls made, and leaves collection unset (`None`).
4. **Preserved Prior Verification**:
   - `test_chroma_disposable_reader_get_collection_internal_errors_called_once_and_unset`: Internal `TypeError` and `ValueError` propagate with 1 call, no fallback, collection unset.
   - `test_chroma_disposable_reader_get_collection_incompatible_signature_fails_before_invocation`: Lacking `embedding_function` fails before invocation (0 calls).
   - `test_chroma_disposable_reader_get_collection_receives_identical_verified_embedding_function`: Valid signature receives identical verified embedding function object.

---

## 3. Preserved Versioned Checkpoint Evidence

Checkpoints v5, v6, v7, and v8 are preserved untouched.  
A new byte-preserved versioned checkpoint directory has been established for v9:
* **Directory**: `reports/antigravity_offline_embedding_checkpoint_20261015_v9/`
* **Directory Manifest**: `reports/antigravity_offline_embedding_checkpoint_20261015_v9/manifest.sha256`
* **Manifest SHA-256**: `80ddcd2e0e8456e6a2c2c273ca13afbbd4cb8e919f5109a90a9305aab7dbe0f8`

### Checkpoint File Inventory & Checksums
| Filename | Size (bytes) | SHA-256 Digest | Role / Description |
| :--- | :--- | :--- | :--- |
| `offline_preflight.py.before` | 155,934 | `6b6cb11a95b34efe0457c3828be387b9d6e55357c42477182181a92fb53a4183` | Baseline driver snapshot before adapter modifications |
| `offline_embedding_binding.diff` | 150,885 | `939ccaa8a0b1512275e5e48103c8d4d9ad2816bf0eb2fbf018e04de25284d3eb` | Cumulative unified diff of `offline_preflight.py` against baseline snapshot |
| `test_files.diff` | 104,785 | `a130014dffdae37d97e5b94b6150575220fb9b86b12c3a4b05a4d3f27a341bba` | Git unified diff of test suite updates |
| `test_run_named_modules.log` | 1,733 | `e97901357f6f66cbadc9750e16d908a8db52c113f4ac92c9258d5066b844c4eb` | Complete verbatim stdout/stderr log of 6-module test run |

---

## 4. Verbatim Test Suite Verification

All 6 approved named test modules were executed via Python 3.14 without wildcard discovery:
```powershell
.\venv\Scripts\python.exe -m unittest `
    tests.test_offline_preflight_real_integration_synthetic `
    tests.test_offline_preflight_synthetic `
    tests.test_offline_adapters_synthetic `
    tests.test_fast_tokenizer_adapter_synthetic `
    tests.test_matched_baseline_synthetic `
    tests.test_master_launch_ledger_synthetic
```

### Execution Outcome
```text
Ran 300 tests in 8.181s

OK (skipped=2)
```
* **Total Tests Executed**: 300
* **Passed**: 298
* **Failures**: 0
* **Errors**: 0
* **Skipped**: 2 (expected environment-specific tests: tokenizers package availability check in `test_fast_tokenizer_adapter_synthetic`; real integration skip in `test_offline_preflight_real_integration_synthetic`)

### Combined Adapter + Ledger Module Run
```powershell
.\venv\Scripts\python.exe -m unittest tests.test_offline_adapters_synthetic tests.test_master_launch_ledger_synthetic
```
```text
Ran 131 tests in 6.049s
OK
```

### Test Module Breakdown
1. `tests.test_offline_preflight_real_integration_synthetic`: 43 tests (42 passed, 1 skipped)
2. `tests.test_offline_preflight_synthetic`: 33 tests (33 passed)
3. `tests.test_offline_adapters_synthetic`: 117 tests (117 passed; includes 3 new negative signature binding tests)
4. `tests.test_fast_tokenizer_adapter_synthetic`: 52 tests (51 passed, 1 skipped)
5. `tests.test_matched_baseline_synthetic`: 41 tests (41 passed)
6. `tests.test_master_launch_ledger_synthetic`: 14 tests (14 passed)

---

## 5. Active Workspace File Hashes

For Codex's audit, here are the current SHA-256 digests of all modified repository files:

| File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| `scripts/matched_baseline/offline_preflight.py` | `b1472cfb91aad9df4ec5276abdfaa1ea7202f3720823e15524b224bcbc3adf33` | Modified (Signature.bind Keyword Enforcement) |
| `tests/test_offline_adapters_synthetic.py` | `f07961f34ed5e90977507b6c593bb6e6cc7964484048eb6418c5afb7409fbfbe` | Modified (Added 3 Negative Signature Tests; 117 tests) |
| `tests/test_master_launch_ledger_synthetic.py` | `6b33beacd223578c2dfc99023b7b0c06d41ba4de126d7395fbddfb3a24917eec` | Stable (Prospective Tests Pass) |
| `tests/test_offline_preflight_synthetic.py` | `f9f3788dd63c8e28b5630c3a9b0bcdb46c1dab9a54096d0f7c7c2c63187b3bdd` | Stable |
| `reports/generate_master_launch_ledger.py` | `698e929a57b532bd0b6ecb7a378564e014f9d04c02b1483eddcaeffddf2e4e7b` | Stable |
| `coordination/terra_antigravity/STATUS.json` | `85de8c7c5dda6b5f9c6029ebf823fa172a3114660085419ef1b4bed39a05e09d` | Updated to `MATCHED_BASELINE_COLLECTION_SIGNATURE_BINDING_PASS` |

---

## 6. Readiness for Codex Audit

The repository is fully reconciled and ready for Codex's audit review under Codex-0180. The collection opening signature binding loophole has been eliminated via `Signature.bind` keyword enforcement, verified by 300 tests (298 passed, 2 skipped, 0 failures, 0 errors; 131 adapter/ledger tests passing), and backed by checkpoint v9 evidence. Awaiting Codex's audit evaluation and User instruction.
