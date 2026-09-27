"""
scripts/run_temporal_leakage_phase3.py - Canonical Phase 3 Temporal Leakage Runner
===================================================================================
Executes the full 50-probe temporal leakage evaluation across:
  - 2 Experimental Conditions:
      * Condition A: Default Benchmark Prompt (standard legal query prompt)
      * Condition B: Explicit Historical Instruction (temporal pre-T constraint)
  - 3 Core Pipelines producing 4 Evaluated Variants:
      1. 1_Direct_LLM (Parametric direct generation, no RAG context)
      2. 2_Flat_Vector_RAG (Standard vector RAG over pre-T ChromaDB view)
      3. TERRA_ungated (GraphRAG over G_<=T, pre-T collection, ungated candidate)
      4. TERRA_gated (Same candidate evaluated by Llama 3.3 70B NLI Smart Grader)

Key Invariants:
  - Single-Candidate Caching: For each (query, condition), TERRA generates candidate once,
    asserting candidate_sha256(ungated) == candidate_sha256(gated).
  - Dynamic Horizon Switching: Uses TemporalHorizonContext to swap G_<=T and pre-T ChromaDB
    collection without mutating the global 1980 chroma_client.
  - Zero Post-T Contamination: Runtime assertions enforce doc_year <= T and node_year <= T.
  - Complete Attribution Telemetry: candidate_generated, nli_gate_evaluated, nli_gate_passed,
    nli_gate_refusal, nli_gate_applied_to_output, other_safety_intervention, final_action,
    global_state_restored.
  - Atomic Checkpointing: Saves to data/temporal_leakage_eval_raw.json after every query (scratch/ used as fallback only).
"""

import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import openai
import ask_terra
from baselines.common import (
    get_databricks_client,
    MANDATORY_MODEL_STRING,
    MANDATORY_TEMPERATURE,
    MANDATORY_MAX_TOKENS,
    NEUTRAL_SYSTEM_INSTRUCTION,
    NEUTRAL_DIRECT_SYSTEM_INSTRUCTION,
    format_neutral_prompt
)
from baselines.temporal_context_manager import (
    TemporalHorizonContext,
    flat_vector_rag_temporal,
    get_temporal_collection,
    load_temporal_subgraph,
    provenance_guard
)

DEFAULT_PROBE_PATH = ROOT_DIR / "data" / "temporal_leakage_probe_50.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "temporal_leakage_eval_raw.json"
FALLBACK_SCRATCH_OUTPUT_PATH = ROOT_DIR / "scratch" / "temporal_leakage_eval_raw.json"

SAFETY_REFUSAL_TEXT = (
    "I apologize, but I do not have sufficient validated legal context in my databases "
    "to answer this query accurately without risking hallucination."
)

PIPELINE_NAMES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "TERRA_ungated",
    "TERRA_gated"
]


def compute_sha256(text: str) -> str:
    """Computes standard SHA256 hex digest."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def clean_json_text(text: str) -> str:
    """Strips markdown code blocks and extracts JSON substring."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p_strip = p.strip()
            if p_strip.startswith("json"):
                p_strip = p_strip[4:].strip()
            if p_strip.startswith("{") and p_strip.endswith("}"):
                return p_strip
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


def atomic_save(data: List[Dict[str, Any]], filepath: Path, max_retries: int = 10) -> None:
    """Thread-safe atomic JSON file save with temp file swap."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_path = filepath.parent / f"{filepath.name}.tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    for attempt in range(max_retries):
        try:
            if filepath.exists():
                os.replace(temp_path, filepath)
            else:
                os.rename(temp_path, filepath)
            return
        except (PermissionError, OSError) as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.2 * (attempt + 1))


def call_generator(
    client: openai.OpenAI,
    prompt: str,
    system_instruction: str,
    max_retries: int = 5
) -> Tuple[str, float, float]:
    """
    Calls databricks-meta-llama-3-3-70b-instruct under temperature=0.0 and max_tokens=4096.
    Returns (generated_text, latency_ms, retry_sleep_ms).
    """
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]
    retry_sleep_ms = 0.0
    for attempt in range(max_retries):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MANDATORY_MODEL_STRING,
                messages=messages,
                temperature=MANDATORY_TEMPERATURE,
                max_tokens=MANDATORY_MAX_TOKENS
            )
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            text = resp.choices[0].message.content.strip()
            return text, elapsed_ms, retry_sleep_ms
        except Exception as e:
            wait_s = 2 * (attempt + 1)
            print(f"    [WARN] Generator call error: {e}. Retrying in {wait_s}s (attempt {attempt+1}/{max_retries})...")
            time.sleep(wait_s)
            retry_sleep_ms += wait_s * 1000.0
            if attempt == max_retries - 1:
                raise e

    raise RuntimeError("Generator failed after max retries.")


class NLIGateEvaluationError(RuntimeError):
    """Raised when NLI gate evaluation fails after exhausting retries."""
    pass


def evaluate_terra_nli_gate(
    client: openai.OpenAI,
    query_text: str,
    compiled_context: str,
    candidate_answer: str,
    max_retries: int = 5
) -> Dict[str, Any]:
    """
    Evaluates whether the compiled pre-T legal context logically entails the candidate answer.
    Uses canonical legal NLI verifier under temperature=0.0.
    """
    # Deterministic empty/trivial context gate (anti-hallucination safety invariant)
    clean_ctx = compiled_context.strip() if compiled_context else ""
    for marker in ["[Top Retrieved Cases]", "[GRAPH EXPANSION CONTEXT]", "[STRUCTURAL CONNECTIONS]", "[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]", "No relevant legal context found."]:
        clean_ctx = clean_ctx.replace(marker, "").strip()

    if len(clean_ctx) < 50:
        return {
            "entails": False,
            "confidence_score": 1.0,
            "confidence_defaulted": False,
            "reasoning": f"Context too short or empty ({len(clean_ctx)} chars after boilerplate stripping). Immediate fail.",
            "latency_ms": 0.0,
            "prompt_sha256": compute_sha256(clean_ctx),
            "context_sha256": compute_sha256(compiled_context),
            "model_used": "DETERMINISTIC_EMPTY_CONTEXT_GATE"
        }

    nli_prompt = f"""
    You are an NLI (Natural Language Inference) model acting as a legal quality control grader.
    Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query, and whether the Candidate Answer is fully entailed by the Legal Context without relying on external or post-cutoff legal developments.
    
    GUIDELINES:
    - Set "entails": true if the Legal Context contains the relevant case holdings, legal principles, historical connections, or subsequent citing/overruling precedents needed to address the query, and the Candidate Answer is factually and legally grounded strictly in the provided Context.
    - Set "entails": false if:
      (1) The Legal Context completely lacks relevant legal information or is on an entirely unrelated subject.
      (2) The query requests specific factual citations, reporter volumes, or page numbers that are absent from the context.
      (3) The Candidate Answer asserts legal precedents, doctrines, or holdings not supported by or contrary to the provided Legal Context.
    
    User Query: {query_text}
    
    Candidate Answer:
    {candidate_answer}
    
    Legal Context: 
    {compiled_context}
    
    Output strictly a valid JSON object with keys:
      "entails": boolean (true or false),
      "confidence_score": float (0.0 to 1.0),
      "reasoning": string explanation
    """

    prompt_hash = compute_sha256(nli_prompt)
    context_hash = compute_sha256(compiled_context)

    for attempt in range(max_retries):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MANDATORY_MODEL_STRING,
                messages=[{"role": "user", "content": nli_prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            raw_text = resp.choices[0].message.content
            parsed = json.loads(clean_json_text(raw_text))

            entails_val = parsed.get("entails", False)
            if isinstance(entails_val, str):
                entails_val = entails_val.strip().lower() in ("true", "yes", "entailed", "entails")

            raw_conf = parsed.get("confidence_score")
            conf_defaulted = False
            if raw_conf is not None:
                try:
                    conf_score = float(raw_conf)
                except (ValueError, TypeError):
                    conf_score = 0.95
                    conf_defaulted = True
            else:
                conf_score = 0.95
                conf_defaulted = True

            if conf_defaulted:
                print(f"      [WARN] NLI gate JSON missing or invalid 'confidence_score'; defaulted to 0.95.")
            elif conf_score == 0.95:
                print(f"      [INFO] NLI gate returned explicit confidence_score=0.95 (model output, not defaulted).")

            return {
                "entails": bool(entails_val),
                "confidence_score": conf_score,
                "confidence_defaulted": conf_defaulted,
                "reasoning": str(parsed.get("reasoning", "")),
                "latency_ms": elapsed_ms,
                "model_used": MANDATORY_MODEL_STRING,
                "prompt_sha256": prompt_hash,
                "context_sha256": context_hash,
                "raw_response": raw_text
            }
        except Exception as e:
            wait_s = 2 * (attempt + 1)
            print(f"    [WARN] NLI Gate error: {e}. Retrying in {wait_s}s (attempt {attempt+1}/{max_retries})...")
            time.sleep(wait_s)
            if attempt == max_retries - 1:
                raise NLIGateEvaluationError(f"NLI Gate failed after {max_retries} attempts: {e}") from e

    raise NLIGateEvaluationError(f"NLI Gate failed after {max_retries} attempts.")


def build_terra_temporal_context(
    query_text: str,
    cutoff_year: int,
    target_case_node_id: Optional[str] = None,
    target_case_name: Optional[str] = None
) -> Tuple[str, List[Dict[str, Any]], float]:
    """
    Compiles pre-T context for TERRA:
      1. Exact landmark node seeding from target case and title matches in G_<=T.
      2. Vector search in thinking_traces_T{cutoff_year}.
      3. Graph BFS traversal on G_<=T (up to depth 2).
      4. Synthesizes seed summaries, citing successors, and top vector traces.
      5. Enforces provenance assertion (year <= cutoff_year).
    Must be called inside TemporalHorizonContext(cutoff_year).
    """
    t_start = time.time()

    # 1. Exact Seeding
    seeded_metadatas = []
    seeded_ids = set()

    # Seed target case from probe if present in temporal subgraph
    if target_case_node_id and target_case_node_id in ask_terra.eeg.nodes:
        node_data = ask_terra.eeg.nodes[target_case_node_id]
        seeded_ids.add(target_case_node_id)
        seeded_metadatas.append({
            "node_id": target_case_node_id,
            "case_id": target_case_node_id,
            "title": node_data.get("title", target_case_name or target_case_node_id),
            "category": node_data.get("category", "")
        })

    # Exact title matching against active temporal subgraph nodes
    query_lower = query_text.lower()
    for nid in ask_terra.eeg.nodes:
        title = ask_terra.eeg.nodes[nid].get("title", "")
        if title and len(title) > 3 and title.lower() in query_lower:
            if nid not in seeded_ids:
                seeded_ids.add(nid)
                seeded_metadatas.append({
                    "node_id": nid,
                    "case_id": nid,
                    "title": title,
                    "category": ask_terra.eeg.nodes[nid].get("category", "")
                })
                if len(seeded_metadatas) >= 5:
                    break

    # 2. Vector Retrieval from active temporal ChromaDB collection
    vector_results = ask_terra.collection.query(
        query_texts=[query_text],
        n_results=2
    )
    retrieved_traces = vector_results.get("documents", [[]])[0]
    retrieved_metas = vector_results.get("metadatas", [[]])[0]

    # Combine exact seeds with vector metadatas
    combined_metas = seeded_metadatas + [
        m for m in retrieved_metas
        if (m.get("node_id") or m.get("case_id")) not in seeded_ids
    ]

    # Provenance safety check on vector retrieval
    provenance_guard(retrieved_metas, cutoff_year, item_type="doc", context_label=f"TERRA_VDB_T{cutoff_year}")

    # 3. BFS Citation Graph Traversal on G_<=T
    structural_context = ask_terra.extract_graph_context(combined_metas, max_depth=2)

    # 4. Precedent evolution / citing successors header
    successor_lines = [
        line.strip() for line in structural_context.splitlines()
        if ("CHRONOLOGICAL FLOW" in line or "LOGICAL RELATION" in line or "OVERRULING SUCCESSOR" in line)
    ]
    graph_evolution_block = ""
    if successor_lines:
        succ_header = "\n".join(successor_lines[:100])
        graph_evolution_block = f"[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n{succ_header}\n\n"

    # 5. Seeded case summaries
    seed_summaries = []
    for nid in seeded_ids:
        ndata = ask_terra.eeg.nodes.get(nid, {})
        ntitle = ndata.get("title", nid)
        holding = ndata.get("substantive_holding")
        if not holding:
            holding = ask_terra.clean_case_snippet(ndata.get("text", ""), max_chars=1200)
        else:
            holding = holding[:1200]
        try:
            chroma_res = ask_terra.collection.get(ids=[nid])
            trace = chroma_res["documents"][0] if (chroma_res and chroma_res.get("documents")) else ""
        except Exception:
            trace = ""
        summary = f"{trace}\n[Holding]: {holding}".strip() if (trace or holding) else ""
        if ntitle or summary:
            seed_summaries.append(f"[SEEDED CASE] {ntitle}:\n{summary}")

    seed_header = "\n\n".join(seed_summaries) if seed_summaries else ""
    traces_context = "\n".join([f"- {t}" for t in retrieved_traces])

    # Observation #1 Resolution: Explicitly wire precedent evolution & citing successors into compiled context
    context_sections = []
    if graph_evolution_block:
        context_sections.append(graph_evolution_block.strip())
    if seed_header:
        context_sections.append(seed_header.strip())
    context_sections.append(f"[GRAPH EXPANSION CONTEXT]\n{structural_context}")
    if traces_context:
        context_sections.append(traces_context.strip())

    compiled_context = "\n\n".join(context_sections)

    # Pre-truncate context to 60,000 chars matching TERRA safety window
    compiled_context = compiled_context[:60000]
    retrieval_ms = round((time.time() - t_start) * 1000, 2)

    return compiled_context, retrieved_metas, retrieval_ms


def execute_probe_for_condition(
    probe: Dict[str, Any],
    condition: str,
    client: openai.OpenAI,
    existing_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Executes all pipelines for a single probe and condition.
    Returns the list of completed records (up to 4 records: Direct, Flat, TERRA_ungated, TERRA_gated).
    """
    qid = probe["query_id"]
    cutoff = probe["cutoff_year"]
    q_text = probe["query_text"]
    ref = probe.get("ground_truth_holding", "")
    target_nid = probe.get("target_case_node_id")
    target_name = probe.get("target_case_name")
    target_year = probe.get("target_case_year")
    stratum = probe.get("stratum", "")
    domain = probe.get("domain", "")
    depth = probe.get("reasoning_depth", 1)

    new_records = []

    # Helper to check if already completed in existing checkpoint
    def is_done(pipe_name: str) -> bool:
        return any(
            r["query_id"] == qid and r["condition"] == condition and r["pipeline"] == pipe_name
            for r in (existing_records + new_records)
        )

    # -------------------------------------------------------------------------
    # 1. Direct LLM (Parametric, No RAG Context)
    # -------------------------------------------------------------------------
    if not is_done("1_Direct_LLM"):
        print(f"      -> Running 1_Direct_LLM ({condition})...")
        if condition == "Condition_A":
            prompt = f"User Legal Query: {q_text}\n\nAnswer:"
            system_inst = NEUTRAL_DIRECT_SYSTEM_INSTRUCTION
        else:  # Condition_B
            prompt = (
                f"You are an expert legal historian. Answer the following question strictly as of the year {cutoff}, "
                f"reflecting only the legal precedents and constitutional jurisprudence established at or before {cutoff}. "
                f"Do NOT mention, apply, or rely upon any decisions, statutes, or doctrines decided after {cutoff}.\n\n"
                f"Question: {q_text}\n\nAnswer:"
            )
            system_inst = "You are an expert constitutional legal historian. Strictly restrict your analysis to historical doctrine on or before the specified cutoff year."

        t_pipe_start = time.time()
        ans, gen_ms, retry_sleep = call_generator(client, prompt, system_inst)
        tot_ms = round((time.time() - t_pipe_start) * 1000, 2)

        rec_direct = {
            "query_id": qid,
            "cutoff_year": cutoff,
            "condition": condition,
            "pipeline": "1_Direct_LLM",
            "stratum": stratum,
            "domain": domain,
            "reasoning_depth": depth,
            "target_case_node_id": target_nid,
            "target_case_name": target_name,
            "target_case_year": target_year,
            "query": q_text,
            "reference": ref,
            "prompt_sha256": compute_sha256(prompt),
            "retrieval_context_sha256": compute_sha256("Direct LLM (No RAG Context)"),
            "candidate_sha256": compute_sha256(ans),
            "candidate_generated": True,
            "nli_gate_evaluated": False,
            "nli_gate_passed": None,
            "nli_gate_refusal": False,
            "nli_gate_applied_to_output": False,
            "other_safety_intervention": False,
            "final_action": "release",
            "global_state_restored": True,
            "answer_full": ans,
            "context_full": "Direct LLM (No RAG Context)",
            "timing": {
                "routing_ms": 0.0,
                "retrieval_ms": 0.0,
                "grading_ms": 0.0,
                "generation_ms": gen_ms,
                "total_ms": tot_ms,
                "model_used": MANDATORY_MODEL_STRING,
                "retry_sleep_ms": retry_sleep
            },
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        new_records.append(rec_direct)
    else:
        print(f"      -> 1_Direct_LLM ({condition}) already completed. Skipping.")

    # -------------------------------------------------------------------------
    # 2. Flat Vector RAG (Pre-T Vector DB View)
    # -------------------------------------------------------------------------
    if not is_done("2_Flat_Vector_RAG"):
        print(f"      -> Running 2_Flat_Vector_RAG ({condition})...")
        t_pipe_start = time.time()
        flat_rag_res = flat_vector_rag_temporal(q_text, cutoff_year=cutoff, k=2, enforce_provenance=True)
        flat_context = flat_rag_res["context_text"]
        ret_ms = round((time.time() - t_pipe_start) * 1000, 2)

        if condition == "Condition_A":
            prompt = format_neutral_prompt(q_text, flat_context)
            system_inst = NEUTRAL_SYSTEM_INSTRUCTION
        else:  # Condition_B
            prompt = (
                f"You are an expert legal AI assistant acting as a constitutional historian. "
                f"Answer the user's legal question strictly as of the year {cutoff}, reflecting only "
                f"the legal precedents established at or before {cutoff}. You must ground your answer "
                f"strictly on the provided historical context.\n\n"
                f"[HISTORICAL CONTEXT (ON OR BEFORE {cutoff})]:\n{flat_context}\n\n"
                f"[LEGAL QUESTION]:\n{q_text}\n\nAnswer:"
            )
            system_inst = "You are an expert legal AI assistant. Answer the user's legal question accurately based strictly on the provided context. If the context does not contain sufficient validated information to answer the query, state that you do not have sufficient validated legal context. Do not hallucinate, speculate, or affirm unverified historical or legal premises."

        t_gen_start = time.time()
        ans, gen_ms, retry_sleep = call_generator(client, prompt, system_inst)
        tot_ms = round((time.time() - t_pipe_start) * 1000, 2)

        rec_flat = {
            "query_id": qid,
            "cutoff_year": cutoff,
            "condition": condition,
            "pipeline": "2_Flat_Vector_RAG",
            "stratum": stratum,
            "domain": domain,
            "reasoning_depth": depth,
            "target_case_node_id": target_nid,
            "target_case_name": target_name,
            "target_case_year": target_year,
            "query": q_text,
            "reference": ref,
            "prompt_sha256": compute_sha256(prompt),
            "retrieval_context_sha256": compute_sha256(flat_context),
            "candidate_sha256": compute_sha256(ans),
            "candidate_generated": True,
            "nli_gate_evaluated": False,
            "nli_gate_passed": None,
            "nli_gate_refusal": False,
            "nli_gate_applied_to_output": False,
            "other_safety_intervention": False,
            "final_action": "release",
            "global_state_restored": True,
            "answer_full": ans,
            "context_full": flat_context,
            "timing": {
                "routing_ms": 0.0,
                "retrieval_ms": ret_ms,
                "grading_ms": 0.0,
                "generation_ms": gen_ms,
                "total_ms": tot_ms,
                "model_used": MANDATORY_MODEL_STRING,
                "retry_sleep_ms": retry_sleep
            },
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        new_records.append(rec_flat)
    else:
        print(f"      -> 2_Flat_Vector_RAG ({condition}) already completed. Skipping.")

    # -------------------------------------------------------------------------
    # 3. TERRA Single-Candidate Generation & NLI Gate Branching
    # -------------------------------------------------------------------------
    terra_ungated_done = is_done("TERRA_ungated")
    terra_gated_done = is_done("TERRA_gated")

    if not (terra_ungated_done and terra_gated_done):
        print(f"      -> Running TERRA Single-Candidate Generation ({condition})...")
        t_terra_start = time.time()

        # Step 3a: Traversal and context compilation within TemporalHorizonContext
        # Issue #1 Resolution: Record pre-context module attributes and strictly assert restoration on exit
        orig_eeg = getattr(ask_terra, "eeg", None)
        orig_collection = getattr(ask_terra, "collection", None)
        orig_graph_path = getattr(ask_terra, "GRAPH_INDEX_PATH", None)
        orig_vector_path = getattr(ask_terra, "VECTOR_DB_PATH", None)

        with TemporalHorizonContext(cutoff_year=cutoff, strict_provenance=True):
            terra_context, _, ret_ms = build_terra_temporal_context(
                query_text=q_text,
                cutoff_year=cutoff,
                target_case_node_id=target_nid,
                target_case_name=target_name
            )

        # Issue #1 Invariant: Assert global module state has returned 100% to original 1980 pointers
        assert ask_terra.eeg is orig_eeg, (
            f"[TEMPORAL HORIZON RESTORATION FAILURE] ask_terra.eeg not restored after context exit!"
        )
        assert ask_terra.collection is orig_collection, (
            f"[TEMPORAL HORIZON RESTORATION FAILURE] ask_terra.collection not restored after context exit!"
        )
        assert ask_terra.GRAPH_INDEX_PATH == orig_graph_path, (
            f"[TEMPORAL HORIZON RESTORATION FAILURE] ask_terra.GRAPH_INDEX_PATH not restored!"
        )
        assert ask_terra.VECTOR_DB_PATH == orig_vector_path, (
            f"[TEMPORAL HORIZON RESTORATION FAILURE] ask_terra.VECTOR_DB_PATH not restored!"
        )
        state_restored = bool(
            (ask_terra.eeg is orig_eeg) and
            (ask_terra.collection is orig_collection) and
            (ask_terra.GRAPH_INDEX_PATH == orig_graph_path) and
            (ask_terra.VECTOR_DB_PATH == orig_vector_path)
        )

        # ARCHITECTURAL NOTE: The TemporalHorizonContext context manager scope intentionally terminates
        # here upon completion of retrieval. Context compilation produces a completely self-contained text string
        # (terra_context). Subsequent LLM candidate generation and NLI gate verification are purely prompt-based
        # API calls that do not invoke ask_terra module state. Releasing the context manager immediately ensures
        # global module attributes are restored and prevents holding monkey-patched state across network I/O.

        # Step 3b: Construct Generator Prompt
        if condition == "Condition_A":
            system_prompt = f"""You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.

[QUESTION]
{q_text}

[CONTEXT DATA]
{terra_context}

[INSTRUCTIONS]
1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.
2. If CONTEXT DATA indicates that an earlier precedent has been [OVERRULES / REPUDIATES] by a subsequent decision, or if citing cases establish that an earlier doctrine has been rejected, your answer must explicitly state that the historical doctrine is NO LONGER valid law and cite the modifying or overruling decision.
3. Detail the legal transitions, rulings, and standards grounded strictly in the provided case text.
4. The Question is a valid, complete legal query. Provide a direct, substantive, and grounded legal answer.

TERRA Grounded Answer:"""
            system_inst = "You are an expert legal reasoning AI. Ground your answers strictly on the provided context."
        else:  # Condition_B
            system_prompt = f"""You are TERRA, an expert legal reasoning AI acting as a constitutional historian. Answer the Question below strictly as of the year {cutoff}, reflecting only the legal precedents and constitutional jurisprudence established at or before {cutoff}.

[QUESTION]
{q_text}

[CONTEXT DATA]
{terra_context}

[INSTRUCTIONS]
1. Answer the Question strictly as of the year {cutoff}.
2. Ground your reasoning strictly in the provided CONTEXT DATA (which contains only historical law on or before {cutoff}).
3. Do NOT mention, apply, or rely upon any decisions, statutes, or constitutional developments decided after {cutoff}.
4. Provide a direct, substantive, and historically accurate legal answer based strictly on the provided record.

TERRA Grounded Answer:"""
            system_inst = "You are an expert legal reasoning AI acting as a constitutional historian. Ground your answers strictly on the provided historical record on or before the cutoff."

        # Step 3c: Single Candidate Generation (Generate ONCE)
        candidate_text, gen_ms, retry_sleep = call_generator(client, system_prompt, system_inst)
        candidate_sha256 = compute_sha256(candidate_text)
        prompt_sha256 = compute_sha256(system_prompt)
        ctx_sha256 = compute_sha256(terra_context)

        # Step 3d: NLI Gate Evaluation with Issue #3 Fail-Safe Error Handling
        print(f"      -> Evaluating NLI Gate for TERRA candidate ({condition})...")
        t_gate_start = time.time()
        try:
            gate_verdict = evaluate_terra_nli_gate(
                client=client,
                query_text=q_text,
                compiled_context=terra_context,
                candidate_answer=candidate_text
            )
            grade_ms = gate_verdict.get("latency_ms", round((time.time() - t_gate_start) * 1000, 2))
            nli_passed = gate_verdict["entails"]
            gate_eval_success = True
        except Exception as e:
            grade_ms = round((time.time() - t_gate_start) * 1000, 2)
            print(f"      [WARN] NLI Gate evaluation failed after retries: {e}. Activating conservative fail-safe refusal.")
            gate_verdict = {
                "entails": False,
                "confidence_score": 0.0,
                "confidence_defaulted": False,
                "reasoning": f"[FAIL-SAFE] NLI Gate evaluation error: {str(e)}. Conservative refusal triggered.",
                "latency_ms": grade_ms,
                "model_used": "FAIL_SAFE_ERROR_GATE",
                "error": str(e)
            }
            nli_passed = False
            gate_eval_success = False

        tot_ms = round((time.time() - t_terra_start) * 1000, 2)

        # Record 1: TERRA_ungated (Issue #2 Resolution: Telemetry explicitly records gate evaluation on candidate)
        if not terra_ungated_done:
            rec_ungated = {
                "query_id": qid,
                "cutoff_year": cutoff,
                "condition": condition,
                "pipeline": "TERRA_ungated",
                "stratum": stratum,
                "domain": domain,
                "reasoning_depth": depth,
                "target_case_node_id": target_nid,
                "target_case_name": target_name,
                "target_case_year": target_year,
                "query": q_text,
                "reference": ref,
                "prompt_sha256": prompt_sha256,
                "retrieval_context_sha256": ctx_sha256,
                "candidate_sha256": candidate_sha256,
                "candidate_generated": True,
                "nli_gate_evaluated": gate_eval_success,
                "nli_gate_passed": nli_passed if gate_eval_success else None,
                "nli_gate_refusal": False,
                "nli_gate_applied_to_output": False,
                "other_safety_intervention": False,
                "final_action": "release",
                "global_state_restored": state_restored,
                "answer_full": candidate_text,
                "context_full": terra_context,
                "nli_gate_telemetry": {
                    "confidence_score": gate_verdict.get("confidence_score"),
                    "confidence_defaulted": gate_verdict.get("confidence_defaulted", False),
                    "reasoning": gate_verdict.get("reasoning"),
                    "nli_model_used": gate_verdict.get("model_used"),
                    "applied_to_output": False,
                    "evaluation_success": gate_eval_success
                },
                "timing": {
                    "routing_ms": 0.0,
                    "retrieval_ms": ret_ms,
                    "grading_ms": grade_ms,
                    "generation_ms": gen_ms,
                    "total_ms": tot_ms,
                    "model_used": MANDATORY_MODEL_STRING,
                    "retry_sleep_ms": retry_sleep
                },
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            new_records.append(rec_ungated)

        # Record 2: TERRA_gated (Issue #2 Resolution: Telemetry records gating intervention applied to output)
        if not terra_gated_done:
            gated_answer = candidate_text if nli_passed else SAFETY_REFUSAL_TEXT
            final_action = "release" if nli_passed else "refuse"

            rec_gated = {
                "query_id": qid,
                "cutoff_year": cutoff,
                "condition": condition,
                "pipeline": "TERRA_gated",
                "stratum": stratum,
                "domain": domain,
                "reasoning_depth": depth,
                "target_case_node_id": target_nid,
                "target_case_name": target_name,
                "target_case_year": target_year,
                "query": q_text,
                "reference": ref,
                "prompt_sha256": prompt_sha256,
                "retrieval_context_sha256": ctx_sha256,
                "candidate_sha256": candidate_sha256,
                "candidate_generated": True,
                "nli_gate_evaluated": gate_eval_success,
                "nli_gate_passed": nli_passed if gate_eval_success else False,
                "nli_gate_refusal": not nli_passed,
                "nli_gate_applied_to_output": True,
                "other_safety_intervention": False,
                "final_action": final_action,
                "global_state_restored": state_restored,
                "answer_full": gated_answer,
                "context_full": terra_context,
                "nli_gate_telemetry": {
                    "confidence_score": gate_verdict.get("confidence_score"),
                    "confidence_defaulted": gate_verdict.get("confidence_defaulted", False),
                    "reasoning": gate_verdict.get("reasoning"),
                    "nli_model_used": gate_verdict.get("model_used"),
                    "applied_to_output": True,
                    "evaluation_success": gate_eval_success
                },
                "timing": {
                    "routing_ms": 0.0,
                    "retrieval_ms": ret_ms,
                    "grading_ms": grade_ms,
                    "generation_ms": gen_ms,
                    "total_ms": tot_ms,
                    "model_used": MANDATORY_MODEL_STRING,
                    "retry_sleep_ms": retry_sleep
                },
                "created_at": datetime.utcnow().isoformat() + "Z"
            }

            # Cryptographic Invariant Assertion
            assert rec_gated["candidate_sha256"] == candidate_sha256, (
                f"[INVARIANT VIOLATION] Gated candidate_sha256 mismatch for {qid}: "
                f"{rec_gated['candidate_sha256']} != {candidate_sha256}"
            )
            new_records.append(rec_gated)

    else:
        print(f"      -> TERRA pipelines ({condition}) already completed. Skipping.")

    return new_records


def run_phase3_evaluation(
    probe_path: Path = DEFAULT_PROBE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    max_queries: Optional[int] = None,
    horizon_filter: Optional[int] = None,
    query_id_filter: Optional[str] = None,
    condition_filter: str = "all",
    resume: bool = True
) -> None:
    """Main execution orchestrator for Phase 3 evaluation."""
    print("\n" + "=" * 80)
    print("PHASE 3: CANONICAL TEMPORAL LEAKAGE EXPERIMENTAL RUNNER")
    print("=" * 80)
    print(f"Probe File:      {probe_path}")
    print(f"Output Checkpoint: {output_path}")
    print(f"Target Model:    {MANDATORY_MODEL_STRING} (T=0.0)")
    print(f"Horizon Filter:  {horizon_filter or 'All (1890, 1930, 1950, 1970, 1980)'}")
    print(f"Condition:       {condition_filter}")
    print(f"Resume Mode:     {resume}")

    # 1. Ingest Probes
    if not probe_path.exists():
        raise FileNotFoundError(f"Probe file not found: {probe_path}")
    with open(probe_path, "r", encoding="utf-8") as f:
        all_probes = json.load(f)
    print(f"Loaded {len(all_probes)} pre-registered historical probes from {probe_path.name}.")

    # 2. Checkpoint Accounting & Resumption (Observation #2: primary data/ path with scratch/ fallback)
    results: List[Dict[str, Any]] = []
    checkpoint_to_load = output_path
    if resume:
        if not checkpoint_to_load.exists() and FALLBACK_SCRATCH_OUTPUT_PATH.exists():
            print(f"[INFO] Primary checkpoint {output_path} not found. Checking scratch fallback: {FALLBACK_SCRATCH_OUTPUT_PATH}")
            checkpoint_to_load = FALLBACK_SCRATCH_OUTPUT_PATH

        if checkpoint_to_load.exists():
            try:
                with open(checkpoint_to_load, "r", encoding="utf-8") as f:
                    results = json.load(f)
                print(f"Loaded {len(results)} existing records from checkpoint ({checkpoint_to_load}).")
            except Exception as e:
                print(f"[WARN] Failed to parse checkpoint {checkpoint_to_load}: {e}. Starting fresh.")
                results = []

    # Filter target conditions
    if condition_filter == "Condition_A":
        active_conditions = ["Condition_A"]
    elif condition_filter == "Condition_B":
        active_conditions = ["Condition_B"]
    else:
        active_conditions = ["Condition_A", "Condition_B"]

    expected_records_per_query = len(active_conditions) * len(PIPELINE_NAMES)

    # Calculate completed queries
    completed_qids = set()
    from collections import Counter
    q_counter = Counter(r["query_id"] for r in results if r.get("condition") in active_conditions)
    for qid, count in q_counter.items():
        if count >= expected_records_per_query:
            completed_qids.add(qid)

    # 3. Filter probes to run
    probes_to_run = []
    for p in all_probes:
        if horizon_filter and p["cutoff_year"] != horizon_filter:
            continue
        if query_id_filter and p["query_id"] != query_id_filter:
            continue
        if resume and p["query_id"] in completed_qids:
            continue
        probes_to_run.append(p)

    print(f"Completed Queries in Checkpoint: {len(completed_qids)}")
    print(f"Queries Remaining to Execute:     {len(probes_to_run)} / {len(all_probes)}")

    if not probes_to_run:
        print("\n>>> ALL TARGET PROBES ALREADY FULLY COMPLETED IN CHECKPOINT. <<<")
        print(f"Output File: {output_path} ({len(results)} total records).")
        return

    # 4. Initialize Databricks Client
    client = get_databricks_client()

    # 5. Execution Loop
    start_time = time.time()
    queries_processed = 0

    print("\n" + "-" * 80)
    print("STARTING TEMPORAL EXECUTION LOOP")
    print("-" * 80)

    for idx, probe in enumerate(probes_to_run, 1):
        if max_queries is not None and queries_processed >= max_queries:
            print(f"\n[HARD STOP] Reached maximum requested queries ({max_queries}). Halting session.")
            break

        qid = probe["query_id"]
        cutoff = probe["cutoff_year"]
        stratum = probe.get("stratum", "")
        domain = probe.get("domain", "")
        q_text = probe["query_text"]

        print(f"\n[{idx}/{len(probes_to_run)}] Query {qid} (T={cutoff} | {stratum} | {domain})")
        print(f"  Target Case: {probe.get('target_case_name')} ({probe.get('target_case_year')})")
        print(f"  Query Text:  \"{q_text[:80]}...\"")

        for cond in active_conditions:
            print(f"   [{cond}] Processing pipelines...")
            new_recs = execute_probe_for_condition(
                probe=probe,
                condition=cond,
                client=client,
                existing_records=results
            )

            # Append new records to results
            results.extend(new_recs)

            # Assert invariant on candidate SHA256 equality if both were generated
            ungated = next((r for r in new_recs if r["pipeline"] == "TERRA_ungated"), None)
            gated = next((r for r in new_recs if r["pipeline"] == "TERRA_gated"), None)
            if ungated and gated:
                assert ungated["candidate_sha256"] == gated["candidate_sha256"], (
                    f"[INVARIANT VIOLATION] Candidate SHA256 mismatch for {qid} ({cond})!"
                )
                print(f"      [INVARIANT PASS] candidate_sha256 identical: {ungated['candidate_sha256'][:16]}...")
                print(f"      [GATE ACTION] nli_gate_passed={gated['nli_gate_passed']} -> final_action='{gated['final_action']}'")

        # Atomic Checkpoint after each query
        atomic_save(results, output_path)
        queries_processed += 1
        print(f" -> Query {qid} completed & checkpointed. Total records in checkpoint: {len(results)}.")

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 80)
    print(f"EXECUTION FINISHED in {elapsed}s (~{round(elapsed/60, 2)} mins).")
    print(f"Queries processed this session: {queries_processed}")
    print(f"Total records in {output_path}: {len(results)}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="TERRA Phase 3 Canonical Temporal Leakage Runner")
    parser.add_argument("--probe", type=str, default=str(DEFAULT_PROBE_PATH), help="Path to temporal leakage probe JSON")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH), help="Path to raw output evaluation JSON")
    parser.add_argument("--max-queries", type=int, default=None, help="Maximum number of queries to process")
    parser.add_argument("--horizon", type=int, default=None, choices=[1890, 1930, 1950, 1970, 1980], help="Filter by specific historical cutoff year")
    parser.add_argument("--query-id", type=str, default=None, help="Execute only a specific probe query ID (e.g., TLP-01)")
    parser.add_argument("--condition", type=str, default="all", choices=["Condition_A", "Condition_B", "all"], help="Filter by experimental condition")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing checkpoint (default: True)")
    parser.add_argument("--no-resume", action="store_true", help="Overwrite checkpoint instead of resuming")

    args = parser.parse_args()
    resume_flag = False if args.no_resume else args.resume

    run_phase3_evaluation(
        probe_path=Path(args.probe),
        output_path=Path(args.output),
        max_queries=args.max_queries,
        horizon_filter=args.horizon,
        query_id_filter=args.query_id,
        condition_filter=args.condition,
        resume=resume_flag
    )


if __name__ == "__main__":
    main()
