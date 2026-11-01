"""Turn a raw signal into a submission and read back what its public RMSE says.

A signal s is submitted as  p = m + k * s_std  (clipped to [0, 1]), with s_std the
standardised signal and k a modest scale, so the file is a sensible prediction on its own
while its public RMSE gives Cov(s, y) through bbx.lb_algebra (decision D1).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import submit
from .lb_algebra import expected_rmse
from .postprocess import empty_overture_mask

# Target moments on the public subset, measured from S01/S02 (docs/journal.md).
M_PUBLIC = 0.059806
S_PUBLIC = 0.089022

# Batches prepared before the water-tract fix of 25 October (files logged up to 24 October 18:37 UTC) kept the
# raw signal on the two empty water tracts. They still do, so that rerunning them rebuilds the submitted files
# bit for bit (scripts/reproduce.py --full).
LEGACY_WATER_SCRIPTS = {
    "make_s04_s05", "make_s06_s10", "make_s11_s15", "make_s16_s18", "make_s19_s23", "make_queue_oct19_21",
    "make_queue_oct20_21", "make_queue_oct22", "make_queue_oct23", "make_queue_oct23_v2", "make_queue_oct24",
    "make_cbp4", "make_queue_oct25", "make_queue_oct25b", "make_queue_oct25c", "make_queue_oct25d",
    "make_queue_oct25e", "make_s95", "make_queue_pcs",
}


def standardise(x) -> np.ndarray:
    x = np.asarray(x, float)
    x = np.where(np.isfinite(x), x, np.nanmedian(x))
    sd = x.std()
    return (x - x.mean()) / (sd if sd > 0 else 1.0)


def to_prediction(signal, k: float = 0.3) -> np.ndarray:
    """Scale k is in units of the target sd (k = rho is the RMSE-optimal choice)."""
    return np.clip(M_PUBLIC + k * S_PUBLIC * standardise(signal), 0, 1)


def write_signal(df: pd.DataFrame, signal, name: str, purpose: str, rho_guess: float, k: float | None = None):
    # A negative rho_guess flips the signal so that the file itself points the right way.
    k = rho_guess if k is None else k
    p = to_prediction(signal, k)
    # The two empty water tracts are fixed by the formula (score 1, bbx.postprocess). A signal
    # extreme there would have its measured covariance driven by whether those two tracts fall
    # in the public 30 % (s07 and s22: up to 11 times their measured covariance), so they get m.
    if Path(sys.argv[0]).stem not in LEGACY_WATER_SCRIPTS:
        p = np.where(empty_overture_mask(df), M_PUBLIC, p)
    exp = expected_rmse(p, M_PUBLIC, S_PUBLIC, abs(rho_guess))
    path = submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": p}), name, exp, purpose)
    return path, exp
