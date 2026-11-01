"""Interstate local names as extra TIGER records (research of 30 October, round 60).

Companion of s140 (scripts/make_s140.py). The MTFCC is carried by the edge (TIGER/Line technical
documentation: "the MTFCC identifies the specific code for the primary feature on the edge"), so every
name on a primary-road edge becomes one more S1100 record in the All Roads file, Interstates included
("Pan Am Expressway" over I-35). s140 left the Interstates out; this signal adds only them.

v7Li: local-name copies of Interstate segments at weight 0.5 (bbx.features_roadref majiloc), Texas
FM/RM and Oklahoma county weights re-solved to the published 1.59 and 0.71 (0.065 and 0.084).

s141_t7li_c_transport_delta: v7Li transport contribution minus v7 (same seed). On the 65-signal basis
80 % new, and still 80 % new once s140 is added (independent of it); in-span orientation +0.04.
To submit on 31 October only if s140 scores well.

Correction of 30 October (round 67, as scripts/make_s140.py): the local names of Interstate business
loops ('US:I:Business:Loop', multiplicity 0 in v7) are left out, so the shares of tracts without a
road component stay those of v7 (California 37.6 -> 37.9 %); FM 0.067, OK county 0.085; 78 % new
beside the corrected s140, in-span orientation +0.07.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

W_INTERSTATE = 0.5
df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_uncounted.parquet"), on="GEOID", how="left")
for c in ("majloc_b10", "majiloc_b10"):  # local names of counted Interstates only
    df[c] = df[c] - df["zloc1_b10"].fillna(0.0)
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
local = lambda d: W_INTERSTATE * d["majiloc_b10"].sum()
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx)) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
print(f"TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
v7li = simulate(df, Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    local_name_weight=0.0, interstate_local_weight=W_INTERSTATE,
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5}))
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
path, exp = write_signal(df, np.asarray(v7li["c_transport"] - v7["c_transport"], float), "s141_t7li_c_transport_delta",
                         f"v7 transport with Interstate local names as extra TIGER records (weight {W_INTERSTATE}), minus v7",
                         rho_guess=0.05)
print(f"{path.name}: expected public RMSE {exp:.6f}")
