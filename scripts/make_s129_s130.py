"""Metro-level transport slopes, second pair (research of 28 October, round 33).

Same construction as s125-s128 (scripts/make_s125_s128.py) for the two metro areas that round 32
left out. On the 54-signal basis of the four public regions they are the least explained of all
metro copies and carry the most transport variance:

s129_t7_c_transport_dfw: Dallas-Fort Worth, 11 counties (1,702 tracts): R2 0.18, in-span
    orientation +0.11, 7.3 % of the v7 transport variance (Houston: 0.09, +0.10, 5.6 %);
s130_t7_c_transport_okc_tulsa: Oklahoma City and Tulsa metros, 7 counties (648 tracts): R2 0.36,
    orientation +0.24, 11.2 % of the variance. Each metro alone is under 300 tracts' worth of
    signal for Tulsa (274), so the two are pooled (decision D1-bis).

Residual correlations with the four earlier metro copies are at most 0.12 in absolute value.
Tucson (270 tracts) and Sacramento (201) are under 300 and get no copy.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
county = df["GEOID"].str[:5]
METROS = [("s129_t7_c_transport_dfw", ["48113", "48439", "48085", "48121", "48139", "48397", "48257", "48251", "48367", "48221", "48231"]),
          ("s130_t7_c_transport_okc_tulsa", ["40109", "40027", "40017", "40143", "40145", "40131", "40113"])]
for name, counties in METROS:
    inside = county.isin(counties).to_numpy()
    path, exp = write_signal(df, np.asarray(v7["c_transport"] * inside, float), name,
                             f"structural v7 transport contribution, counties {'/'.join(counties)} only ({inside.sum()} tracts)",
                             rho_guess=0.08)
    print(f"{path.name}: {inside.sum()} tracts, expected public RMSE {exp:.6f}")
