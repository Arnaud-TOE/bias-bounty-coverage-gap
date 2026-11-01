"""Data access with a compliance guard.

The scored pipeline may only read the permitted challenge data (Overture extracts,
ACS housing, strata tables, tract geometry, sample submission). Every file read goes
through `permitted()`, and strata columns derived from building footprints are dropped
(decision D2, docs/decisions.md).
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd

from . import config

# Withdrawn reference layers and anything that could carry organiser targets.
_FORBIDDEN_PATH = re.compile(
    r"tiger|microsoft|msft|ms-?building|hifld|usgs-?structures|cbp|business-?patterns|coverage-gap",
    re.IGNORECASE,
)
# Strata columns derived from building footprints (D2): USFS building / housing-unit /
# population layers are built on Microsoft footprints, as is CarbonPlan's building count.
_FORBIDDEN_COLUMN = re.compile(
    r"usfs_building|usfs_hu|usfs_pop|carbonplan_buildings", re.IGNORECASE
)


class ForbiddenDataError(RuntimeError):
    pass


def permitted(path: str | Path) -> Path:
    """Return the path if the scored pipeline may read it, else raise."""
    p = Path(path)
    if _FORBIDDEN_PATH.search(p.as_posix()):
        raise ForbiddenDataError(f"Scored pipeline may not read {p}")
    return p


def drop_forbidden_columns(df: pd.DataFrame) -> pd.DataFrame:
    bad = [c for c in df.columns if _FORBIDDEN_COLUMN.search(c)]
    return df.drop(columns=bad)


def connect(threads: int | None = None) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    if threads:
        con.sql(f"SET threads={int(threads)};")
    return con


def ref_path(region: str, layer: str) -> Path:
    """Path of a reference/ layer, e.g. ref_path('eastern-ok', 'overture-pois')."""
    suffix = ".csv" if layer == "sample-submission" else ".parquet"
    return permitted(config.REFERENCE / region / f"{region}-{layer}{suffix}")


def strata_path(region: str, table: str) -> Path:
    return permitted(config.STRATA / region / f"{region}-{table}.parquet")


def read_sample_submission(region: str | None = None) -> pd.DataFrame:
    """Scored tract list. GEOID is always text (Maricopa is state FIPS 04)."""
    regions = [region] if region else list(config.REGIONS)
    frames = []
    for r in regions:
        df = pd.read_csv(ref_path(r, "sample-submission"), dtype={"GEOID": str})
        df["region"] = r
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def read_strata(region: str | None = None, columns: list[str] | None = None) -> pd.DataFrame:
    regions = [region] if region else list(config.REGIONS)
    frames = []
    for r in regions:
        df = pd.read_parquet(strata_path(r, "strata-tract-table"), columns=columns)
        df["GEOID"] = df["GEOID"].astype(str)
        frames.append(drop_forbidden_columns(df))
    return pd.concat(frames, ignore_index=True)
