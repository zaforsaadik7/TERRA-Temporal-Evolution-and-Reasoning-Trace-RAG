"""
common_serializer.py
--------------------
Standardized evidence formatter, context packer, and tokenizer interface.
Guarantees byte-level formatting parity across Arm H and Arm T,
enforces exact token budget ceilings, and prevents double BOS/EOS insertion.
"""

from abc import ABC, abstractmethod
import json
import re
from typing import Any, Dict, List, Optional


class ConfigurationError(Exception):
    """Raised when an unauthorized or unverified production artifact is accessed."""
    pass


class TokenizerInterface(ABC):
    """Abstract interface decoupling token counting and chat templating."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Return exact token count for the given text."""
        pass

    @abstractmethod
    def apply_chat_template(
        self,
        messages: List[Dict[str, str]],
        add_generation_prompt: bool = True,
    ) -> str:
        """Format a list of chat messages into a model input string."""
        pass


class MockBpeTokenizer(TokenizerInterface):
    """
    Deterministic tokenizer for synthetic testing and CI.
    Emulates LLaMA 3.3 BPE tokenization and chat formatting markers.
    """

    def __init__(self, vocab_marker: str = "synthetic_llama3"):
        self.vocab_marker = vocab_marker

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        # Tokenize by word-pieces, punctuation, whitespace
        tokens = re.findall(r"\w+|[^\w\s]|\s+", text)
        return len(tokens)

    def apply_chat_template(
        self,
        messages: List[Dict[str, str]],
        add_generation_prompt: bool = True,
    ) -> str:
        """
        Emulate LLaMA 3.3 Instruct chat template without double-BOS.
        Format:
          <|start_header_id|>role<|end_header_id|>
          
          content<|eot_id|>
        """
        parts = ["<|begin_of_text|>"]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
        if add_generation_prompt:
            parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        return "".join(parts)


class ProductionTokenizer(TokenizerInterface):
    """
    Production LLaMA 3.3 tokenizer wrapper.
    Fail-closed: raises ConfigurationError unless verified artifact is explicitly loaded.
    """

    def __init__(self, tokenizer_path: Optional[str] = None):
        if not tokenizer_path:
            raise ConfigurationError(
                "Production tokenizer artifact path is required but not provided. "
                "Operation blocked under fail-closed code-only governance."
            )
        raise ConfigurationError(
            f"Production tokenizer at '{tokenizer_path}' has not yet been authorized or verified. "
            "Offline preflight download gate must be passed first."
        )

    def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    def apply_chat_template(
        self,
        messages: List[Dict[str, str]],
        add_generation_prompt: bool = True,
    ) -> str:
        raise NotImplementedError


def format_evidence_item(item: Dict[str, Any], index: int) -> str:
    """
    Format a single evidence node into a standardized string.
    Guarantees deterministic, byte-identical formatting regardless of retrieval arm.
    """
    doc_id = str(item.get("case_id", ""))
    title = str(item.get("title", "Unknown Title")).strip()
    date = str(item.get("decision_date", item.get("date", "Unknown Date"))).strip()
    holding = str(item.get("holding", item.get("substantive_holding", ""))).strip()
    scaffold = str(item.get("thinking_trace", "")).strip()
    snippet = str(item.get("snippet", item.get("text_snip", ""))).strip()
    rel = str(item.get("relation_context", "")).strip()

    lines = [f"[Document {index}] ID: {doc_id} | Title: {title} ({date})"]
    if holding:
        lines.append(f"Holding: {holding}")
    if scaffold:
        lines.append(f"Procedural Scaffold: {scaffold}")
    if rel:
        lines.append(f"Relation Context: {rel}")
    if snippet:
        lines.append(f"Snippet: {snippet}")

    return "\n".join(lines)


class CommonSerializer:
    """
    Standard serializer packing prompt, instructions, and retrieved evidence.
    Enforces maximum prompt token ceiling (default 6,000 tokens).
    """

    def __init__(
        self,
        tokenizer: TokenizerInterface,
        max_prompt_tokens: int = 6000,
        output_token_reservation: int = 4096,
    ):
        self.tokenizer = tokenizer
        self.max_prompt_tokens = max_prompt_tokens
        self.output_token_reservation = output_token_reservation

    def serialize_prompt(
        self,
        system_instruction: str,
        query: str,
        evidence_items: List[Dict[str, Any]],
    ) -> Tuple[str, int, int]:
        """
        Build formatted prompt with chat template, trimming evidence items if needed
        to stay strictly under max_prompt_tokens.
        
        Returns: (final_serialized_prompt, prompt_token_count, num_evidence_items_retained)
        """
        # Greedily include evidence items from rank 1 to N
        retained_items: List[Dict[str, Any]] = []

        for item in evidence_items:
            candidate_list = retained_items + [item]
            evidence_blocks = [
                format_evidence_item(it, idx + 1)
                for idx, it in enumerate(candidate_list)
            ]
            evidence_text = "\n\n---\n\n".join(evidence_blocks)

            user_content = f"Query:\n{query}\n\nEvidence Documents:\n{evidence_text}\n\nAnswer the query faithfully based strictly on the provided evidence."
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ]
            rendered = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True)
            token_count = self.tokenizer.count_tokens(rendered)

            if token_count <= self.max_prompt_tokens:
                retained_items = candidate_list
            else:
                # Adding this document exceeds the budget; stop adding further documents
                break

        # Render final prompt with retained items
        final_blocks = [
            format_evidence_item(it, idx + 1)
            for idx, it in enumerate(retained_items)
        ]
        final_evidence_text = "\n\n---\n\n".join(final_blocks) if final_blocks else "No evidence provided."
        final_user_content = f"Query:\n{query}\n\nEvidence Documents:\n{final_evidence_text}\n\nAnswer the query faithfully based strictly on the provided evidence."
        final_messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": final_user_content},
        ]
        final_rendered = self.tokenizer.apply_chat_template(final_messages, add_generation_prompt=True)
        final_token_count = self.tokenizer.count_tokens(final_rendered)

        return final_rendered, final_token_count, len(retained_items)
