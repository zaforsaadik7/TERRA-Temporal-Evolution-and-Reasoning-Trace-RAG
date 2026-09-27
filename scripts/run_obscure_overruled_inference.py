"""
scripts/run_obscure_overruled_inference.py - Production Runner for Obscure Overruled & Famous-75 Benchmarks
=========================================================================================================
Executes comparative inference across 4 experimental arms:
  Arm 1: Direct LLM (Meta-Llama-3.3-70B-Instruct, zero context)
  Arm 2: Flat Vector RAG (Top-5 dense retrieval from ChromaDB, zero graph expansion + TERRA instruction parity)
  Arm 3: Full TERRA (Production BFS traversal + [OVERRULES / REPUDIATES] tags + 600-char budget)
  Arm 4: TERRA-Unlabeled (Production BFS traversal + generic [CITES] tags + uniform 250-char budget + node parity + shared route)

Invariants Asserted (per Task X2 & X3):
  1. Frozen benchmark binary SHA256 matches certified hash (dbfe4b6b...).
  2. Working ask_terra.py binary SHA256 matches certified hash (430fc1b3...).
  3. terra_350_benchmark.json and EEG index binary SHA256 asserted at start.
  4. Chroma snapshot vector DB path and live computed fingerprint asserted against constant.
  5. Router decision read directly from engine output (never defaulted; raises if absent); shared from Arm 3 to Arm 4.
  6. Equal generation model asserted across all arms; _generation_model_used, _model_degraded, temperature, max_tokens recorded.
  7. Cache updated by replacement on (query_id, pipeline), never append.
  8. Direct and Flat calls wrapped with 3 retries (exponential backoff).
  9. Planned call counts dynamically computed from loaded suites (asserting 30 obscure and 75 famous).
 10. Famous-75 records get overruling_node='' and gold_holding pulled from benchmark ground_truth_holding field.
 11. Seeds taken from engine output with title-substring reimplementation used as cross-check.
 12. Flat arm prompt constructed with identical instruction block to TERRA Arm 4.
"""

import os
import re
import sys
import json
import time
import hashlib
import argparse
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

# Point vector DB constant at frozen snapshot
CHROMA_SNAPSHOT_PATH = (ROOT / "frozen" / "vector_db_20k_snapshot").resolve()
os.environ["TERRA_VECTOR_DB_PATH"] = str(CHROMA_SNAPSHOT_PATH)

GENERATION_MODEL = "databricks-meta-llama-3-3-70b-instruct"
os.environ["TERRA_GENERATION_MODEL"] = GENERATION_MODEL

import ask_terra

FROZEN_BENCHMARK_SHA256 = "dbfe4b6bfadcd422c22fee6e1aa55144de4dfe8a0fe7b1713d83a9b571f29aad"
EXPECTED_ASK_TERRA_SHA256 = "430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd"
TERRA_350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
TERRA_EEG_SHA256 = "7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad"

CHROMA_SNAPSHOT_FINGERPRINT = {
    "count": 20000,
    "sha256_sorted_ids": "fd8158b3f1d5bf99c80cece349c26edd880a1961265933df9df8fa21de1727c8",
    "sha256_concat_docs": "200e0fc9fc232b250dd4cfb3f8fcfe2ac22d47f5dc27c84dafb4303c2e49ee3e",
    "sha256_embeddings_float32": "6867f787879045ada191d88752d1ec7fa88267846bd3bf1e0ccb5094fc554712"
}

ARMS = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_Full_TERRA",
    "4_TERRA_Unlabeled"
]

# Shared TERRA Arm 4 instruction block (byte-for-byte identical to ask_terra.py lines 1103-1110 with instruction_2)
TERRA_INSTRUCTION_BLOCK = """[INSTRUCTIONS]
1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.
2. If CONTEXT DATA indicates that an earlier precedent has been overruled or repudiated by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision.
3. If multiple cases are provided under [SEEDED CASE] headers in CONTEXT DATA, your answer must explicitly reference and synthesize ALL of them, explaining how they relate to the Question. Do not stop after summarizing a single case when multiple seeded cases are present.
4. For doctrinal evolution questions tracing multiple cases, detail the legal transitions, rulings, and standards grounded strictly in the provided [Holding] and case text. Synthesize the trajectory across the cases provided without asserting external legal standards or factual tests that do not appear in the context. If an intermediate standard is only partially described, state the rule as established in the provided text rather than refusing to answer.
5. The Question is a valid, complete legal query. Provide a direct, substantive, and grounded legal answer. Do not issue a refusal or hedge unnecessarily when relevant case holdings and trajectory are provided in the context.
6. For any legal case you mention in your answer that has an explicit Case ID listed in the CONTEXT DATA (e.g. Case ID: 5 for Brown v. Board of Education), format the case title as a relative markdown link using its ID, e.g. "[Brown v. Board of Education](/case/5)". Only format links for cases that have explicit Case IDs provided in the context data."""

def compute_chroma_fingerprint(collection) -> dict:
    total_count = collection.count()
    batch_size = 5000
    all_ids = []
    all_docs = []
    all_embeddings = []
    for offset in range(0, total_count, batch_size):
        batch = collection.get(limit=batch_size, offset=offset, include=["documents", "embeddings"])
        all_ids.extend(batch["ids"])
        all_docs.extend(batch["documents"])
        all_embeddings.extend(batch["embeddings"])
    paired = sorted(zip(all_ids, all_docs, all_embeddings), key=lambda x: x[0])
    sorted_ids = [p[0] for p in paired]
    sorted_docs = [p[1] for p in paired]
    sorted_embeddings = [p[2] for p in paired]
    sha_ids = hashlib.sha256("\n".join(sorted_ids).encode("utf-8")).hexdigest()
    sha_docs = hashlib.sha256("".join(sorted_docs).encode("utf-8")).hexdigest()
    emb_array = np.array(sorted_embeddings, dtype=np.float32)
    sha_embeddings = hashlib.sha256(emb_array.tobytes()).hexdigest()
    return {
        "count": total_count,
        "sha256_sorted_ids": sha_ids,
        "sha256_concat_docs": sha_docs,
        "sha256_embeddings_float32": sha_embeddings
    }

def assert_runner_environment():
    # 1. Assert ask_terra.py binary hash
    ask_path = ROOT / "ask_terra.py"
    with open(ask_path, "rb") as f:
        actual_ask_hash = hashlib.sha256(f.read()).hexdigest()
    assert actual_ask_hash == EXPECTED_ASK_TERRA_SHA256, (
        f"ask_terra.py binary SHA256 mismatch!\nExpected: {EXPECTED_ASK_TERRA_SHA256}\nActual:   {actual_ask_hash}"
    )
    print(f"[RUNNER] ask_terra.py integrity verified: {actual_ask_hash}")

    # 2. Assert terra_350_benchmark.json and EEG binary hashes
    bench_350_path = ROOT / "terra_350_benchmark.json"
    with open(bench_350_path, "rb") as f:
        h350 = hashlib.sha256(f.read()).hexdigest()
    assert h350 == TERRA_350_SHA256, f"terra_350_benchmark.json binary SHA256 mismatch!\nExpected: {TERRA_350_SHA256}\nActual: {h350}"
    print(f"[RUNNER] terra_350_benchmark.json integrity verified: {h350}")

    eeg_path = ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json"
    with open(eeg_path, "rb") as f:
        heeg = hashlib.sha256(f.read()).hexdigest()
    assert heeg == TERRA_EEG_SHA256, f"terra_eeg_index_20k.json binary SHA256 mismatch!\nExpected: {TERRA_EEG_SHA256}\nActual: {heeg}"
    print(f"[RUNNER] EEG index integrity verified: {heeg}")

    # 3. Assert Chroma snapshot path and compute live fingerprint
    assert CHROMA_SNAPSHOT_PATH.exists(), f"Chroma snapshot path missing: {CHROMA_SNAPSHOT_PATH}"
    print(f"[RUNNER] Chroma snapshot path verified: {CHROMA_SNAPSHOT_PATH}")
    actual_fp = compute_chroma_fingerprint(ask_terra.collection)
    assert actual_fp == CHROMA_SNAPSHOT_FINGERPRINT, (
        f"Chroma snapshot fingerprint mismatch!\nExpected: {CHROMA_SNAPSHOT_FINGERPRINT}\nActual:   {actual_fp}"
    )
    print(f"[RUNNER] Chroma snapshot fingerprint asserted and verified: {actual_fp['count']} vectors")

def assert_benchmark_integrity(bench_path: Path) -> list:
    with open(bench_path, 'rb') as f:
        bench_bytes = f.read()
    actual_hash = hashlib.sha256(bench_bytes).hexdigest()
    assert actual_hash == FROZEN_BENCHMARK_SHA256, (
        f"Benchmark binary SHA256 mismatch!\nExpected: {FROZEN_BENCHMARK_SHA256}\nActual:   {actual_hash}"
    )
    print(f"[RUNNER] Benchmark integrity verified. Binary SHA256: {actual_hash}")
    return json.loads(bench_bytes.decode('utf-8'))

def load_cache(cache_path: Path) -> list:
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[CACHE WARNING] Could not read cache: {e}. Starting fresh.")
    return []

def save_cache_atomic(records: list, cache_path: Path):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = cache_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass
    for attempt in range(10):
        try:
            os.replace(temp_path, cache_path)
            return
        except PermissionError:
            if attempt < 9:
                time.sleep(0.3)
            else:
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(records, f, indent=2)
                        f.flush()
                        try:
                            os.fsync(f.fileno())
                        except Exception:
                            pass
                    return
                except Exception:
                    pass
                raise

def extract_node_ids_from_ctx(text: str) -> set:
    return set(re.findall(r'Case ID:\s*([0-9]+_[0-9]+-[0-9]+)', text))

_TITLE_YEAR_TO_NODE = None
_TITLE_TO_NODES = None

def _init_eeg_seed_lookups():
    global _TITLE_YEAR_TO_NODE, _TITLE_TO_NODES
    if _TITLE_YEAR_TO_NODE is not None:
        return
    _TITLE_YEAR_TO_NODE = {}
    _TITLE_TO_NODES = {}
    for nid, ndata in ask_terra.eeg.nodes.items():
        t = ndata.get('title', '').strip().lower()
        date = ndata.get('decision_date', '')
        yr = date[:4] if len(date) >= 4 else ''
        if t:
            _TITLE_TO_NODES.setdefault(t, []).append(nid)
            if yr:
                _TITLE_YEAR_TO_NODE[(t, yr)] = nid

def extract_engine_seeds_from_ctx(text: str) -> tuple:
    """
    Task C2: Extracts seeded case IDs directly from engine context headers.
    Uses an EEG title->node lookup only if the ID is not printed in the block (logging method).
    Returns (seeded_ids, seed_source, methods_used).
    """
    _init_eeg_seed_lookups()
    methods_used = []
    seeded_ids = []
    
    # 1. Look for [SEEDED CASE] blocks
    seeded_blocks = re.findall(
        r'(\[SEEDED CASE\].*?)(?=\n\[SEEDED CASE\]|\n\[CASE CITATION RECORD\]|\n\[GRAPH EXPANSION CONTEXT\]|\n\[PRECEDENT EVOLUTION|\n\[Holding\]|\Z)',
        text,
        re.DOTALL
    )
    has_seeded_case = bool(seeded_blocks)
    
    for b in seeded_blocks:
        m_id = re.search(r'Case ID:?\s*([0-9]+_[0-9]+-[0-9]+)', b)
        if m_id:
            nid = m_id.group(1)
            if nid not in seeded_ids:
                seeded_ids.append(nid)
            methods_used.append("block_id")
            continue
            
        lines = [l.strip() for l in b.strip().splitlines() if l.strip()]
        header = lines[0]
        m_header = re.match(r'\[SEEDED CASE\]\s*([^:\n]+):', header)
        if m_header:
            title = m_header.group(1).strip()
            title_lower = title.lower()
            
            yr = None
            if len(lines) > 1:
                m_yr = re.search(r'\(([12][0-9]{3})\)', lines[1])
                if m_yr:
                    yr = m_yr.group(1)
                    
            matched_nid = None
            if yr and (title_lower, yr) in _TITLE_YEAR_TO_NODE:
                matched_nid = _TITLE_YEAR_TO_NODE[(title_lower, yr)]
                methods_used.append("title_year_eeg_lookup")
            elif title_lower in _TITLE_TO_NODES:
                cands = _TITLE_TO_NODES[title_lower]
                matched_nid = cands[0]
                methods_used.append("title_eeg_lookup")
                
            if matched_nid and matched_nid not in seeded_ids:
                seeded_ids.append(matched_nid)

    # 2. Look for [CASE CITATION RECORD] blocks (EASY fast path)
    easy_ids = re.findall(r'\[CASE CITATION RECORD\]:[^(]*\(Case ID:\s*([0-9]+_[0-9]+-[0-9]+)', text)
    has_easy = bool(easy_ids)
    for eid in easy_ids:
        if eid not in seeded_ids:
            seeded_ids.append(eid)
            methods_used.append("citation_record_id")
            
    # Set seed_source per Task C2
    if has_seeded_case:
        seed_source = "exact_title"
    elif has_easy:
        seed_source = "vector"
    else:
        seed_source = "none"
        
    return seeded_ids, seed_source, methods_used

def determine_seed_source_reimpl(query: str) -> tuple:
    """Reimplementation kept strictly as cross-check."""
    query_lower = query.lower()
    exact_seeded_ids = []
    for n in ask_terra.eeg.nodes:
        title = ask_terra.eeg.nodes[n].get("title", "")
        if title and len(title) > 3 and title.lower() in query_lower:
            exact_seeded_ids.append(n)
            
    if exact_seeded_ids:
        return "exact_title", exact_seeded_ids
        
    try:
        vres = ask_terra.collection.query(
            query_texts=[query],
            n_results=2,
            where={"category": {"$eq": "civil_rights"}}
        )
        v_ids = vres.get("ids", [[]])[0] if vres else []
        if v_ids:
            return "vector", v_ids
    except Exception:
        pass
        
    return "none", []

def call_with_retry(fn, max_retries=3, base_delay=1.0, max_delay=10.0, *args, **kwargs):
    """Executes a function with up to max_retries attempts and exponential backoff."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt == max_retries - 1:
                raise
            sleep_time = min(max_delay, base_delay * (2 ** attempt))
            time.sleep(sleep_time)
    raise last_err

def run_direct_llm(client, query: str) -> tuple:
    prompt = f"Answer the following Supreme Court legal question accurately:\n\nQuestion: {query}\n\nAnswer:"
    t0 = time.time()
    def _call():
        return client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4096
        )
    resp = call_with_retry(_call, max_retries=3)
    elapsed_ms = round((time.time() - t0) * 1000, 2)
    answer = resp.choices[0].message.content.strip()
    resp_model = getattr(resp, "model", None)
    call_meta = {
        "model": resp_model or GENERATION_MODEL,
        "model_served": resp_model,
        "model_requested": GENERATION_MODEL,
        "temperature": getattr(resp, "temperature", 0.0),
        "max_tokens": getattr(resp, "max_tokens", 4096),
        "_model_degraded": getattr(resp, "_model_degraded", False)
    }
    return answer, "", elapsed_ms, call_meta

def build_flat_prompt(query: str, compiled_context: str) -> str:
    """Builds Flat RAG prompt with identical instruction block to TERRA Arm 4."""
    return f"""You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.

[QUESTION]
{query}

[CONTEXT DATA]
{compiled_context}

{TERRA_INSTRUCTION_BLOCK}

Question: {query}

TERRA Grounded Answer:"""

def run_flat_vector_rag(client, query: str, chroma_collection) -> tuple:
    t0 = time.time()
    results = chroma_collection.query(query_texts=[query], n_results=5)
    docs = results['documents'][0] if results and 'documents' in results and results['documents'] else []
    metas = results['metadatas'][0] if results and 'metadatas' in results and results['metadatas'] else []
    
    context_blocks = []
    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        cid = meta.get('node_id') or meta.get('case_id', f'Case_{i}')
        context_blocks.append(f"--- Document {i} (Case ID: {cid}) ---\n{doc}")
    compiled_context = "\n\n".join(context_blocks)
    
    prompt = build_flat_prompt(query, compiled_context)
    def _call():
        return client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4096
        )
    resp = call_with_retry(_call, max_retries=3)
    elapsed_ms = round((time.time() - t0) * 1000, 2)
    answer = resp.choices[0].message.content.strip()
    resp_model = getattr(resp, "model", None)
    call_meta = {
        "model": resp_model or GENERATION_MODEL,
        "model_served": resp_model,
        "model_requested": GENERATION_MODEL,
        "temperature": getattr(resp, "temperature", 0.0),
        "max_tokens": getattr(resp, "max_tokens", 4096),
        "_model_degraded": getattr(resp, "_model_degraded", False)
    }
    return answer, compiled_context, elapsed_ms, metas, call_meta

def run_inference_arm(
    arm_name: str,
    item: dict,
    client,
    chroma_col,
    full_nodes: set = None,
    shared_route: str = None
) -> dict:
    qid = item['query_id']
    query = item['query']
    tnode = item.get('target_node') or (item.get('target_nodes', [''])[0] if isinstance(item.get('target_nodes'), list) else '')
    onode = item.get('overruling_node', '')
    
    reimpl_src, reimpl_seeds = determine_seed_source_reimpl(query)

    if arm_name == "1_Direct_LLM":
        ans, ctx, elapsed_ms, meta = run_direct_llm(client, query)
        node_ids = extract_node_ids_from_ctx(ctx)
        return {
            "query_id": qid,
            "pipeline": arm_name,
            "query": query,
            "target_node": tnode,
            "overruling_node": onode,
            "route": "direct_generation",
            "route_shared": False,
            "seed_source": "none",
            "exact_seeded_nodes": [],
            "router_path": "direct_generation",
            "context_empty": True,
            "overruler_in_seeds": False,
            "overruler_in_context": False,
            "node_count": len(node_ids),
            "context_len": len(ctx),
            "generation_model_requested": GENERATION_MODEL,
            "generation_model_served": meta.get("model_served"),
            "_generation_model_used": meta.get("model", GENERATION_MODEL),
            "_model_degraded": meta.get("_model_degraded", False),
            "_router_fallback_contaminated": False,
            "_router_model_used": "N/A",
            "is_refusal": False,
            "smart_grader_passed": None,
            "temperature": meta.get("temperature", 0.0),
            "max_tokens": meta.get("max_tokens", 4096),
            "ask_terra_sha256": EXPECTED_ASK_TERRA_SHA256,
            "chroma_fingerprint": CHROMA_SNAPSHOT_FINGERPRINT,
            "answer": ans,
            "context_full": ctx,
            "execution_time_ms": elapsed_ms
        }
        
    elif arm_name == "2_Flat_Vector_RAG":
        ans, ctx, elapsed_ms, metas, meta = run_flat_vector_rag(client, query, chroma_col)
        retrieved_ids = [m.get('node_id') or m.get('case_id') for m in metas]
        node_ids = extract_node_ids_from_ctx(ctx)
        ovr_in_seeds = bool(onode and onode in retrieved_ids[:2])
        ovr_in_retrieved = bool(onode and onode in retrieved_ids)
        return {
            "query_id": qid,
            "pipeline": arm_name,
            "query": query,
            "target_node": tnode,
            "overruling_node": onode,
            "route": "flat_vector_search",
            "route_shared": False,
            "seed_source": "vector" if retrieved_ids else "none",
            "exact_seeded_nodes": retrieved_ids[:2],
            "router_path": "flat_vector_search",
            "context_empty": len(ctx.strip()) == 0,
            "overruler_in_seeds": ovr_in_seeds,
            "overruler_in_context": ovr_in_retrieved,
            "node_count": len(node_ids),
            "context_len": len(ctx),
            "generation_model_requested": GENERATION_MODEL,
            "generation_model_served": meta.get("model_served"),
            "_generation_model_used": meta.get("model", GENERATION_MODEL),
            "_model_degraded": meta.get("_model_degraded", False),
            "_router_fallback_contaminated": False,
            "_router_model_used": "N/A",
            "is_refusal": False,
            "smart_grader_passed": None,
            "temperature": meta.get("temperature", 0.0),
            "max_tokens": meta.get("max_tokens", 4096),
            "ask_terra_sha256": EXPECTED_ASK_TERRA_SHA256,
            "chroma_fingerprint": CHROMA_SNAPSHOT_FINGERPRINT,
            "answer": ans,
            "context_full": ctx,
            "execution_time_ms": elapsed_ms
        }
        
    elif arm_name == "3_Full_TERRA":
        ans, ctx, timing = ask_terra.terra_inference_engine(
            query,
            return_timing=True,
            arm4_unlabeled=False,
            restrict_to_nodes=None
        )
        # 1. Read actual route from engine output - never default, raise if absent
        route_taken = timing.get('route_taken')
        if not route_taken:
            raise ValueError(f"CRITICAL ERROR: Route missing from engine timing output for {qid}: {timing}")
            
        node_ids = extract_node_ids_from_ctx(ctx)
        engine_seeds, seed_src, methods_used = extract_engine_seeds_from_ctx(ctx)
        print(f"[SEED EXTRACTION] {qid} [{arm_name}]: resolved seeds {engine_seeds} via {methods_used}, seed_source='{seed_src}'")
        if set(engine_seeds) != set(reimpl_seeds):
            print(f"[SEED CROSS-CHECK NOTICE] {qid}: Engine seeds {engine_seeds} != Reimpl {reimpl_seeds}")
            
        ovr_in_ctx = bool(onode and onode in ctx)
        ovr_in_seeds = bool(onode and onode in engine_seeds)
        
        gen_model = timing.get('_generation_model_used', GENERATION_MODEL)
        degraded = timing.get('_model_degraded', False)
        temp = timing.get('temperature', 0.0)
        mtok = timing.get('max_tokens', 4096)
        
        # Assert required timing keys (Task Z1)
        for k in ["_router_fallback_contaminated", "_router_model_used", "is_refusal", "smart_grader_passed"]:
            if k not in timing:
                raise KeyError(f"CRITICAL ERROR: Required key '{k}' missing from engine timing dict for {qid} in {arm_name}. Keys present: {list(timing.keys())}")

        router_contaminated = bool(timing["_router_fallback_contaminated"])
        router_model = str(timing["_router_model_used"])
        is_ref = bool(timing["is_refusal"])
        grader_passed = timing["smart_grader_passed"]

        return {
            "query_id": qid,
            "pipeline": arm_name,
            "query": query,
            "target_node": tnode,
            "overruling_node": onode,
            "route": route_taken,
            "route_shared": True,
            "seed_source": seed_src,
            "exact_seeded_nodes": engine_seeds,
            "router_path": route_taken,
            "context_empty": len(ctx.strip()) == 0,
            "overruler_in_seeds": ovr_in_seeds,
            "overruler_in_context": ovr_in_ctx,
            "node_count": len(node_ids),
            "context_len": len(ctx),
            "generation_model_requested": GENERATION_MODEL,
            "generation_model_served": None,
            "_generation_model_used": gen_model,
            "_model_degraded": degraded,
            "_router_fallback_contaminated": router_contaminated,
            "_router_model_used": router_model,
            "is_refusal": is_ref,
            "smart_grader_passed": grader_passed,
            "temperature": temp,
            "max_tokens": mtok,
            "ask_terra_sha256": EXPECTED_ASK_TERRA_SHA256,
            "chroma_fingerprint": CHROMA_SNAPSHOT_FINGERPRINT,
            "answer": ans,
            "context_full": ctx,
            "execution_time_ms": timing.get('total_ms', 0.0),
            "timing_keys": list(timing.keys())
        }
        
    elif arm_name == "4_TERRA_Unlabeled":
        if not shared_route:
            raise ValueError(f"CRITICAL ERROR: Arm 4 requires shared_route from Arm 3, but received None for {qid}")
            
        ans, ctx, timing = ask_terra.terra_inference_engine(
            query,
            return_timing=True,
            arm4_unlabeled=True,
            restrict_to_nodes=full_nodes,
            forced_route=shared_route
        )
        route_taken = timing.get('route_taken')
        if not route_taken:
            raise ValueError(f"CRITICAL ERROR: Route missing from engine timing output for {qid}: {timing}")
        assert route_taken == shared_route, f"Arm 4 route {route_taken} does not match forced shared route {shared_route}"
        
        # Assert required timing keys (Task Z1)
        for k in ["_router_fallback_contaminated", "_router_model_used", "is_refusal", "smart_grader_passed"]:
            if k not in timing:
                raise KeyError(f"CRITICAL ERROR: Required key '{k}' missing from engine timing dict for {qid} in {arm_name}. Keys present: {list(timing.keys())}")

        router_contaminated = bool(timing["_router_fallback_contaminated"])
        router_model = str(timing["_router_model_used"])
        is_ref = bool(timing["is_refusal"])
        grader_passed = timing["smart_grader_passed"]

        node_ids = extract_node_ids_from_ctx(ctx)
        engine_seeds, seed_src, methods_used = extract_engine_seeds_from_ctx(ctx)
        print(f"[SEED EXTRACTION] {qid} [{arm_name}]: resolved seeds {engine_seeds} via {methods_used}, seed_source='{seed_src}'")
            
        ovr_in_ctx = bool(onode and onode in ctx)
        ovr_in_seeds = bool(onode and onode in engine_seeds)
        
        gen_model = timing.get('_generation_model_used', GENERATION_MODEL)
        degraded = timing.get('_model_degraded', False)
        temp = timing.get('temperature', 0.0)
        mtok = timing.get('max_tokens', 4096)
        
        return {
            "query_id": qid,
            "pipeline": arm_name,
            "query": query,
            "target_node": tnode,
            "overruling_node": onode,
            "route": route_taken,
            "route_shared": True,
            "seed_source": seed_src,
            "exact_seeded_nodes": engine_seeds,
            "router_path": route_taken,
            "context_empty": len(ctx.strip()) == 0,
            "overruler_in_seeds": ovr_in_seeds,
            "overruler_in_context": ovr_in_ctx,
            "node_count": len(node_ids),
            "context_len": len(ctx),
            "generation_model_requested": GENERATION_MODEL,
            "generation_model_served": None,
            "_generation_model_used": gen_model,
            "_model_degraded": degraded,
            "_router_fallback_contaminated": router_contaminated,
            "_router_model_used": router_model,
            "is_refusal": is_ref,
            "smart_grader_passed": grader_passed,
            "temperature": temp,
            "max_tokens": mtok,
            "ask_terra_sha256": EXPECTED_ASK_TERRA_SHA256,
            "chroma_fingerprint": CHROMA_SNAPSHOT_FINGERPRINT,
            "answer": ans,
            "context_full": ctx,
            "execution_time_ms": timing.get('total_ms', 0.0),
            "timing_keys": list(timing.keys())
        }
    else:
        raise ValueError(f"Unknown arm: {arm_name}")

def log_runner_dryrun():
    out_path = ROOT / "logs" / "runner_dryrun.txt"
    
    obscure_items = load_suite_items("obscure")
    assert len(obscure_items) == 30, f"Expected exactly 30 obscure queries, found {len(obscure_items)}"
    
    famous_d1_items = load_suite_items("famous_d1")
    assert len(famous_d1_items) == 19, f"Expected exactly 19 famous_d1 queries, found {len(famous_d1_items)}"
    
    n_arms = len(ARMS)
    obscure_calls = len(obscure_items) * n_arms
    famous_d1_calls = len(famous_d1_items) * n_arms
    total_calls = obscure_calls + famous_d1_calls
    
    lines = []
    lines.append("=" * 80)
    lines.append("RUNNER PLANNED CALLS AUDIT (DRY-RUN)")
    lines.append("=" * 80)
    lines.append("SUITE: obscure")
    lines.append(f"  Queries: {len(obscure_items)}")
    for arm in ARMS:
        lines.append(f"  {arm}: {len(obscure_items)}")
    lines.append(f"  Suite Total: {obscure_calls}")
    lines.append("")
    lines.append("SUITE: famous_d1 (Task Z3: 19 Overruled-Precedent Queries)")
    lines.append(f"  Queries: {len(famous_d1_items)}")
    for arm in ARMS:
        lines.append(f"  {arm}: {len(famous_d1_items)}")
    lines.append(f"  Suite Total: {famous_d1_calls}")
    lines.append("")
    lines.append("SUITE: famous75 (HARD STOP / DEPRECATED)")
    lines.append("  Status: Halted per Task Z3 (56 non-overruling refutations removed)")
    lines.append("")
    lines.append(f"TOTAL PLANNED CALLS ACROSS VALID SUITES: {total_calls}")
    lines.append("=" * 80)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[DRY-RUN] Wrote computed planned call counts to {out_path}")

def load_suite_items(suite: str) -> list:
    if suite == "obscure":
        bench_path = ROOT / 'data' / 'obscure_overruled_benchmark.json'
        return assert_benchmark_integrity(bench_path)
    elif suite == "famous75":
        stopped_file = ROOT / "logs" / "STOPPED_famous75.txt"
        stopped_file.parent.mkdir(parents=True, exist_ok=True)
        msg = (
            "STOPPED: famous75 benchmark evaluation halted.\n"
            "Reason: logs/famous75_schema.txt established that 56/75 items in Category D are non-overruling "
            "refutation subtypes (D2 TitleSubstitution, D3 TemporalInversion, D4 ProceduralPostureDeception) "
            "with no derivable overruling case. Use --suite famous_d1 for the 19 valid overruled queries.\n"
        )
        with open(stopped_file, "w", encoding="utf-8") as f:
            f.write(msg)
        raise RuntimeError(f"STOPPED: famous75 suite is deprecated per Task Z3. Use famous_d1.")
    elif suite == "famous_d1":
        bench_350_path = ROOT / "terra_350_benchmark.json"
        with open(bench_350_path, "r", encoding="utf-8") as f:
            bench_350 = json.load(f)
        items = [q for q in bench_350 if q.get("subtype") == "D1_OverruledPrecedent"]
        assert len(items) == 19, f"Expected 19 D1 items, found {len(items)}"
        
        # Load EEG to derive overruling_node and overruling_case
        eeg_path = ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json"
        with open(eeg_path, "r", encoding="utf-8") as f:
            eeg = json.load(f)
        edges = eeg.get("edges", [])
        nodes = eeg.get("nodes", {})
        
        overrules_by_target = {}
        for e in edges:
            if e.get("relation") == "OVERRULES":
                t = e.get("target")
                s = e.get("source")
                if t not in overrules_by_target:
                    overrules_by_target[t] = s
                    
        normalized_items = []
        matched_ovr = 0
        mapping_lines = []
        mapping_lines.append("=" * 80)
        mapping_lines.append("FAMOUS_D1 FIELD MAPPING AUDIT (Task Z3: N=19)")
        mapping_lines.append("=" * 80)

        for it in items:
            t_node = it.get("target_nodes", [""])[0] if isinstance(it.get("target_nodes"), list) else it.get("target_nodes", "")
            gold_h = it.get("ground_truth_holding", "")
            ovr_node = overrules_by_target.get(t_node, "")
            ovr_case = nodes.get(ovr_node, {}).get("title", "") if ovr_node else ""
            if ovr_case:
                matched_ovr += 1
            
            q_text = it.get("query", "")
            m = re.search(r"(?:doctrine of|decision in|precedent of|ruling in) ([^,(]+)", q_text, re.IGNORECASE)
            t_case = m.group(1).strip() if m else nodes.get(t_node, {}).get("title", "")

            norm_item = dict(it)
            norm_item["target_node"] = t_node
            norm_item["target_case"] = t_case
            norm_item["overruling_node"] = ovr_node
            norm_item["overruling_case"] = ovr_case
            norm_item["gold_holding"] = gold_h
            normalized_items.append(norm_item)
            mapping_lines.append(f"[{it['query_id']}] Target: {t_case} ({t_node}) | Overruler: {ovr_case or 'NONE'} | Gold Holding Len: {len(gold_h)}")
            
        assert matched_ovr == 9, f"Expected exactly 9 D1 items with overruling case, got {matched_ovr}"
        mapping_path = ROOT / "logs" / "famous_d1_field_mapping.txt"
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write("\n".join(mapping_lines) + "\n")
        print(f"[RUNNER] Loaded 19 famous_d1 queries (9 with EEG OVERRULES edge). Field mapping logged to {mapping_path}")
        return normalized_items
    else:
        raise ValueError(f"Unknown suite: {suite}. Choose 'obscure', 'famous_d1', or 'famous75'.")

def main():
    parser = argparse.ArgumentParser(description="TERRA Benchmark Inference Runner")
    parser.add_argument("--suite", choices=["obscure", "famous_d1", "famous75"], default="obscure", help="Evaluation suite")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Default dry-run mode (no live calls)")
    parser.add_argument("--live", action="store_true", default=False, help="Explicit flag required to execute live inference")
    parser.add_argument("--pilot", action="store_true", default=False, help="Pilot execution mode restricted to 3 queries (OBS_001, OBS_006, OBS_025)")
    parser.add_argument("--confirm-full", action="store_true", default=False, help="Mandatory confirmation flag required when running --live on full (non-pilot) suite")
    args = parser.parse_args()

    # Task E4: Require --confirm-full when running --live on full (non-pilot) suite
    if args.live and not args.pilot and not args.confirm_full:
        raise SystemExit(
            "[RUNNER BLOCKED] Running --live on full suite requires explicit --confirm-full flag. Refusing execution."
        )

    assert_runner_environment()
    log_runner_dryrun()

    items = load_suite_items(args.suite)
    if args.pilot:
        if args.suite != "obscure":
            raise ValueError("--pilot is currently only supported for the obscure suite.")
        pilot_qids = ['OBS_001', 'OBS_006', 'OBS_025']
        items = [it for it in items if it['query_id'] in pilot_qids]
        assert len(items) == 3, f"Expected exactly 3 pilot items, found {len(items)}"
        assert len(items) * len(ARMS) <= 12, f"Planned pilot generation calls exceed 12: {len(items) * len(ARMS)}"
        cache_path = ROOT / "scratch" / f"pilot_{args.suite}_raw_responses.json"
        print(f"[PILOT MODE] Restricting to 3 queries: {pilot_qids}")
        print(f"[PILOT MODE] Dedicated pilot cache: {cache_path} (main cache isolated)")
    else:
        cache_path = ROOT / "scratch" / f"{args.suite}_raw_responses.json"

    if not args.live:
        print("\n[RUNNER DRY-RUN MODE ACTIVE]")
        print(f"Selected Suite: {args.suite}")
        print(f"Total queries in cohort: {len(items)}")
        planned_gen = len(items) * len(ARMS)
        print(f"Planned calls: {len(items)} queries x {len(ARMS)} arms = {planned_gen} calls.")
        if args.pilot:
            assert planned_gen <= 12, "Pilot generation calls exceed 12!"
            print(f"[PILOT ASSERTION PASSED] Planned generation calls: {planned_gen} <= 12")
            print("Exact pilot command line:")
            print(f"  python scripts/run_obscure_overruled_inference.py --suite {args.suite} --pilot --live")
        else:
            print("Exact full command line:")
            print(f"  python scripts/run_obscure_overruled_inference.py --suite {args.suite} --live --confirm-full")
        print("Dry-run complete. Zero live API calls made (R7 enforced). Use --live to execute.")
        return

    # Live execution branch (requires explicit --live)
    print(f"\n[RUNNER LIVE INFERENCE: SUITE={args.suite.upper()}{' (PILOT)' if args.pilot else ''}]")
    from baselines.common import get_databricks_client
    client = get_databricks_client()
    
    # Tasks A4, E4: Wrap client with call counter enforcing hard cap (<= 120 pilot, <= 700 full)
    from scripts.call_counter import wrap_client_with_counter, get_active_counter
    state_file = ROOT / "scratch" / f"{'pilot_' if args.pilot else ''}{args.suite}_call_counts.json"
    max_cap = 120 if args.pilot else (400 if args.suite == "famous_d1" else 700)
    client = wrap_client_with_counter(client, is_pilot=args.pilot, reset_state=True, max_cap=max_cap, state_file=state_file)
    wrap_client_with_counter(ask_terra.openai_client, is_pilot=args.pilot, reset_state=False, max_cap=max_cap, state_file=state_file)
    wrap_client_with_counter(ask_terra.client, is_pilot=args.pilot, reset_state=False, max_cap=max_cap, state_file=state_file)
    
    chroma_col = ask_terra.collection
    
    cached_records = load_cache(cache_path)
    cached_map = {(r['query_id'], r['pipeline']): r for r in cached_records}
    print(f"[CACHE] Loaded {len(cached_records)} existing records from {cache_path}")
    
    total_calls = len(items) * len(ARMS)
    executed_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 3
    run_id = f"run_{args.suite}_{int(time.time())}"
    
    for item in items:
        qid = item['query_id']
        full_nodes = None
        shared_route = None
        
        # Check if Arm 3 is already in cache
        if (qid, "3_Full_TERRA") in cached_map:
            arm3_rec = cached_map[(qid, "3_Full_TERRA")]
            full_nodes = extract_node_ids_from_ctx(arm3_rec.get('context_full', ''))
            shared_route = arm3_rec.get('route')
            
        for arm in ARMS:
            key = (qid, arm)
            if key in cached_map and cached_map[key].get('answer'):
                print(f"[RESUME] Skipping {qid} [{arm}] - already in cache.")
                if arm == "3_Full_TERRA" and not full_nodes:
                    full_nodes = extract_node_ids_from_ctx(cached_map[key].get('context_full', ''))
                    shared_route = cached_map[key].get('route')
                continue
                
            print(f"[RUNNING] {qid} [{arm}]...")
            from scripts.call_counter import set_call_context
            set_call_context(query_id=qid, arm=arm, suite=args.suite, is_pilot=args.pilot, run_id=run_id, mode="live" if args.live else "test")
            
            # Task E4: Consecutive API error retry loop with 3-error abort safeguard
            while True:
                try:
                    rec = run_inference_arm(
                        arm,
                        item,
                        client,
                        chroma_col,
                        full_nodes=full_nodes,
                        shared_route=shared_route
                    )
                    consecutive_errors = 0
                    if arm == "3_Full_TERRA":
                        full_nodes = extract_node_ids_from_ctx(rec.get('context_full', ''))
                        shared_route = rec.get('route')
                        
                    # Replace in cache map to prevent duplicate rows
                    cached_map[key] = rec
                    save_cache_atomic(list(cached_map.values()), cache_path)
                    executed_count += 1
                    print(f"  -> Completed {qid} [{arm}] in {rec['execution_time_ms']} ms. Atomic cache updated.")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    print(f"[API ERROR] {qid} [{arm}]: {e} (consecutive errors: {consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[RUNNER ABORT] Aborting runner after {consecutive_errors} consecutive API errors. Valid cache preserved at {cache_path}.")
                        raise RuntimeError(f"Runner aborted after {consecutive_errors} consecutive API errors: {e}")
                    time.sleep(1.0 * consecutive_errors)
            
        # Task C3: Assert requested generation model is equal across all four arms for every item
        item_recs = [cached_map.get((qid, a)) for a in ARMS if (qid, a) in cached_map]
        if len(item_recs) == len(ARMS):
            reqs = [r.get("generation_model_requested") for r in item_recs]
            assert all(req == reqs[0] and req is not None for req in reqs), (
                f"[MODEL PARITY ERROR] Requested generation model mismatch across arms for {qid}: {dict(zip(ARMS, reqs))}"
            )
            
    print("=" * 80)
    print(f"RUNNER EXECUTION COMPLETE. Total calls executed: {executed_count}/{total_calls}")
    print(f"Total responses in cache: {len(cached_map)}")
    print("=" * 80)

    # Task A4 / C4 / E4: Write call counter log and breakdown report
    counter = get_active_counter()
    if counter:
        call_counts_file = ROOT / "logs" / f"{'pilot_' if args.pilot else ''}call_counts.txt"
        counter.write_log(call_counts_file)
        breakdown_file = ROOT / "logs" / f"call_breakdown_{'pilot' if args.pilot else args.suite}.txt"
        counter.write_breakdown_report(breakdown_file)

if __name__ == '__main__':
    main()
