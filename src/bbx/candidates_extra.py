"""Second-pass candidate signals (boundary facilities, footprint size, ZIP allocation of CBP).

Requires data/features/features_extra.parquet (bbx.features_extra.build()).
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from . import config
from .candidates import _gap
from .dataset import load_table
from .io import ref_path, strata_path


def tract_zip_counts() -> pd.DataFrame:
    """Overture places per (tract, 5-digit postcode)."""
    con = duckdb.connect()
    con.sql("LOAD spatial; SET enable_progress_bar=false;")
    q = []
    for r in config.REGIONS:
        q.append(f"""
            SELECT t.GEOID, substr(p.addresses[1].postcode, 1, 5) AS z, count(*) AS n
            FROM '{strata_path(r, "census-tracts").as_posix()}' t
            JOIN '{ref_path(r, "overture-pois").as_posix()}' p ON ST_Contains(t.geometry, p.geometry)
            WHERE len(p.addresses) > 0 AND p.addresses[1].postcode IS NOT NULL
            GROUP BY 1, 2""")
    tz = con.sql(" UNION ALL ".join(q)).df()
    return tz[tz["z"].str.fullmatch(r"\d{5}")]


def zip_allocated_ratio(df: pd.DataFrame, tz: pd.DataFrame, base: str) -> pd.Series:
    """Tract places / (ZIP places allocated to tracts by `base` x the tract's share of the ZIP).

    Mimics establishments published per ZIP and spread to tracts in proportion to land area or
    population, with each tract's place-postcode mix standing in for its ZIP overlap.
    """
    tz = tz.copy()
    tz["share"] = tz["n"] / tz.groupby("GEOID")["n"].transform("sum")
    tz = tz.merge(df[["GEOID", base]], on="GEOID")
    tz["a"] = tz[base].clip(lower=0) * tz["share"]
    tz["A"] = tz.groupby("z")["a"].transform("sum")
    tz["R"] = tz["z"].map(tz.groupby("z")["n"].sum()) * tz["a"] / tz["A"].where(tz["A"] > 0)
    alloc = tz.groupby("GEOID")["R"].sum()
    return df["poi_n"] / df["GEOID"].map(alloc)


def build() -> pd.DataFrame:
    df = load_table().merge(pd.read_parquet(config.FEATURES / "features_extra.parquet"), on="GEOID", how="left")
    st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
    w_half = 1 / (2 * st["n_defined"].clip(lower=1))
    fire0 = df["poi_fire"] == 0
    c = {
        "fire0_nbr300": (fire0 & (df["fire_out_300m"].fillna(0) > 0)).astype(float),
        "fire0_no_nbr1km": (fire0 & (df["fire_out_1km"].fillna(0) == 0)).astype(float),
        "fire0_nbr1km": (fire0 & (df["fire_out_1km"].fillna(0) > 0)).astype(float),
        "log_msft_area": np.log1p(df["msft_area_mean"].fillna(df["msft_area_mean"].median())),
        "log_osm_area": np.log1p(df["osm_area_mean"].fillna(df["osm_area_mean"].median())),
    }
    tz = tract_zip_counts()
    for base in ("ALAND", "pop_total"):
        rel = zip_allocated_ratio(df, tz, base)
        for k in (1.0, 0.5):
            c[f"zip_{base}_k{k}"] = _gap(rel / k) * w_half
    out = pd.DataFrame({k: np.nan_to_num(np.asarray(v, float)) for k, v in c.items()})
    out.insert(0, "GEOID", df["GEOID"].to_numpy())
    return out
