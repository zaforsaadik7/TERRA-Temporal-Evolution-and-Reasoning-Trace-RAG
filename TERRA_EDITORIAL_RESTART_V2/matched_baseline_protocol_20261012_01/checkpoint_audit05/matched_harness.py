"""
matched_harness.py
------------------
Paired pipeline orchestrator comparing Arm H and Arm T.
Enforces:
- Strict SyntheticMockAdapter verification across all callbacks and fetchers.
- Two-phase pre-call ledger reservation with in-flight monetary cost reservation and reload on resume.
- Settle-on-failure across ALL stages (router, verifier, generator, judges) with preserved partial state.
- Separation of full dense candidate stream (Arm H, 100) vs graph seed slice (Arm T, 2).
- Accurate refusal/refutation classification with quotation and negation awareness.
- Atomic OS-level lock (O_CREAT | O_EXCL), journal validation, duplicate prevention, and clean lock ownership.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .common_serializer import (
    CommonSerializer,
    ConfigurationError,
    EvidenceItem,
    PackedEvidence,
    SecurityViolationError,
    TokenBudgetExceededError,
)
from .hybrid_retriever import HybridRetriever
from .terra_retriever import TerraRetriever


class ExecutionMode(str, Enum):
    SYNTHETIC_MOCK = "SYNTHETIC_MOCK"
    AUTHORIZED_LIVE = "AUTHORIZED_LIVE"


class OutcomeType(str, Enum):
    SUBSTANTIVE_ANSWER = "SUBSTANTIVE_ANSWER"
    PREMISE_REFUTATION = "PREMISE_REFUTATION"
    EXPLICIT_ABSTENTION = "EXPLICIT_ABSTENTION"
    MIXED_OR_UNCERTAIN = "MIXED_OR_UNCERTAIN"
    EMPTY_OR_UNPARSEABLE = "EMPTY_OR_UNPARSEABLE"
    API_ERROR = "API_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class TransportNetworkError(Exception):
    """Explicit transport or network failure exception."""
    pass


class DuplicateExecutionError(Exception):
    """Raised when attempting to execute an already completed query."""
    pass


class DuplicateRecordError(Exception):
    """Raised when duplicate query records exist in the journal."""
    pass


class CorruptedJournalError(Exception):
    """Raised when journal or results file is corrupted."""
    pass


class UnresolvedCallError(Exception):
    """Raised when un-settled in-flight calls are detected upon restart."""
    pass


class SyntheticMockAdapter:
    """Wrapper marking a callable as a verified synthetic mock fixture."""

    def __init__(self, fn: Callable, name: str = "mock"):
        self.fn = fn
        self.name = name
        self.is_synthetic_mock = True

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


def mock_adapter(fn: Callable, name: str = "mock") -> SyntheticMockAdapter:
    return SyntheticMockAdapter(fn, name)


@dataclass(frozen=True)
class QueryInput:
    """Strictly query-only runtime input with sanitized ID."""
    query_id: str
    query_text: str
    category: str = "B"

    def __post_init__(self):
        if not re.match(r"^[a-zA-Z0-9_\-]+$", self.query_id):
            raise ValueError(f"Invalid query_id '{self.query_id}': contains unsafe characters.")


@dataclass
class ArmResult:
    arm_name: str  # 'Arm_H' or 'Arm_T'
    retrieved_ids: List[str]
    retained_ids: List[str]
    dropped_ids: List[str]
    prompt_tokens: int
    evidence_tokens: int
    evidence_sha256: str
    router_route: str  # 'EASY' or 'HARD'
    outcome_type: OutcomeType
    verifier_passed: bool
    is_refusal: bool
    refusal_reason: Optional[str]
    output_text: Optional[str]
    judge1_faithfulness: Optional[float]
    judge2_faithfulness: Optional[float]
    composite_faithfulness: Optional[float]
    latency_ms: float = 0.0
    attempts: int = 1
    api_error: bool = False
    error_message: Optional[str] = None


@dataclass
class PairedResult:
    query_id: str
    category: str
    arm_h: ArmResult
    arm_t: ArmResult
    faithfulness_diff: Optional[float]  # Arm_T - Arm_H
    execution_order: Tuple[str, str]
    timestamp_utc: float = field(default_factory=time.time)


@dataclass
class CallLedgerEntry:
    call_id: str
    query_id: str
    stage: str
    arm_name: Optional[str]
    call_index: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    reserved_cost_usd: float = 0.0
    cost_usd: float = 0.0
    status: str = "RESERVED"


class CallLedger:
    """
    Two-phase call ledger: reserves ceiling and in-flight cost BEFORE callback dispatch,
    settles after. Reloads existing state on resume and detects unresolved in-flight calls.
    """

    def __init__(
        self,
        max_logical_calls: int = 3150,
        max_spend_usd: float = 100.0,
        ledger_path: Optional[Path] = None,
    ):
        self.max_logical_calls = max_logical_calls
        self.max_spend_usd = max_spend_usd
        self.ledger_path = ledger_path
        self.entries: List[CallLedgerEntry] = []
        self._counter: int = 0
        self._cumulative_settled_cost_usd: float = 0.0
        self._in_flight_cost_usd: float = 0.0
        self._budget_breached: bool = False

        if self.ledger_path and self.ledger_path.exists():
            self._reload_from_file()

    def _reload_from_file(self):
        call_map: Dict[str, CallLedgerEntry] = {}
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                clean = line.strip()
                if not clean:
                    continue
                try:
                    data = json.loads(clean)
                    entry = CallLedgerEntry(**data)
                except (json.JSONDecodeError, TypeError) as ex:
                    raise CorruptedJournalError(f"Corrupted ledger entry at line {line_no}: {ex}")

                # Monotonic sequence & transition replay validation
                if entry.call_id not in call_map:
                    call_map[entry.call_id] = entry
                else:
                    prev = call_map[entry.call_id]
                    if prev.status != "RESERVED":
                        raise DuplicateRecordError(
                            f"Duplicate settlement for call '{entry.call_id}' at line {line_no}"
                        )
                    call_map[entry.call_id] = entry

        # After full replay, check if any call ended in unresolved RESERVED state
        unresolved = [e for e in call_map.values() if e.status == "RESERVED"]
        if unresolved:
            first_unresolved = unresolved[0]
            raise UnresolvedCallError(
                f"Unresolved in-flight call '{first_unresolved.call_id}' detected. "
                "Manual reconciliation required before restart."
            )

        self.entries = list(call_map.values())
        self._cumulative_settled_cost_usd = sum(e.cost_usd for e in self.entries)
        self._counter = len(self.entries)
        if self._cumulative_settled_cost_usd > self.max_spend_usd:
            self._budget_breached = True

    def reserve_call(
        self,
        query_id: str,
        stage: str,
        arm_name: Optional[str],
        estimated_cost_usd: float = 0.0,
    ) -> str:
        """Reserve call slot and in-flight cost before dispatch."""
        if self._budget_breached:
            raise ConfigurationError(
                f"Monetary spend cap breached (settled ${self._cumulative_settled_cost_usd:.2f} > cap ${self.max_spend_usd:.2f}). "
                "Further dispatch halted."
            )
        if not isinstance(estimated_cost_usd, (int, float)) or math.isnan(estimated_cost_usd) or math.isinf(estimated_cost_usd) or estimated_cost_usd < 0.0:
            raise ValueError(f"Invalid estimated_cost_usd: {estimated_cost_usd}")

        if self._counter + 1 > self.max_logical_calls:
            raise ConfigurationError(
                f"Logical call envelope exceeded before dispatch: attempt {self._counter + 1} > max {self.max_logical_calls}"
            )
        projected_total = self._cumulative_settled_cost_usd + self._in_flight_cost_usd + estimated_cost_usd
        if projected_total > self.max_spend_usd:
            raise ConfigurationError(
                f"Monetary spend cap exceeded: in-flight reservation ${projected_total:.2f} > cap ${self.max_spend_usd:.2f}"
            )

        self._counter += 1
        self._in_flight_cost_usd += estimated_cost_usd
        call_id = f"call_{self._counter}_{uuid.uuid4().hex[:8]}"
        entry = CallLedgerEntry(
            call_id=call_id,
            query_id=query_id,
            stage=stage,
            arm_name=arm_name,
            call_index=self._counter,
            reserved_cost_usd=estimated_cost_usd,
            status="RESERVED",
        )
        self.entries.append(entry)
        self._persist_entry(entry)
        return call_id

    def settle_call(
        self,
        call_id: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        status: str = "COMPLETED",
        cost_usd: float = 0.0,
    ) -> None:
        """Settle call usage, cost, and status after callback execution."""
        if not isinstance(cost_usd, (int, float)) or math.isnan(cost_usd) or math.isinf(cost_usd) or cost_usd < 0.0:
            raise ValueError(f"Invalid cost_usd: {cost_usd}")

        entry = None
        for e in self.entries:
            if e.call_id == call_id:
                entry = e
                break

        if not entry:
            raise ValueError(f"Unknown call_id '{call_id}' in call ledger settlement.")
        if entry.status != "RESERVED":
            raise ValueError(f"Call '{call_id}' was already settled with status '{entry.status}'.")

        # Deduct in-flight reservation
        self._in_flight_cost_usd = max(0.0, self._in_flight_cost_usd - entry.reserved_cost_usd)

        # Record actual usage and cost truthfully
        entry.prompt_tokens = prompt_tokens
        entry.completion_tokens = completion_tokens
        entry.latency_ms = latency_ms
        entry.cost_usd = float(cost_usd)
        self._cumulative_settled_cost_usd += float(cost_usd)

        if self._cumulative_settled_cost_usd > self.max_spend_usd:
            self._budget_breached = True
            entry.status = "BUDGET_BREACH"
            self._persist_entry(entry)
            raise ConfigurationError(
                f"Settled cost ${self._cumulative_settled_cost_usd:.2f} breached cap ${self.max_spend_usd:.2f}. "
                "Incurred spend recorded truthfully; further dispatch halted."
            )

        entry.status = status
        self._persist_entry(entry)

    def _persist_entry(self, entry: CallLedgerEntry):
        if self.ledger_path:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")

    @property
    def total_calls(self) -> int:
        return self._counter

    @property
    def cumulative_settled_cost(self) -> float:
        return self._cumulative_settled_cost_usd


class RunPersistenceManager:
    """
    Exclusive atomic process run manager with OS-level locking (O_CREAT | O_EXCL),
    strict duplicate prevention, and corruption detection.
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.session_uuid = uuid.uuid4().hex
        self.lock_file = self.run_dir / ".run.lock"
        self.results_file = self.run_dir / "paired_results.jsonl"
        self.ledger_file = self.run_dir / "call_ledger.jsonl"
        self._acquire_atomic_lock()

    def _acquire_atomic_lock(self):
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.lock_file), flags, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"PID={os.getpid()}\nUUID={self.session_uuid}\nSTART={time.time()}\n")
        except FileExistsError:
            raise FileExistsError(
                f"Run lock exists at '{self.lock_file}'. Another process is active or terminated abnormally. "
                "Manual reconciliation required before proceeding."
            )

    def release_lock(self):
        if not self.lock_file.exists():
            raise FileNotFoundError(f"Lock file '{self.lock_file}' does not exist to release.")
        content = self.lock_file.read_text(encoding="utf-8")
        if f"UUID={self.session_uuid}" not in content:
            raise PermissionError("Attempted to release lock owned by another session.")
        self.lock_file.unlink()

    def get_completed_query_ids(self) -> Set[str]:
        if not self.results_file.exists():
            return set()
        completed = set()
        with open(self.results_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                clean = line.strip()
                if not clean:
                    continue
                try:
                    record = json.loads(clean)
                    qid = record.get("query_id")
                    if not qid or "arm_h" not in record or "arm_t" not in record:
                        raise CorruptedJournalError(f"Incomplete record structure at line {line_no}")
                    if qid in completed:
                        raise DuplicateRecordError(f"Duplicate query_id '{qid}' at line {line_no}")
                    completed.add(qid)
                except json.JSONDecodeError as ex:
                    raise CorruptedJournalError(
                        f"Corrupted journal record at {self.results_file}:{line_no}: {ex}"
                    )
        return completed

    def atomic_append_result(self, result: PairedResult):
        record_dict = asdict(result)
        line = json.dumps(record_dict, default=str) + "\n"
        with open(self.results_file, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


class MatchedHarness:
    """
    Executes paired evaluations across Arm H and Arm T under identical conditions.
    """

    def __init__(
        self,
        serializer: CommonSerializer,
        router_fn: Callable[[str], str],
        verifier_fn: Callable[[str, Tuple[EvidenceItem, ...]], Tuple[bool, Optional[str]]],
        generator_fn: Callable[[str], str],
        judge1_fn: Callable[[str, str, Tuple[EvidenceItem, ...]], float],
        judge2_fn: Callable[[str, str, Tuple[EvidenceItem, ...]], float],
        execution_mode: ExecutionMode = ExecutionMode.SYNTHETIC_MOCK,
        persistence_manager: Optional[RunPersistenceManager] = None,
        call_ledger: Optional[CallLedger] = None,
    ):
        if execution_mode == ExecutionMode.AUTHORIZED_LIVE:
            raise ConfigurationError("AUTHORIZED_LIVE mode is not permitted in code-only stage.")

        # Guard: In mock mode, ALL callbacks must be verified SyntheticMockAdapters
        for name, fn in [
            ("router_fn", router_fn),
            ("verifier_fn", verifier_fn),
            ("generator_fn", generator_fn),
            ("judge1_fn", judge1_fn),
            ("judge2_fn", judge2_fn),
        ]:
            if not getattr(fn, "is_synthetic_mock", False):
                raise SecurityViolationError(
                    f"Callback '{name}' is not a verified SyntheticMockAdapter. "
                    "Only synthetic mock adapters are authorized in SYNTHETIC_MOCK mode."
                )

        self.serializer = serializer
        self.router_fn = router_fn
        self.verifier_fn = verifier_fn
        self.generator_fn = generator_fn
        self.judge1_fn = judge1_fn
        self.judge2_fn = judge2_fn
        self.execution_mode = execution_mode
        self.persistence_manager = persistence_manager
        self.call_ledger = call_ledger or CallLedger(
            ledger_path=persistence_manager.ledger_file if persistence_manager else None
        )

    def classify_output(self, text: Optional[str]) -> Tuple[OutcomeType, bool]:
        """
        Classify generated output under the agreed rubric.
        Distinguishes substantive premise refutation from genuine epistemic abstention.
        """
        if text is None or not str(text).strip():
            return OutcomeType.EMPTY_OR_UNPARSEABLE, False

        clean_text = str(text).strip()
        lower = clean_text.lower()

        # Check for negation/quotation contexts that should NOT be classified as refusal
        is_negated_or_quoted = bool(
            re.search(r"\b(not\s+decline|did\s+not\s+refuse|not\s+unable|quoted\s+statement|the\s+claim\s+that)\b", lower)
            or ('"i cannot' in lower or "'i cannot" in lower)
        )

        # Genuine abstention patterns
        abstention_patterns = [
            "i cannot answer",
            "i decline to answer",
            "unable to answer",
            "insufficient evidence to determine",
            "i cannot provide an answer",
            "as an ai, i cannot",
        ]
        has_abstention = any(pat in lower for pat in abstention_patterns) and not is_negated_or_quoted

        # Premise refutation / historical overruling explanation
        refutation_patterns = [
            "was overruled by",
            "is overruled by",
            "no longer good law",
            "precedent was superseded",
            "repudiated by",
        ]
        has_refutation = any(pat in lower for pat in refutation_patterns)

        if has_abstention and has_refutation:
            return OutcomeType.MIXED_OR_UNCERTAIN, False
        if has_abstention:
            return OutcomeType.EXPLICIT_ABSTENTION, True
        if has_refutation:
            return OutcomeType.PREMISE_REFUTATION, False

        return OutcomeType.SUBSTANTIVE_ANSWER, False

    def run_arm(
        self,
        arm_name: str,
        query: QueryInput,
        route: str,
        raw_evidence: List[Dict[str, Any]],
        system_instruction: str,
    ) -> ArmResult:
        """
        Execute a single arm under pre-call ledger reservation and strict exception typing.
        """
        t0 = time.perf_counter()
        retrieved_ids = [str(it.get("case_id", "")) for it in raw_evidence if isinstance(it, dict)]

        # Step 1: Pack evidence
        packed: PackedEvidence = self.serializer.pack_and_serialize(
            system_instruction=system_instruction,
            query=query.query_text,
            raw_evidence=raw_evidence,
        )

        # Step 2: NLI Verifier check with pre-call reservation
        call_id_v = self.call_ledger.reserve_call(query.query_id, "VERIFIER", arm_name)
        try:
            t_v0 = time.perf_counter()
            v_passed, v_refusal_reason = self.verifier_fn(query.query_text, packed.retained_items)
            t_v_ms = (time.perf_counter() - t_v0) * 1000.0
            self.call_ledger.settle_call(
                call_id_v, prompt_tokens=packed.evidence_tokens, latency_ms=t_v_ms, status="COMPLETED"
            )
        except TransportNetworkError as ex:
            self.call_ledger.settle_call(call_id_v, status="FAILED")
            return self._build_api_error_result(arm_name, retrieved_ids, route, str(ex), t0, packed=packed)

        if not v_passed:
            # Epistemic refusal triggered by verifier
            refusal_text = v_refusal_reason or "Precedent overruled or insufficient evidence."
            j1, j2 = self._evaluate_dual_judges(query.query_id, arm_name, query.query_text, refusal_text, packed)
            both_ok = (j1 is not None and j2 is not None)
            comp = (j1 + j2) / 2.0 if both_ok else None
            total_lat = (time.perf_counter() - t0) * 1000.0

            return ArmResult(
                arm_name=arm_name,
                retrieved_ids=retrieved_ids,
                retained_ids=list(packed.retained_ids),
                dropped_ids=list(packed.dropped_ids),
                prompt_tokens=packed.prompt_tokens,
                evidence_tokens=packed.evidence_tokens,
                evidence_sha256=packed.content_sha256,
                router_route=route,
                outcome_type=OutcomeType.EXPLICIT_ABSTENTION,
                verifier_passed=False,
                is_refusal=True,
                refusal_reason=refusal_text,
                output_text=refusal_text,
                judge1_faithfulness=j1,
                judge2_faithfulness=j2,
                composite_faithfulness=comp,
                latency_ms=total_lat,
                api_error=(not both_ok),
                error_message=None if both_ok else "One or more judge evaluations failed",
            )

        # Step 3: Generator call with pre-call reservation
        call_id_g = self.call_ledger.reserve_call(query.query_id, "GENERATOR", arm_name)
        try:
            t_g0 = time.perf_counter()
            gen_text = self.generator_fn(packed.prompt_text)
            t_g_ms = (time.perf_counter() - t_g0) * 1000.0
            g_tokens = self.serializer.tokenizer.count_tokens(gen_text) if gen_text else 0
            self.call_ledger.settle_call(
                call_id_g,
                prompt_tokens=packed.prompt_tokens,
                completion_tokens=g_tokens,
                latency_ms=t_g_ms,
                status="COMPLETED",
            )
        except TransportNetworkError as ex:
            self.call_ledger.settle_call(call_id_g, status="FAILED")
            return self._build_api_error_result(arm_name, retrieved_ids, route, str(ex), t0, packed=packed)

        # Step 4: Classify output
        outcome, is_ref = self.classify_output(gen_text)

        # If output is empty or whitespace, do NOT call judges
        if outcome == OutcomeType.EMPTY_OR_UNPARSEABLE:
            total_lat = (time.perf_counter() - t0) * 1000.0
            return ArmResult(
                arm_name=arm_name,
                retrieved_ids=retrieved_ids,
                retained_ids=list(packed.retained_ids),
                dropped_ids=list(packed.dropped_ids),
                prompt_tokens=packed.prompt_tokens,
                evidence_tokens=packed.evidence_tokens,
                evidence_sha256=packed.content_sha256,
                router_route=route,
                outcome_type=OutcomeType.EMPTY_OR_UNPARSEABLE,
                verifier_passed=True,
                is_refusal=False,
                refusal_reason=None,
                output_text=gen_text,
                judge1_faithfulness=None,
                judge2_faithfulness=None,
                composite_faithfulness=None,
                latency_ms=total_lat,
            )

        # Evaluate dual judges
        j1, j2 = self._evaluate_dual_judges(query.query_id, arm_name, query.query_text, gen_text, packed)
        both_ok = (j1 is not None and j2 is not None)
        comp = (j1 + j2) / 2.0 if both_ok else None
        total_lat = (time.perf_counter() - t0) * 1000.0

        return ArmResult(
            arm_name=arm_name,
            retrieved_ids=retrieved_ids,
            retained_ids=list(packed.retained_ids),
            dropped_ids=list(packed.dropped_ids),
            prompt_tokens=packed.prompt_tokens,
            evidence_tokens=packed.evidence_tokens,
            evidence_sha256=packed.content_sha256,
            router_route=route,
            outcome_type=outcome,
            verifier_passed=True,
            is_refusal=is_ref,
            refusal_reason=gen_text if is_ref else None,
            output_text=gen_text,
            judge1_faithfulness=j1,
            judge2_faithfulness=j2,
            composite_faithfulness=comp,
            latency_ms=total_lat,
            api_error=(not both_ok),
            error_message=None if both_ok else "One or more judge evaluations failed",
        )

    def _evaluate_dual_judges(
        self,
        query_id: str,
        arm_name: str,
        query_text: str,
        answer_text: str,
        packed: PackedEvidence,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Evaluate Judge 1 and Judge 2 independently, preserving partial scores on failure."""
        j1_score: Optional[float] = None
        j2_score: Optional[float] = None

        # Judge 1
        call_id_j1 = self.call_ledger.reserve_call(query_id, "JUDGE1", arm_name)
        try:
            t_j1_0 = time.perf_counter()
            score = float(self.judge1_fn(query_text, answer_text, packed.retained_items))
            t_j1_ms = (time.perf_counter() - t_j1_0) * 1000.0
            if math.isnan(score) or math.isinf(score) or not (0.0 <= score <= 1.0):
                raise ValueError(f"Judge 1 score {score} outside [0, 1]")
            self.call_ledger.settle_call(call_id_j1, latency_ms=t_j1_ms, status="COMPLETED")
            j1_score = score
        except (TransportNetworkError, ValueError):
            self.call_ledger.settle_call(call_id_j1, status="FAILED")

        # Judge 2
        call_id_j2 = self.call_ledger.reserve_call(query_id, "JUDGE2", arm_name)
        try:
            t_j2_0 = time.perf_counter()
            score = float(self.judge2_fn(query_text, answer_text, packed.retained_items))
            t_j2_ms = (time.perf_counter() - t_j2_0) * 1000.0
            if math.isnan(score) or math.isinf(score) or not (0.0 <= score <= 1.0):
                raise ValueError(f"Judge 2 score {score} outside [0, 1]")
            self.call_ledger.settle_call(call_id_j2, latency_ms=t_j2_ms, status="COMPLETED")
            j2_score = score
        except (TransportNetworkError, ValueError):
            self.call_ledger.settle_call(call_id_j2, status="FAILED")

        return j1_score, j2_score

    def _build_api_error_result(
        self,
        arm_name: str,
        retrieved_ids: List[str],
        route: str,
        msg: str,
        t0: float,
        packed: Optional[PackedEvidence] = None,
        output_text: Optional[str] = None,
        outcome_type: OutcomeType = OutcomeType.API_ERROR,
        verifier_passed: bool = False,
        is_refusal: bool = False,
        refusal_reason: Optional[str] = None,
        judge1_faithfulness: Optional[float] = None,
        judge2_faithfulness: Optional[float] = None,
    ) -> ArmResult:
        lat = (time.perf_counter() - t0) * 1000.0
        return ArmResult(
            arm_name=arm_name,
            retrieved_ids=retrieved_ids,
            retained_ids=list(packed.retained_ids) if packed else [],
            dropped_ids=list(packed.dropped_ids) if packed else [],
            prompt_tokens=packed.prompt_tokens if packed else 0,
            evidence_tokens=packed.evidence_tokens if packed else 0,
            evidence_sha256=packed.content_sha256 if packed else "",
            router_route=route,
            outcome_type=outcome_type,
            verifier_passed=verifier_passed,
            is_refusal=is_refusal,
            refusal_reason=refusal_reason,
            output_text=output_text,
            judge1_faithfulness=judge1_faithfulness,
            judge2_faithfulness=judge2_faithfulness,
            composite_faithfulness=None,
            latency_ms=lat,
            api_error=True,
            error_message=msg,
        )

    def run_query_pair(
        self,
        query: QueryInput,
        dense_candidate_fetcher_fn: Callable[[str], List[str]],
        terra_retriever: TerraRetriever,
        hybrid_retriever: HybridRetriever,
        system_instruction: str,
        seed_k: int = 2,
    ) -> PairedResult:
        """
        Complete end-to-end query execution connecting router to retrieval policies.
        Separates full dense candidate stream (Arm H) from graph seed slice (Arm T).
        """
        if not getattr(dense_candidate_fetcher_fn, "is_synthetic_mock", False):
            raise SecurityViolationError("dense_candidate_fetcher_fn is not a verified SyntheticMockAdapter.")

        if self.persistence_manager:
            completed = self.persistence_manager.get_completed_query_ids()
            if query.query_id in completed:
                raise DuplicateExecutionError(f"Query '{query.query_id}' already executed.")

        # Step 0: Router with pre-call reservation
        call_id_r = self.call_ledger.reserve_call(query.query_id, "ROUTER", None)
        try:
            t_r0 = time.perf_counter()
            route = self.router_fn(query.query_text)
            t_r_ms = (time.perf_counter() - t_r0) * 1000.0
            self.call_ledger.settle_call(call_id_r, latency_ms=t_r_ms, status="COMPLETED")
        except TransportNetworkError as ex:
            self.call_ledger.settle_call(call_id_r, status="FAILED")
            res_h = self._build_api_error_result("Arm_H", [], "UNKNOWN", str(ex), time.perf_counter())
            res_t = self._build_api_error_result("Arm_T", [], "UNKNOWN", str(ex), time.perf_counter())
            paired = PairedResult(query.query_id, query.category, res_h, res_t, None, ("Arm_H", "Arm_T"))
            if self.persistence_manager:
                self.persistence_manager.atomic_append_result(paired)
            return paired

        if route not in ("EASY", "HARD"):
            raise ConfigurationError(f"Invalid route '{route}'. Allowed: EASY, HARD.")

        # Fetch dense candidates stream
        dense_candidates = dense_candidate_fetcher_fn(query.query_text)
        seed_slice = dense_candidates[:seed_k]

        # Dispatch retrieval policies
        if route == "EASY":
            # EASY route: Arm H runs hybrid fusion on dense stream; Arm T uses seeds directly without expansion (0-hop)
            ev_h = hybrid_retriever.retrieve(query.query_text, dense_ranked_ids=dense_candidates)
            ev_t = terra_retriever.retrieve(seed_node_ids=seed_slice, top_n=seed_k, max_depth_override=0)
        else:
            # HARD route: Arm H runs full hybrid fusion; Arm T runs full multi-hop traversal
            ev_h = hybrid_retriever.retrieve(query.query_text, dense_ranked_ids=dense_candidates)
            ev_t = terra_retriever.retrieve(seed_node_ids=seed_slice)

        # Prospective order interleaving
        q_hash = int(hashlib.sha256(query.query_id.encode("utf-8")).hexdigest(), 16)
        if q_hash % 2 == 0:
            order = ("Arm_H", "Arm_T")
            res_h = self.run_arm("Arm_H", query, route, ev_h, system_instruction)
            res_t = self.run_arm("Arm_T", query, route, ev_t, system_instruction)
        else:
            order = ("Arm_T", "Arm_H")
            res_t = self.run_arm("Arm_T", query, route, ev_t, system_instruction)
            res_h = self.run_arm("Arm_H", query, route, ev_h, system_instruction)

        diff = None
        if res_h.composite_faithfulness is not None and res_t.composite_faithfulness is not None:
            diff = res_t.composite_faithfulness - res_h.composite_faithfulness

        paired = PairedResult(
            query_id=query.query_id,
            category=query.category,
            arm_h=res_h,
            arm_t=res_t,
            faithfulness_diff=diff,
            execution_order=order,
        )

        if self.persistence_manager:
            self.persistence_manager.atomic_append_result(paired)

        return paired
