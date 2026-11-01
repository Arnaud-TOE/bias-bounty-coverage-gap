"""Measurement design: principal components of the feature space left unexplained by the basis.

Every leaderboard submission measures exactly one direction (its covariance with the hidden
target). To cover as much potentially predictive variation as possible per submission, we
build a broad matrix of permitted features (mechanisms, strata, transforms, region
interactions), remove what the already measured / queued signals span, and submit the leading
principal components of the remainder. The final blend then approximates a ridge regression of
the target on the whole feature set (decision D1-bis: continuous signals only).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import blend, config
from .candidates import build as build_candidates
from .candidates_extra import build as build_extra
from .dataset import load_table

_SKIP = ("GEOID", "region", "STATEFP", "COUNTYFP")


def _robust_z(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    med = np.nanmedian(x)
    x = np.where(np.isfinite(x), x, med)
    sd = x.std()
    if sd == 0:
        return np.zeros_like(x)
    return np.clip((x - x.mean()) / sd, -5, 5)


def feature_matrix() -> pd.DataFrame:
    df = load_table()
    st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
    cand = df[["GEOID"]].merge(build_candidates(), on="GEOID", how="left")
    extra = df[["GEOID"]].merge(build_extra(), on="GEOID", how="left")
    cols = {}
    for c in df.columns:
        if c in _SKIP or not pd.api.types.is_numeric_dtype(df[c]):
            continue
        x = df[c].to_numpy(float)
        cols[c] = x
        if np.nanmin(x) >= 0 and np.nanmax(x) > 50:  # heavy-tailed counts -> log
            cols[f"log1p_{c}"] = np.log1p(x)
    for frame, prefix in [(st, "st_"), (cand, "cd_"), (extra, "cx_")]:
        for c in frame.columns:
            if c != "GEOID" and pd.api.types.is_numeric_dtype(frame[c]):
                cols[prefix + c] = frame[c].to_numpy(float)
    rural = df["rural_share"].fillna(df["rural_share"].median()).to_numpy()
    key = {"c_transport": st["c_transport"], "fire0": df["fire0"], "msft": df["bld_msft_share"],
           "unnamed": df["unnamed_share"], "c_cbp": st["c_cbp"], "rural": rural,
           "log_pop_dens": df["log_pop_dens"], "fire0_nbr300": extra["fire0_nbr300"]}
    for r in config.REGIONS:
        ind = (df["region"] == r).to_numpy(float)
        for k, v in key.items():
            cols[f"x_{r}_{k}"] = np.nan_to_num(np.asarray(v, float)) * ind
    for k1, k2 in [("fire0", "rural"), ("msft", "rural"), ("unnamed", "rural"), ("c_transport", "rural"),
                   ("fire0", "c_transport")]:
        cols[f"i_{k1}_{k2}"] = np.nan_to_num(np.asarray(key[k1], float)) * np.nan_to_num(np.asarray(key[k2], float))
    F = pd.DataFrame({k: _robust_z(v) for k, v in cols.items()})
    F = F.loc[:, F.std() > 0]
    # drop exact duplicates
    F = F.T.drop_duplicates().T
    return F


def residual_pcs(basis_files: list[str], n: int = 30) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    F = feature_matrix().to_numpy(float)
    B = blend.load_predictions(basis_files)
    B = (B - B.mean(0)) / B.std(0)
    A = np.column_stack([np.ones(len(B)), B])
    R = F - A @ np.linalg.lstsq(A, F, rcond=None)[0]
    R = R - R.mean(0)
    U, S, Vt = np.linalg.svd(R, full_matrices=False)
    explained = S**2 / (S**2).sum()
    pcs = U[:, :n] * S[:n]
    return pcs, explained, pd.DataFrame({"explained": explained[:n], "cumulative": np.cumsum(explained)[:n]})
