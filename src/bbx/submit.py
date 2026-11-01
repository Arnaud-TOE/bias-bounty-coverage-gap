"""Write validated submission files and keep the submission log.

Every file is checked against the official tract list before it is written, and every
file gets a SHA-256 and a pre-registered expected public RMSE in submissions/log.csv.
"""
from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config
from .io import read_sample_submission

LOG = config.SUBMISSIONS / "log.csv"
LOG_FIELDS = [
    "prepared_utc", "file", "sha256", "n_rows", "mean", "sd",
    "expected_public_rmse", "purpose", "zindi_id", "public_rmse", "submitted_utc",
]


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(sub: pd.DataFrame) -> pd.DataFrame:
    ref = read_sample_submission()[["GEOID"]]
    if not {"GEOID", "coverage_gap_score"} <= set(sub.columns):
        raise ValueError("submission needs GEOID and coverage_gap_score")
    sub = sub.copy()
    sub["GEOID"] = sub["GEOID"].astype(str)
    if sub["GEOID"].duplicated().any():
        raise ValueError("duplicate GEOIDs")
    missing = set(ref["GEOID"]) - set(sub["GEOID"])
    extra = set(sub["GEOID"]) - set(ref["GEOID"])
    if missing or extra:
        raise ValueError(f"GEOID mismatch: {len(missing)} missing, {len(extra)} extra")
    y = sub["coverage_gap_score"].to_numpy(dtype=float)
    if not np.isfinite(y).all() or (y < 0).any() or (y > 1).any():
        raise ValueError("scores must be finite and within [0, 1]")
    if sub.isna().any().any():
        raise ValueError("blank cells are rejected by Zindi")
    # Keep the official row order, and only the two scored columns in this order: the grader
    # scores the first column after GEOID (Zindi #35361), and the official sample puts
    # transport_gap there.
    return ref.merge(sub[["GEOID", "coverage_gap_score"]], on="GEOID", how="left")


def record(file: str, zindi_id: str, public_rmse: float, submitted_utc: str) -> None:
    """Store the Zindi id and public score of a logged file."""
    log = pd.read_csv(LOG, dtype=str, keep_default_na=False)
    hit = log["file"] == file
    if hit.sum() != 1:
        raise ValueError(f"{file} appears {hit.sum()} times in the log")
    log.loc[hit, ["zindi_id", "public_rmse", "submitted_utc"]] = [zindi_id, f"{public_rmse:.9f}", submitted_utc]
    log.to_csv(LOG, index=False, lineterminator="\n")


def write(sub: pd.DataFrame, name: str, expected_public_rmse: float | None, purpose: str):
    sub = validate(sub)
    config.SUBMISSIONS.mkdir(parents=True, exist_ok=True)
    path = config.SUBMISSIONS / f"{name}.csv"
    # 6 decimals: rounding error <= 5e-7, far below any RMSE difference we act on.
    sub.to_csv(path, index=False, lineterminator="\n", float_format="%.6f")
    y = sub["coverage_gap_score"].to_numpy(dtype=float)
    row = {
        "prepared_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "file": path.name,
        "sha256": sha256(path),
        "n_rows": len(sub),
        "mean": f"{y.mean():.6f}",
        "sd": f"{y.std():.6f}",
        "expected_public_rmse": "" if expected_public_rmse is None else f"{expected_public_rmse:.6f}",
        "purpose": purpose,
        "zindi_id": "",
        "public_rmse": "",
        "submitted_utc": "",
    }
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return path
