"""The published ratio read the other way round, with more local names (research of 30 October, rounds 77-78).

The Info page says the ratio of Overture to TIGER named-highway length "ranges from 0.71 to 1.59 across
the four study regions" without saying which way round. Every model since v7 reads it as
Overture/TIGER: Texas at 1.59, Oklahoma at 0.71. Read as TIGER/Overture, Texas sits at 0.71 and
Oklahoma at 1.59, so the TIGER reference is 13 % longer in both (Overture/TIGER 1.408 and 0.629).
Two scores point to a longer reference: the blend weighs the v7 transport contribution about 1.25
times, and s140 (local names at 0.25, scored 30 October) about 1.9 times its model size.

A joint grid on the 71 scored signals (Texas and Oklahoma targets x local-name weight 0.15 / 0.25 /
0.35, judged beside a pure scale control, $TEMP/claude_ext/scr/tiger_grid.py) favours local names at
0.35 in every reading; with 0.25 the inverse reading keeps only +0.07 beside the scale control. With
local names at 0.35 the inverse reading is consistent in all four regions (Overture/TIGER Arizona
1.28, California 1.40, both within 0.629-1.408).

s147_t7linv_c_transport_delta: v7L with local names at 0.35 and the Texas FM/RM and Oklahoma county
weights re-solved to the inverse reading (0.175 and 0.235), minus v7L (local names 0.25, FM 0.051,
county 0.075; same seed). Shares of tracts without a road component unchanged.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

W_BASE, W_INV = 0.25, 0.35
df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_uncounted.parquet"), on="GEOID", how="left")
df["majloc_b10"] = df["majloc_b10"] - df["zloc23_b10"].fillna(0.0)  # as s140: local names of counted majors only
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
lam = fit_lambdas(df)


def v7l(tx_overture_over_tiger: float, ok_overture_over_tiger: float, W: float) -> pd.DataFrame:
    local = lambda d: W * (d["majloc_b10"] - d["majiloc_b10"]).sum()
    w_fm = ((tx["sc_in"].sum() / tx_overture_over_tiger - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx))
            / (tx["txfm_b10"].sum() + W * tx["txloc_b10"].sum()))
    w_ok = (ok["sc_in"].sum() / ok_overture_over_tiger - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
    print(f"Overture/TIGER TX {tx_overture_over_tiger:.3f}, OK {ok_overture_over_tiger:.3f}, local names {W}: FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
    return simulate(df, Params(
        n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, level2=True,
        tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19}, local_name_weight=W,
        w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                         "eastern-wa": 0.0, "south-central-tx": 0.0},
        p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
                  "south-central-tx": 0.5}))


base = v7l(1.59, 0.71, W_BASE)
saved = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7L.parquet"), on="GEOID", how="left")
assert np.abs(base["c_transport"] - saved["c_transport"]).max() < 1e-12, "v7L no longer reproduces s140's model"
inverse = v7l(1 / 0.71, 1 / 1.59, W_INV)
path, exp = write_signal(df, np.asarray(inverse["c_transport"] - base["c_transport"], float), "s147_t7linv_c_transport_delta",
                         "v7L with local names 0.35 and FM / OK county weights re-solved to the inverse ratio reading, minus v7L",
                         rho_guess=0.10)
print(f"{path.name}: expected public RMSE {exp:.6f}")
