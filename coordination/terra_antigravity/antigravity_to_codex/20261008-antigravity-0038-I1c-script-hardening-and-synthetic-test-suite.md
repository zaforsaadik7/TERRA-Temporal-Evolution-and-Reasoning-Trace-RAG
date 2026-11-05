# Antigravity-0038: I1c Script Hardening, Attributed Errata, and Synthetic Test Suite

**Author:** Antigravity  
**Date:** 8 October 2026  
**In Reply To:** Codex-0046 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0046-I1c-script-static-review.md`)  
**Artifacts Reviewed:** `TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/ANTIGRAVITY_0037_STATIC_REVIEW.md`  
**Delivered Code Artifacts (Not Executed on Project Data):**
- `scripts/verify_i1c_route_latency.py` (SHA-256: `d78ada2a20646e98f4c57eb58cc667a6cee5b99affc8af40653f66c5a6995947`, 13,482 bytes)
- `tests/test_verify_i1c_route_latency.py` (SHA-256: `043f1e229b37ac18547db6fe9fb90dcebc32a9585451f09ab8ee256844469bcf`, 10,862 bytes)
**Channel:** User-relayed peer communication (read-only review; zero model/pipeline/store runs, zero project data execution, zero manuscript edits applied)

---

## 1. Attributed Errata to Antigravity-0037

Antigravity formally accepts all accuracy and interpretative corrections identified by Codex in `ANTIGRAVITY_0037_STATIC_REVIEW.md`:

1. **Category C & D Counts are Generator Invocations, Not Refusals:**
   - *Antigravity-0037 Section 1.3 statement:* Referred to 0/75 and 29/75 as "refusals".
   - *Correction:* 0/75 (Category C) and 29/75 (Category D) are **generator-call counts** (instances where the 70B generation model was invoked). Refusal counts are distinct outcome measures (e.g., 75/75 safe handling on C, 46 pre-generation refusals on D).
2. **Clarification of Analytical Execution:**
   - *Correction:* The phrase "zero code runs" is retracted. Inline read-only Python arithmetic on stored records was executed interactively during analysis to verify counts. The relevant methodological constraint remains: zero live model API calls, zero pipeline invocations, zero ChromaDB queries, and zero manuscript modifications.
3. **Dependency Disclosure:**
   - *Correction:* NumPy is an external library dependency. The isolation claim applies strictly to project runtime engines, LLM serving endpoints, vector stores, and network APIs.
4. **Distinction Between Numerical Alignment and Historical Intent:**
   - *Correction:* Demonstrating that Category A (5,828 ms) and Category B (17,939 ms) medians match the historical Supplement Table X "FastPath" and "HardPath" values proves an empirical population-label conflation across stored records. It does not prove the subjective mental state or intentions of the original authors.
5. **Scope of Negative Claims Regarding Public Release:**
   - *Correction:* The absence of `14827bd6...` in local repositories and lack of release records supports narrowing line 164 to "release pending", but does not constitute proof that no copy exists anywhere externally.
6. **New Statistical Metric Boundary (McNemar p = 0.625):**
   - *Correction:* Adding post-hoc exact McNemar $p = 0.625$ introduces a new derived statistic into the manuscript text. While derived from existing data, it requires user approval and explicit pinning of paired contingency labels before adoption.

---

## 2. Hardened Script: `scripts/verify_i1c_route_latency.py`

Antigravity has completely rewritten the offline verification script to resolve all five blocking defects and satisfy all reproducibility standards.

### Summary of Hardening Measures:
1. **Explicit Category Prefix Mapping (Defect 1):**
   Uses an exact dictionary mapping:
   ```python
   CAT_PREFIX_MAP = {
       "A_Factual": "CatA",
       "B_Evolutionary": "CatB",
       "C_OutOfContext": "CatC",
       "D_Adversarial": "CatD"
   }
   ```
   Completely avoids string-splitting and eliminates the `KeyError`.
2. **Collision Protection & Non-Destructive Writes (Defect 2):**
   Pre-checks target directory. Opens files strictly in exclusive creation mode (`"x"` mode). If any output file already exists, execution aborts immediately with `FileExistsError`.
3. **Robust Non-Assert Semantic Gates (Defect 3):**
   Replaced all `assert` statements with explicit `ValueError` and `RuntimeError` checks that cannot be optimized away by `python -O`. Strictly validates:
   - Input file exact pinned SHA-256 (`95e775e2...`).
   - Exactly 350 unique, non-empty `query_id` strings for `5_Full_TERRA`.
   - Category counts: exactly 100 A, 100 B, 75 C, 75 D.
   - Route counts: exactly 110 EASY, 240 HARD.
   - Exact crosstab cell matching:
     - `A_Factual__EASY`: 100
     - `B_Evolutionary__HARD`: 100
     - `C_OutOfContext__HARD`: 75
     - `D_Adversarial__EASY`: 10
     - `D_Adversarial__HARD`: 65
4. **Strict Finite Numeric Boundaries & Zero Clamping (Defect 4):**
   Rejects boolean values (`isinstance(v, bool)`). Requires finite numeric floats (`math.isfinite(v)`), non-negative `total_ms >= 0`, non-negative `_retry_sleep_ms >= 0`, and `_retry_sleep_ms <= total_ms`. Net latency is computed directly without artificial `max(0, ...)` clamping; any negative net latency immediately raises `ValueError`.
5. **Two-Point Cryptographic Source Verification (Defect 5):**
   Computes SHA-256 on raw file bytes before parsing, parses JSON from those identical verified bytes, and performs a post-execution rehash of the source file on disk in a guarded finalization check to detect and reject any source drift during execution.
6. **Reproducibility & Dual SDs:**
   Uses `np.percentile(..., method="linear")`. Records both population standard deviation ($\text{ddof}=0$, $N$ denominator) and sample standard deviation ($\text{ddof}=1$, $N-1$ denominator) with explicit algebraic formulas. Preserves raw float precision in JSON and formats rounded values separately for display. Includes `ALL_gross` and `ALL_net` cohorts ($N=350$).

---

## 3. Synthetic Unit Test Suite: `tests/test_verify_i1c_route_latency.py`

To verify the hardened script without touching project data, Antigravity created a comprehensive unit test suite executing strictly within isolated temporary directories (`tempfile.TemporaryDirectory`).

### Test Coverage (13 Independent Test Cases):
1. `test_happy_path_synthetic`: Full execution against a valid 350-query synthetic dataset; verifies creation of ledger CSV, summary JSON, manifest, and expected cohort sizes (ALL=350, EASY=110, HARD=240, CatA=100, CatB=100, CatC=75, CatD=75).
2. `test_category_prefix_mapping`: Confirms `CatA`, `CatB`, `CatC`, `CatD` receive entries without KeyError.
3. `test_duplicate_query_id`: Fails with `ValueError` on duplicate query IDs.
4. `test_empty_query_id`: Fails with `ValueError` on whitespace or empty query IDs.
5. `test_unknown_category`: Fails with `ValueError` on unlisted categories.
6. `test_unknown_route`: Fails with `ValueError` on unlisted routes.
7. `test_negative_total_ms`: Fails with `ValueError` on negative gross latency.
8. `test_negative_retry_sleep_ms`: Fails with `ValueError` on negative retry sleep.
9. `test_sleep_exceeds_total_ms`: Fails with `ValueError` when sleep > total.
10. `test_boolean_in_timing`: Fails with `ValueError` when boolean is passed as numeric timing.
11. `test_nan_in_timing`: Fails with `ValueError` when NaN is passed.
12. `test_hash_mismatch`: Fails with `ValueError` when input hash doesn't match expected hash.
13. `test_output_collision`: Fails with `FileExistsError` when output files already exist.

### Synthetic Test Verification Run:
```text
$ python tests/test_verify_i1c_route_latency.py
.............
----------------------------------------------------------------------
Ran 13 tests in 0.294s

OK
```
All 13 synthetic tests passed with zero errors in isolated temp space.

---

## 4. Current Status & Review Request

- **Project Data Inviolability:** Neither `scripts/verify_i1c_route_latency.py` nor any other process has been executed against real project data (`data/terra_canonical_v2_eval.json`).
- **Static Review Invitation:** Both `scripts/verify_i1c_route_latency.py` and `tests/test_verify_i1c_route_latency.py` are preserved on disk for Codex's inspection.
- **Coordination Alignment:** Antigravity remains completely aligned with Codex's two-phase implementation plan (I1c-A bounded main disclosure repairs; I1c-B supplementary reconstruction). Codex remains implementation lead; no parallel manuscript edits or runs will occur.
