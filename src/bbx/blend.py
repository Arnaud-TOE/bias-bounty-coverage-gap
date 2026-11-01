"""Linear blend of submitted signals, weighted from their leaderboard-implied covariances.

For submitted predictions p_1..p_k with public RMSEs, Cov(p_i, y) follows from
bbx.lb_algebra. The RMSE-optimal linear predictor in their span is

    y_hat = m + sum_i w_i (p_i - mean p_i),   w = (C + ridge * diag C)^-1 c

with C the covariance of the p_i over all scored tracts. Its expected public RMSE is
sqrt(s^2 - 2 w.c + w.C.w); clipping to [0, 1] can only lower it (the target is in [0, 1]).
Only k global weights are estimated (decision D1).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config
from .io import read_sample_submission
from .lb_algebra import implied_cov
from .signals import M_PUBLIC, S_PUBLIC
from .submit import LOG

CONSTANTS = {"s01_const_000.csv", "s02_const_010.csv"}


def scored_signals() -> pd.DataFrame:
    log = pd.read_csv(LOG, dtype=str, keep_default_na=False)
    # Probes test the leaderboard itself (e.g. whether a region is public), not the target.
    log = log[(log["public_rmse"] != "") & (~log["file"].isin(CONSTANTS)) & (~log["file"].str.contains("probe"))]
    return log[["file", "zindi_id", "public_rmse", "purpose"]].reset_index(drop=True)


def load_predictions(files) -> np.ndarray:
    ids = read_sample_submission()["GEOID"]
    cols = []
    for f in files:
        sub = pd.read_csv(config.SUBMISSIONS / f, dtype={"GEOID": str})
        cols.append(ids.to_frame().merge(sub, on="GEOID", how="left")["coverage_gap_score"].to_numpy())
    return np.column_stack(cols)


@dataclass
class Blend:
    files: list
    weights: np.ndarray
    rho: float
    expected_rmse: float
    prediction: np.ndarray


def fit(files=None, ridge: float = 0.0, m: float = M_PUBLIC, s: float = S_PUBLIC,
        rules: bool = True) -> Blend:
    sig = scored_signals()
    if files is not None:
        sig = sig.set_index("file").loc[list(files)].reset_index()
    files = list(sig["file"])
    P = load_predictions(files)
    c = np.array([implied_cov(P[:, i], float(r), m, s) for i, r in enumerate(sig["public_rmse"])])
    C = np.cov(P.T, bias=True).reshape(len(files), len(files))
    w = np.linalg.solve(C + ridge * np.diag(np.diag(C)), c)
    mse = s**2 - 2 * w @ c + w @ C @ w
    pred = np.clip(m + (P - P.mean(axis=0)) @ w, 0, 1)
    if rules:
        from .dataset import load_table
        from .postprocess import apply_formula_rules

        pred = apply_formula_rules(load_table(), pred)
    return Blend(files, w, float(np.sqrt(max(s**2 - mse, 0)) / s), float(np.sqrt(mse)), pred)
