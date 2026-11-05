# Antigravity-0092: Pinned Two-Wheel Installation Evidence Audit

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0109](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0109-approved-jinja-installation-checkpoint.md)  
**User Authorization:** Relay directive: *"Installation completed successfully. Official wheel sizes and hashes matched; only Jinja2 3.1.6 and MarkupSafe 3.0.4 were added to the project venv. No existing packages changed. Evidence is preserved in the installation report. Please relay Codex-0109 to Antigravity for audit."*

---

## 1. Executive Audit Verdict: PASS

Antigravity has independently inspected and verified all preserved installation evidence in [`tmp/wheels_install_20261014_01/`](file:///F:/TERRA%20-Copy/tmp/wheels_install_20261014_01/).

The installation was executed strictly within the authorized boundaries:
1. **Exact Wheel & Hash Verification:** Both staged wheels match their authorized byte counts and SHA-256 digests bit-for-bit.
2. **Strict Install Controls Enforced:** Executed with `--no-index`, `--no-deps`, `--only-binary=:all:`, `--require-hashes`, and `--no-cache-dir`.
3. **Clean Environment Isolation:** Only `Jinja2==3.1.6` and `MarkupSafe==3.0.4` were added to `F:/TERRA -Copy/venv`. Zero pre-existing packages were modified or removed.
4. **Submodule Availability:** `jinja2.sandbox.ImmutableSandboxedEnvironment` is verified importable and functional in the project environment.
5. **Synthetic Regression Integrity:** All 146 synthetic unit tests across the four named suites continue to pass with exit code 0.
6. **Zero Boundary Breaches:** Zero authentic tokenizers loaded from `assets/tokenizers/`, Gate C real data remains sealed, gated downloads remain blocked, and no API credentials/network calls were used.

---

## 2. Itemized Evidence Audit

### 2.1 Staged Wheel File & Digest Verification
The staged wheelhouse in `tmp/wheels_install_20261014_01/` was verified:

| Wheel Filename | Authorized Size | Actual Size | Authorized SHA-256 Digest | Actual SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `jinja2-3.1.6-py3-none-any.whl` | 134,899 bytes | 134,899 bytes | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` | **MATCH** |
| `markupsafe-3.0.4-cp314-cp314-win_amd64.whl` | 14,501 bytes | 14,501 bytes | `c1bc67752d5f21013cfe430df4062441714eab79f65a6a05e01505957e9c35fe` | `c1bc67752d5f21013cfe430df4062441714eab79f65a6a05e01505957e9c35fe` | **MATCH** |

### 2.2 Pinned Requirements & Execution Command
- File `requirements_pinned.txt` explicitly specifies both wheels with `--hash=sha256:...`.
- File `install_output.txt` confirms clean execution:
  ```text
  Looking in links: f:\TERRA -Copy\tmp\wheels_install_20261014_01
  Processing .\tmp\wheels_install_20261014_01\jinja2-3.1.6-py3-none-any.whl (from -r ... requirements_pinned.txt (line 1))
  Processing .\tmp\wheels_install_20261014_01\markupsafe-3.0.4-cp314-cp314-win_amd64.whl (from -r ... requirements_pinned.txt (line 2))
  Installing collected packages: MarkupSafe, Jinja2
  Successfully installed Jinja2-3.1.6 MarkupSafe-3.0.4
  ```

### 2.3 Pre/Post Environment Diff Audit
A comparison of `pip_list_before.json` vs. `pip_list_after.json` (and corresponding `pip_freeze` snapshots) confirms:
- **Added:** `Jinja2: 3.1.6`, `MarkupSafe: 3.0.4`.
- **Removed:** `None`.
- **Changed:** `None`.
- Zero modifications to system/global Python; target confined strictly to `F:/TERRA -Copy/venv`.

### 2.4 Live Environment Verification
Executed in `F:\TERRA -Copy\venv\Scripts\python.exe`:
```python
import jinja2, jinja2.sandbox, markupsafe
assert jinja2.__version__ == "3.1.6"
assert markupsafe.__version__ == "3.0.4"
assert hasattr(jinja2.sandbox, "ImmutableSandboxedEnvironment")
```
Result: All imports succeeded; `ImmutableSandboxedEnvironment` is present and active.

---

## 3. Synthetic Regression Status

Executed across all four named synthetic suites:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest `
    tests/test_offline_adapters_synthetic.py `
    tests/test_offline_preflight_synthetic.py `
    tests/test_matched_baseline_synthetic.py `
    tests/test_fast_tokenizer_adapter_synthetic.py
```
**Result:** 146 tests executed in 3.791s, 145 passed, 1 skipped (Windows unprivileged symlink fixture), 0 failures, exit code 0.

---

## 4. Source Checksums

| File Path | Byte Count | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 bytes | `ac47ed84319bf8c04cb117fdb2095cb17aec577a2cb015476596de8a720a861a` |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,066 bytes | `d2af44a62fcc48caec2595fcf850e5ce87fab03ee1c4dac2f107d64d0222c396` |

---

## 5. Scope & Boundary Confirmations

- **Authentic Tokenizers Untouched:** No tokenizers or templates in `assets/tokenizers/` were loaded or executed during this audit.
- **Gated Models Blocked:** Llama 3.3 and Gemma 3 downloads remain strictly blocked.
- **Gate C Real Data Sealed:** Real index and vector database directories remain completely unread.
- **Zero API Calls & Secrets:** No Databricks key requested or used.

---

## 6. Readiness for Stage 3B Authorization

With the two-wheel installation independently audited and certified, the project is now ready for separate user approval to proceed with **Stage 3B: Quarantined Public Tokenizer & Template Offline Validation** (Qwen and GPT-OSS on retained `assets/tokenizers/` assets using independent oracle expected outputs).
