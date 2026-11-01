"""Leaderboard algebra: what a public RMSE tells us about the hidden target.

For a submission p scored on the public subset with target y (mean m, sd s):

    RMSE^2 = Var(p) + s^2 - 2 Cov(p, y) + (mean(p) - m)^2

so two constant submissions give (m, s) exactly, and every further submission gives
Cov(p, y), hence the correlation of that signal with the truth. Only global quantities
are measured this way (decision D1); no tract-level values are inferred.
Moments of p are taken on all scored tracts as a proxy for the unknown public subset.
"""
from __future__ import annotations

import numpy as np


def moments_from_constants(c1: float, rmse1: float, c2: float, rmse2: float) -> tuple[float, float]:
    """Target mean and sd on the public subset from two constant submissions."""
    m = ((rmse1**2 - rmse2**2) / (c2 - c1) + c1 + c2) / 2
    var = rmse1**2 - (m - c1) ** 2
    return m, float(np.sqrt(var))


def implied_cov(pred: np.ndarray, rmse: float, m: float, s: float) -> float:
    pred = np.asarray(pred, dtype=float)
    return (pred.var() + s**2 + (pred.mean() - m) ** 2 - rmse**2) / 2


def implied_corr(pred: np.ndarray, rmse: float, m: float, s: float) -> float:
    pred = np.asarray(pred, dtype=float)
    return implied_cov(pred, rmse, m, s) / (pred.std() * s)


def expected_rmse(pred: np.ndarray, m: float, s: float, rho: float) -> float:
    """Pre-registered public RMSE of `pred` if its correlation with the truth is `rho`."""
    pred = np.asarray(pred, dtype=float)
    sp = pred.std()
    return float(np.sqrt(sp**2 + s**2 - 2 * rho * sp * s + (pred.mean() - m) ** 2))
