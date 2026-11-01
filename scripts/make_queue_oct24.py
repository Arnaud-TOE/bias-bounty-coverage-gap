"""Queue for 24 October, after s77 (structural v3 transport) scored 0.074257 alone (rho 0.563).

The transport contribution is now the strongest signal, and its regional calibration (TIGER
S1200 coverage of county and FM roads, Overture/TIGER ratio) is the most uncertain part. Four
region-restricted copies of the v3 contribution let the blend set one transport weight per
region (eastern-wa = s77 minus the four others):

s81_t3_tx, s82_t3_az, s83_t3_ok, s84_t3_ca: s77 restricted to one region,
s85_t3_txfm05: v3 transport contribution with Texas FM/RM/Loop/Spur km at weight 0.5 in the
    reference proxy (only part of the FM network is S1200 in TIGER).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
v3 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v3.parquet"), on="GEOID", how="left")
cal = dict(w_county_region={"eastern-ok": 0.24, "maricopa-az": 0.0, "northern-ca": 0.0,
                            "eastern-wa": 0.0, "south-central-tx": 0.0})
fm = simulate(df, Params(n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True,
                         w_txsec=0.5, **cal))
fm.to_parquet(config.INTERIM / "structural_v3_txfm05.parquet", index=False)

jobs = []
for name, region, rho in [("s81_t3_tx", "south-central-tx", 0.45), ("s82_t3_az", "maricopa-az", 0.15),
                          ("s83_t3_ok", "eastern-ok", 0.25), ("s84_t3_ca", "northern-ca", 0.12)]:
    sig = v3["c_transport"] * (df["region"] == region)
    jobs.append((name, sig, rho, f"structural v3 transport contribution (s77), {region} only"))
jobs.append(("s85_t3_txfm05", fm["c_transport"], 0.53,
             "structural v3 transport contribution with Texas FM/RM km at weight 0.5"))
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = [j[0] for j in jobs]
(config.SUBMISSIONS / "upload_2026-10-24.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
