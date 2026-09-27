import os
import sys
import json
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
OUT_LOG = ROOT / "logs" / "u5_regression.txt"

sys.path.insert(0, str(ROOT))

# Configure environment variables for offline execution
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "mock_key_offline")
os.environ["TERRA_GRAPH_PATH"] = "dataset_20k_cap/terra_eeg_index_20k.json"
os.environ["TERRA_VECTOR_DB_PATH"] = "./dataset_20k_cap/vector_db_20k"

import ask_terra as mod_work

strip_path = ROOT / "scratch" / "ask_terra_strip.py"
spec_strip = importlib.util.spec_from_file_location("ask_terra_strip", str(strip_path))
mod_strip = importlib.util.module_from_spec(spec_strip)
spec_strip.loader.exec_module(mod_strip)

class MockInterceptor:
    def __init__(self):
        self.last_prompt = None
    def generate(self, prompt, query_id, pipeline_name):
        self.last_prompt = prompt
        class Resp:
            text = "MOCK_RESPONSE"
            model_used = "mock_model"
            retry_sleep_ms = 0.0
        return Resp()

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def build_fallback_prompt(user_query: str, full_compiled_context: str, instruction_2: str) -> str:
    truncated_context = full_compiled_context[:60000] if len(full_compiled_context) > 60000 else full_compiled_context
    if len(full_compiled_context) > 60000:
        truncated_context += "\n...[Context truncated to 60000 chars — safety cap]..."
        
    return f"""
    You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.
    
    [QUESTION]
    {user_query}
    
    [CONTEXT DATA]
    {truncated_context}
    
    [INSTRUCTIONS]
    1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.
    {instruction_2}
    3. If multiple cases are provided under [SEEDED CASE] headers in CONTEXT DATA, your answer must explicitly reference and synthesize ALL of them, explaining how they relate to the Question. Do not stop after summarizing a single case when multiple seeded cases are present.
    4. For doctrinal evolution questions tracing multiple cases, detail the legal transitions, rulings, and standards grounded strictly in the provided [Holding] and case text. Synthesize the trajectory across the cases provided without asserting external legal standards or factual tests that do not appear in the context. If an intermediate standard is only partially described, state the rule as established in the provided text rather than refusing to answer.
    5. The Question is a valid, complete legal query. Provide a direct, substantive, and grounded legal answer. Do not issue a refusal or hedge unnecessarily when relevant case holdings and trajectory are provided in the context.
    6. For any legal case you mention in your answer that has an explicit Case ID listed in the CONTEXT DATA (e.g. Case ID: 5 for Brown v. Board of Education), format the case title as a relative markdown link using its ID, e.g. "[Brown v. Board of Education](/case/5)". Only format links for cases that have explicit Case IDs provided in the context data.
    
    Question: {user_query}
    
    TERRA Grounded Answer:
    """

DEFAULT_INST2 = "2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision."

# 1. Load 30 benchmark queries
with open(ROOT / "data" / "obscure_overruled_benchmark.json", "r", encoding="utf-8") as f:
    bench_30 = json.load(f)

# 2. Load 20 queries from 350 benchmark (first 5 of each category A-D)
with open(ROOT / "terra_350_benchmark.json", "r", encoding="utf-8") as f:
    bench_350 = json.load(f)

cats = {"A": [], "B": [], "C": [], "D": []}
for item in bench_350:
    c = item.get("category", "")
    prefix = c[0].upper() if c else ""
    if prefix in cats:
        cats[prefix].append(item)

sampled_20 = []
for p in ["A", "B", "C", "D"]:
    sorted_items = sorted(cats[p], key=lambda x: x.get("id", x.get("query_id", "")))
    sampled_20.extend(sorted_items[:5])

# 3. Load terra_baselines_eval_raw.json
stored_contexts = {}
try:
    with open(ROOT / "terra_baselines_eval_raw.json", "r", encoding="utf-8") as f:
        raw_baselines = json.load(f)
    for record in raw_baselines:
        if record.get("pipeline") == "5_Full_TERRA":
            qid = record.get("query_id")
            if qid:
                stored_contexts[qid] = record.get("context_full", "")
except Exception as e:
    print(f"Notice: Could not load terra_baselines_eval_raw.json: {e}")

log_lines = []
log_lines.append("=" * 130)
log_lines.append("U5 REGRESSION AUDIT: WORKING (ask_terra.py) VS STRIPPED (scratch/ask_terra_strip.py)")
log_lines.append("=" * 130)

all_identical = True

# --- SECTION 1: 30 OBSCURE BENCHMARK QUERIES ---
log_lines.append("\n--- PART 1: 30 OBSCURE OVERRULED BENCHMARK QUERIES ---")
log_lines.append(f"{'QUERY_ID':<10} | {'WORK_CTX_LEN':<12} | {'STRIP_CTX_LEN':<13} | {'WORK_PRM_LEN':<12} | {'STRIP_PRM_LEN':<13} | {'CTX_MATCH':<9} | {'PRM_MATCH':<9} | {'STORED_RAW_CTX'}")
log_lines.append("-" * 130)

for item in bench_30:
    qid = item["query_id"]
    query = item["query"]
    
    interceptor_work = MockInterceptor()
    _, ctx_work = mod_work.terra_inference_engine(
        query,
        disable_nli_grader=True,
        force_hard_path=True,
        interceptor=interceptor_work,
        query_id=qid
    )
    prm_work = interceptor_work.last_prompt or build_fallback_prompt(query, ctx_work, DEFAULT_INST2)
    
    interceptor_strip = MockInterceptor()
    _, ctx_strip = mod_strip.terra_inference_engine(
        query,
        disable_nli_grader=True,
        force_hard_path=True,
        interceptor=interceptor_strip,
        query_id=qid
    )
    prm_strip = interceptor_strip.last_prompt or build_fallback_prompt(query, ctx_strip, DEFAULT_INST2)
    
    ctx_match = (ctx_work == ctx_strip)
    prm_match = (prm_work == prm_strip)
    if not (ctx_match and prm_match):
        all_identical = False
        
    stored_str = stored_contexts.get(qid)
    if stored_str is None:
        stored_desc = "NONE"
    else:
        stored_desc = f"LEN={len(stored_str)} SHA={hash_text(stored_str)[:12]}"
        
    log_lines.append(
        f"{qid:<10} | {len(ctx_work):<12} | {len(ctx_strip):<13} | {len(prm_work):<12} | {len(prm_strip):<13} | "
        f"{'IDENTICAL' if ctx_match else 'DIFFERENT':<9} | {'IDENTICAL' if prm_match else 'DIFFERENT':<9} | {stored_desc}"
    )
    log_lines.append(f"   SHA-256 Ctx:  Work={hash_text(ctx_work)} | Strip={hash_text(ctx_strip)}")
    log_lines.append(f"   SHA-256 Prm:  Work={hash_text(prm_work)} | Strip={hash_text(prm_strip)}")

# --- SECTION 2: 20 QUERIES FROM 350 BENCHMARK (A-D) ---
log_lines.append("\n\n--- PART 2: 20 QUERIES FROM TERRA 350 BENCHMARK (FIRST 5 OF CATS A, B, C, D) ---")
log_lines.append(f"{'QUERY_ID':<10} | {'WORK_CTX_LEN':<12} | {'STRIP_CTX_LEN':<13} | {'WORK_PRM_LEN':<12} | {'STRIP_PRM_LEN':<13} | {'CTX_MATCH':<9} | {'PRM_MATCH':<9} | {'STORED_VS_REGEN'}")
log_lines.append("-" * 130)

for item in sampled_20:
    qid = item.get("id", item.get("query_id"))
    query = item.get("query") or item.get("text")
    
    interceptor_work = MockInterceptor()
    _, ctx_work = mod_work.terra_inference_engine(
        query,
        disable_nli_grader=True,
        force_hard_path=True,
        interceptor=interceptor_work,
        query_id=qid
    )
    prm_work = interceptor_work.last_prompt or build_fallback_prompt(query, ctx_work, DEFAULT_INST2)
    
    interceptor_strip = MockInterceptor()
    _, ctx_strip = mod_strip.terra_inference_engine(
        query,
        disable_nli_grader=True,
        force_hard_path=True,
        interceptor=interceptor_strip,
        query_id=qid
    )
    prm_strip = interceptor_strip.last_prompt or build_fallback_prompt(query, ctx_strip, DEFAULT_INST2)
    
    ctx_match = (ctx_work == ctx_strip)
    prm_match = (prm_work == prm_strip)
    if not (ctx_match and prm_match):
        all_identical = False
        
    stored_str = stored_contexts.get(qid)
    if stored_str is None:
        stored_desc = "NONE"
    else:
        reg_vs_stored = "IDENTICAL" if (ctx_work == stored_str) else "DIFFERENT"
        stored_desc = f"StoredLen={len(stored_str)} ({reg_vs_stored})"
        
    log_lines.append(
        f"{qid:<10} | {len(ctx_work):<12} | {len(ctx_strip):<13} | {len(prm_work):<12} | {len(prm_strip):<13} | "
        f"{'IDENTICAL' if ctx_match else 'DIFFERENT':<9} | {'IDENTICAL' if prm_match else 'DIFFERENT':<9} | {stored_desc}"
    )
    log_lines.append(f"   SHA-256 Ctx:  Work={hash_text(ctx_work)} | Strip={hash_text(ctx_strip)}")
    log_lines.append(f"   SHA-256 Prm:  Work={hash_text(prm_work)} | Strip={hash_text(prm_strip)}")
    if stored_str is not None:
        log_lines.append(f"   SHA-256 Stored Ctx: {hash_text(stored_str)}")

log_lines.append("\n" + "=" * 130)
log_lines.append(f"SUMMARY VERDICT: Working ask_terra.py vs Stripped scratch/ask_terra_strip.py IDENTICAL across all 50 queries: {all_identical}")
log_lines.append("=" * 130)

OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines) + "\n")

print(f"Completed U5 regression! Results written to {OUT_LOG}")
print(f"Overall parity: {all_identical}")
