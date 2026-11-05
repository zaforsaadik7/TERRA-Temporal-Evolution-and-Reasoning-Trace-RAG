"""
scoring_analyzer.py
-------------------
Implements the pre-specified statistical analysis plan:
- Primary estimand: paired Category B faithfulness difference.
- Paired cluster bootstrap 95% CI (10,000 resamples).
- Two-sided paired randomization test (100,000 sign-flips and exact enumeration for small n).
- Expected cohort denominator protection against omitted queries.
- Mutual consistency validation (rejects API_ERROR with non-null scores).
- Computable full-cohort sensitivity bounds even when valid pairs = 0.
"""

import itertools
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from .matched_harness import PairedResult


class ScoringAnalyzer:
    """
    Computes statistical tests and confidence intervals on paired evaluation results.
    """

    def __init__(
        self,
        bootstrap_resamples: int = 10000,
        randomization_flips: int = 100000,
        expected_cohort_size: Optional[int] = 100,
        seed: int = 42,
    ):
        if not isinstance(bootstrap_resamples, int) or bootstrap_resamples <= 0:
            raise ValueError(f"bootstrap_resamples must be a positive int, got {bootstrap_resamples}")
        if not isinstance(randomization_flips, int) or randomization_flips <= 0:
            raise ValueError(f"randomization_flips must be a positive int, got {randomization_flips}")

        self.bootstrap_resamples = bootstrap_resamples
        self.randomization_flips = randomization_flips
        self.expected_cohort_size = expected_cohort_size
        self.seed = seed

    def compute_paired_bootstrap_ci(
        self,
        diffs: List[float],
        confidence_level: float = 0.95,
    ) -> Optional[Tuple[float, float, float]]:
        """
        Compute mean difference and percentile bootstrap CI on paired differences.
        """
        if not diffs:
            return None

        if not (0.0 < confidence_level < 1.0):
            raise ValueError(f"confidence_level must be between 0 and 1, got {confidence_level}")

        n = len(diffs)
        for d in diffs:
            if not isinstance(d, (int, float)) or math.isnan(d) or math.isinf(d) or not (-1.0 <= d <= 1.0):
                raise ValueError(f"Invalid diff value for bootstrap: {d}")

        obs_mean = sum(diffs) / float(n)

        rng = random.Random(self.seed)
        boot_means: List[float] = []

        for _ in range(self.bootstrap_resamples):
            sample = [diffs[rng.randint(0, n - 1)] for _ in range(n)]
            boot_means.append(sum(sample) / float(n))

        boot_means.sort()
        alpha = 1.0 - confidence_level
        low_idx = int(math.floor(alpha / 2.0 * self.bootstrap_resamples))
        high_idx = int(math.ceil((1.0 - alpha / 2.0) * self.bootstrap_resamples)) - 1
        low_idx = max(0, min(low_idx, self.bootstrap_resamples - 1))
        high_idx = max(0, min(high_idx, self.bootstrap_resamples - 1))

        ci_lower = boot_means[low_idx]
        ci_upper = boot_means[high_idx]
        return obs_mean, ci_lower, ci_upper

    def compute_exact_paired_randomization_test(
        self,
        diffs: List[float],
    ) -> Optional[Tuple[float, float]]:
        """
        Analytical reference oracle: exact enumeration of all 2^n sign flips (for n <= 15).
        """
        if not diffs:
            return None

        n = len(diffs)
        obs_mean = sum(diffs) / float(n)
        abs_obs = abs(obs_mean)

        exceedances = 0
        total_flips = 1 << n  # 2^n

        for signs in itertools.product((-1.0, 1.0), repeat=n):
            sim_sum = sum(d * s for d, s in zip(diffs, signs))
            sim_mean = sim_sum / float(n)
            if abs(sim_mean) >= abs_obs - 1e-12:
                exceedances += 1

        p_value = float(exceedances) / float(total_flips)
        return obs_mean, p_value

    def compute_paired_randomization_test(
        self,
        diffs: List[float],
    ) -> Optional[Tuple[float, float]]:
        """
        Two-sided paired sign-flip randomization test.
        Uses exact enumeration if n <= 14, otherwise Monte Carlo with (exceedances + 1) / (B + 1).
        """
        if not diffs:
            return None

        n = len(diffs)
        for d in diffs:
            if not isinstance(d, (int, float)) or math.isnan(d) or math.isinf(d) or not (-1.0 <= d <= 1.0):
                raise ValueError(f"Invalid diff value for randomization test: {d}")

        if n <= 14:
            return self.compute_exact_paired_randomization_test(diffs)

        obs_mean = sum(diffs) / float(n)
        abs_obs = abs(obs_mean)

        rng = random.Random(self.seed + 1)
        exceedances = 0

        for _ in range(self.randomization_flips):
            sim_sum = 0.0
            for d in diffs:
                sign = 1.0 if rng.random() >= 0.5 else -1.0
                sim_sum += d * sign
            sim_mean = sim_sum / float(n)
            if abs(sim_mean) >= abs_obs - 1e-12:
                exceedances += 1

        p_value = float(exceedances + 1) / float(self.randomization_flips + 1)
        return obs_mean, p_value

    def analyze_results(
        self,
        paired_results: List[PairedResult],
        target_category: str = "B",
        expected_manifest_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run complete analysis on paired results filtered by target category.
        Enforces mutual consistency, protects expected cohort denominator,
        validates manifest membership when provided, and computes valid sensitivity
        bounds even when valid_pairs = 0.
        """
        cat_results = [r for r in paired_results if r.category == target_category]
        supplied_cohort_size = len(cat_results)

        # Denominator protection: if exact manifest provided, validate against it
        if expected_manifest_ids is not None:
            manifest_set = set(expected_manifest_ids)
            total_cohort_denominator = len(manifest_set)
            unexpected_ids = {r.query_id for r in cat_results if r.query_id not in manifest_set}
            if unexpected_ids:
                raise ValueError(f"Unexpected query_id(s) in cohort not in manifest: {sorted(unexpected_ids)}")
            missing_ids = manifest_set - {r.query_id for r in cat_results}
            omitted_queries = len(missing_ids)
        else:
            total_cohort_denominator = supplied_cohort_size
            if self.expected_cohort_size is not None:
                total_cohort_denominator = max(supplied_cohort_size, self.expected_cohort_size)
            omitted_queries = max(0, total_cohort_denominator - supplied_cohort_size)

        # Step 1: Validate cohort uniqueness
        seen_qids: Set[str] = set()
        for r in cat_results:
            if r.query_id in seen_qids:
                raise ValueError(f"Duplicate query_id detected in cohort: '{r.query_id}'")
            seen_qids.add(r.query_id)

        # Step 2: Mutual consistency and component auditing
        valid_diffs: List[float] = []
        valid_pairs_count = 0
        missing_pairs_count = omitted_queries
        api_error_count = 0
        refusals_h = 0
        refusals_t = 0

        worst_case_sum = -1.0 * float(omitted_queries)
        best_case_sum = 1.0 * float(omitted_queries)

        for r in cat_results:
            # Mutual consistency checks
            if r.arm_h.api_error and r.arm_h.composite_faithfulness is not None:
                raise ValueError(f"Query '{r.query_id}' Arm_H: api_error is True but composite_faithfulness is not None")
            if r.arm_t.api_error and r.arm_t.composite_faithfulness is not None:
                raise ValueError(f"Query '{r.query_id}' Arm_T: api_error is True but composite_faithfulness is not None")

            # Check individual judge average vs composite score
            if r.arm_h.judge1_faithfulness is not None and r.arm_h.judge2_faithfulness is not None:
                exp_h = (r.arm_h.judge1_faithfulness + r.arm_h.judge2_faithfulness) / 2.0
                if r.arm_h.composite_faithfulness is not None and abs(r.arm_h.composite_faithfulness - exp_h) > 1e-6:
                    raise ValueError(f"Query '{r.query_id}' Arm_H composite score does not match average of judges")
            if r.arm_t.judge1_faithfulness is not None and r.arm_t.judge2_faithfulness is not None:
                exp_t = (r.arm_t.judge1_faithfulness + r.arm_t.judge2_faithfulness) / 2.0
                if r.arm_t.composite_faithfulness is not None and abs(r.arm_t.composite_faithfulness - exp_t) > 1e-6:
                    raise ValueError(f"Query '{r.query_id}' Arm_T composite score does not match average of judges")

            if r.arm_h.api_error or r.arm_t.api_error:
                api_error_count += 1
            if r.arm_h.is_refusal:
                refusals_h += 1
            if r.arm_t.is_refusal:
                refusals_t += 1

            score_h = r.arm_h.composite_faithfulness
            score_t = r.arm_t.composite_faithfulness

            if score_h is not None and not (0.0 <= score_h <= 1.0):
                raise ValueError(f"Query '{r.query_id}' Arm_H score {score_h} outside [0.0, 1.0]")
            if score_t is not None and not (0.0 <= score_t <= 1.0):
                raise ValueError(f"Query '{r.query_id}' Arm_T score {score_t} outside [0.0, 1.0]")

            if score_h is not None and score_t is not None:
                recomputed_diff = score_t - score_h
                if not (-1.0 <= recomputed_diff <= 1.0):
                    raise ValueError(f"Recomputed diff {recomputed_diff} outside [-1.0, 1.0]")
                valid_diffs.append(recomputed_diff)
                valid_pairs_count += 1
                worst_case_sum += recomputed_diff
                best_case_sum += recomputed_diff
            else:
                missing_pairs_count += 1
                if score_h is not None and score_t is None:
                    worst_case_sum += (0.0 - score_h)
                    best_case_sum += (1.0 - score_h)
                elif score_h is None and score_t is not None:
                    worst_case_sum += (score_t - 1.0)
                    best_case_sum += (score_t - 0.0)
                else:
                    worst_case_sum += -1.0
                    best_case_sum += 1.0

        # Sensitivity bounds computable across full cohort denominator
        denom = float(total_cohort_denominator) if total_cohort_denominator > 0 else 1.0
        worst_bound = worst_case_sum / denom
        best_bound = best_case_sum / denom

        if valid_pairs_count == 0:
            return {
                "status": "UNAVAILABLE",
                "target_category": target_category,
                "total_cohort_denominator": total_cohort_denominator,
                "supplied_pairs": supplied_cohort_size,
                "valid_pairs": 0,
                "missing_pairs": missing_pairs_count,
                "omitted_queries": omitted_queries,
                "api_error_pairs": api_error_count,
                "refusals_arm_h": refusals_h,
                "refusals_arm_t": refusals_t,
                "observed_mean_diff": None,
                "bootstrap_ci_95": None,
                "randomization_p_value": None,
                "sensitivity_bounds_mean_diff": (worst_bound, best_bound),
                "message": "No valid pairs available for statistical inference. Full-cohort bounds retained.",
            }

        boot_res = self.compute_paired_bootstrap_ci(valid_diffs)
        obs_mean, ci_low, ci_high = boot_res if boot_res else (0.0, 0.0, 0.0)
        rand_res = self.compute_paired_randomization_test(valid_diffs)
        _, p_val = rand_res if rand_res else (0.0, 1.0)

        return {
            "status": "SUCCESS",
            "target_category": target_category,
            "total_cohort_denominator": total_cohort_denominator,
            "supplied_pairs": supplied_cohort_size,
            "valid_pairs": valid_pairs_count,
            "missing_pairs": missing_pairs_count,
            "omitted_queries": omitted_queries,
            "api_error_pairs": api_error_count,
            "refusals_arm_h": refusals_h,
            "refusals_arm_t": refusals_t,
            "observed_mean_diff": obs_mean,
            "bootstrap_ci_95": (ci_low, ci_high),
            "randomization_p_value": p_val,
            "sensitivity_bounds_mean_diff": (worst_bound, best_bound),
            "assumptions": "Paired exchangeability and sign symmetry under sharp null H0: diff_i = 0.",
        }
