"""
scripts/verify_llm_parity.py - Gate 2 Invariant Verification
Live pre-flight smoke test verifying that API calls intercept outgoing HTTP payloads,
enforcing exact model string (databricks-meta-llama-3-3-70b-instruct) and T=0.0.
"""

import os
import sys
import json

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baselines.common import (
    PayloadParityInterceptor,
    MANDATORY_MODEL_STRING,
    MANDATORY_TEMPERATURE,
    PAYLOAD_AUDIT_LOG
)


def run_llm_parity_check():
    print("\n" + "=" * 70)
    print("GATE 2 AUDIT: Live Generator LLM Parity Verification (Workstream 1.2)")
    print("=" * 70)

    interceptor = PayloadParityInterceptor()
    test_query = "What is the holding in Brown v. Board of Education in one sentence?"
    test_context = "Brown v. Board of Education, 347 U.S. 483 (1954), held that racial segregation in public schools violates the Equal Protection Clause."

    print(f"Mandatory Model:       {MANDATORY_MODEL_STRING}")
    print(f"Mandatory Temperature: {MANDATORY_TEMPERATURE}")
    print(f"Target Audit Log:      {PAYLOAD_AUDIT_LOG}")
    print("\nExecuting live intercepted test call to Databricks Model Serving...")

    try:
        resp = interceptor.generate(
            prompt=f"Context: {test_context}\n\nQuestion: {test_query}",
            query_id="SMOKE_TEST_GATE2",
            pipeline_name="PreFlight_Verification"
        )
    except Exception as e:
        print(f"[FAIL] Intercepted generator call failed: {e}")
        sys.exit(1)

    print(f"Generated Text:        {resp.text[:100]}...")
    print(f"Model Used Reported:   {resp.model_used}")

    if resp.model_used != MANDATORY_MODEL_STRING:
        print(f"[FAIL] Model mismatch! {resp.model_used} != {MANDATORY_MODEL_STRING}")
        sys.exit(1)

    # Inspect audit log file to verify recorded payload
    if not os.path.exists(PAYLOAD_AUDIT_LOG):
        print(f"[FAIL] Audit log file was not created: {PAYLOAD_AUDIT_LOG}")
        sys.exit(1)

    with open(PAYLOAD_AUDIT_LOG, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    last_entry = json.loads(lines[-1])
    print(f"Last Logged Payload:   {json.dumps(last_entry, indent=2)}")

    assert last_entry["model"] == MANDATORY_MODEL_STRING, "Audit log model mismatch!"
    assert last_entry["temperature"] == MANDATORY_TEMPERATURE, "Audit log temperature mismatch!"
    assert last_entry["query_id"] == "SMOKE_TEST_GATE2", "Audit log query_id mismatch!"

    print("[PASS] Payload intercepted and verified: Model and T=0.0 strictly enforced.")
    print("=" * 70)
    print("GATE 2 PASSED: 100% LLM Parity Enforced and Verified.\n")


if __name__ == "__main__":
    run_llm_parity_check()
