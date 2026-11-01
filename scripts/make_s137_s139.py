"""Signals for 30 October (research of 29 October, round 44): the edges of the corrected fire model.

The 29 October lot showed that the fire term of v8 had two faults: town cores (s134, the best gain
since 26 October) and the rural/urban station rates (s136). v9 is v8 with both corrections (town
core as station evidence; one station per 2,000 rural and 36,000 urban residents). The score edges
paid before (s102), and the edges of v9 differ from those of v8 where the fire term moved:

s137_t9_p_score_ge30_delta: P(score >= 0.30) under v9 minus under v8 (6,197 public-region tracts
    moved; on the 65-signal basis 45 % new, in-span orientation +0.30);
s138_t9_p_zero_delta: P(score = 0) under v8 minus under v9 (33 % new, orientation +0.20; residual
    correlation -0.51 with s137, the two ends of the score);
s139_t8_fire_fewer_schools: v8 fire contribution with fewer reference schools (pi 0.5, kappa 0)
    minus v8: a school that the reference lacks leaves the fire gap a larger share of the
    facilities half (40 % new, orientation +0.10).
Same parameters and seed as structural_v8e (scripts/make_s116_s117.py).
"""
from dataclasses import replace

import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table()
df = df.merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_osmfac.parquet"), on="GEOID", how="left")
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()) / ok["cty2_b10"].sum()
v8_params = Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9)
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8e.parquet"), on="GEOID", how="left")
town = df["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
v9 = simulate(df.assign(fire_misfiled_clean=df["fire_misfiled_clean"].fillna(0) + town),
              replace(v8_params, fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000))
v9.to_parquet(config.INTERIM / "structural_v9.parquet", index=False)
schools = simulate(df, replace(v8_params, pi_school=0.5, kappa_school=0.0))

for name, x, purpose, rho in [
    ("s137_t9_p_score_ge30_delta", v9["p_score_ge30"] - v8["p_score_ge30"],
     "P(score >= 0.30), v9 (town cores, rural/urban station rates) minus v8", 0.15),
    ("s138_t9_p_zero_delta", v8["p_zero"] - v9["p_zero"],
     "P(score = 0), v8 minus v9 (town cores, rural/urban station rates)", 0.10),
    ("s139_t8_fire_fewer_schools", schools["c_fire"] - v8["c_fire"],
     "v8 fire contribution with fewer reference schools (pi 0.5, kappa 0), minus v8", 0.05),
]:
    path, exp = write_signal(df, np.asarray(x, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
