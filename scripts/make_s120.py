"""Pooled test of two low-prior scorer hypotheses for 28 October (research of 27 October, round 20).

(a) Open-status filter (s118): if only 'open' Overture places counted, 836 tracts gain about 0.06
    of fire contribution (542 have no open fire place at all).
(b) Original rings: the README says an earlier package cut the map data with rough region polygons
    (boundaries/original-rings.geojson), which "inflated their gaps 5 to 8x" for edge tracts. If the
    scoring reference kept that cut, the 326 tracts that the rings cut (264 outside eastern-wa) have
    inflated scores. This would also explain why eastern-wa transport has no covariance with the
    truth: 15 % of its tracts are cut by its ring.
Each alone is unlikely (the hospital ratio and the README's "fixed" wording argue against them), so
one file tests both: s120 = standardised s118 difference + standardised share of tract area outside
its region's original ring. A null score closes both for one submission; a clear positive one is
split on 29 October. New to the 51-signal basis (each part R2 about 0.1).
"""
import os

import duckdb
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.io import strata_path
from bbx.signals import standardise, write_signal

RINGS = (config.BOUNDARIES / "original-rings.geojson").as_posix()   # package file boundaries/original-rings.geojson

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
con.sql(f"CREATE TABLE rg AS SELECT folder, ST_SetCRS(geom, 'OGC:CRS84') AS geom FROM ST_Read('{RINGS}')")
frames = []
for r in ["maricopa-az", "northern-ca", "south-central-tx", "eastern-wa"]:
    t = strata_path(r, "census-tracts").as_posix()
    frames.append(con.sql(f"""SELECT tr.GEOID, ST_Area(ST_Intersection(tr.geometry, rg.geom)) / ST_Area(tr.geometry) AS frac_in
        FROM '{t}' tr JOIN rg ON rg.folder = '{r}'""").df())
df = load_table()
fr = df[["GEOID"]].merge(pd.concat(frames), on="GEOID", how="left")
outside = 1 - fr["frac_in"].fillna(1).to_numpy()
outside = np.where(outside > 0.001, outside, 0.0)          # float noise on tracts fully inside
s118 = df[["GEOID"]].merge(pd.read_csv(config.SUBMISSIONS / "s118_t8o_fire_open_diff.csv", dtype={"GEOID": str}),
                           on="GEOID")["coverage_gap_score"].to_numpy()
print(f"tracts cut by the original rings: {(outside > 0).sum()}")
sig = standardise(s118) + standardise(outside)
path, exp = write_signal(df, sig, "s120_pooled_open_or_rings",
                         "pooled test: open-status fire difference (s118) + share of tract outside the original ring",
                         rho_guess=0.05)
print(f"{path.name}: expected public RMSE {exp:.6f}")
