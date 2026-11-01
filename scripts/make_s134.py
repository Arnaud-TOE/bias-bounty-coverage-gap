"""Town-core fire stations (research of 28 October, round 41).

A micropolitan or small-town core tract (RUCA primary code 4 or 7) hosts its town's central fire
station almost by definition, but the v8 fire prior counts urban residents at one station per
18,000, so it expects few reference stations there (mean fire contribution 0.015-0.020). Where
Overture has no fire_department place in such a tract, the fire gap is 1 as soon as the USGS
station is there. 63 % of micropolitan cores and 48 % of small-town cores have no Overture
fire_department place.

s134_t8_fire_towncore: v8 with the town core as one more piece of reference-station evidence
(the same rule as a name-verified misfiled station: P(H >= 1) = 0.9 where Overture has none),
minus v8. Non-zero on 342 tracts, 317 of them in the four public regions (decision D1-bis); on
the 60-signal basis it is 87 % new, in-span orientation +0.11, and its residual is nearly
independent of the 29 October lot (|correlation| <= 0.07). Same parameters and seed as
scripts/make_s116_s117.py (structural_v8e), so only the town-core tracts move.
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
    fire_evidence="clean", p_misfiled_fire=0.9)
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8e.parquet"), on="GEOID", how="left")
town = df["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
with_town = df.assign(fire_misfiled_clean=df["fire_misfiled_clean"].fillna(0) + town)
v8t = simulate(with_town, params)
delta = (v8t["c_fire"] - v8["c_fire"]).to_numpy()
moved = np.abs(delta) > 1e-9
assert (moved <= town).all(), "only town-core tracts may move (same seed as structural_v8e)"
path, exp = write_signal(df, delta, "s134_t8_fire_towncore",
                         f"v8 fire contribution with RUCA 4/7 town cores as station evidence, minus v8 ({moved.sum()} tracts)",
                         rho_guess=0.10)
print(f"{path.name}: {moved.sum()} tracts moved, expected public RMSE {exp:.6f}")
