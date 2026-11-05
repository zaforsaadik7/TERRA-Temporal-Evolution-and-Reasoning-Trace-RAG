"""
scoring_analyzer.py
-------------------
Implements the pre-specified statistical analysis plan:
- Primary estimand: paired Category B faithfulness difference.
- Paired cluster bootstrap 95% CI (10,000 resamples).
- Two-sided paired randomization test (100,000 sign-flips).
- Explicit missingness, API_ERROR sensitivity bounds, and refusal accounting.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

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
        self.bootstrap_resamples = bootstrap_resamples
        self.randomization_flips = randomization_flips
        self.seed = seed

    def compute_paired_bootstrap_ci(
        self,
        diffs: List[float],
        confidence_level: float = 0.95,
    ) -> Tuple[float, float, float]:
        """
        Compute mean difference and percentile bootstrap CI on paired differences.
        Returns: (observed_mean, ci_lower, ci_upper)
        """
        if not diffs:
            return 0.0, 0.0, 0.0

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
    ) -> Tuple[float, float]:
        """
        Perform a two-sided paired sign-flip randomization test.
        Null hypothesis H0: E[diff] = 0 (symmetric around zero).
        Returns: (observed_mean, monte_carlo_p_value)
        """
        if not diffs:
            return 0.0, 1.0

        n = len(diffs)
        obs_mean = sum(diffs) / float(n)
        abs_obs = abs(obs_mean)

        rng = random.Random(self.seed + 1)
        exceedances = 0

        for _ in range(self.randomization_flips):
            # Under H0, each diff has equal probability of + or - sign
            sim_sum = 0.0
            for d in diffs:
                sign = 1.0 if rng.random() >= 0.5 else -1.0
                sim_sum += d * sign
            sim_mean = sim_sum / float(n)
            if abs(sim_mean) >= abs_obs:
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
        """
        cat_results = [r for r in paired_results if r.category == target_category]

        valid_diffs: List[float] = []
        api_errors = 0
        refusals_h = 0
        refusals_t = 0

        for r in cat_results:
            if r.arm_h.api_error or r.arm_t.api_error:
                api_errors += 1
                continue
            if r.arm_h.is_refusal:
                refusals_h += 1
            if r.arm_t.is_refusal:
                refusals_t += 1
            if r.faithfulness_diff is not None:
                valid_diffs.append(r.faithfulness_diff)

        obs_mean, ci_low, ci_high = self.compute_paired_bootstrap_ci(valid_diffs)
        _, p_val = self.compute_paired_randomization_test(valid_diffs)

        # Sensitivity bounds on API errors (worst case: all errors = -1.0; best case: all errors = +1.0)
        total_pairs = len(cat_results)
        worst_case_mean = (sum(valid_diffs) - float(api_errors)) / float(total_pairs) if total_pairs > 0 else 0.0
        best_case_mean = (sum(valid_diffs) + float(api_errors)) / float(total_pairs) if total_pairs > 0 else 0.0

        return {
            "target_category": target_category,
            "total_pairs": total_pairs,
            "valid_pairs": len(valid_diffs),
            "api_error_pairs": api_errors,
            "refusals_arm_h": refusals_h,
            "refusals_arm_t": refusals_t,
            "observed_mean_diff": obs_mean,
            "bootstrap_ci_95": (ci_low, ci_high),
            "randomization_p_value": p_val,
            "sensitivity_bounds_mean_diff": (worst_case_mean, best_case_mean),
        }
