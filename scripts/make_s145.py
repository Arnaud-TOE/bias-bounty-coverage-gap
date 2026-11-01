"""Fire stations: more reference stations than Overture ones where Overture has stations (round 73).

Our best blend sits above the calibrated v9 composite in tracts that hold Overture fire stations, and
more so with more stations (Texas -0.013 / +0.018 / +0.031 for 0 / 1 / 2+ stations; Oklahoma +0.020 /
+0.059 / +0.075; research of 30 October, round 63). The USGS layer can list several stations of a
department where Overture lists the headquarters, or a station twice; with o Overture stations and h
reference ones, the fire gap is 1 - min(1, o / h), so any h > o leaves a partial gap. Here the v9 rate
gets DELTA x o more reference stations in tracts with o >= 1 (2,746 scored tracts).

s145_t9_fire_multistation: v9 fire contribution with the extra stations minus v9 (two seeds averaged).
On the 65-signal basis 50 % new, in-span orientation +0.13; beside s143 and s144 50 % new, +0.12
(delta 0.15: +0.10 / +0.07).
"""
from dataclasses import replace

import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

DELTA = 0.3  # extra expected reference stations per Overture station

df = load_table()
for name in ("features_roadref", "features_osmfac"):
    df = df.merge(pd.read_parquet(config.FEATURES / f"{name}.parquet"), on="GEOID", how="left")
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()) / ok["cty2_b10"].sum()
v9_params = Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9, fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000)
town = df["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
d9 = df.assign(fire_misfiled_clean=df["fire_misfiled_clean"].fillna(0) + town)  # v9: town cores as evidence

pop_r, pop_u, area = df["pop_rural"].fillna(0).to_numpy(), df["pop_urban"].fillna(0).to_numpy(), df["area_km2"].to_numpy()
lam = pop_r * v9_params.fire_per_rural_pop + pop_u * v9_params.fire_per_urban_pop + area * v9_params.fire_per_km2
o = df["poi_fire"].fillna(0).to_numpy()
scale = np.where((o > 0) & (lam > 0), (lam + DELTA * o) / np.maximum(lam, 1e-9), 1.0)
print(f"{int((o > 0).sum())} tracts with Overture fire stations; mean scale there {scale[o > 0].mean():.2f}")

# bbx.structural reads rural / urban population and area only for the fire rate.
scaled = d9.assign(pop_rural=pop_r * scale, pop_urban=pop_u * scale, area_km2=area * scale)
delta = np.zeros(len(df))
for seed_shift in (0, 1):
    p = replace(v9_params, seed=v9_params.seed + seed_shift)
    delta += (simulate(scaled, p)["c_fire"] - simulate(d9, p)["c_fire"]).to_numpy() / 2
path, exp = write_signal(df, delta, "s145_t9_fire_multistation",
                         "v9 fire contribution with 0.3 extra reference stations per Overture station where Overture has some, minus v9",
                         rho_guess=0.06)
print(f"{path.name}: expected public RMSE {exp:.6f}")
