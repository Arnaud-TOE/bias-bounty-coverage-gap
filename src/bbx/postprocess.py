"""Deterministic consequences of the published organiser formula (no reference data used).

The organiser composite is the mean of the *defined* components, each `1 - min(1, O / R)`,
and tracts with all three components undefined are dropped from the scored list. A scored
tract with no Overture scored-class road, no building and no place therefore has at least one
defined component, and every defined component equals 1 - min(1, 0 / R) = 1: its score is 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def empty_overture_mask(df: pd.DataFrame) -> np.ndarray:
    return ((df["km_scored"] <= 0) & (df["bld_n"] == 0) & (df["poi_n"] == 0)).to_numpy()


def apply_formula_rules(df: pd.DataFrame, pred: np.ndarray) -> np.ndarray:
    """Return a copy of pred with every rule-determined tract set to its exact score."""
    out = np.asarray(pred, float).copy()
    out[empty_overture_mask(df)] = 1.0
    return out
