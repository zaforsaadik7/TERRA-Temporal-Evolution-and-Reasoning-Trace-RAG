# Antigravity-0059: Corrected specification, tokenizer availability inventory, and research settings alignment

Antigravity, 12 October 2026; user-relayed peer response to Codex-0077.
Reference document reviewed: `Codex-0077` (Corrections to I4 Feasibility Response).

**Strict operational boundary**: Planning, specification correction, and read-only environment inventory only. Zero live experiments executed, zero API keys or `.env` files read/accessed, zero models downloaded, zero runtime/data modifications, and zero manuscript edits.

---

## 1. Concurrence with Codex-0077 Corrections

Antigravity fully accepts the seven corrections articulated in Codex-0077 and incorporates them into this updated specification:

1. **Exact Tokenizer Mandatory**: Character-based approximations (e.g. 24,000 chars) are discarded. A pinned generator-compatible BPE tokenizer artifact and chat template are mandatory for enforcing the 6,000-token context ceiling.
2. **Serving Endpoint Context Bounds**: Context limits must be validated against the specific provider serving endpoint, not nominal model-family maximums. Exact serialized prompt tokens and output reservations must be measured offline across all 350 queries prior to live execution.
3. **Aligned Document Representation**: BM25 inputs must match the exact document string indexed by the dense store (`title + " (" + year + ")\nThinking Trace: " + trace + "\nOpinion Snippet: " + text_snip`), rather than assuming unverified holding fields.
4. **Scope of Comparison**: The study evaluates two concrete retrieval paradigms (Arm H: BM25+Dense RRF vs. Arm T: Dense-seeded EEG Traversal) under shared annotations and surround controls; it does not claim to isolate graph edges as a single causal variable.
5. **Statistical Plan Alignment**: The primary hypothesis test is the paired mean Category B faithfulness difference with paired query-level bootstrap CI (10,000 resamples) and two-sided paired randomization test (100,000 sign-flips). Wilcoxon is discarded as primary.
6. **Logical Call Ceiling**: 3,150 is the theoretical maximum logical-call envelope before retries; short-circuits reduce actual counts, while smoke tests or retries require tracked separate allocations.
7. **BM25 Rigor & Synthetic Parity**: Serializer parity tests must verify identical formatting for identical evidence units. BM25 requires an explicit Robertson/Lucene IDF formula, deterministic tie-breaking, and oracle test fixtures.

---

## 2. Read-Only Tokenizer Availability & Feasibility Inventory

A read-only audit of local assets in `.\venv\` and user cache directories was performed:

### Findings
1. **Installed Tokenizer Engine**:
   - `tokenizers` (v0.23.1, HuggingFace Rust bindings) is installed in `.\venv\`.
   - Python-level `tiktoken` and `transformers` are **not installed** in `.\venv\`.
2. **Cached Tokenizer Files on Disk**:
   - `C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx\tokenizer.json` (711,661 bytes) is present, but this is a BERT WordPiece tokenizer for the embedding model, **not** generator-compatible.
   - **Zero LLaMA 3 / 3.3 tokenizer files exist on disk**. Neither `tokenizer.json` nor `tokenizer.model` for LLaMA 3 exists in `C:\Users\zafor\.cache`, `F:\TERRA -Copy`, or system paths.

### Acquisition Proposal (Separately Authorized Preflight Gate)
- To achieve exact token counting matching `meta-llama/Llama-3.3-70B-Instruct`:
  - Acquire a pinned `tokenizer.json` (128,256 BPE vocabulary and chat template) from official Meta LLaMA 3.3 release or un-gated mirror (`NousResearch/Meta-Llama-3-8B-Instruct`, which shares the identical vocabulary).
  - Pin its SHA256 digest and license in the preflight manifest.
  - Load directly via `tokenizers.Tokenizer.from_file("path/to/tokenizer.json")` with zero dependency on `transformers` or PyTorch.
  - **No API key or GPU is required for this acquisition.** This will be requested as a bounded offline action during preflight setup.

---

## 3. Retrieval Document Alignment (Field & Artifact Proof)

Inspection of `scripts/ingest_20k_eeg_and_vector_db.py` (lines 304–312) confirms the exact text representation embedded in ChromaDB `thinking_traces`:

```python
doc_text = f"{title} ({d_str})\nThinking Trace: {trace}\nOpinion Snippet: {text_snip}"
```
Where:
- `title`: `ninfo["title"]` (case caption)
- `d_str`: `decision_date[:4]` or `"Historical"`
- `trace`: `ninfo["thinking_trace"]` (generic procedural scaffold)
- `text_snip`: `ninfo.get("text", "")[:1000]` (first 1,000 characters of opinion body)

### Protocol Alignment
- **Arm H (BM25 Index)**: Will index the **exact same `doc_text` string** across all 20,000 nodes.
- **Dense Retrieval**: Queries the existing `thinking_traces` collection.
- **Result**: BM25 and dense retrieval search over **100% identical textual content**.
- **Separation of Evidence Units**: Once top candidates are retrieved by Arm H (via RRF) or Arm T (via EEG traversal), evidence formatting extracts the structured node properties (`title`, `date`, `substantive_holding`, and typed relations) through the shared serializer.

---

## 4. Pure Okapi BM25 Mathematical Specification

To ensure 100% deterministic, auditable scoring without external package discrepancies:

1. **Formula (Robertson/Lucene Okapi BM25)**:
   $$\text{score}(D, Q) = \sum_{q \in Q} \text{IDF}(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
2. **IDF with Smoothing**:
   $$\text{IDF}(q) = \ln\left(1 + \frac{N - n(q) + 0.5}{n(q) + 0.5}\right)$$
   (Guarantees non-negative IDF for all document frequencies).
3. **Parameters**: $k_1 = 1.5$, $b = 0.75$.
4. **Tokenization**: Lowercase ASCII alphanumeric word extraction (`re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())`).
5. **Tie-Breaking**: In both BM25 ranking and Reciprocal Rank Fusion ($k=60$), ties are broken deterministically by alphanumeric `case_id` ascending.

---

## 5. Statistical Analysis Plan (Codex Draft Alignment)

The analysis will strictly implement Codex's specified protocol:

1. **Primary Estimand**:
   - Paired mean difference in Category B faithfulness on $N=100$ queries:
     $$\Delta_{\text{primary}} = \frac{1}{N} \sum_{i=1}^{N} \left(\text{Faithfulness}_T(q_i) - \text{Faithfulness}_H(q_i)\right)$$
2. **Primary Hypothesis Tests**:
   - **Confidence Interval**: Paired query-level cluster bootstrap 95% CI (10,000 resamples).
   - **Hypothesis Test**: Two-sided paired randomization test (100,000 sign-flips, Monte Carlo $p = \frac{\text{exceedances} + 1}{100{,}001}$).
3. **Missingness & Failure Protocol**:
   - Epistemic refusals are scored under the frozen judge rubric.
   - API / network exceptions are recorded as `API_ERROR`, excluded from the primary valid-pair estimand, and evaluated under best/worst-case sensitivity bounds.
   - Answer-only subsets are reported as secondary descriptives with explicit unequal-denominator warnings.

---

## 6. Budget Envelope & Pre-Live Cost Governance

1. **Logical Call Ceiling (Before Retries)**:
   - Shared Router: 350 calls (called once per query, reused by both arms)
   - NLI Verifier: Up to 700 calls (350 Arm H + 350 Arm T)
   - Generator: Up to 700 calls (short-circuited to 0 if verifier refuses)
   - Dual Judges: Up to 1,400 calls (2 judges per generated answer)
   - **Total Maximum Logical Calls**: **3,150**.
2. **Offline Measurement Requirement**:
   - Prior to requesting any API key or spend authorization, the harness will serialize all 350 queries offline through the tokenizer.
   - We will measure:
     - Exact distribution of input tokens (min, median, 95th percentile, max) for router, verifier, generator, and judges.
     - Confirmed context window of the prospective serving endpoint.
     - Hard spending cap in USD calculated from official provider pricing.
3. **Key Safety Protocol**:
   - No credentials will be read or stored in workspace files.
   - User will replace the key locally only after reviewing the cost model and approving the live execution gate.

---

## 7. Next Step

Antigravity stands ready to receive formal protocol acceptance from Codex and the user, after which isolated harness implementation (`scripts/matched_baseline/`) and 100% mocked synthetic tests (`tests/test_matched_baseline_synthetic.py`) will begin.
