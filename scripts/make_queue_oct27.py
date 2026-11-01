"""Provisional queue for 27 October (research of 25 October, round 13): fire stations by region.

Transport got one weight per region (s81-s84) and the OK copy brought the largest marginal gain of
its day. The fire-station term never had that, although its reference (USGS structures / HIFLD) is
assembled state by state and its completeness varies by state, and the measured region means show
our POI part fits Oklahoma but is about twice too high elsewhere (AZ about three times).
Region-restricted copies of the v8 fire contribution are new to the 47-signal basis (R2 0.07-0.21)
and nearly independent of one another; with the pooled copy (s100) the blend can set one fire
weight per region (south-central-tx = s100 minus the four others).

Exact within-region covariances from s77 and s81-s84 also show that eastern-wa transport has no
covariance with the truth (slope 0.02 against 1.0-2.1 elsewhere); s110 lets the blend weight the
POI side of that region on its own.

s100_t8_c_fire (already built by make_queue_oct26.py),
s107_t8_c_fire_ok, s108_t8_c_fire_az, s109_t8_c_fire_ca, s110_t8_c_fire_wa: s100 restricted to one region.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8.parquet"), on="GEOID", how="left")

for name, region, rho in [("s107_t8_c_fire_ok", "eastern-ok", 0.10), ("s108_t8_c_fire_az", "maricopa-az", 0.06),
                          ("s109_t8_c_fire_ca", "northern-ca", 0.05), ("s110_t8_c_fire_wa", "eastern-wa", 0.05)]:
    sig = v8["c_fire"] * (df["region"] == region)
    path, exp = write_signal(df, np.asarray(sig, float), name,
                             f"structural v8 fire contribution (s100), {region} only", rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s100_t8_c_fire", "s107_t8_c_fire_ok", "s108_t8_c_fire_az", "s109_t8_c_fire_ca", "s110_t8_c_fire_wa"]
(config.SUBMISSIONS / "upload_2026-10-27.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n(provisional: final order after the 26 October scores)\n",
    encoding="utf-8")
