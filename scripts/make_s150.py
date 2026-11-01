"""Edge of the score under the transport that paid on 31 October (research of 31 October, round 94).

s146 (Interstate and Texas loop local names at 0.25, on top of v7L) scored on 31 October: removal cost
0.00083, implied correlation +0.14. s147 (inverse reading of the published ratio, local names 0.35)
gave an implied correlation of +0.40, almost all of it inside the span of the measured signals.
Edges of the composite paid right after a model change that paid (s102 after s97, s117 after v8);
s149 is the edge of s140's transport alone (v9L).

v9LFinv: v9 fire (town cores, rural / urban station rates) with the transport of s146 and s147 read
together: local names of counted non-Interstate majors and Texas loops at 0.35, Interstate local
names at 0.25 (business loops and unnumbered toll systems out, as s146), Texas FM/RM and Oklahoma
county weights re-solved to the inverse reading (Overture/TIGER 1/0.71 and 1/1.59: 0.137 and 0.213).

s150_t9lfi_p_score_ge30_delta: P(score >= 0.30) under v9LFinv minus under v9 (same seed). On the
72-signal basis 34 % new, in-span orientation +0.53 (s149: 38 % new, +0.34); correlated +0.72 with
s149, +0.46 with s147, +0.17 with s146.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from bbx import config
from bbx.signals import write_signal

W_LOCAL, W_INTERSTATE = 0.35, 0.25
TX_RATIO, OK_RATIO = 1 / 0.71, 1 / 1.59  # Overture/TIGER, inverse reading
# s146's local-name tables (Texas loops, toll-system Interstate names) and its feature table, without running s146
_src = Path(__file__).with_name("make_s146.py").read_text(encoding="utf-8")
exec(_src[:_src.index("zero = np.zeros")])

osm = pd.read_parquet(config.FEATURES / "features_osmfac.parquet")
df = df.merge(osm[[c for c in osm.columns if c == "GEOID" or c not in df.columns]], on="GEOID", how="left")
left_out = df["zloc1_b10"].fillna(0.0) + df["ztoll1_b10"]
d = df.assign(majiloc_b10=df["majiloc_b10"] - left_out, majloc_b10=df["majloc_b10"] - left_out)
extra = W_LOCAL * d["txothloc_b10"].to_numpy()
tx, ok = d[d["region"] == "south-central-tx"], d[d["region"] == "eastern-ok"]
local = lambda x: W_LOCAL * (x["majloc_b10"] - x["majiloc_b10"]).sum() + W_INTERSTATE * x["majiloc_b10"].sum()
w_fm = ((tx["sc_in"].sum() / TX_RATIO - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx) - extra[tx.index].sum())
        / (tx["txfm_b10"].sum() + W_LOCAL * tx["txloc_b10"].sum()))
w_ok = (ok["sc_in"].sum() / OK_RATIO - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
print(f"TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
town = d["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
v9lfi = simulate(d.assign(maj2x_b10=d["maj2x_b10"] + extra, fire_misfiled_clean=d["fire_misfiled_clean"].fillna(0) + town), Params(
    n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    local_name_weight=W_LOCAL, interstate_local_weight=W_INTERSTATE,
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9, fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000))
v9 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v9.parquet"), on="GEOID", how="left")
delta = np.asarray(v9lfi["p_score_ge30"] - v9["p_score_ge30"], float)
path, exp = write_signal(df, delta, "s150_t9lfi_p_score_ge30_delta",
                         "P(score >= 0.30) under v9LFinv (v9 fire, s146 + s147 transport) minus under v9", rho_guess=0.07)
print(f"{path.name}: {(np.abs(delta) > 1e-9).sum()} tracts moved, expected public RMSE {exp:.6f}")
