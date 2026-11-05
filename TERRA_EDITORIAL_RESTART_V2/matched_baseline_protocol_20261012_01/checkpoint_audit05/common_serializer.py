"""
common_serializer.py
--------------------
Standardized evidence formatter, context packer, and tokenizer interface.
Guarantees byte-level formatting parity across Arm H and Arm T,
enforces immutable PackedEvidence payloads, and guards token ceilings.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple


class ConfigurationError(Exception):
    """Raised when an unauthorized, missing, or unverified production artifact is accessed."""
    pass


class SecurityViolationError(Exception):
    """Raised when forbidden operations (e.g. live network calls in mock mode) are attempted."""
    pass


class TokenBudgetExceededError(Exception):
    """Raised when base prompt or mandatory text exceeds the allocated token ceiling."""
    pass


@dataclass(frozen=True)
class EvidenceItem:
    """Strictly validated evidence item schema ensuring information parity."""
    case_id: str
    title: str
    decision_date: str
    holding: str
    thinking_trace: str = ""
    snippet: str = ""
    relation_context: Optional[str] = None

    def __post_init__(self):
        if not self.case_id or not str(self.case_id).strip():
            raise ValueError("EvidenceItem requires a non-empty 'case_id'.")
        if not self.title or not str(self.title).strip():
            object.__setattr__(self, "title", "Unknown Title")
        if not self.decision_date:
            object.__setattr__(self, "decision_date", "Unknown Date")


@dataclass(frozen=True)
class PackedEvidence:
    """
    Immutable representation of evidence packed within token budgets.
    Guarantees exact identity between generator, verifier, and judges.
    """
    retained_items: Tuple[EvidenceItem, ...]
    retained_ids: Tuple[str, ...]
    dropped_items: Tuple[EvidenceItem, ...]
    dropped_ids: Tuple[str, ...]
    prompt_text: str
    prompt_tokens: int
    evidence_tokens: int
    base_template_tokens: int
    content_sha256: str


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
    Synthetic mock tokenizer for CI and synthetic test execution only.
    Note: This is a synthetic regex tokenizer for test determinism,
    NOT an authoritative byte-level emulation of official LLaMA 3 BPE.
    """

    def __init__(self, vocab_marker: str = "synthetic_mock_bpe"):
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
        Synthesize chat template with explicit boundary markers without double-BOS.
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
    Production LLaMA 3.3 tokenizer wrapper placeholder.
    Fail-closed: raises ConfigurationError in code-only mode.
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


def format_evidence_item(item: EvidenceItem, index: int) -> str:
    """
    Format a single EvidenceItem into a standardized string.
    Guarantees deterministic, byte-identical formatting regardless of retrieval arm.
    """
    lines = [f"[Document {index}] ID: {item.case_id} | Title: {item.title} ({item.decision_date})"]
    if item.holding:
        lines.append(f"Holding: {item.holding}")
    if item.thinking_trace:
        lines.append(f"Procedural Scaffold: {item.thinking_trace}")
    if item.relation_context:
        lines.append(f"Relation Context: {item.relation_context}")
    if item.snippet:
        lines.append(f"Snippet: {item.snippet}")
    return "\n".join(lines)


class CommonSerializer:
    """
    Standard serializer packing prompt, instructions, and retrieved evidence.
    Enforces distinct evidence token budget and total prompt token ceilings,
    and returns an immutable PackedEvidence payload.
    """

    def __init__(
        self,
        tokenizer: TokenizerInterface,
        max_evidence_tokens: int = 6000,
        max_prompt_tokens: int = 7000,
        output_token_reservation: int = 4096,
        provider_context_window: int = 128000,
    ):
        if max_prompt_tokens + output_token_reservation > provider_context_window:
            raise ConfigurationError(
                f"Configuration violates context window limit: prompt ({max_prompt_tokens}) + "
                f"reservation ({output_token_reservation}) = "
                f"{max_prompt_tokens + output_token_reservation} > window ({provider_context_window})"
            )
        self.tokenizer = tokenizer
        self.max_evidence_tokens = max_evidence_tokens
        self.max_prompt_tokens = max_prompt_tokens
        self.output_token_reservation = output_token_reservation
        self.provider_context_window = provider_context_window

    def pack_and_serialize(
        self,
        system_instruction: str,
        query: str,
        raw_evidence: List[Dict[str, Any]],
    ) -> PackedEvidence:
        """
        Build formatted prompt with chat template, trimming evidence items if needed.
        Raises TokenBudgetExceededError if base template exceeds max_prompt_tokens.
        Returns immutable PackedEvidence object.
        """
        # Step 0: Validate raw evidence into EvidenceItem objects
        validated_items: List[EvidenceItem] = []
        for raw in raw_evidence:
            if isinstance(raw, EvidenceItem):
                validated_items.append(raw)
            elif isinstance(raw, dict):
                c_id = str(raw.get("case_id", "")).strip()
                if not c_id:
                    continue  # Ignore unidentifiable items
                title = str(raw.get("title", "Unknown Title")).strip()
                date = str(raw.get("decision_date", raw.get("date", "Unknown Date"))).strip()
                holding = str(raw.get("holding", raw.get("substantive_holding", ""))).strip()
                trace = str(raw.get("thinking_trace", "")).strip()
                snip = str(raw.get("snippet", raw.get("text_snip", ""))).strip()
                rel = str(raw.get("relation_context", "")).strip() or None
                validated_items.append(
                    EvidenceItem(
                        case_id=c_id,
                        title=title,
                        decision_date=date,
                        holding=holding,
                        thinking_trace=trace,
                        snippet=snip,
                        relation_context=rel,
                    )
                )

        # Step 1: Base prompt template token measurement (empty evidence)
        empty_user_content = (
            f"Query:\n{query}\n\nEvidence Documents:\nNo evidence provided.\n\n"
            f"Answer the query faithfully based strictly on the provided evidence."
        )
        base_messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": empty_user_content},
        ]
        base_rendered = self.tokenizer.apply_chat_template(base_messages, add_generation_prompt=True)
        base_tokens = self.tokenizer.count_tokens(base_rendered)

        if base_tokens > self.max_prompt_tokens:
            raise TokenBudgetExceededError(
                f"Base prompt template alone ({base_tokens} tokens) exceeds maximum prompt token ceiling "
                f"({self.max_prompt_tokens})."
            )

        # Step 2: Greedily pack evidence items within budgets
        retained: List[EvidenceItem] = []
        dropped: List[EvidenceItem] = []

        for item in validated_items:
            candidate_list = retained + [item]
            cand_blocks = [format_evidence_item(it, idx + 1) for idx, it in enumerate(candidate_list)]
            cand_evidence_text = "\n\n---\n\n".join(cand_blocks)
            cand_evidence_tokens = self.tokenizer.count_tokens(cand_evidence_text)

            cand_user_content = (
                f"Query:\n{query}\n\nEvidence Documents:\n{cand_evidence_text}\n\n"
                f"Answer the query faithfully based strictly on the provided evidence."
            )
            cand_messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": cand_user_content},
            ]
            cand_rendered = self.tokenizer.apply_chat_template(cand_messages, add_generation_prompt=True)
            cand_prompt_tokens = self.tokenizer.count_tokens(cand_rendered)

            if cand_evidence_tokens <= self.max_evidence_tokens and cand_prompt_tokens <= self.max_prompt_tokens:
                retained.append(item)
            else:
                dropped.append(item)

        # Step 3: Render final prompt with retained items
        if retained:
            final_blocks = [format_evidence_item(it, idx + 1) for idx, it in enumerate(retained)]
            final_evidence_text = "\n\n---\n\n".join(final_blocks)
            final_evidence_tokens = self.tokenizer.count_tokens(final_evidence_text)
            final_user_content = (
                f"Query:\n{query}\n\nEvidence Documents:\n{final_evidence_text}\n\n"
                f"Answer the query faithfully based strictly on the provided evidence."
            )
        else:
            final_evidence_tokens = 0
            final_user_content = empty_user_content

        final_messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": final_user_content},
        ]
        final_prompt = self.tokenizer.apply_chat_template(final_messages, add_generation_prompt=True)
        final_prompt_tokens = self.tokenizer.count_tokens(final_prompt)

        # Step 4: Build immutable PackedEvidence
        evidence_fingerprint = hashlib.sha256(final_prompt.encode("utf-8")).hexdigest()

        return PackedEvidence(
            retained_items=tuple(retained),
            retained_ids=tuple(it.case_id for it in retained),
            dropped_items=tuple(dropped),
            dropped_ids=tuple(it.case_id for it in dropped),
            prompt_text=final_prompt,
            prompt_tokens=final_prompt_tokens,
            evidence_tokens=final_evidence_tokens,
            base_template_tokens=base_tokens,
            content_sha256=evidence_fingerprint,
        )

    # Backward compatibility alias
    def serialize_prompt(
        self,
        system_instruction: str,
        query: str,
        evidence_items: List[Dict[str, Any]],
    ) -> Tuple[str, int, int]:
        packed = self.pack_and_serialize(system_instruction, query, evidence_items)
        return packed.prompt_text, packed.prompt_tokens, len(packed.retained_items)
