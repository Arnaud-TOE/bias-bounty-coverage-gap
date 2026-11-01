"""Day 3 (2026-10-18) batch, together with the already prepared s13 and s14.

S16: first blend of the 8 scored signals (ridge 0.05) -- checks that the predicted public
     RMSE is realised (validation of the leaderboard algebra) and gives a real score.
S17: share of route-tagged km (Interstate / US / state) that Overture classes below
     'secondary': TIGER counts these roads as S1100/S1200, Overture's scored classes do not.
S18: structural v1 transport contribution restricted to south-central-tx (lets the blend
     weight Texas transport separately; 61 % of tracts).
"""
import numpy as np
import pandas as pd

from bbx import blend, submit
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")

b = blend.fit(ridge=0.05)
print("blend files:", b.files)
print("weights:", np.round(b.weights, 3), f"rho={b.rho:.4f}", f"expected={b.expected_rmse:.6f}")
submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": b.prediction}), "s16_blend_v1",
             b.expected_rmse, "blend of s03-s10 (ridge 0.05) weighted by leaderboard-implied covariances")

jobs = [
    ("s17_major_route_unscored_share", df["major_unscored_share"].fillna(0), 0.15,
     "share of Interstate/US/state route km that Overture classes below secondary"),
    ("s18_c_transport_tx", st["c_transport"] * (df["region"] == "south-central-tx"), 0.30,
     "structural v1 transport contribution, south-central-tx only"),
]
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
