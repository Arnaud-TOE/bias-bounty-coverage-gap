"""Provisional queue for 26 October (prepared 25 October; final order after the 25 October scores).

Structural v8 = v7 transport (bbx.structural level2 / tx_split, see make_queue_oct25e.py) with clean
fire evidence: a reference station is forced (p 0.9) where Overture has a name-verified station
under another category (vendors excluded), an OSM fire-station building, or fire_department as an
alternate category -- instead of the v1 name regex, which also caught extinguisher vendors.
Screened on the 42-signal basis (R2): v8 score 0.87 (its difference from the v7 score is 95 %
new), v8 fire contribution 0.78.

s99_t8_score: v8 composite,
s100_t8_c_fire: v8 fire contribution,
s101_t7_transport_gap: v7 expected transport gap (component level; v3 version s88 not submitted),
s102_t7_p_transport_one: v7 probability that the transport gap equals 1,
s103_t8_p_fire_defined: v8 probability that the reference has a fire station.
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
v8.to_parquet(config.INTERIM / "structural_v8.parquet", index=False)
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")

for name, sig, rho, purpose in [
    ("s99_t8_score", v8["score"], 0.45, "structural v8 composite: v7 transport, clean fire-station evidence"),
    ("s100_t8_c_fire", v8["c_fire"], 0.10, "structural v8 fire contribution (clean fire-station evidence)"),
    ("s101_t7_transport_gap", v7["transport"].fillna(0), 0.45, "structural v7 expected transport gap (component level)"),
    ("s102_t7_p_transport_one", v7["p_transport_one"], 0.10, "structural v7 probability that the transport gap equals 1"),
    ("s103_t8_p_fire_defined", v8["p_fire_defined"], 0.15, "structural v8 probability that the reference has a fire station"),
]:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s99_t8_score", "s100_t8_c_fire", "s101_t7_transport_gap", "s102_t7_p_transport_one",
         "s103_t8_p_fire_defined"]
(config.SUBMISSIONS / "upload_2026-10-26.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n(provisional: final order after the 25 October scores)\n",
    encoding="utf-8")
