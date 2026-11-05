"""
scoring_analyzer.py
-------------------
Implements the pre-specified statistical analysis plan:
- Primary estimand: paired Category B faithfulness difference.
- Paired cluster bootstrap 95% CI (10,000 resamples).
- Two-sided paired randomization test (100,000 sign-flips).
- Rigorous missingness accounting, component-tightened sensitivity bounds,
  duplicate-ID validation, finite-range checks, and explicit UNAVAILABLE status.
"""

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
        seed: int = 42,
    ):
        if bootstrap_resamples <= 0:
            raise ValueError(f"bootstrap_resamples must be > 0, got {bootstrap_resamples}")
        if randomization_flips <= 0:
            raise ValueError(f"randomization_flips must be > 0, got {randomization_flips}")

        self.bootstrap_resamples = bootstrap_resamples
        self.randomization_flips = randomization_flips
        self.seed = seed

    def compute_paired_bootstrap_ci(
        self,
        diffs: List[float],
        confidence_level: float = 0.95,
    ) -> Optional[Tuple[float, float, float]]:
        """
        Compute mean difference and percentile bootstrap CI on paired differences.
        Returns: (observed_mean, ci_lower, ci_upper) or None if diffs is empty.
        """
        if not diffs:
            return None

        if not (0.0 < confidence_level < 1.0):
            raise ValueError(f"confidence_level must be between 0 and 1, got {confidence_level}")

        n = len(diffs)
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

    def compute_paired_randomization_test(
        self,
        diffs: List[float],
    ) -> Optional[Tuple[float, float]]:
        """
        Perform a two-sided paired sign-flip randomization test.
        Assumes exchangeability and symmetry under the sharp null hypothesis H0: diff_i = 0.
        Returns: (observed_mean, monte_carlo_p_value) or None if diffs is empty.
        """
        if not diffs:
            return None

        n = len(diffs)
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
    ) -> Dict[str, Any]:
        """
        Run complete analysis on paired results filtered by target category.
        Validates duplicate query IDs, finite ranges, recomputes differences,
        and derives component-tightened missingness bounds.
        """
        cat_results = [r for r in paired_results if r.category == target_category]
        total_cohort = len(cat_results)

        # Step 1: Validate cohort uniqueness
        seen_qids: Set[str] = set()
        for r in cat_results:
            if r.query_id in seen_qids:
                raise ValueError(f"Duplicate query_id detected in cohort: '{r.query_id}'")
            seen_qids.add(r.query_id)

        # Step 2: Extract valid pairs and audit components
        valid_diffs: List[float] = []
        valid_pairs_count = 0
        missing_pairs_count = 0
        api_error_count = 0
        refusals_h = 0
        refusals_t = 0

        worst_case_sum = 0.0
        best_case_sum = 0.0

        for r in cat_results:
            score_h = r.arm_h.composite_faithfulness
            score_t = r.arm_t.composite_faithfulness

            # Track refusal counts
            if r.arm_h.is_refusal:
                refusals_h += 1
            if r.arm_t.is_refusal:
                refusals_t += 1
            if r.arm_h.api_error or r.arm_t.api_error:
                api_error_count += 1

            # Validate range if scores present
            if score_h is not None and not (0.0 <= score_h <= 1.0):
                raise ValueError(f"Query '{r.query_id}' Arm_H score {score_h} outside [0.0, 1.0]")
            if score_t is not None and not (0.0 <= score_t <= 1.0):
                raise ValueError(f"Query '{r.query_id}' Arm_T score {score_t} outside [0.0, 1.0]")

            if score_h is not None and score_t is not None:
                # Both present: valid pair
                recomputed_diff = score_t - score_h
                if not (-1.0 <= recomputed_diff <= 1.0):
                    raise ValueError(f"Recomputed diff {recomputed_diff} outside [-1.0, 1.0]")
                valid_diffs.append(recomputed_diff)
                valid_pairs_count += 1
                worst_case_sum += recomputed_diff
                best_case_sum += recomputed_diff
            else:
                # Missing pair: derive component-tightened bounds
                missing_pairs_count += 1
                if score_h is not None and score_t is None:
                    # Arm T missing: worst case score_t=0.0 -> diff = -score_h; best case score_t=1.0 -> diff = 1.0 - score_h
                    worst_case_sum += (0.0 - score_h)
                    best_case_sum += (1.0 - score_h)
                elif score_h is None and score_t is not None:
                    # Arm H missing: worst case score_h=1.0 -> diff = score_t - 1.0; best case score_h=0.0 -> diff = score_t
                    worst_case_sum += (score_t - 1.0)
                    best_case_sum += (score_t - 0.0)
                else:
                    # Both missing: worst case -1.0; best case +1.0
                    worst_case_sum += -1.0
                    best_case_sum += 1.0

        # Step 3: Handle empty valid data
        if valid_pairs_count == 0 or total_cohort == 0:
            return {
                "status": "UNAVAILABLE",
                "target_category": target_category,
                "total_pairs": total_cohort,
                "valid_pairs": 0,
                "missing_pairs": missing_pairs_count,
                "api_error_pairs": api_error_count,
                "refusals_arm_h": refusals_h,
                "refusals_arm_t": refusals_t,
                "observed_mean_diff": None,
                "bootstrap_ci_95": None,
                "randomization_p_value": None,
                "sensitivity_bounds_mean_diff": None,
                "message": "No valid pairs available for statistical inference.",
            }

        # Step 4: Compute inference on valid pairs
        boot_res = self.compute_paired_bootstrap_ci(valid_diffs)
        obs_mean, ci_low, ci_high = boot_res if boot_res else (0.0, 0.0, 0.0)
        rand_res = self.compute_paired_randomization_test(valid_diffs)
        _, p_val = rand_res if rand_res else (0.0, 1.0)

        # Sensitivity bounds evaluated across full cohort denominator
        worst_bound = worst_case_sum / float(total_cohort)
        best_bound = best_case_sum / float(total_cohort)

        return {
            "status": "SUCCESS",
            "target_category": target_category,
            "total_pairs": total_cohort,
            "valid_pairs": valid_pairs_count,
            "missing_pairs": missing_pairs_count,
            "api_error_pairs": api_error_count,
            "refusals_arm_h": refusals_h,
            "refusals_arm_t": refusals_t,
            "observed_mean_diff": obs_mean,
            "bootstrap_ci_95": (ci_low, ci_high),
            "randomization_p_value": p_val,
            "sensitivity_bounds_mean_diff": (worst_bound, best_bound),
            "assumptions": "Paired exchangeability and sign symmetry under sharp null H0: diff_i = 0.",
        }
