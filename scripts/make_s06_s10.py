"""Basis signals for the leaderboard-measured blend (decision D1), day 2.

S06-S08: additive contributions of the structural model v1 (transport, CBP, schools);
together with S04 (their sum plus fire/building/EMS) they let the blend re-weight
mechanisms. S09-S10: regional offsets (eastern-ok, maricopa-az indicators).
"""
import pandas as pd

from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")

jobs = [
    ("s06_c_transport", st["c_transport"], 0.25, "structural v1 transport contribution (route proxy vs Overture scored classes)"),
    ("s07_c_cbp", st["c_cbp"], 0.15, "structural v1 CBP-half contribution (places vs establishment proxy)"),
    ("s08_c_school", st["c_school"], 0.10, "structural v1 school contribution"),
    ("s09_region_ok", (df["region"] == "eastern-ok").astype(float), 0.25, "regional offset: eastern-ok indicator"),
    ("s10_region_az", (df["region"] == "maricopa-az").astype(float), -0.10, "regional offset: maricopa-az indicator"),
]
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, sig.to_numpy(), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
