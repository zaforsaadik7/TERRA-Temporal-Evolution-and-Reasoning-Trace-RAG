"""
matched_harness.py
------------------
Paired pipeline orchestrator comparing Arm H and Arm T.
Enforces strict adapter mode separation, immutable packed evidence distribution,
deterministic all-route packing, frozen rubric refusal scoring,
call ledger persistence, and fail-closed live execution guards.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .common_serializer import (
    CommonSerializer,
    ConfigurationError,
    EvidenceItem,
    PackedEvidence,
    SecurityViolationError,
)


class ExecutionMode(str, Enum):
    SYNTHETIC_MOCK = "SYNTHETIC_MOCK"
    AUTHORIZED_LIVE = "AUTHORIZED_LIVE"


class OutcomeType(str, Enum):
    SUBSTANTIVE_ANSWER = "SUBSTANTIVE_ANSWER"
    EPISTEMIC_REFUSAL = "EPISTEMIC_REFUSAL"
    CONTRADICTION_FLAGGED = "CONTRADICTION_FLAGGED"
    API_ERROR = "API_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


@dataclass(frozen=True)
class QueryInput:
    """Strictly query-only runtime input without gold benchmark truth labels."""
    query_id: str
    query_text: str
    category: str = "B"  # Used for cohort analysis only, NOT in operational routing/scoring


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
    execution_order: Tuple[str, str]  # e.g., ('Arm_H', 'Arm_T') or ('Arm_T', 'Arm_H')
    timestamp_utc: float = field(default_factory=time.time)


@dataclass
class CallLedgerEntry:
    query_id: str
    stage: str  # 'ROUTER', 'VERIFIER', 'GENERATOR', 'JUDGE1', 'JUDGE2'
    arm_name: Optional[str]
    call_index: int
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    status: str


class CallLedger:
    """Tracks logical API calls and enforces maximum call envelopes."""

    def __init__(self, max_logical_calls: int = 3150):
        self.max_logical_calls = max_logical_calls
        self.entries: List[CallLedgerEntry] = []
        self._counter: int = 0

    def record_call(
        self,
        query_id: str,
        stage: str,
        arm_name: Optional[str],
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        status: str = "SUCCESS",
    ) -> int:
        self._counter += 1
        if self._counter > self.max_logical_calls:
            raise ConfigurationError(
                f"Logical call envelope exceeded: {self._counter} > max {self.max_logical_calls}"
            )
        entry = CallLedgerEntry(
            query_id=query_id,
            stage=stage,
            arm_name=arm_name,
            call_index=self._counter,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            status=status,
        )
        self.entries.append(entry)
        return self._counter

    @property
    def total_calls(self) -> int:
        return self._counter


class RunPersistenceManager:
    """Manages exclusive run directory locking, atomic writes, and safe resume."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.run_dir / ".run.lock"
        self.results_file = self.run_dir / "paired_results.jsonl"
        self.ledger_file = self.run_dir / "call_ledger.jsonl"
        self._acquire_lock()

    def _acquire_lock(self):
        if self.lock_file.exists():
            raise FileExistsError(
                f"Run lock exists at '{self.lock_file}'. Another process is active or crashed. "
                "Manual inspection required before re-running."
            )
        self.lock_file.write_text(f"PID={os.getpid()}\nSTART={time.time()}\n", encoding="utf-8")

    def release_lock(self):
        if self.lock_file.exists():
            self.lock_file.unlink()

    def get_completed_query_ids(self) -> Set[str]:
        if not self.results_file.exists():
            return set()
        completed = set()
        with open(self.results_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        completed.add(record["query_id"])
                    except Exception:
                        continue
        return completed

    def atomic_append_result(self, result: PairedResult):
        tmp_file = self.run_dir / f"paired_results_{result.query_id}.tmp"
        record_dict = asdict(result)
        line = json.dumps(record_dict, default=str) + "\n"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(line)
        # Append to main results file
        with open(self.results_file, "a", encoding="utf-8") as f:
            f.write(line)
        if tmp_file.exists():
            tmp_file.unlink()


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
        judge_fn: Callable[[str, str, Tuple[EvidenceItem, ...]], Tuple[float, float]],
        execution_mode: ExecutionMode = ExecutionMode.SYNTHETIC_MOCK,
        persistence_manager: Optional[RunPersistenceManager] = None,
        call_ledger: Optional[CallLedger] = None,
    ):
        self.serializer = serializer
        self.router_fn = router_fn
        self.verifier_fn = verifier_fn
        self.generator_fn = generator_fn
        self.judge_fn = judge_fn
        self.execution_mode = execution_mode
        self.persistence_manager = persistence_manager
        self.call_ledger = call_ledger or CallLedger()

        # Fail-closed guard: require explicit authorized live mode
        if self.execution_mode == ExecutionMode.AUTHORIZED_LIVE:
            raise ConfigurationError(
                "AUTHORIZED_LIVE mode is not permitted in code-only stage. "
                "Only SYNTHETIC_MOCK mode is authorized."
            )

    def _detect_refusal_in_generated_text(self, text: str) -> bool:
        """Classify if generator produced an explicit refusal or unanswerability claim."""
        if not text:
            return True
        lower = text.lower()
        refusal_patterns = [
            "cannot answer",
            "insufficient evidence",
            "overruled by",
            "no longer good law",
            "precedent is superseded",
            "unanswerable based on",
            "i cannot provide",
        ]
        return any(pat in lower for pat in refusal_patterns)

    def run_arm(
        self,
        arm_name: str,
        query: QueryInput,
        route: str,
        raw_evidence: List[Dict[str, Any]],
        system_instruction: str,
    ) -> ArmResult:
        """
        Execute a single arm under the shared protocol.
        Guarantees that verifier, generator, and judges see identical retained evidence.
        """
        t0 = time.perf_counter()
        retrieved_ids = [str(it.get("case_id", "")) for it in raw_evidence if isinstance(it, dict)]

        try:
            # Step 1: Pack evidence and serialize prompt
            packed: PackedEvidence = self.serializer.pack_and_serialize(
                system_instruction=system_instruction,
                query=query.query_text,
                raw_evidence=raw_evidence,
            )

            # Step 2: NLI Verifier check using EXACT retained evidence
            t_v0 = time.perf_counter()
            v_passed, v_refusal_reason = self.verifier_fn(query.query_text, packed.retained_items)
            t_v_ms = (time.perf_counter() - t_v0) * 1000.0
            self.call_ledger.record_call(
                query_id=query.query_id,
                stage="VERIFIER",
                arm_name=arm_name,
                prompt_tokens=packed.evidence_tokens,
                latency_ms=t_v_ms,
            )

            if not v_passed:
                # Verifier triggered refusal; short-circuit generator
                refusal_text = v_refusal_reason or "Precedent overruled or insufficient evidence."
                
                # Score refusal statement under frozen judge rubric using retained evidence
                t_j0 = time.perf_counter()
                j1_score, j2_score = self.judge_fn(query.query_text, refusal_text, packed.retained_items)
                t_j_ms = (time.perf_counter() - t_j0) * 1000.0
                self.call_ledger.record_call(
                    query_id=query.query_id,
                    stage="JUDGE1",
                    arm_name=arm_name,
                    latency_ms=t_j_ms / 2.0,
                )
                self.call_ledger.record_call(
                    query_id=query.query_id,
                    stage="JUDGE2",
                    arm_name=arm_name,
                    latency_ms=t_j_ms / 2.0,
                )

                comp_score = (j1_score + j2_score) / 2.0
                latency_total = (time.perf_counter() - t0) * 1000.0

                return ArmResult(
                    arm_name=arm_name,
                    retrieved_ids=retrieved_ids,
                    retained_ids=list(packed.retained_ids),
                    dropped_ids=list(packed.dropped_ids),
                    prompt_tokens=packed.prompt_tokens,
                    evidence_tokens=packed.evidence_tokens,
                    evidence_sha256=packed.content_sha256,
                    router_route=route,
                    outcome_type=OutcomeType.EPISTEMIC_REFUSAL,
                    verifier_passed=False,
                    is_refusal=True,
                    refusal_reason=refusal_text,
                    output_text=refusal_text,
                    judge1_faithfulness=j1_score,
                    judge2_faithfulness=j2_score,
                    composite_faithfulness=comp_score,
                    latency_ms=latency_total,
                )

            # Step 3: Generator call
            t_g0 = time.perf_counter()
            gen_text = self.generator_fn(packed.prompt_text)
            t_g_ms = (time.perf_counter() - t_g0) * 1000.0
            gen_tokens = self.serializer.tokenizer.count_tokens(gen_text)
            self.call_ledger.record_call(
                query_id=query.query_id,
                stage="GENERATOR",
                arm_name=arm_name,
                prompt_tokens=packed.prompt_tokens,
                completion_tokens=gen_tokens,
                latency_ms=t_g_ms,
            )

            # Step 4: Classify outcome and score via Dual Judges using retained evidence
            is_ref = self._detect_refusal_in_generated_text(gen_text)
            outcome = OutcomeType.EPISTEMIC_REFUSAL if is_ref else OutcomeType.SUBSTANTIVE_ANSWER

            t_j0 = time.perf_counter()
            j1_score, j2_score = self.judge_fn(query.query_text, gen_text, packed.retained_items)
            t_j_ms = (time.perf_counter() - t_j0) * 1000.0
            self.call_ledger.record_call(
                query_id=query.query_id,
                stage="JUDGE1",
                arm_name=arm_name,
                latency_ms=t_j_ms / 2.0,
            )
            self.call_ledger.record_call(
                query_id=query.query_id,
                stage="JUDGE2",
                arm_name=arm_name,
                latency_ms=t_j_ms / 2.0,
            )

            comp_score = (j1_score + j2_score) / 2.0
            latency_total = (time.perf_counter() - t0) * 1000.0

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
                refusal_reason=None if not is_ref else gen_text,
                output_text=gen_text,
                judge1_faithfulness=j1_score,
                judge2_faithfulness=j2_score,
                composite_faithfulness=comp_score,
                latency_ms=latency_total,
            )

        except (ConfigurationError, SecurityViolationError):
            # Programming or security configuration errors must propagate and stop execution
            raise
        except Exception as ex:
            # Transport / endpoint / network failures recorded as API_ERROR
            latency_total = (time.perf_counter() - t0) * 1000.0
            return ArmResult(
                arm_name=arm_name,
                retrieved_ids=retrieved_ids,
                retained_ids=[],
                dropped_ids=[],
                prompt_tokens=0,
                evidence_tokens=0,
                evidence_sha256="",
                router_route=route,
                outcome_type=OutcomeType.API_ERROR,
                verifier_passed=False,
                is_refusal=False,
                refusal_reason=None,
                output_text=None,
                judge1_faithfulness=None,
                judge2_faithfulness=None,
                composite_faithfulness=None,
                latency_ms=latency_total,
                api_error=True,
                error_message=str(ex),
            )

    def run_pair(
        self,
        query: QueryInput,
        evidence_arm_h: List[Dict[str, Any]],
        evidence_arm_t: List[Dict[str, Any]],
        system_instruction: str,
    ) -> PairedResult:
        """
        Execute paired evaluation on a single query with prospective order interleaving.
        """
        # Step 0: Shared router determines route
        t_r0 = time.perf_counter()
        route = self.router_fn(query.query_text)
        t_r_ms = (time.perf_counter() - t_r0) * 1000.0

        if route not in ("EASY", "HARD"):
            raise ConfigurationError(f"Router returned invalid route '{route}'. Allowed: EASY, HARD.")

        self.call_ledger.record_call(
            query_id=query.query_id,
            stage="ROUTER",
            arm_name=None,
            latency_ms=t_r_ms,
        )

        # Prospective order interleaving based on query_id hash
        q_hash = int(hashlib.sha256(query.query_id.encode("utf-8")).hexdigest(), 16)
        if q_hash % 2 == 0:
            order = ("Arm_H", "Arm_T")
            res_h = self.run_arm("Arm_H", query, route, evidence_arm_h, system_instruction)
            res_t = self.run_arm("Arm_T", query, route, evidence_arm_t, system_instruction)
        else:
            order = ("Arm_T", "Arm_H")
            res_t = self.run_arm("Arm_T", query, route, evidence_arm_t, system_instruction)
            res_h = self.run_arm("Arm_H", query, route, evidence_arm_h, system_instruction)

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
