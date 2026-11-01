"""Edge of the score under the s140 transport (research of 30 October, round 90).

The edges of the composite paid twice right after a model change that paid: s102 (P(transport gap =
1) under v7, after s97) and s117 (P(score >= 0.30) under v8). s140 (v7L transport, local names) paid
on 30 October; the matching edge under v9L (v9 fire with the v7L transport,
scripts/make_structural_v9L.py) has never been measured.

s149_t9l_p_score_ge30_delta: P(score >= 0.30) under v9L minus under v9 (same seed). On the 71-signal
basis 38 % new, in-span orientation +0.35. Its sibling built from a fire change (s137, v9 - v8) gave
0.00004; this one comes from the transport change.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v9 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v9.parquet"), on="GEOID", how="left")
v9l = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v9L.parquet"), on="GEOID", how="left")
delta = np.asarray(v9l["p_score_ge30"] - v9["p_score_ge30"], float)
path, exp = write_signal(df, delta, "s149_t9l_p_score_ge30_delta",
                         "P(score >= 0.30) under v9L (v9 fire, v7L transport) minus under v9", rho_guess=0.07)
print(f"{path.name}: {(np.abs(delta) > 1e-9).sum()} tracts moved, expected public RMSE {exp:.6f}")
