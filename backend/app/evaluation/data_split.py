"""
Scenario-Level Data Splitting.
Enforces strict scenario-level partitioning to prevent time-series autocorrelation leakage.
Holds out the Nonlinear degradation family for generalization validation.
"""

from typing import List, Dict, Any, Tuple
import numpy as np

def split_scenarios_by_family(
    suite: List[Dict[str, Any]],
    holdout_family: str = "nonlinear",
    test_ratio: float = 0.25,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Splits scenarios into Training, Validation, and Held-out Test sets.
    The holdout_family is placed ENTIRELY into the test set to evaluate out-of-distribution generalization.
    """
    rng = np.random.default_rng(seed)

    holdout_scenarios = [s for s in suite if s["degradation_type"] == holdout_family]
    standard_scenarios = [s for s in suite if s["degradation_type"] != holdout_family]

    # Shuffle standard scenarios
    indices = np.arange(len(standard_scenarios))
    rng.shuffle(indices)

    val_count = int(len(standard_scenarios) * 0.15)
    test_count = int(len(standard_scenarios) * (test_ratio - 0.05))

    val_indices = indices[:val_count]
    test_indices = indices[val_count:val_count + test_count]
    train_indices = indices[val_count + test_count:]

    train_set = [standard_scenarios[i] for i in train_indices]
    val_set = [standard_scenarios[i] for i in val_indices]
    test_set = [standard_scenarios[i] for i in test_indices] + holdout_scenarios

    return train_set, val_set, test_set
