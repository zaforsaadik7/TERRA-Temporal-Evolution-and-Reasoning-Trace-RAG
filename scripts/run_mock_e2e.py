"""
scripts/run_mock_e2e.py - Task X4 Offline End-to-End Mock Test (No Network)
============================================================================
Runs all 4 experimental arms for OBS_001, OBS_006, OBS_025, and 2 famous queries.
Enforces:
  1. Socket guard (zero network calls).
  2. Router, generation, and judge calls patched with canned outputs.
  3. Strict assertions:
     - Record keys complete across all arms.
     - Route is not defaulted (read from engine timing).
     - Arm 4 route equals Arm 3 route.
     - Node set Arm 4 == Arm 3.
     - Empty-context item (OBS_006) yields context_empty=True.
     - A second run adds no duplicate rows (replacement idempotency).
Logs results to logs/mock_e2e.txt.
"""

import os
import sys
import json
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 1. Socket Guard to prevent any outbound network connections (Rule R7)
def socket_guard_connect(self, *args, **kwargs):
    raise RuntimeError("SOCKET GUARD ENFORCED: Outbound network call attempted during offline mock test (R7)!")
socket.socket.connect = socket_guard_connect
socket.create_connection = socket_guard_connect

# Point to snapshot vector DB
os.environ["TERRA_VECTOR_DB_PATH"] = str((ROOT / "frozen" / "vector_db_20k_snapshot").resolve())

import ask_terra
from scripts.run_obscure_overruled_inference import (
    run_inference_arm,
    load_suite_items,
    extract_node_ids_from_ctx,
    save_cache_atomic,
    load_cache,
    ARMS,
    GENERATION_MODEL
)

OUT_LOG = ROOT / "logs" / "mock_e2e.txt"
OUT_LOG_V2 = ROOT / "logs" / "mock_e2e_v2.txt"

# Tracking state for Task Y1 inspection
router_calls_by_query = {}
captured_generation_calls = []
current_execution_context = {"arm": None, "query_id": None}

# Mock Databricks / OpenAI client for Direct and Flat arms
class MockChatCompletionChoice:
    def __init__(self, content):
        self.message = type("msg", (), {"content": content})()

class MockChatCompletionResponse:
    def __init__(self, content, model=GENERATION_MODEL):
        self.choices = [MockChatCompletionChoice(content)]
        self.model = model
        self.temperature = 0.0
        self.max_tokens = 4096
        self._model_degraded = False

class MockCompletions:
    def create(self, model, messages, temperature=0.0, max_tokens=4096, **kwargs):
        call_info = {
            "arm": current_execution_context["arm"],
            "query_id": current_execution_context["query_id"],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "kwargs": kwargs,
            "messages_count": len(messages)
        }
        captured_generation_calls.append(call_info)
        prompt = messages[0]["content"] if messages else ""
        return MockChatCompletionResponse(f"Canned mock model response for: {prompt[:40]}...", model=model)

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    def __init__(self):
        self.chat = MockChat()

# Canned mock for ask_terra.generate_content_with_retry_openai
class MockCleanResponse:
    def __init__(self, text, model_used=GENERATION_MODEL):
        self.text = text
        self.model_used = model_used
        self.model = model_used
        self.temperature = 0.0
        self.max_tokens = 4096
        self.retry_sleep_ms = 0.0
        self._model_degraded = False

def mock_engine_generation(openai_client, model, contents, config=None, max_retries=5):
    call_info = {
        "arm": current_execution_context["arm"],
        "query_id": current_execution_context["query_id"],
        "model": model,
        "temperature": 0.0,
        "max_tokens": 4096,
        "kwargs": {"config": config, "contents_len": len(contents)}
    }
    captured_generation_calls.append(call_info)
    return MockCleanResponse(f"Canned TERRA grounded answer acknowledging overruling under modern doctrine.", model_used=model)

# Canned mock for router (Task Y1: designated EASY route for D001)
def mock_router(query, return_metadata=False, model_override=None):
    router_calls_by_query[query] = router_calls_by_query.get(query, 0) + 1
    # D001 (Plessy v. Ferguson) returns EASY; other queries return HARD
    if "D001" in query or "plessy v. ferguson" in query.lower():
        route = "EASY"
        reason = "Single landmark precedent query routed to fast path"
    else:
        route = "HARD"
        reason = "Complex doctrinal overrule query requiring deep citation graph reasoning"
    meta = {"router_model_used": "MOCK_ROUTER_OFFLINE", "fallback_contaminated": False}
    if return_metadata:
        return route, reason, meta
    return route

# Monkeypatch generation, router, and smart_grader in ask_terra
ask_terra.generate_content_with_retry_openai = mock_engine_generation
ask_terra.traffic_cop_router = mock_router
ask_terra.smart_grader = lambda user_query, retrieved_context: True

def run_mock_test():
    log_lines = []
    log_lines.append("=" * 100)
    log_lines.append("OFFLINE END-TO-END MOCK EXECUTION AUDIT (Task X4 & Y1)")
    log_lines.append("=" * 100)
    log_lines.append("Socket Guard: ACTIVE (Outbound network calls blocked)")

    mock_client = MockClient()
    chroma_col = ask_terra.collection

    # 1. Select items: OBS_001, OBS_006, OBS_025, and 2 famous queries (D001, D002)
    obscure_all = load_suite_items("obscure")
    famous_all = load_suite_items("famous_d1")

    target_obscure_ids = {"OBS_001", "OBS_006", "OBS_025"}
    selected_obscure = [it for it in obscure_all if it["query_id"] in target_obscure_ids]
    selected_famous = famous_all[:2] # D001, D002

    eval_items = selected_obscure + selected_famous
    log_lines.append(f"Selected evaluation cohort: {[it['query_id'] for it in eval_items]}")
    log_lines.append(f"Arms evaluated per query:   {ARMS}")
    log_lines.append("-" * 100)

    REQUIRED_RECORD_KEYS = {
        "query_id", "pipeline", "query", "target_node", "overruling_node",
        "route", "route_shared", "seed_source", "exact_seeded_nodes",
        "router_path", "context_empty", "overruler_in_seeds", "overruler_in_context",
        "node_count", "context_len", "_generation_model_used", "_model_degraded",
        "_router_fallback_contaminated", "_router_model_used", "is_refusal", "smart_grader_passed",
        "generation_model_requested", "generation_model_served",
        "temperature", "max_tokens", "ask_terra_sha256", "chroma_fingerprint",
        "answer", "context_full", "execution_time_ms"
    }

    mock_cache = {}
    mock_cache_file = ROOT / "scratch" / "mock_e2e_responses.json"

    # Execution Pass 1
    for it in eval_items:
        qid = it["query_id"]
        log_lines.append(f"\n>>> Executing Query: {qid} | {it['query'][:60]}...")
        
        arm_records = {}
        full_nodes = None
        shared_route = None

        # Execute Arm 3 first to capture nodes, route, and timing keys
        current_execution_context["arm"] = "3_Full_TERRA"
        current_execution_context["query_id"] = qid
        rec3 = run_inference_arm("3_Full_TERRA", it, mock_client, chroma_col)
        arm_records["3_Full_TERRA"] = rec3
        full_nodes = extract_node_ids_from_ctx(rec3["context_full"])
        shared_route = rec3["route"]

        # Log timing keys for Arm 3
        timing_keys_3 = rec3.get("timing_keys", [])
        log_lines.append(f"  [Engine Timing Keys] Arm 3: {sorted(list(timing_keys_3))}")
        assert "route_taken" in timing_keys_3, f"[{qid}] route_taken missing from engine timing keys: {timing_keys_3}"

        # Execute remaining arms
        for arm in ["1_Direct_LLM", "2_Flat_Vector_RAG", "4_TERRA_Unlabeled"]:
            current_execution_context["arm"] = arm
            current_execution_context["query_id"] = qid
            rec = run_inference_arm(
                arm, it, mock_client, chroma_col,
                full_nodes=full_nodes,
                shared_route=shared_route
            )
            arm_records[arm] = rec

        rec4 = arm_records["4_TERRA_Unlabeled"]
        timing_keys_4 = rec4.get("timing_keys", [])
        log_lines.append(f"  [Engine Timing Keys] Arm 4: {sorted(list(timing_keys_4))}")
        assert "route_taken" in timing_keys_4, f"[{qid}] route_taken missing from Arm 4 engine timing keys"

        # Store in cache
        for arm, rec in arm_records.items():
            mock_cache[(qid, arm)] = rec

        # Assertions per item
        for arm, rec in arm_records.items():
            # Check keys complete
            missing_keys = REQUIRED_RECORD_KEYS - set(rec.keys())
            assert not missing_keys, f"[{qid}][{arm}] Missing record keys: {missing_keys}"
            # Check generation model logged and equal (unless empty context safety gate)
            if rec["context_empty"]:
                assert rec["_generation_model_used"] in [GENERATION_MODEL, "SAFETY_GATE_EMPTY_CONTEXT"], f"[{qid}][{arm}] Unexpected model for empty context: {rec['_generation_model_used']}"
            else:
                assert rec["_generation_model_used"] == GENERATION_MODEL, f"[{qid}][{arm}] Generation model mismatch: {rec['_generation_model_used']} != {GENERATION_MODEL}"
            assert rec["temperature"] == 0.0, f"[{qid}][{arm}] Temperature not 0.0!"
            assert rec["max_tokens"] == 4096, f"[{qid}][{arm}] Max tokens not 4096!"

        # Route assertions & Task Y1(a) EASY route verification
        log_lines.append(f"  Arm 3 Route: {rec3['route']} | Arm 4 Route: {rec4['route']}")
        assert rec3["route"] in ["HARD", "EASY"], f"[{qid}] Route defaulted or invalid: {rec3['route']}"
        assert rec4["route"] == rec3["route"], f"[{qid}] Arm 4 route ({rec4['route']}) != Arm 3 route ({rec3['route']})"

        if qid == "D001":
            log_lines.append(f"  [TASK Y1(a) VERIFICATION] Query {qid} returned EASY route!")
            log_lines.append(f"  Arm 3 Route: {rec3['route']} == EASY | Arm 4 Route: {rec4['route']} == EASY")
            assert rec3["route"] == "EASY", f"[{qid}] Expected Arm 3 route EASY, got {rec3['route']}"
            assert rec4["route"] == "EASY", f"[{qid}] Expected Arm 4 route EASY, got {rec4['route']}"
            calls_for_query = router_calls_by_query.get(it["query"], 0)
            log_lines.append(f"  Router call count for query: {calls_for_query} (Asserted: 1 call)")
            assert calls_for_query == 1, f"[{qid}] Router called {calls_for_query} times; expected exactly 1!"

        # Node set parity assertion
        nodes_arm3 = extract_node_ids_from_ctx(rec3["context_full"])
        nodes_arm4 = extract_node_ids_from_ctx(rec4["context_full"])
        log_lines.append(f"  Node set parity: {nodes_arm3 == nodes_arm4} (Arm3={len(nodes_arm3)}, Arm4={len(nodes_arm4)})")
        assert nodes_arm3 == nodes_arm4, f"[{qid}] Node set mismatch between Arm 3 and Arm 4!"

        # Empty context item check: OBS_006
        if qid == "OBS_006":
            log_lines.append(f"  OBS_006 context_empty check: Arm3={rec3['context_empty']}, Arm4={rec4['context_empty']}")
            assert rec3["context_empty"] is True, f"OBS_006 expected context_empty=True in Arm 3, got {rec3['context_empty']}"
            assert rec4["context_empty"] is True, f"OBS_006 expected context_empty=True in Arm 4, got {rec4['context_empty']}"

        # Task Y1(b) Kwargs capturing & equality check across arms for this query
        q_calls = [c for c in captured_generation_calls if c["query_id"] == qid]
        log_lines.append(f"  Captured Generation Calls: {len(q_calls)}")
        for c in q_calls:
            log_lines.append(f"    - Arm {c['arm']}: model={c['model']}, temperature={c['temperature']}, max_tokens={c['max_tokens']}")
            assert c["model"] == GENERATION_MODEL, f"[{qid}] Model mismatch: {c['model']}"
            assert c["temperature"] == 0.0, f"[{qid}] Temperature mismatch: {c['temperature']}"
            assert c["max_tokens"] == 4096, f"[{qid}] Max tokens mismatch: {c['max_tokens']}"

    # Save cache
    save_cache_atomic(list(mock_cache.values()), mock_cache_file)
    initial_cache_count = len(mock_cache)
    log_lines.append(f"\nPass 1 Complete. Saved {initial_cache_count} records to {mock_cache_file}")

    # Pass 2: Rerun to verify replacement idempotency (no duplicate rows)
    log_lines.append("\n--- PASS 2: TESTING CACHE REPLACEMENT IDEMPOTENCY ---")
    reloaded_records = load_cache(mock_cache_file)
    cache_map = {(r["query_id"], r["pipeline"]): r for r in reloaded_records}

    # Simulate rerun of OBS_001 across all arms
    it_rerun = eval_items[0]
    qid_rerun = it_rerun["query_id"]
    for arm in ARMS:
        current_execution_context["arm"] = arm
        current_execution_context["query_id"] = qid_rerun
        rec_rerun = run_inference_arm(
            arm, it_rerun, mock_client, chroma_col,
            full_nodes=extract_node_ids_from_ctx(cache_map[(qid_rerun, "3_Full_TERRA")]["context_full"]),
            shared_route=cache_map[(qid_rerun, "3_Full_TERRA")]["route"]
        )
        # Update by replacement
        cache_map[(qid_rerun, arm)] = rec_rerun

    save_cache_atomic(list(cache_map.values()), mock_cache_file)
    final_reloaded = load_cache(mock_cache_file)
    final_cache_count = len(final_reloaded)

    log_lines.append(f"Pass 1 records: {initial_cache_count}")
    log_lines.append(f"Pass 2 records after rerun of {qid_rerun}: {final_cache_count}")
    log_lines.append(f"Zero duplicate rows added: {initial_cache_count == final_cache_count}")
    assert initial_cache_count == final_cache_count, f"Duplicate rows detected! {initial_cache_count} != {final_cache_count}"

    log_lines.append("\n" + "=" * 100)
    log_lines.append("ALL TASK X4 & Y1 MOCK INFERENCE ASSERTIONS PASSED (ZERO NETWORK CALLS)")
    log_lines.append("=" * 100)

    log_content = "\n".join(log_lines) + "\n"
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LOG, "w", encoding="utf-8") as f:
        f.write(log_content)
    with open(OUT_LOG_V2, "w", encoding="utf-8") as f:
        f.write(log_content)
    print(f"Wrote mock e2e logs to {OUT_LOG} and {OUT_LOG_V2}")

if __name__ == '__main__':
    run_mock_test()
