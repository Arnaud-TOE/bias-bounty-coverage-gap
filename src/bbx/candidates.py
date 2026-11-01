"""Candidate basis signals for the leaderboard-measured blend (decision D1-bis).

Every candidate is a continuous mechanism defined on all 9,794 tracts, or a large-group
indicator (>= 300 tracts). All are computed from permitted data only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .dataset import load_table


def _gap(ratio) -> np.ndarray:
    r = np.asarray(ratio, float)
    return np.where(np.isfinite(r), 1 - np.minimum(1, r), 0.0)


def county_relative_density(df: pd.DataFrame, num: str, den: str) -> np.ndarray:
    """(num/den) of the tract divided by the same ratio over its county's scored tracts."""
    county = df["GEOID"].str[:5]
    tot = df.groupby(county)[[num, den]].transform("sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        tract = df[num] / df[den].where(df[den] > 0)
        cty = tot[num] / tot[den].where(tot[den] > 0)
        return (tract / cty).to_numpy()


def build(structural: pd.DataFrame | None = None) -> pd.DataFrame:
    df = load_table()
    st = df[["GEOID"]].merge(structural if structural is not None
                             else pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
    w_half = 1 / (2 * st["n_defined"].clip(lower=1))  # weight of a POI half in the composite
    rural = df["rural_share"].fillna(df["rural_share"].median())
    c = {}

    # CBP half: establishments allocated to tracts by population / housing units / land area.
    df["poi_open"] = df["poi_n"] - df["poi_closed"]
    for base, den in [("pop", "pop_total"), ("hu", "housing_units"), ("area", "ALAND")]:
        rel = county_relative_density(df, "poi_n", den)
        for k in (0.5, 1.0):
            c[f"cbp_{base}_k{k}"] = _gap(rel / k) * w_half
    c["cbp_open_pop_k0.5"] = _gap(county_relative_density(df, "poi_open", "pop_total") / 0.5) * w_half

    # Building component: where Overture may hold fewer structures than an older ML footprint set.
    c["bld_esri_share"] = df["bld_esri_share"].fillna(0)
    c["bld_small_share"] = df["bld_small_share"].fillna(0)
    c["bld_msft_x_small"] = df["bld_msft_share"].fillna(0) * df["bld_small_share"].fillna(0)
    c["bld_per_hu_low"] = _gap(df["bld_per_hu"] / 1.0)
    c["bld_osm_share_rural"] = df["bld_osm_share"].fillna(0) * rural

    # Transport variants.
    proxy = df["km_rt_major"] + 0.55 * df["km_rt_txsec"]
    det = np.where(proxy > 0, _gap(df["km_scored"] / proxy.where(proxy > 0)), 0.0)
    c["tr_det_major_fm055"] = det / st["n_defined"].clip(lower=1)
    c["tr_det_major_only"] = np.where(df["km_rt_major"] > 0,
                                      _gap(df["km_scored"] / df["km_rt_major"].where(df["km_rt_major"] > 0)), 0.0)
    c["unrouted_scored_share"] = (df["km_nort_scored"] / df["km_scored"].where(df["km_scored"] > 0)).fillna(0)
    c["p_transport_defined"] = st["p_transport_defined"]
    c["n_defined"] = st["n_defined"]

    # Region x rurality (large groups) and other strata.
    for r in ["eastern-ok", "south-central-tx", "maricopa-az"]:
        c[f"rural_x_{r}"] = rural * (df["region"] == r)
    c["region_wa"] = (df["region"] == "eastern-wa").astype(float)
    c["region_ca"] = (df["region"] == "northern-ca").astype(float)
    c["unnamed_share"] = df["unnamed_share"].fillna(0)
    c["import_share"] = df["import_share"].fillna(0)
    c["whp_log"] = np.log1p(df["usfs_WHP_mean"].fillna(0))
    c["tribal_pct"] = df["tribal_pct"].fillna(0)
    c["log_pop_dens"] = df["log_pop_dens"]
    c["poi_closed_share"] = df["poi_closed_share"].fillna(0)
    c["school0"] = df["school0"]
    out = pd.DataFrame(c)
    out.insert(0, "GEOID", df["GEOID"].to_numpy())
    return out
