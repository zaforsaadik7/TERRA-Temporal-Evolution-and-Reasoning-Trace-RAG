#!/usr/bin/env python3
"""
scripts/export_reproducibility_artifacts.py
Deterministic export engine for TERRA Issue #39 Reproducibility Package.

Generates the 9 Phase-3 reproducibility artifacts:
1. data/terra_eeg_edges_145k.tsv (145,366 directed citation & overruling edges)
2. data/doctrine_invalidation_pairs_19.json (19 verified landmark invalidation pairs)
3. data/terra_canonical_v2_eval.json (Canonical dual-judged evaluation records, 15.1 MB)
4. prompts/router_system_prompt.txt (Google Gemma 3 12B intent routing prompt)
5. prompts/fast_path_prompt.txt (Grounded fast path generation prompt)
6. prompts/generator_system_prompt.txt (Multi-hop precedent traversal prompt)
7. prompts/nli_grader_prompt.txt (NLI Smart Grader entailment verification prompt)
8. prompts/dual_judge_prompt.txt (Standardized dual-judge skeptical rubric prompt)
9. configs/terra_config.json (Frozen system architecture configurations)
"""

import os
import sys
import json
import shutil
import hashlib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def export_edges_tsv():
    print("\n[1/5] Exporting standalone citation edge list (data/terra_eeg_edges_145k.tsv)...")
    src_index = "dataset_20k_cap/terra_eeg_index_20k.json"
    if not os.path.exists(src_index):
        raise FileNotFoundError(f"Missing source index: {src_index}")

    with open(src_index, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    os.makedirs("data", exist_ok=True)
    out_path = "data/terra_eeg_edges_145k.tsv"

    cites_count = 0
    overrules_count = 0

    with open(out_path, 'w', encoding='utf-8', newline='') as out:
        out.write("source_id\ttarget_id\trelation\tsource_year\ttarget_year\r\n")
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            rel = e.get("relation", "")
            if rel == "CITES":
                cites_count += 1
            elif rel == "OVERRULES":
                overrules_count += 1

            s_date = nodes.get(src, {}).get("decision_date", "")
            t_date = nodes.get(tgt, {}).get("decision_date", "")
            s_yr = s_date[:4] if len(s_date) >= 4 else "NA"
            t_yr = t_date[:4] if len(t_date) >= 4 else "NA"

            out.write(f"{src}\t{tgt}\t{rel}\t{s_yr}\t{t_yr}\r\n")

    total_edges = cites_count + overrules_count
    assert total_edges == 145366, f"Expected 145,366 edges, got {total_edges}"
    assert cites_count == 145310, f"Expected 145,310 CITES, got {cites_count}"
    assert overrules_count == 56, f"Expected 56 OVERRULES, got {overrules_count}"

    with open(out_path, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    assert line_count == 145367, f"Expected 145,367 lines in TSV, got {line_count}"

    size = os.path.getsize(out_path)
    h = sha256_file(out_path)
    print(f"  Created {out_path} ({size:,} B, {line_count:,} lines: {cites_count:,} CITES, {overrules_count} OVERRULES)")
    print(f"  SHA256: {h}")
    return out_path, size, h

def export_invalidation_pairs():
    print("\n[2/5] Exporting 19 doctrine-invalidation landmark pairs (data/doctrine_invalidation_pairs_19.json)...")
    src_bm = "terra_350_benchmark.json"
    if not os.path.exists(src_bm):
        raise FileNotFoundError(f"Missing benchmark file: {src_bm}")

    with open(src_bm, 'r', encoding='utf-8') as f:
        bm = json.load(f)

    d1_items = [q for q in bm if q.get("adversarial_subtype") == "overruled_precedent_trap"]
    assert len(d1_items) == 19, f"Expected 19 Category D1 items, got {len(d1_items)}"

    out_path = "data/doctrine_invalidation_pairs_19.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(d1_items, f, indent=2)

    size = os.path.getsize(out_path)
    h = sha256_file(out_path)
    print(f"  Created {out_path} ({size:,} B, {len(d1_items)} pairs)")
    print(f"  SHA256: {h}")
    return out_path, size, h

def copy_canonical_eval():
    print("\n[3/5] Deploying canonical dual-judge evaluation records (data/terra_canonical_v2_eval.json)...")
    src_eval = "scratch/canonical_v2/terra_canonical_v2_eval.json"
    if not os.path.exists(src_eval):
        raise FileNotFoundError(f"Missing canonical eval source: {src_eval}")

    out_path = "data/terra_canonical_v2_eval.json"
    shutil.copyfile(src_eval, out_path)

    expected_hash = "95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507"
    size = os.path.getsize(out_path)
    h = sha256_file(out_path)
    assert h == expected_hash, f"Canonical eval hash mismatch: got {h}, expected {expected_hash}"

    print(f"  Created {out_path} ({size:,} B)")
    print(f"  SHA256: {h} (Matches expected)")
    return out_path, size, h

def export_prompts():
    print("\n[4/5] Exporting verbatim system prompt templates (prompts/)...")
    os.makedirs("prompts", exist_ok=True)
    created = []

    # 1. Router System Prompt
    router_p = "prompts/router_system_prompt.txt"
    with open(router_p, "w", encoding="utf-8") as f:
        f.write(
            "You are a routing classifier for a legal AI system. Classify the query below as either 'EASY' or 'HARD'.\n\n"
            "EASY — Use when the query is a simple, single-point factual lookup:\n"
            "  - Asking for a specific year or date (e.g. \"In what year was X decided?\")\n"
            "  - Asking for a case citation (e.g. \"What is the U.S. Reports citation for X?\")\n"
            "  - Asking for the name of a ruling, doctrine, or single case fact\n"
            "  - Any question answerable with one sentence from memory\n"
            "  Examples: \"When was Brown v. Board decided?\", \"What is the citation for Plessy v. Ferguson?\"\n\n"
            "HARD — Use when the query requires reasoning, comparison, or multiple cases:\n"
            "  - Tracking legal evolution over time (e.g., \"How did X change from Y to Z?\")\n"
            "  - Comparing multiple cases or doctrines\n"
            "  - Questions outside the civil rights constitutional law domain\n"
            "  - Any open-ended analytical question\n\n"
            "Domain Relevance Flag: {domain_relevance}\n"
            "IMPORTANT: If OUT-OF-DOMAIN and the query cannot be answered from SCOTUS civil rights cases, you MUST classify as HARD (which triggers safety refusal).\n\n"
            "Query: {user_query}\n\n"
            "Respond with JSON containing keys \"complexity\" (EASY or HARD) and \"reason\".\n"
        )
    created.append((router_p, os.path.getsize(router_p), sha256_file(router_p)))

    # 2. Fast Path Prompt
    fast_p = "prompts/fast_path_prompt.txt"
    with open(fast_p, "w", encoding="utf-8") as f:
        f.write(
            "You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately, concisely, and factually using ONLY the provided context data.\n\n"
            "[CONTEXT DATA]\n"
            "{fast_context}\n\n"
            "[QUESTION]\n"
            "{user_query}\n\n"
            "[INSTRUCTIONS]\n"
            "1. Answer the question directly and factually based strictly on the CONTEXT DATA.\n"
            "2. If the query asserts a false factual premise not supported by the context or legal doctrine, explicitly state the correct factual holding.\n"
            "3. Keep the answer direct, grounded, and concise.\n\n"
            "TERRA Grounded Answer:\n"
        )
    created.append((fast_p, os.path.getsize(fast_p), sha256_file(fast_p)))

    # 3. Generator System Prompt
    gen_p = "prompts/generator_system_prompt.txt"
    with open(gen_p, "w", encoding="utf-8") as f:
        f.write(
            "You are TERRA, an advanced legal reasoning AI. Answer the Question below accurately using ONLY the provided context data.\n\n"
            "[QUESTION]\n"
            "{user_query}\n\n"
            "[CONTEXT DATA]\n"
            "{truncated_context}\n\n"
            "[INSTRUCTIONS]\n"
            "1. Answer the Question directly, thoroughly, and factually based ONLY on CONTEXT DATA.\n"
            "2. ADVERSARIAL REPUTIATION REQUIREMENT: If the query asks whether a historical doctrine is currently constitutional, binding, or enforceable, and the context proves that doctrine was overruled, you MUST explicitly state that the doctrine was overruled and is no longer good law.\n"
            "3. If multiple cases are provided under [SEEDED CASE] headers in CONTEXT DATA, your answer must explicitly reference and synthesize the doctrinal evolution across these authorities.\n"
            "4. NEVER invent citations, holding details, or constitutional rationales not grounded in the provided context.\n\n"
            "TERRA Grounded Answer:\n"
        )
    created.append((gen_p, os.path.getsize(gen_p), sha256_file(gen_p)))

    # 4. NLI Grader Prompt
    nli_p = "prompts/nli_grader_prompt.txt"
    with open(nli_p, "w", encoding="utf-8") as f:
        f.write(
            "You are an NLI (Natural Language Inference) model acting as a legal quality control grader.\n"
            "Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query.\n\n"
            "GUIDELINES:\n"
            "- Set \"entails\": true if the Legal Context contains the relevant case holdings, legal principles, historical connections, or subsequent citing/overruling precedents needed to address the query.\n"
            "- DOCTRINAL EVOLUTION & ADVERSARIAL QUERIES: If a query asks whether a historical doctrine is currently binding, enforceable, or constitutional, evidence showing that the precedent was overruled, repudiated, or superseded ENTAILS the necessary information to formulate a correct refusal or refutation.\n"
            "- Set \"entails\": false if the context is empty, generic, completely off-topic, or lacks the necessary doctrinal authority.\n\n"
            "[USER QUERY]\n"
            "{user_query}\n\n"
            "[LEGAL CONTEXT]\n"
            "{retrieved_context}\n\n"
            "Output JSON with keys \"entails\" (boolean) and \"rationale\" (string).\n"
        )
    created.append((nli_p, os.path.getsize(nli_p), sha256_file(nli_p)))

    # 5. Dual Judge Prompt
    judge_p = "prompts/dual_judge_prompt.txt"
    with open(judge_p, "w", encoding="utf-8") as f:
        f.write(
            "You are a SKEPTICAL legal AI auditor. Your job is to find flaws, hallucinations, and relevance gaps. Be strict. Do not be generous.\n\n"
            "Evaluate this generation for a legal query against the provided reference context.\n\n"
            "Query: {query}\n"
            "Retrieved Context: {context}\n"
            "Generated Answer: {answer}\n\n"
            "Scoring Criteria (5-point Likert Scale):\n"
            "Faithfulness (1-5):\n"
            "1 - Severe Hallucination / Contradiction of Legal Context\n"
            "2 - Unsubstantiated claims present\n"
            "3 - Mostly grounded with minor extrapolation\n"
            "4 - Well-grounded in evidence\n"
            "5 - Flawlessly faithful to retrieved authority\n\n"
            "Relevance (1-5):\n"
            "1 - Off-topic or fails to answer the core legal question\n"
            "2 - Peripheral relevance\n"
            "3 - Answers partially with gaps\n"
            "4 - Addresses core question directly\n"
            "5 - Comprehensive, exact answer with proper legal nuance\n\n"
            "Output strictly a valid json object with keys:\n"
            "  \"faithfulness_score\": integer between 1 and 5,\n"
            "  \"faithfulness_reasoning\": detailed explanation string,\n"
            "  \"relevance_score\": integer between 1 and 5,\n"
            "  \"relevance_reasoning\": detailed explanation string.\n"
        )
    created.append((judge_p, os.path.getsize(judge_p), sha256_file(judge_p)))

    for p, sz, h in created:
        print(f"  Created {p} ({sz:,} B) | SHA256: {h}")

    return created

def export_configs():
    print("\n[5/5] Exporting system architecture configuration (configs/terra_config.json)...")
    os.makedirs("configs", exist_ok=True)
    cfg_path = "configs/terra_config.json"

    cfg = {
        "system": {
            "name": "TERRA",
            "full_name": "Temporal-Evolution and Reasoning-Trace RAG",
            "version": "2.0-canonical",
            "description": "Dual-phase GraphRAG architecture unifying Event Evolution Graphs and Procedural Reasoning Traces via Semantic Entailment"
        },
        "retrieval": {
            "vector_store": {
                "client": "chromadb.PersistentClient",
                "collection_name": "thinking_traces",
                "initial_top_k": 2,
                "expansion_increment": 2,
                "metric": "euclidean_l2",
                "proximity_threshold": 1.3
            },
            "dense_embedder": {
                "model_identifier": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_dimensions": 384,
                "distance_metric": "Euclidean L2",
                "license": "Apache-2.0"
            }
        },
        "graph_traversal": {
            "graph_type": "directed_event_evolution_graph",
            "traversal_algorithm": "temporal_bfs",
            "maximum_depth": 2,
            "hub_degree_cap": 50,
            "temporal_directionality_enforced": True,
            "subgraph_extraction": "source_seeded_precedent_chains"
        },
        "models": {
            "generator": {
                "hf_model_id": "meta-llama/Llama-3.3-70B-Instruct",
                "serving_endpoint": "databricks-meta-llama-3-3-70b-instruct",
                "temperature": 0.0,
                "max_tokens": 4096
            },
            "traffic_cop_router": {
                "hf_model_id": "google/gemma-3-12b-it",
                "serving_endpoint": "databricks-gemma-3-12b",
                "temperature": 0.0,
                "schema_validation": "pydantic_structured_json"
            },
            "nli_smart_grader": {
                "hf_model_id": "meta-llama/Llama-3.3-70B-Instruct",
                "serving_endpoint": "databricks-meta-llama-3-3-70b-instruct",
                "temperature": 0.0,
                "schema_validation": "pydantic_structured_json"
            },
            "independent_judges": {
                "judge_1": {
                    "serving_endpoint": "databricks-qwen3-next-80b-a3b-instruct",
                    "role": "Adversarial Skeptical Critic Judge 1",
                    "temperature": 0.0
                },
                "judge_2": {
                    "serving_endpoint": "databricks-gpt-oss-120b",
                    "role": "Adversarial Skeptical Critic Judge 2",
                    "temperature": 0.0
                }
            }
        },
        "evaluation_hyperparameters": {
            "random_seed": 42,
            "benchmark_suite": "terra_350_benchmark.json",
            "total_evaluations": 1750,
            "comparative_pipelines": [
                "1_Direct_LLM",
                "2_Flat_Vector_RAG",
                "3_HippoRAG_Adapted",
                "4_GraphRAG_Adapted",
                "5_Full_TERRA"
            ]
        }
    }

    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    sz = os.path.getsize(cfg_path)
    h = sha256_file(cfg_path)
    print(f"  Created {cfg_path} ({sz:,} B)")
    print(f"  SHA256: {h}")
    return cfg_path, sz, h

def main():
    print("=" * 80)
    print("TERRA ISSUE #39: EXPORTING REPRODUCIBILITY ARTIFACTS")
    print("=" * 80)

    generated = []

    # 1. Edge List TSV
    p, sz, h = export_edges_tsv()
    generated.append((p, sz, h))

    # 2. Invalidation Pairs JSON
    p, sz, h = export_invalidation_pairs()
    generated.append((p, sz, h))

    # 3. Canonical Eval JSON
    p, sz, h = copy_canonical_eval()
    generated.append((p, sz, h))

    # 4. Five Prompt Files
    prompts = export_prompts()
    generated.extend(prompts)

    # 5. Config JSON
    p, sz, h = export_configs()
    generated.append((p, sz, h))

    print("\n" + "=" * 80)
    print(f"PHASE 3 ARTIFACT GENERATION COMPLETE: {len(generated)}/9 ARTIFACTS PRODUCED")
    print("=" * 80)
    for idx, (path, sz, h) in enumerate(generated, 1):
        print(f"  {idx}. {path:<42} | Size: {sz:>10,} B | SHA256: {h}")

    print("\nAll 9 Phase-3 generated artifacts verified and ready.")

if __name__ == "__main__":
    main()
