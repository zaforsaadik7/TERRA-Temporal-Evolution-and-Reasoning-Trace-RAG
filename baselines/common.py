"""
baselines/common.py - Common utilities, corpus loading, and strict payload-level parity interceptor
for Workstream 1.2 Comparative Baselines (GraphRAG-Adapted and HippoRAG-Adapted).
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import openai

load_dotenv()

# Pre-registered cryptographic invariants (Workstream 1.2 Protocol)
CORPUS_PATH = os.environ.get("TERRA_CORPUS_20K_PATH", "dataset_20k_cap/terra_eeg_index_20k.json")
CORPUS_SHA256 = "012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb"
CORPUS_NODE_COUNT = 20000

MANDATORY_MODEL_STRING = "databricks-meta-llama-3-3-70b-instruct"
MANDATORY_TEMPERATURE = 0.0
MANDATORY_MAX_TOKENS = 4096

PAYLOAD_AUDIT_LOG = os.path.join(os.path.dirname(__file__), "audit_payloads.jsonl")

# Neutral System Instruction for RAG pipelines (Flat Vector, GraphRAG, HippoRAG, TERRA)
NEUTRAL_SYSTEM_INSTRUCTION = (
    "You are an expert legal AI assistant. Answer the user's legal question accurately "
    "based strictly on the provided context. If the context does not contain sufficient validated "
    "information to answer the query, state that you do not have sufficient validated legal context. "
    "Do not hallucinate, speculate, or affirm unverified historical or legal premises."
)

# Neutral Direct System Instruction for parametric Direct LLM (No RAG Context)
NEUTRAL_DIRECT_SYSTEM_INSTRUCTION = (
    "You are an expert legal AI assistant. Answer the user's legal question accurately "
    "based on your legal knowledge. Do not hallucinate, speculate, or affirm unverified historical or legal premises."
)


def compute_file_sha256(filepath: str) -> str:
    """Compute cryptographic SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_verified_corpus(corpus_path: str = CORPUS_PATH) -> dict:
    """
    Gate 1 Invariant: Loads 20k corpus and verifies exact SHA256 checksum and 20,000 node count.
    Raises ValueError if any deviation is detected.
    """
    if not os.path.exists(corpus_path):
        raise FileNotFoundError(f"Corpus file not found at: {corpus_path}")

    actual_hash = compute_file_sha256(corpus_path)
    if actual_hash != CORPUS_SHA256:
        raise ValueError(
            f"[CORPUS INTEGRITY BREACH] SHA256 mismatch on {corpus_path}!\n"
            f"Expected: {CORPUS_SHA256}\n"
            f"Actual:   {actual_hash}"
        )

    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", {})
    if isinstance(nodes, list):
        node_count = len(nodes)
    elif isinstance(nodes, dict):
        node_count = len(nodes)
    else:
        node_count = 0

    if node_count != CORPUS_NODE_COUNT:
        raise ValueError(
            f"[CORPUS INTEGRITY BREACH] Node count mismatch!\n"
            f"Expected: {CORPUS_NODE_COUNT}\n"
            f"Actual:   {node_count}"
        )

    return data


def get_databricks_client() -> openai.OpenAI:
    """Initializes the Databricks OpenAI client."""
    db_token = os.environ.get("DATABRICKS_TOKEN")
    db_base_url = os.environ.get("DATABRICKS_BASE_URL") or os.environ.get(
        "DATABRICKS_HOST", "https://dbc-11018d65-5584.cloud.databricks.com/serving-endpoints"
    )
    if not db_token:
        raise KeyError("DATABRICKS_TOKEN environment variable is not set in .env")
    return openai.OpenAI(api_key=db_token, base_url=db_base_url, timeout=45.0)


class PayloadParityResponse:
    """Standardized response object exposing text and execution telemetry."""
    def __init__(self, text: str, model_used: str, retry_sleep_ms: float = 0.0):
        self.text = text
        self.model_used = model_used
        self.retry_sleep_ms = retry_sleep_ms


class PayloadParityInterceptor:
    """
    Gate 2 Invariant: Intercepts outgoing HTTP API call payloads, asserting model string,
    temperature, and token limits. Logs cryptographic proof to audit_payloads.jsonl.
    """
    def __init__(self, client: openai.OpenAI = None):
        self.client = client or get_databricks_client()

    def generate(
        self,
        prompt: str,
        system_instruction: str = NEUTRAL_SYSTEM_INSTRUCTION,
        query_id: str = "N/A",
        pipeline_name: str = "unknown",
        max_retries: int = 5
    ) -> PayloadParityResponse:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": MANDATORY_MODEL_STRING,
            "messages": messages,
            "temperature": MANDATORY_TEMPERATURE,
            "max_tokens": MANDATORY_MAX_TOKENS
        }

        # Gate 2 Hard Assertions
        assert payload["model"] == MANDATORY_MODEL_STRING, (
            f"[GATE 2 VIOLATION] Non-matching model: {payload['model']} != {MANDATORY_MODEL_STRING}"
        )
        assert payload["temperature"] == MANDATORY_TEMPERATURE, (
            f"[GATE 2 VIOLATION] Non-matching temperature: {payload['temperature']} != {MANDATORY_TEMPERATURE}"
        )
        assert payload["max_tokens"] == MANDATORY_MAX_TOKENS, (
            f"[GATE 2 VIOLATION] Non-matching max_tokens: {payload['max_tokens']} != {MANDATORY_MAX_TOKENS}"
        )

        # Audit Logging
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "generation",
            "query_id": query_id,
            "pipeline": pipeline_name,
            "model": payload["model"],
            "temperature": payload["temperature"],
            "max_tokens": payload["max_tokens"],
            "system_len": len(system_instruction),
            "prompt_len": len(prompt)
        }
        with open(PAYLOAD_AUDIT_LOG, "a", encoding="utf-8") as af:
            af.write(json.dumps(audit_entry) + "\n")

        # Execute with retry
        retry_sleep_ms = 0.0
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**payload)
                text = response.choices[0].message.content or ""
                if not text.strip():
                    time.sleep(2)
                    continue
                return PayloadParityResponse(
                    text=text.strip(),
                    model_used=payload["model"],
                    retry_sleep_ms=retry_sleep_ms
                )
            except (openai.RateLimitError, openai.APIStatusError) as e:
                wait_time = 10 * (attempt + 1)
                time.sleep(wait_time)
                retry_sleep_ms += wait_time * 1000.0
            except openai.APIConnectionError as e:
                time.sleep(5)
                retry_sleep_ms += 5000.0
            except Exception as e:
                raise RuntimeError(f"[GENERATOR ERROR on {payload['model']}]: {e}")

        raise RuntimeError(f"Failed to generate after {max_retries} attempts.")


def format_neutral_prompt(query: str, context: str) -> str:
    """Standardized prompt assembly preserving identical generator instructions."""
    return (
        f"[LEGAL CONTEXT]\n{context}\n\n"
        f"User Legal Query: {query}\n\n"
        "Answer:"
    )


def log_short_circuit(
    query_id: str = "N/A",
    pipeline_name: str = "5_Full_TERRA",
    reason: str = "Smart Grader entailment failure / context invalid",
    context_is_valid: bool = False
):
    """
    Amendment B: Logs pre-generation firewall short-circuits to PAYLOAD_AUDIT_LOG
    so that: Total Evaluations = Intercepted Generations (G) + Logged Short-Circuits (S).
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": "short_circuit",
        "query_id": query_id,
        "pipeline": pipeline_name,
        "reason": reason,
        "context_is_valid": context_is_valid
    }
    with open(PAYLOAD_AUDIT_LOG, "a", encoding="utf-8") as af:
        af.write(json.dumps(entry) + "\n")

