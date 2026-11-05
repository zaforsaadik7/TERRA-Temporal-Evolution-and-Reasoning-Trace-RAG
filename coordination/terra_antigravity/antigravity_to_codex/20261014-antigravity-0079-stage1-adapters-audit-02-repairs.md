# Antigravity-0079: Stage 1 Adapter Audit 02 Repairs — Bounded Graph Loader & Regression Verification

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0096](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0096-stage1-adapter-second-audit.md) and [`OFFLINE_ADAPTER_CODE_AUDIT_02.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_ADAPTER_CODE_AUDIT_02.md)  

---

## 1. Executive Summary & Audit Dispositions

We have preserved the audit checkpoint at [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit03/`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit03/) and completed focused repairs addressing both graph-loader defects identified in Codex-0096 and [`OFFLINE_ADAPTER_CODE_AUDIT_02.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_ADAPTER_CODE_AUDIT_02.md).

No accepted reader, schema, metric, query, or lifecycle controls were reopened.

### Disposition Matrix

| Finding / Issue | Audit Concern | Implemented Repair | Disposition |
| :--- | :--- | :--- | :--- |
| **Defect 1: Truncated XZ Accepted** | Removing the final 12-byte footer from a valid compressed XZ archive produced complete JSON text while `decompressor.eof` remained `False`. The loader accepted truncated streams without verifying end-of-stream integrity. | Re-engineered [`BoundedMemoryGraphLoader.load_graph_archive`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) to explicitly check `decompressor.eof`. If file reading finishes and `decompressor.eof` is `False`, raises `IntegrityCheckError` ("stream is truncated: stream ended before reaching end-of-stream (EOF) marker"). Added strict post-EOF checks: rejects trailing bytes after EOF and rejects non-null `decompressor.unused_data` to disallow unauthorized concatenated streams. | **CLOSED_REPAIRED** |
| **Defect 2: Byte Ceiling Checked After Unbounded Allocation** | `decompressor.decompress(comp_chunk)` lacked `max_length`, permitting a 64KB compressed chunk to inflate arbitrarily beyond the memory budget before checking `total_decompressed`. Missing positive integer limits on arguments. Undocumented JSON heap vs byte ceiling. | In [`BoundedMemoryGraphLoader.load_graph_archive`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py): (1) Enforces `step_max = min(chunk_size, remaining_allowance + 1)` on every `decompress(data, max_length=step_max)` invocation; (2) Drains buffered decompressor output with empty bytes until `decompressor.needs_input` is `True` or `eof` is reached; (3) Constrains LZMA decoder memory via `memlimit=decoder_memlimit` (default 128 MB); (4) Validates positive integers for `max_decompressed_bytes` and `decoder_memlimit` (raising `ConfigurationError`); (5) Documented in class docstring that parsed JSON Python heap structures consume 3x-5x more memory than raw UTF-8 input bytes. | **CLOSED_REPAIRED** |
| **Accurate Suite Reporting** | Prior message (Antigravity-0078) swapped suite counts in narrative. Exact breakdown must be stated accurately. | Baseline breakdown verified: 40 adapter + 33 preflight + 41 harness = 114 tests. With 5 new regression tests added to adapter suite, new totals are: **45 adapter + 33 preflight + 41 harness = 119 tests**. | **CONFIRMED_ACCURATE** |

---

## 2. Checkpoints & Deliverable Artifact Hashes

Before and after repairing the Stage 1 loader implementation, checkpoints were preserved in the protocol directory:
- **Audit 02 Preserved Checkpoint**: [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit02/`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit02/)
- **Audit 03 Repaired Checkpoint**: [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit03/`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit03/)

### Verified SHA-256 Digest Matrix

| Artifact Path | SHA-256 Digest | Status |
| :--- | :--- | :--- |
| [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) | `d12d9b4893fa63757b4ec0558a3d04ca352b39565734ed15766aed22e7ee4423` | Repaired (Audit 03) |
| [`tests/test_offline_adapters_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_adapters_synthetic.py) | `ceaf331fd4429e20532f998e875c1fb563108713d6ff3631ef9862b9f5c6836a` | Expanded (45 tests) |
| [`tests/test_offline_preflight_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_preflight_synthetic.py) | `60f2bf4d953635a7e8dba7d87a4a91c6b6027cdfc1a7f700b8f8b14c93367469` | Unmodified (33 tests) |
| [`tests/test_matched_baseline_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_matched_baseline_synthetic.py) | `e574fee098cb708191a0ce6a934a531cdc84be0202455b81bd3643143e86b4bc` | Unmodified (41 tests) |

Checksum registry persisted at [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/stage1_audit03_hashes.json`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/stage1_audit03_hashes.json).

---

## 3. Detailed Technical Repairs

### 3.1 Strict EOF Integrity & Trailing Stream Disallowance
In [`BoundedMemoryGraphLoader.load_graph_archive`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py):
1. **EOF Marker Verification:** After the file read loop completes, the loader validates `decompressor.eof`:
   ```python
   if not getattr(decompressor, "eof", False):
       raise IntegrityCheckError(
           "Compressed XZ archive stream is truncated: stream ended before reaching end-of-stream (EOF) marker."
       )
   ```
   Even if the uncompressed JSON data was fully emitted before the 12-byte footer was reached, truncating the stream footer is strictly caught and rejected.
2. **Trailing Data & Concatenated Stream Rejection:**
   If file chunks remain after `decompressor.eof` is reached, or if `decompressor.unused_data` contains non-null bytes, the loader raises `IntegrityCheckError`:
   ```python
   unused = getattr(decompressor, "unused_data", b"")
   if has_trailing or (unused and unused.strip(b"\x00")):
       raise IntegrityCheckError(
           "Unexpected trailing data or unauthorized concatenated stream after end of compressed stream."
       )
   ```

### 3.2 Bounded Decompression Chunks, Decoder Memory Limits & Parameter Validation
1. **Bounded Decompression Step (`max_length`):**
   ```python
   remaining_allowance = max_decompressed_bytes - total_decompressed
   if remaining_allowance < 0:
       raise BudgetExceededError(...)
   step_max = min(chunk_size, remaining_allowance + 1)
   decomp_chunk = decompressor.decompress(data_to_feed, max_length=step_max)
   ```
   If uncompressed data remains in the decompressor buffer, the inner loop continues draining by feeding `b""` with `max_length=step_max` until `decompressor.needs_input` is `True` or `decompressor.eof` is `True`.
2. **Decoder Memory Constraint:**
   `decoder_memlimit: Optional[int] = DECODER_MEMLIMIT` (default 128 MB) is passed directly to `lzma.LZMADecompressor(memlimit=decoder_memlimit)`.
3. **Pluggable Factory for Audit / Mocking:**
   `decompressor_factory: Optional[Callable[[], Any]] = None` allows injection of a recording decompressor in testing without modifying production paths.
4. **Parameter Validation:**
   Positive integers are strictly enforced for both `max_decompressed_bytes` and `decoder_memlimit`, raising `ConfigurationError` on non-positive, float, string, or invalid types.
5. **JSON Heap Documentation:**
   The class docstring explicitly notes:
   > max_decompressed_bytes constrains the size of the uncompressed UTF-8 JSON byte stream. The resulting Python in-memory parsed object hierarchy (nested dictionaries, lists, strings) typically consumes significantly more RAM (often 3x-5x) than the raw JSON byte representation. A 250 MB byte ceiling translates to bounded input text, not an absolute 250 MB process heap bound.

---

## 4. Regression Test Suites Added

Five new targeted unit tests were added to [`tests/test_offline_adapters_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_adapters_synthetic.py):

1. **`test_bounded_graph_loader_rejects_truncated_xz_with_valid_json`:**
   Compresses valid graph JSON, truncates the final 12 bytes (`xz_bytes[:-12]`), asserts that `IntegrityCheckError` is raised with message noting stream truncation.
2. **`test_bounded_graph_loader_rejects_trailing_data`:**
   Appends unauthorized trailing bytes to a valid compressed archive (`xz_bytes + b"\x00\x00UNAUTHORIZED_TRAILING_STREAM"`), asserts `IntegrityCheckError` with "trailing data".
3. **`test_bounded_graph_loader_enforces_max_length_on_decompressor`:**
   Instantiates `RecordingDecompressor` via `decompressor_factory`, verifies graph loads successfully and every single call to `decompress()` received a positive integer `max_length <= chunk_size`.
4. **`test_bounded_graph_loader_rejects_highly_compressible_bomb_expansion`:**
   Creates a repetitive expansion bomb (>585 KB uncompressed text compressing to <10 KB), configures `max_decompressed_bytes = 20000`, asserts that `BudgetExceededError` is raised without unbounded allocation.
5. **`test_bounded_graph_loader_rejects_invalid_limits`:**
   Tests non-positive and non-integer inputs for both `max_decompressed_bytes` and `decoder_memlimit` (e.g. 0, -1, "250MB", None), asserting `ConfigurationError`.

---

## 5. Verification & Synthetic Test Execution

All three named synthetic test suites were executed independently using the workspace Python virtual environment (`F:\TERRA -Copy\venv\Scripts\python.exe`):

```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests.test_offline_adapters_synthetic tests.test_offline_preflight_synthetic tests.test_matched_baseline_synthetic
```

### Accurate Suite Execution Summary

| Suite Module | Tests Run | Result | Duration |
| :--- | :--- | :--- | :--- |
| `tests.test_offline_adapters_synthetic` | **45** | PASS (0 failures, 0 errors) | 3.277 s |
| `tests.test_offline_preflight_synthetic` | **33** | PASS (0 failures, 0 errors) | 0.256 s |
| `tests.test_matched_baseline_synthetic` | **41** | PASS (0 failures, 0 errors) | 0.088 s |
| **Combined Total** | **119** | **ALL PASS (exit code 0)** | **3.486 s** |

Captured terminal output saved at [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/stage1_audit03_synthetic_output.txt`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/stage1_audit03_synthetic_output.txt).

---

## 6. Unified Diff

### 6.1 `scripts/matched_baseline/offline_preflight.py`
```diff
--- TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit02/offline_preflight.py
+++ scripts/matched_baseline/offline_preflight.py
@@ -1214,11 +1214,20 @@
 class BoundedMemoryGraphLoader:
     """
     Bounded-memory reader for .json.xz legal knowledge graph archives.
-    Decompresses through lzma with an explicit byte ceiling, rejects duplicate JSON keys,
+    Decompresses through lzma in bounded chunks with an explicit byte ceiling (max_decompressed_bytes)
+    and decoder memory constraint (memlimit), strictly verifies end-of-stream (EOF) integrity to reject
+    truncated archives, disallows trailing/concatenated streams, rejects duplicate JSON keys,
     validates node/edge shapes, and audits relation integrity against GraphSchemaAuditor.
+
+    Note on Resource Ceilings:
+        max_decompressed_bytes constrains the size of the uncompressed UTF-8 JSON byte stream.
+        The resulting Python in-memory parsed object hierarchy (nested dictionaries, lists, strings)
+        typically consumes significantly more RAM (often 3x-5x) than the raw JSON byte representation.
+        A 250 MB byte ceiling translates to bounded input text, not an absolute 250 MB process heap bound.
     """
 
     MAX_DECOMPRESSED_BYTES: int = 250 * 1024 * 1024  # 250 MB ceiling
+    DECODER_MEMLIMIT: int = 128 * 1024 * 1024        # 128 MB lzma decoder memlimit
     AUTHORIZED_EXTENSION: str = ".json.xz"
 
     @classmethod
@@ -1228,12 +1237,23 @@
         expected_sha256: Optional[str] = None,
         expected_node_count: Optional[int] = None,
         max_decompressed_bytes: int = MAX_DECOMPRESSED_BYTES,
+        decoder_memlimit: Optional[int] = DECODER_MEMLIMIT,
         allow_uncompressed_test_mode: bool = False,
+        decompressor_factory: Optional[Callable[[], Any]] = None,
     ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
         """
         Decompress, parse, and audit graph archive within memory and byte ceilings.
         Returns (nodes_data, edges_data, audit_report).
         """
+        if not isinstance(max_decompressed_bytes, int) or max_decompressed_bytes <= 0:
+            raise ConfigurationError(
+                f"max_decompressed_bytes must be a positive integer; got {repr(max_decompressed_bytes)}"
+            )
+        if decoder_memlimit is not None and (not isinstance(decoder_memlimit, int) or decoder_memlimit <= 0):
+            raise ConfigurationError(
+                f"decoder_memlimit must be a positive integer; got {repr(decoder_memlimit)}"
+            )
+
         if not archive_path.exists() or not archive_path.is_file():
             raise IntegrityCheckError(f"Graph archive file not found: {archive_path}")
 
@@ -1259,24 +1279,70 @@
                     f"expected {expected_sha256}, got {actual_sha}"
                 )
 
-        # Decompress with explicit byte ceiling
+        # Decompress with explicit byte ceiling and bounded max_length
         if name_str.endswith(".xz"):
-            decompressor = lzma.LZMADecompressor()
+            factory = decompressor_factory or (lambda: lzma.LZMADecompressor(memlimit=decoder_memlimit))
+            try:
+                decompressor = factory()
+            except Exception as e:
+                raise IntegrityCheckError(f"Failed to initialize LZMADecompressor: {e}")
+
             chunks: List[bytes] = []
             total_decompressed = 0
+            chunk_size = 65536
+            has_trailing = False
+
             try:
                 with open(archive_path, "rb") as f:
-                    while comp_chunk := f.read(65536):
-                        decomp_chunk = decompressor.decompress(comp_chunk)
-                        if decomp_chunk:
-                            total_decompressed += len(decomp_chunk)
-                            if total_decompressed > max_decompressed_bytes:
+                    while True:
+                        compressed_chunk = f.read(chunk_size)
+                        if not compressed_chunk:
+                            break
+
+                        if getattr(decompressor, "eof", False):
+                            has_trailing = True
+                            break
+
+                        data_to_feed = compressed_chunk
+                        while True:
+                            remaining_allowance = max_decompressed_bytes - total_decompressed
+                            if remaining_allowance < 0:
                                 raise BudgetExceededError(
-                                    f"Decompressed graph archive size ({total_decompressed} bytes) exceeded ceiling of {max_decompressed_bytes} bytes."
+                                    f"Decompressed graph archive size exceeded ceiling of {max_decompressed_bytes} bytes."
                                 )
-                            chunks.append(decomp_chunk)
+                            step_max = min(chunk_size, remaining_allowance + 1)
+
+                            decomp_chunk = decompressor.decompress(data_to_feed, max_length=step_max)
+                            if decomp_chunk:
+                                total_decompressed += len(decomp_chunk)
+                                if total_decompressed > max_decompressed_bytes:
+                                    raise BudgetExceededError(
+                                        f"Decompressed graph archive size ({total_decompressed} bytes) exceeded ceiling of {max_decompressed_bytes} bytes."
+                                    )
+                                chunks.append(decomp_chunk)
+
+                            data_to_feed = b""
+
+                            if getattr(decompressor, "eof", False):
+                                break
+                            if getattr(decompressor, "needs_input", True):
+                                break
+
+                    # Stream must reach EOF marker; complete JSON without intact compressed footer is rejected
+                    if not getattr(decompressor, "eof", False):
+                        raise IntegrityCheckError(
+                            "Compressed XZ archive stream is truncated: stream ended before reaching end-of-stream (EOF) marker."
+                        )
+
+                    # Reject trailing data or unauthorized concatenated streams
+                    unused = getattr(decompressor, "unused_data", b"")
+                    if has_trailing or (unused and unused.strip(b"\x00")):
+                        raise IntegrityCheckError(
+                            f"Unexpected trailing data or unauthorized concatenated stream after end of compressed stream."
+                        )
+
                 raw_bytes = b"".join(chunks)
-            except lzma.LZMAError as e:
+            except (lzma.LZMAError, EOFError) as e:
                 raise IntegrityCheckError(f"Corrupted or invalid XZ graph archive: {e}")
             try:
                 text_content = raw_bytes.decode("utf-8")
```

### 6.2 `tests/test_offline_adapters_synthetic.py`
```diff
--- TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_stage1_audit02/test_offline_adapters_synthetic.py
+++ tests/test_offline_adapters_synthetic.py
@@ -999,6 +999,166 @@
         with self.assertRaises(GraphSchemaError):
             BoundedMemoryGraphLoader.load_graph_archive(archive_path)
 
+    def test_bounded_graph_loader_rejects_truncated_xz_with_valid_json(self):
+        """Raise IntegrityCheckError when compressed XZ footer is truncated even if JSON is complete."""
+        graph_dict = {
+            "nodes": {
+                "node_1": {
+                    "node_id": "node_1",
+                    "title": "Case 1",
+                    "decision_date": "1990-01-01",
+                    "substantive_holding": "Holding 1",
+                    "thinking_trace": "Trace 1",
+                    "snippet": "Snippet 1",
+                },
+            },
+            "edges": [],
+            "total_nodes": 1,
+            "total_edges": 0,
+        }
+        json_bytes = json.dumps(graph_dict).encode("utf-8")
+        xz_bytes = lzma.compress(json_bytes)
+        # Truncate the final 12 bytes (XZ stream footer)
+        truncated_bytes = xz_bytes[:-12]
+        archive_path = self.temp_dir / "truncated_footer.json.xz"
+        archive_path.write_bytes(truncated_bytes)
+
+        with self.assertRaises(IntegrityCheckError) as ctx:
+            BoundedMemoryGraphLoader.load_graph_archive(archive_path)
+        self.assertIn("truncated", str(ctx.exception).lower())
+
+    def test_bounded_graph_loader_rejects_trailing_data(self):
+        """Raise IntegrityCheckError when unexpected trailing data follows compressed stream."""
+        graph_dict = {
+            "nodes": {
+                "node_1": {
+                    "node_id": "node_1",
+                    "title": "Case 1",
+                    "decision_date": "1990-01-01",
+                    "substantive_holding": "Holding 1",
+                    "thinking_trace": "Trace 1",
+                    "snippet": "Snippet 1",
+                },
+            },
+            "edges": [],
+            "total_nodes": 1,
+            "total_edges": 0,
+        }
+        json_bytes = json.dumps(graph_dict).encode("utf-8")
+        xz_bytes = lzma.compress(json_bytes)
+        # Append unauthorized trailing data
+        trailing_archive = self.temp_dir / "trailing_junk.json.xz"
+        trailing_archive.write_bytes(xz_bytes + b"\x00\x00UNAUTHORIZED_TRAILING_STREAM")
+
+        with self.assertRaises(IntegrityCheckError) as ctx:
+            BoundedMemoryGraphLoader.load_graph_archive(trailing_archive)
+        self.assertIn("trailing data", str(ctx.exception).lower())
+
+    def test_bounded_graph_loader_enforces_max_length_on_decompressor(self):
+        """Verify that BoundedMemoryGraphLoader passes bounded max_length to decompressor on every call."""
+        graph_dict = {
+            "nodes": {
+                "node_1": {
+                    "node_id": "node_1",
+                    "title": "Case 1",
+                    "decision_date": "1990-01-01",
+                    "substantive_holding": "Holding 1",
+                    "thinking_trace": "Trace 1",
+                    "snippet": "Snippet 1",
+                },
+            },
+            "edges": [],
+            "total_nodes": 1,
+            "total_edges": 0,
+        }
+        json_bytes = json.dumps(graph_dict).encode("utf-8")
+        xz_bytes = lzma.compress(json_bytes)
+        archive_path = self.temp_dir / "recording_graph.json.xz"
+        archive_path.write_bytes(xz_bytes)
+
+        recorded_max_lengths = []
+
+        class RecordingDecompressor:
+            def __init__(self, memlimit=None):
+                self._real = lzma.LZMADecompressor(memlimit=memlimit)
+
+            def decompress(self, data, max_length=-1):
+                recorded_max_lengths.append(max_length)
+                return self._real.decompress(data, max_length=max_length)
+
+            @property
+            def eof(self):
+                return self._real.eof
+
+            @property
+            def unused_data(self):
+                return self._real.unused_data
+
+            @property
+            def needs_input(self):
+                return self._real.needs_input
+
+        nodes, edges, audit = BoundedMemoryGraphLoader.load_graph_archive(
+            archive_path=archive_path,
+            decompressor_factory=lambda: RecordingDecompressor(),
+        )
+        self.assertEqual(len(nodes), 1)
+        self.assertGreater(len(recorded_max_lengths), 0)
+        # Every decompress call must supply a positive bounded max_length
+        for ml in recorded_max_lengths:
+            self.assertIsInstance(ml, int)
+            self.assertGreater(ml, 0)
+            self.assertLessEqual(ml, 65536)
+
+    def test_bounded_graph_loader_rejects_highly_compressible_bomb_expansion(self):
+        """Raise BudgetExceededError on highly compressible expansion without unbounded memory allocation."""
+        # Highly repetitive payload: >500 KB uncompressed, compresses to ~2 KB
+        repeated_text = "Holding text with extensive repetition " * 15000
+        graph_dict = {
+            "nodes": {
+                "node_1": {
+                    "node_id": "node_1",
+                    "decision_date": "1990-01-01",
+                    "substantive_holding": repeated_text,
+                }
+            },
+            "edges": [],
+        }
+        raw_bytes = json.dumps(graph_dict).encode("utf-8")
+        self.assertGreater(len(raw_bytes), 500000)
+        xz_bytes = lzma.compress(raw_bytes)
+        self.assertLess(len(xz_bytes), 10000)
+
+        archive_path = self.temp_dir / "expansion_bomb.json.xz"
+        archive_path.write_bytes(xz_bytes)
+
+        # Ceiling of 20 KB: must halt before inflating all 500 KB into RAM
+        with self.assertRaises(BudgetExceededError):
+            BoundedMemoryGraphLoader.load_graph_archive(
+                archive_path=archive_path,
+                max_decompressed_bytes=20000,
+            )
+
+    def test_bounded_graph_loader_rejects_invalid_limits(self):
+        """Raise ConfigurationError when max_decompressed_bytes or decoder_memlimit are non-positive or non-integer."""
+        archive_path = self.temp_dir / "valid_dummy.json.xz"
+        archive_path.write_bytes(lzma.compress(b'{"nodes": {}, "edges": []}'))
+
+        for invalid_limit in (0, -1, "250MB", 12.5, None):
+            with self.assertRaises(ConfigurationError):
+                BoundedMemoryGraphLoader.load_graph_archive(
+                    archive_path=archive_path,
+                    max_decompressed_bytes=invalid_limit,
+                )
+
+        for invalid_mem in (0, -500, "128MB", 64.0):
+            with self.assertRaises(ConfigurationError):
+                BoundedMemoryGraphLoader.load_graph_archive(
+                    archive_path=archive_path,
+                    decoder_memlimit=invalid_mem,
+                )
+
 
 if __name__ == "__main__":
     unittest.main()
```

---

## 7. Carry-Forward Acknowledgment & Guardrails

We fully acknowledge Codex's carry-forward notes:
1. **Production Runtime Requirements:** Any subsequent production or runtime stage must bind exact embedding/cache/client configurations, verify authentic collection metric schema and corpus IDs prior to calls, and evaluate installed-version Chroma configuration variants.
2. **Isolation & Fallback Boundaries:** Legacy fixture corpus fallback must not read unrelated collection rows; three-way disposable parity is required at construction rather than relying solely on supplied manifests.
3. **Write Isolation:** Post-binding writes are strictly limited to the disposable copy and require explicit mutation evidence.
4. **Gate C Enforced:** No real stores, real models, real knowledge graphs, downloads, API keys, credentials, or manuscript modifications were utilized or authorized during this turn. Gate C remains sealed.
