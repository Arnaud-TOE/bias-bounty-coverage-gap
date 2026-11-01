"""Fire-station prior recalibrated: more stations in rural areas, fewer in cities (research of 28 October, round 42).

The v8 prior expects one reference station per 4,000 rural and per 18,000 urban residents. The
measured signals point the other way on both counts: on the 60-signal basis the change of fire
contribution from doubling the rural rate is oriented at +0.20 in its in-span part, and from
doubling the urban rate at -0.24 (s133, fire in the large metros, at -0.06, tells the same).
Rural volunteer stations are many and poorly covered by Overture places; city stations are fewer
per resident than the national average and well covered.

s136_t8_fire_prior_recal: v8 fire contribution with 1 station per 2,000 rural and per 36,000 urban
residents, minus v8 (same seed as structural_v8e, scripts/make_s116_s117.py). Moves 7,846 tracts
(7,504 in the public regions);
on the 60-signal basis 34 % new, in-span orientation +0.26, residual independent of s112, s113,
s121, s133 and s134 (|correlation| <= 0.06).
"""
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
params = Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9,
    fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000)
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8e.parquet"), on="GEOID", how="left")
recal = simulate(df, params)
delta = (recal["c_fire"] - v8["c_fire"]).to_numpy()
path, exp = write_signal(df, delta, "s136_t8_fire_prior_recal",
                         "v8 fire contribution with 1 station per 2,000 rural and 36,000 urban residents, minus v8",
                         rho_guess=0.15)
print(f"{path.name}: {(np.abs(delta) > 1e-9).sum()} tracts moved, expected public RMSE {exp:.6f}")
