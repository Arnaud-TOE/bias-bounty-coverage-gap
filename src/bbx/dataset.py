"""Assemble the modelling table: one row per scored tract (9,794), permitted columns only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .features import LAYERS
from .io import read_sample_submission, read_strata

TABLE = config.FEATURES / "features.parquet"

# Strata columns that are bookkeeping, not signal.
_DROP_STRATA = ("_year", "_vintage", "_edition", "_extent", "_window_", "_record_", "year_min",
                "year_max", "_threshold", "_metric", "_label", "_desc", "rank_universe", "_grain",
                "aiannh_geoid", "aiannh_name", "aiannh_kind", "uhe_city_name", "uhe_city_country",
                "STATEFP", "COUNTYFP", "frac_inside_aoi", "ur_class", "cdcw_grain")


def _safe_div(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.where(b > 0, a / np.where(b > 0, b, 1), np.nan)


def load_layers() -> pd.DataFrame:
    frames = []
    for region in config.REGIONS:
        parts = [pd.read_parquet(config.FEATURES / region / f"{name}.parquet") for name in LAYERS]
        df = parts[0]
        for p in parts[1:]:
            df = df.merge(p, on="GEOID", how="outer", validate="one_to_one")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def strata_columns(st: pd.DataFrame) -> list[str]:
    keep = []
    for c in st.columns:
        if c == "GEOID" or any(s in c for s in _DROP_STRATA):
            continue
        if pd.api.types.is_numeric_dtype(st[c]) or pd.api.types.is_bool_dtype(st[c]):
            keep.append(c)
    return keep


def build_table() -> pd.DataFrame:
    base = read_sample_submission()[["GEOID", "region"]]
    layers = load_layers()
    st = read_strata()  # footprint-derived columns already dropped (D2)
    st = st[["GEOID"] + strata_columns(st)]
    df = base.merge(layers, on="GEOID", how="left", validate="one_to_one")
    df = df.merge(st, on="GEOID", how="left", validate="one_to_one")
    for c in df.columns:
        if pd.api.types.is_bool_dtype(df[c]):
            df[c] = df[c].astype(float)

    area = np.maximum(df["ALAND"].to_numpy(float) / 1e6, 0.01)
    pop = df["pop_total"].to_numpy(float)
    hu = df["housing_units"].to_numpy(float)
    d = {
        "area_km2": area,
        "log_area": np.log(area),
        "rural_share": 1 - df["pct_urban"],
        "log_pop": np.log1p(pop),
        "log_hu": np.log1p(hu),
        "pop_dens": pop / area,
        "log_pop_dens": np.log1p(pop / area),
        "bld_per_hu": _safe_div(df["bld_n"], hu),
        "log_bld_dens": np.log1p(df["bld_n"] / area),
        "bld_osm_share": _safe_div(df["bld_osm"], df["bld_n"]),
        "bld_msft_share": _safe_div(df["bld_msft"], df["bld_n"]),
        "bld_esri_share": _safe_div(df["bld_esri"], df["bld_n"]),
        "bld_multisrc_share": _safe_div(df["bld_multisrc"], df["bld_n"]),
        "bld_small_share": _safe_div(df["bld_small"], df["bld_n"]),
        "log_poi_dens": np.log1p(df["poi_n"] / area),
        "poi_per_1k_pop": _safe_div(1000 * df["poi_n"], pop),
        "poi_closed_share": _safe_div(df["poi_closed"], df["poi_n"]),
        "poi_meta_share": _safe_div(df["poi_src_meta"], df["poi_n"]),
        "fire0": (df["poi_fire"] == 0).astype(float),
        "school0": (df["poi_school"] == 0).astype(float),
        "ems0": (df["poi_ems"] == 0).astype(float),
        "fire0_named_elsewhere": ((df["poi_fire"] == 0) & (df["poi_fire_misfiled"] + df["poi_fire_alt"] > 0)).astype(float),
        "school0_named_elsewhere": ((df["poi_school"] == 0) & (df["poi_school_misfiled"] > 0)).astype(float),
        "log_road_dens": np.log1p(df["km_road"] / area),
        "unnamed_share": _safe_div(df["km_unnamed"], df["km_road"]),
        "import_share": _safe_div(df["km_import_era"], df["km_road"]),
        "service_per_road": _safe_div(df["km_service"], df["km_road"]),
        "track_per_road": _safe_div(df["km_track"], df["km_road"]),
        "scored_over_major": _safe_div(df["km_scored"], df["km_rt_major"]),
        "major_unscored_share": _safe_div(df["km_rt_major_unscored"], df["km_rt_major"]),
        "no_major_route": (df["km_rt_major"] <= 0).astype(float),
        "no_scored_road": (df["km_scored"] <= 0).astype(float),
    }
    df = pd.concat([df, pd.DataFrame(d, index=df.index)], axis=1)
    for r in config.REGIONS:
        df[f"reg_{r}"] = (df["region"] == r).astype(float)
    assert len(df) == config.N_SCORED and df["GEOID"].is_unique
    return df


def save_table() -> pd.DataFrame:
    df = build_table()
    df.to_parquet(TABLE, index=False)
    return df


def load_table() -> pd.DataFrame:
    return pd.read_parquet(TABLE)
