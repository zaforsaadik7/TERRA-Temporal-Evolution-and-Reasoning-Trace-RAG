import os
import sys
import json
import time
import chromadb
import networkx as nx
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

# Load local environment configurations
load_dotenv()

# 1. Configure Gemini Client (Optional if running purely with local LLM / Ollama)
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# Configure OpenAI / OpenRouter / Local Ollama Client
import openai
openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
use_local_ollama = os.environ.get("USE_LOCAL_OLLAMA", "").strip().lower() in ("true", "1", "yes") or openai_api_key.lower() == "ollama"

if use_local_ollama:
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "hf.co/unsloth/gemma-4-12b-it-GGUF:Q4_K_M")
    print(f"[LOCAL OLLAMA] Using local model '{OLLAMA_MODEL}' at http://localhost:11434/v1 (No API key needed!)")
    openai_client = openai.OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
else:
    OLLAMA_MODEL = None
    if not openai_api_key and not client:
        raise KeyError("Neither OPENAI_API_KEY nor GEMINI_API_KEY is set in environment. Please configure at least one in a local .env file.")
    if openai_api_key.startswith("sk-or-"):
        openai_client = openai.OpenAI(api_key=openai_api_key, base_url="https://openrouter.ai/api/v1")
    elif openai_api_key:
        openai_client = openai.OpenAI(api_key=openai_api_key)
    else:
        openai_client = None

def clean_json_text(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p_strip = p.strip()
            if p_strip.startswith("json"):
                p_strip = p_strip[4:].strip()
            if p_strip.startswith("{") and p_strip.endswith("}"):
                return p_strip
            if p_strip.startswith("[") and p_strip.endswith("]"):
                return p_strip
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

class CleanResponse:
    def __init__(self, orig_resp, is_json=False, model_used=None):
        self._orig = orig_resp
        self._is_json = is_json
        self.model_used = model_used
    @property
    def text(self):
        t = self._orig.text
        if self._is_json:
            return clean_json_text(t)
        return t

def generate_content_with_retry(client, model, contents, config=None, max_retries=5):
    # Enforce temperature=0.0 for deterministic outputs (TIER 1.6)
    if config is None:
        config = {}
    is_json = False
    if isinstance(config, dict):
        config['temperature'] = 0.0
        if config.get('response_mime_type') == 'application/json' or 'response_schema' in config:
            is_json = True
    else:
        try:
            config.temperature = 0.0
            if getattr(config, 'response_mime_type', None) == 'application/json' or getattr(config, 'response_schema', None):
                is_json = True
        except AttributeError:
            pass

    # Candidate models for fallback if daily/minute quota exceeded
    candidate_models = [model, "gemma-4-26b-a4b-it", "gemma-4-31b-it", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    for m in models_to_try:
        m_str = m.name.lower() if hasattr(m, "name") else str(m).lower()
        is_unlimited_daily = ("gemma" in m_str)
        effective_retries = max(max_retries, 6) if is_unlimited_daily else max_retries
        for attempt in range(effective_retries):
            try:
                call_config = dict(config) if isinstance(config, dict) else config
                call_contents = contents
                if "gemma" in m_str:
                    # For gemma open-weight models, remove schema from config to prevent server hang/grammar mismatch
                    if isinstance(call_config, dict):
                        schema_obj = call_config.pop('response_schema', None)
                        call_config.pop('response_mime_type', None)
                        if is_json and isinstance(call_contents, str) and "JSON" not in call_contents:
                            if schema_obj and hasattr(schema_obj, '__fields__'):
                                keys = ", ".join(schema_obj.__fields__.keys())
                                call_contents += f"\n\nIMPORTANT: Output strictly a valid JSON object with keys: {keys}. No extra text."
                            else:
                                call_contents += "\n\nIMPORTANT: Output strictly a valid JSON object. No extra text."
                
                r = client.models.generate_content(
                    model=m,
                    contents=call_contents,
                    config=call_config
                )
                return CleanResponse(r, is_json=is_json, model_used=m)
            except Exception as e:
                err_str = str(e)
                if "Quota exceeded" in err_str and ("500" in err_str or "GenerateRequestsPerDay" in err_str):
                    print(f"[QUOTA FALLBACK] Daily quota exceeded for {m}. Trying next candidate model...")
                    sys.stdout.flush()
                    break  # Break inner loop to try next model right away
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                    wait_time = 20
                    print(f"Rate limited or server busy on {m}. Sleeping for {wait_time}s before retry (Attempt {attempt+1}/{effective_retries})...")
                    sys.stdout.flush()
                    time.sleep(wait_time)
                else:
                    print(f"[MODEL ERROR] Error on {m}: {e}. Trying next candidate model...")
                    sys.stdout.flush()
                    break
    raise RuntimeError("Failed to generate content after maximum retries and model fallbacks due to rate limiting or model errors.")

class CleanResponseOpenAI:
    def __init__(self, text, is_json=False, model_used=None):
        self._text = text
        self._is_json = is_json
        self.model_used = model_used
    @property
    def text(self):
        t = self._text
        if self._is_json:
            return clean_json_text(t)
        return t

def generate_content_with_retry_openai(openai_client, model, contents, config=None, max_retries=5):
    model_mapping = {
        "gemma-4-26b-a4b-it-fast": "gpt-4o-mini",
        "gemma-4-26b-a4b-it": "gpt-4o",
        "gemma-4-31b-it": "gpt-4o",
        "gemini-flash-latest": "gpt-4o",
        "gemini-3.5-flash": "gpt-4o",
        "gemini-3-flash-preview": "gpt-4o",
        "gemini-3.1-flash-lite": "gpt-4o",
        "gemini-2.5-flash": "gpt-4o",
    }
    openai_model = model_mapping.get(model, model)
    
    is_json = False
    if config:
        if isinstance(config, dict):
            if config.get('response_mime_type') == 'application/json' or 'response_schema' in config:
                is_json = True
        else:
            if getattr(config, 'response_mime_type', None) == 'application/json' or getattr(config, 'response_schema', None):
                is_json = True

    import openai
    if OLLAMA_MODEL:
        candidate_models = [OLLAMA_MODEL]
    else:
        candidate_models = [openai_model, "gpt-4o", "gpt-4o-mini"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    for m in models_to_try:
        for attempt in range(max_retries):
            try:
                call_contents = contents
                extra_args = {}
                if is_json:
                    if "json" not in call_contents.lower():
                        call_contents += "\n\nIMPORTANT: Output strictly a valid JSON object."
                    if not OLLAMA_MODEL:
                        extra_args["response_format"] = {"type": "json_object"}
                    
                messages = [{"role": "user", "content": call_contents}]
                response = openai_client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=0.0,
                    **extra_args
                )
                text_content = response.choices[0].message.content
                return CleanResponseOpenAI(text_content, is_json=is_json, model_used=m)
            except openai.AuthenticationError as e:
                print(f"[OPENAI AUTH ERROR] Invalid OpenAI API Key: {e}")
                raise RuntimeError("Invalid OPENAI_API_KEY in .env file. Please configure a valid OpenAI API key in .env.") from e
            except openai.BadRequestError as e:
                print(f"[OPENAI BAD REQUEST ERROR] Request rejected by model: {e}")
                if ("context" in str(e).lower() or "exceed" in str(e).lower() or "tokens" in str(e).lower()) and len(call_contents) > 4000:
                    print("[CONTEXT CAP] Truncating oversized prompt to 4000 chars...")
                    call_contents = call_contents[:4000] + "\n... [Context truncated]"
                    continue
                raise e
            except (openai.RateLimitError, openai.APIStatusError) as e:
                err_str = str(e)
                wait_time = 15 * (attempt + 1)
                print(f"[OPENAI RETRY] Rate limit or server error on {m}: {e}. Sleeping {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                sys.stdout.flush()
                time.sleep(wait_time)
            except openai.APIConnectionError as e:
                wait_time = 5
                print(f"[OPENAI CONN ERROR] Connection error on {m}: {e}. Sleeping {wait_time}s...")
                sys.stdout.flush()
                time.sleep(wait_time)
            except Exception as e:
                print(f"[OPENAI ERROR] Unexpected error on {m}: {e}. Trying next candidate model...")
                sys.stdout.flush()
                break
    raise RuntimeError("Failed to generate content via OpenAI after maximum retries and model fallbacks.")

# 2. Reconstruct the Event Evolution Graph (EEG)
print("Loading Event Evolution Graph...")
try:
    with open("terra_eeg_index.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    eeg = nx.node_link_graph(graph_data, edges="edges" if "edges" in graph_data else "links")
except Exception as e:
    print(f"[FATAL ERROR] Could not load graph: {e}")
    exit(1)

# 3. Connect to the Thinking Traces Vector Database
print("Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./terra_vector_db")
collection = chroma_client.get_or_create_collection(name="thinking_traces")


# --- MODULE 3: THE TRAFFIC COP (Structured Intent Router) ---
class RoutingDecision(BaseModel):
    complexity: str  # Must be 'EASY' or 'HARD'
    reason: str

def is_query_in_domain(query_text: str) -> bool:
    """Dynamically checks if a query is in-domain using curated case titles and vector distances."""
    # 1. Direct active curated case name substring matches (filtering out synthetic cases)
    active_case_titles = [
        eeg.nodes[n].get("title", "")
        for n in eeg.nodes
        if eeg.nodes[n].get("title") and not eeg.nodes[n].get("is_synthetic", False)
    ]
    query_lower = query_text.lower()
    for title in active_case_titles:
        if title and len(title) > 4 and title.lower() in query_lower:
            return True
            
    # 2. ChromaDB vector space proximity check (threshold-based semantic safety check)
    try:
        if collection.count() > 0:
            results = collection.query(query_texts=[query_text], n_results=1)
            if results and results.get('distances') and results['distances'][0]:
                distance = results['distances'][0][0]
                # Clean L2 distance threshold for domain boundary: distance < 1.3
                if distance < 1.3:
                    return True
    except Exception as e:
        print(f"[DOMAIN CHECK ERROR] {e}")
    return False

def traffic_cop_router(user_query: str) -> str:
    in_domain = is_query_in_domain(user_query)
    
    # Compile dynamic active titles to contextualize the routing prompt
    active_case_titles = [
        eeg.nodes[n].get("title", "")
        for n in eeg.nodes
        if eeg.nodes[n].get("title") and not eeg.nodes[n].get("is_synthetic", False)
    ]
    titles_list = ", ".join(active_case_titles[:10])
    
    prompt = f"""You are a routing classifier for a legal AI system. Classify the query below as either 'EASY' or 'HARD'.

    EASY — Use when the query is a simple, single-point factual lookup:
      - Asking for a specific year or date (e.g. "In what year was X decided?")
      - Asking for a case citation (e.g. "What is the U.S. Reports citation for X?")
      - Asking for the name of a ruling, doctrine, or single case fact
      - Any question answerable with one sentence from memory
      Examples: "When was Brown v. Board decided?", "What is the citation for Plessy v. Ferguson?"

    HARD — Use when the query requires reasoning, comparison, or multiple cases:
      - Tracking legal evolution over time (e.g., "How did X change from Y to Z?")
      - Comparing multiple cases or doctrines
      - Questions outside the civil rights constitutional law domain
      - Any open-ended analytical question

    Domain Relevance Flag: {"IN-DOMAIN" if in_domain else "OUT-OF-DOMAIN"}
    IMPORTANT: If OUT-OF-DOMAIN and the query cannot be answered from SCOTUS civil rights cases, you MUST classify as HARD (which triggers safety refusal).

    Active in-domain topics include: {titles_list}

    Query: {user_query}

    Respond with JSON containing keys "complexity" (EASY or HARD) and "reason"."""
    try:
        response = generate_content_with_retry_openai(
            openai_client=openai_client,
            model="gemma-4-26b-a4b-it-fast",
            contents=prompt,
            config={'response_mime_type': 'application/json', 'response_schema': RoutingDecision}
        )
        result = json.loads(response.text)
        complexity_raw = result.get('complexity') or result.get('classification') or result.get('route') or "HARD"
        complexity = str(complexity_raw).strip().upper()
        if complexity not in ("EASY", "HARD"):
            complexity = "HARD"
        reason = result.get('reason') or result.get('reasoning') or ""
        print(f"[TRAFFIC COP] Classification: {complexity} | Reason: {reason}")
        return complexity
    except Exception as e:
        print(f"[TRAFFIC COP ERROR] Defaulting to HARD path. Error: {e}")
        return "HARD"


# --- MODULE 4: THE SMART GRADER (Semantic Entailment Check) ---
class GradeDecision(BaseModel):
    entails: bool
    confidence_score: float  # 0.0 to 1.0

def smart_grader(user_query: str, retrieved_context: str) -> bool:
    prompt = f"""
    You are an NLI (Natural Language Inference) model acting as a quality control grader.
    Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query.
    
    User Query: {user_query}
    
    Legal Context: 
    {retrieved_context}
    """
    try:
        response = generate_content_with_retry_openai(
            openai_client=openai_client,
            model="gemma-4-26b-a4b-it",
            contents=prompt,
            config={'response_mime_type': 'application/json', 'response_schema': GradeDecision}
        )
        result = json.loads(response.text)
        print(f"[SMART GRADER] Entailment Passed: {result['entails']} | Confidence: {result['confidence_score']}")
        return result['entails']
    except Exception as e:
        print(f"[SMART GRADER ERROR] Assuming True for safety. Error: {e}")
        return True


# --- INFERENCE ENGINE SUPPORT FUNCTIONS ---

def extract_graph_context(retrieved_metadatas, max_depth=2, max_nodes=15) -> str:
    """
    Upgraded Graph Trajectory Extractor.
    Performs multi-hop traversal with max_depth and max_nodes cap to prevent context explosion.
    """
    structural_context = ""
    visited_nodes = set()
    
    # We will traverse starting from the cases retrieved in the vector search / fallback
    queue = []
    for meta in retrieved_metadatas:
        case_id = meta.get('case_id')
        if case_id and eeg.has_node(case_id):
            queue.append((case_id, 0)) # Store (node, current_depth)
            
    while queue and len(visited_nodes) < max_nodes:
        current_id, depth = queue.pop(0)
        
        if current_id in visited_nodes or depth > max_depth:
            continue
            
        visited_nodes.add(current_id)
        
        # FIX ISSUE 3: Safe dictionary access for the current node
        current_node_data = eeg.nodes.get(current_id, {})
        current_title = current_node_data.get('title', current_id)
        
        structural_context += f"\n--- Structural Path for {current_title} (Case ID: {current_id}) (Depth {depth}) ---\n"
        
        # Safe Neighbor/Successor Traversal
        if eeg.has_node(current_id):
            # Check outgoing relations (e.g., who this case overrules/precedes)
            for neighbor in eeg.neighbors(current_id):
                edge_data = eeg.get_edge_data(current_id, neighbor) or {}
                relation = edge_data.get('relation', 'CONNECTED')
                
                # Safe access for neighbor node
                neighbor_data = eeg.nodes.get(neighbor, {})
                neighbor_title = neighbor_data.get('title', neighbor)
                
                structural_context += f"- LOGICAL RELATION: This case (Case ID: {current_id}) [{relation}] the case: '{neighbor_title}' (Case ID: {neighbor}).\n"
                
                if neighbor not in visited_nodes and depth + 1 <= max_depth:
                    queue.append((neighbor, depth + 1))
            
            # Check predecessors (who chronologically came before)
            for predecessor in eeg.predecessors(current_id):
                edge_data = eeg.get_edge_data(predecessor, current_id) or {}
                relation = edge_data.get('relation', 'CONNECTED')
                
                # Safe access for predecessor node
                pred_data = eeg.nodes.get(predecessor, {})
                pred_title = pred_data.get('title', predecessor)
                
                if relation == "PRECEDES":
                    structural_context += f"- CHRONOLOGICAL FLOW: The older case '{pred_title}' (Case ID: {predecessor}) historically [PRECEDES] this case (Case ID: {current_id}).\n"
                
                if predecessor not in visited_nodes and depth + 1 <= max_depth:
                    queue.append((predecessor, depth + 1))
                    
    return structural_context


# --- MAIN INFERENCE ENGINE ---

def terra_inference_engine(user_query, return_timing=False):
    print(f"\n[TERRA] Ingesting query: '{user_query}'")
    _t_start = time.time()
    _timing = {}

    # STEP 1: Route traffic using the Traffic Cop
    _t0 = time.time()
    route = traffic_cop_router(user_query)
    _timing['routing_ms'] = round((time.time() - _t0) * 1000, 2)
    
    # PATH A: FAST/CHEAP PATH FOR EASY QUERIES
    if route == "EASY":
        print("[TERRA] Executing Fast Path (Direct Answer)...")
        system_prompt = f"Answer this straightforward factual question briefly: {user_query}"
        _t0 = time.time()
        response = generate_content_with_retry_openai(openai_client=openai_client, model="gemma-4-26b-a4b-it-fast", contents=system_prompt)
        _timing['generation_ms'] = round((time.time() - _t0) * 1000, 2)
        _timing['retrieval_ms'] = 0.0
        _timing['grading_ms'] = 0.0
        _timing['total_ms'] = round((time.time() - _t_start) * 1000, 2)
        _timing['_generation_model_used'] = response.model_used
        if return_timing:
            return response.text.strip(), "Direct LLM (No RAG Context)", _timing
        return response.text.strip(), "Direct LLM (No RAG Context)"
    
    # PATH B: COMPLEX GRAPH-RAG PATH FOR HARD QUERIES
    print("[TERRA] Activating Deep GraphRAG Pipeline...")
    
    # FIX ISSUE 4 & 5: Dynamic Retrieval & Self-Correction Loop
    n_results = 2
    full_compiled_context = ""
    context_is_valid = False
    
    for attempt in range(2): # Try twice: primary attempt and expanded fallback
        print(f"[TERRA] Retrieval Attempt {attempt + 1}: Querying ChromaDB with n_results={n_results}")

        _t0 = time.time()
        retrieved_traces = []
        retrieved_metadatas = []
        if collection.count() > 0:
            vector_results = collection.query(query_texts=[user_query], n_results=n_results)
            retrieved_traces = vector_results.get('documents', [[]])[0]
            retrieved_metadatas = vector_results.get('metadatas', [[]])[0]
        else:
            # Fallback to direct EEG graph seeding using title matching
            query_lower = user_query.lower()
            for n, data in eeg.nodes(data=True):
                title = data.get("title", "")
                if title and any(w in title.lower() for w in query_lower.split() if len(w) > 3):
                    retrieved_metadatas.append({"case_id": n})
                    if len(retrieved_metadatas) >= n_results:
                        break

        structural_context = extract_graph_context(retrieved_metadatas, max_depth=2, max_nodes=15)
        traces_context = "\n".join([f"- {t}" for t in retrieved_traces])
        full_compiled_context = f"{structural_context}\n{traces_context}".strip()
        if len(full_compiled_context) > 8000:
            full_compiled_context = full_compiled_context[:8000] + "\n... [Context truncated for optimal LLM context size]"
        _timing.setdefault('retrieval_ms', round((time.time() - _t0) * 1000, 2))

        # Evaluate context quality with the Smart Grader
        _t0 = time.time()
        context_is_valid = smart_grader(user_query, full_compiled_context)
        _timing.setdefault('grading_ms', round((time.time() - _t0) * 1000, 2))

        if context_is_valid:
            break

        print("[TERRA WARNING] Smart Grader detected insufficient context. Attempting expansion...")
        n_results += 2
    
    # Strict Out-of-Context Block
    if not context_is_valid:
        _timing['generation_ms'] = 0.0
        _timing['total_ms'] = round((time.time() - _t_start) * 1000, 2)
        _timing['_generation_model_used'] = None
        refusal = "I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."
        if return_timing:
            return refusal, full_compiled_context, _timing
        return refusal, full_compiled_context
    
    # STEP 3: Generate Final Answer
    system_prompt = f"""
    You are TERRA, an advanced legal reasoning AI. Answer the User Query using ONLY the provided context.
    
    [CONTEXT DATA]
    {full_compiled_context}
    
    [INSTRUCTIONS]
    For any legal case you mention in your answer that has an explicit Case ID listed in the CONTEXT DATA (e.g. Case ID: 5 for Brown v. Board of Education), format the case title as a relative markdown link using its ID, e.g. "[Brown v. Board of Education](/case/5)".
    Only format links for cases that have explicit Case IDs provided in the context data.
    
    User Query: {user_query}
    
    TERRA Grounded Legal Answer:
    """
    
    _t0 = time.time()
    response = generate_content_with_retry_openai(
        openai_client=openai_client,
        model="gemma-4-26b-a4b-it",
        contents=system_prompt
    )
    _timing['generation_ms'] = round((time.time() - _t0) * 1000, 2)
    _timing['total_ms'] = round((time.time() - _t_start) * 1000, 2)
    _timing['_generation_model_used'] = response.model_used
    if return_timing:
        return response.text.strip(), full_compiled_context, _timing
    return response.text.strip(), full_compiled_context


if __name__ == "__main__":
    # Test 1: Hard Evolutionary Query (Will succeed)
    hard_query = "How did the Supreme Court's stance on racial segregation change from the late 1800s to the 1950s, and which specific ruling was completely overturned?"
    answer_hard, _ = terra_inference_engine(hard_query)
    print(f"\n================== HARD QUERY RESPONSE ==================\n{answer_hard}\n========================================================")
    
    print("\n" + "#"*60 + "\n")
    
    # Test 2: Out of context query (Will trigger self-correction, fail, and gracefully decline)
    impossible_query = "What did the Supreme Court rule in Roe v. Wade regarding abortion rights?"
    answer_impossible, _ = terra_inference_engine(impossible_query)
    print(f"\n================== IMPOSSIBLE QUERY RESPONSE ==================\n{answer_impossible}\n========================================================")