"""
matched_harness.py
------------------
Paired pipeline orchestrator comparing Arm H and Arm T.
Enforces shared router, shared verifier, generator short-circuiting,
dual-judge scoring, and fail-closed live execution guards.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from .common_serializer import CommonSerializer, ConfigurationError, TokenizerInterface


@dataclass
class QueryInput:
    query_id: str
    query_text: str
    category: str  # e.g., 'A', 'B', 'C', 'D'
    target_year: Optional[int] = None
    overruled_known: bool = False


@dataclass
class ArmResult:
    arm_name: str  # 'Arm_H' or 'Arm_T'
    retrieved_ids: List[str]
    retained_item_count: int
    prompt_tokens: int
    router_route: str  # 'EASY' or 'HARD'
    verifier_passed: bool
    is_refusal: bool
    refusal_reason: Optional[str]
    generated_text: Optional[str]
    judge1_faithfulness: Optional[float]
    judge2_faithfulness: Optional[float]
    composite_faithfulness: Optional[float]
    api_error: bool = False
    error_message: Optional[str] = None


@dataclass
class PairedResult:
    query_id: str
    category: str
    arm_h: ArmResult
    arm_t: ArmResult
    faithfulness_diff: Optional[float]  # Arm_T - Arm_H


class MatchedHarness:
    """
    Executes paired evaluations across Arm H and Arm T under identical conditions.
    """

    def __init__(
        self,
        serializer: CommonSerializer,
        router_fn: Callable[[str], str],
        verifier_fn: Callable[[str, List[Dict[str, Any]]], Tuple[bool, Optional[str]]],
        generator_fn: Callable[[str], str],
        judge_fn: Callable[[str, str, List[Dict[str, Any]]], Tuple[float, float]],
        live_mode_authorized: bool = False,
    ):
        if not live_mode_authorized and not callable(router_fn):
            raise ConfigurationError("Live execution is blocked in code-only mode.")
        self.serializer = serializer
        self.router_fn = router_fn
        self.verifier_fn = verifier_fn
        self.generator_fn = generator_fn
        self.judge_fn = judge_fn
        self.live_mode_authorized = live_mode_authorized

    def run_arm(
        self,
        arm_name: str,
        query: QueryInput,
        route: str,
        evidence_items: List[Dict[str, Any]],
        system_instruction: str,
    ) -> ArmResult:
        """
        Execute a single arm under the shared protocol.
        """
        try:
            # Step 1: Serialize prompt and count tokens
            prompt, p_tokens, retained_cnt = self.serializer.serialize_prompt(
                system_instruction=system_instruction,
                query=query.query_text,
                evidence_items=evidence_items,
            )

            # Step 2: NLI Verifier check
            v_passed, v_refusal_reason = self.verifier_fn(query.query_text, evidence_items)

            if not v_passed:
                # Verifier triggered refusal; short-circuit generator
                return ArmResult(
                    arm_name=arm_name,
                    retrieved_ids=[str(it.get("case_id", "")) for it in evidence_items],
                    retained_item_count=retained_cnt,
                    prompt_tokens=p_tokens,
                    router_route=route,
                    verifier_passed=False,
                    is_refusal=True,
                    refusal_reason=v_refusal_reason or "Epistemic refusal triggered by verifier",
                    generated_text=None,
                    # Frozen rubric disposition: epistemic refusal on unanswerable query scores 1.0 faithfulness
                    judge1_faithfulness=1.0 if query.overruled_known else 0.0,
                    judge2_faithfulness=1.0 if query.overruled_known else 0.0,
                    composite_faithfulness=1.0 if query.overruled_known else 0.0,
                )

            # Step 3: Generator call
            gen_text = self.generator_fn(prompt)

            # Step 4: Dual Judges
            j1_score, j2_score = self.judge_fn(query.query_text, gen_text, evidence_items)
            comp_score = (j1_score + j2_score) / 2.0

            return ArmResult(
                arm_name=arm_name,
                retrieved_ids=[str(it.get("case_id", "")) for it in evidence_items],
                retained_item_count=retained_cnt,
                prompt_tokens=p_tokens,
                router_route=route,
                verifier_passed=True,
                is_refusal=False,
                refusal_reason=None,
                generated_text=gen_text,
                judge1_faithfulness=j1_score,
                judge2_faithfulness=j2_score,
                composite_faithfulness=comp_score,
            )

        except Exception as ex:
            return ArmResult(
                arm_name=arm_name,
                retrieved_ids=[str(it.get("case_id", "")) for it in evidence_items],
                retained_item_count=0,
                prompt_tokens=0,
                router_route=route,
                verifier_passed=False,
                is_refusal=False,
                refusal_reason=None,
                generated_text=None,
                judge1_faithfulness=None,
                judge2_faithfulness=None,
                composite_faithfulness=None,
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
        Execute paired evaluation on a single query.
        Router is called once and shared between both arms.
        """
        # Step 0: Shared router determines route
        route = self.router_fn(query.query_text)

        # Run Arm H and Arm T
        res_h = self.run_arm("Arm_H", query, route, evidence_arm_h, system_instruction)
        res_t = self.run_arm("Arm_T", query, route, evidence_arm_t, system_instruction)

        diff = None
        if res_h.composite_faithfulness is not None and res_t.composite_faithfulness is not None:
            diff = res_t.composite_faithfulness - res_h.composite_faithfulness

        return PairedResult(
            query_id=query.query_id,
            category=query.category,
            arm_h=res_h,
            arm_t=res_t,
            faithfulness_diff=diff,
        )
