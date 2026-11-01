"""Provisional queue for 28 October (prepared 26 October): the transport-gap-equals-1 term by region.

s102 (v7 probability that the transport gap equals 1) was weak alone (corr +0.07) but brought the
largest marginal gain of 26 October (-0.00066): it carries the extreme part of the transport
term, which a linear blend of expectations cannot build. Its region-restricted copies are new to
the 51-signal basis (R2 0.19-0.46) and let the blend set one weight per region, as s81-s84 did
for the transport expectation (eastern-wa = s102 minus the four others).

s112_t7_p_one_tx, s113_t7_p_one_ok, s114_t7_p_one_az, s115_t7_p_one_ca: s102 restricted to one region.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")

for name, region, rho in [("s112_t7_p_one_tx", "south-central-tx", 0.05), ("s113_t7_p_one_ok", "eastern-ok", 0.05),
                          ("s114_t7_p_one_az", "maricopa-az", 0.03), ("s115_t7_p_one_ca", "northern-ca", 0.03)]:
    sig = v7["p_transport_one"] * (df["region"] == region)
    path, exp = write_signal(df, np.asarray(sig, float), name,
                             f"structural v7 probability that the transport gap equals 1 (s102), {region} only", rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s112_t7_p_one_tx", "s113_t7_p_one_ok", "s114_t7_p_one_az", "s115_t7_p_one_ca", "s105_fire_parea20"]
(config.SUBMISSIONS / "upload_2026-10-28.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n(provisional: final order after the 27 October scores)\n",
    encoding="utf-8")
