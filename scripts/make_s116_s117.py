"""Edge signals for 29 October (research of 27 October, round 16).

s102 (probability that the transport gap equals 1) was weak alone but gave the best marginal
gain of 26 October: the score has point masses (0, and component gaps of exactly 1) that a linear
blend of expectations cannot build. bbx.structural now also returns other edge probabilities;
on the 51-signal basis the two most new ones are:
s116_t8_p_zero: probability that the composite is exactly 0 (R2 0.83, in-span part -0.47),
s117_t8_p_score_ge30: probability that the composite reaches 0.30 (R2 0.78, in-span part +0.44).
Both come from the v8 settings (same parameters and seed as scripts/make_queue_oct26.py, so the
same draws), recomputed here and saved as data/interim/structural_v8e.parquet.
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
v8 = simulate(df, Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9))
v8.to_parquet(config.INTERIM / "structural_v8e.parquet", index=False)
for name, col, rho, purpose in [
    ("s116_t8_p_zero", "p_zero", -0.30, "structural v8 probability that the composite score is exactly 0 (flipped)"),
    ("s117_t8_p_score_ge30", "p_score_ge30", 0.30, "structural v8 probability that the composite score reaches 0.30"),
]:
    path, exp = write_signal(df, np.asarray(v8[col], float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
