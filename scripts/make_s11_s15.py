"""Basis signals, day 3.

S11-S12: remaining regional offsets (eastern-wa, northern-ca; south-central-tx is the base).
S13: share of buildings drawn by Microsoft ML (no local mapper -> thin map overall).
S14: rural (non-urban share > 0.5), populated (>= 1,500) tracts with no Overture
     fire_department place: the fire-station gap concentrated where stations must exist.
S15: probability that the transport component is defined (structural v1); the organiser
     composite averages fewer components where it is undefined.
"""
import pandas as pd

from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
rural = df["rural_share"].fillna(df["rural_share"].median())

jobs = [
    ("s11_region_wa", (df["region"] == "eastern-wa").astype(float), 0.05, "regional offset: eastern-wa indicator"),
    ("s12_region_ca", (df["region"] == "northern-ca").astype(float), 0.02, "regional offset: northern-ca indicator"),
    ("s13_bld_msft_share", df["bld_msft_share"], 0.25, "share of Overture buildings sourced from Microsoft ML"),
    ("s14_rural_pop_no_fire", ((rural > 0.5) & (df["pop_total"] >= 1500) & (df["poi_fire"] == 0)).astype(float),
     0.20, "rural, populated tract with no Overture fire_department place"),
    ("s15_p_transport_defined", st["p_transport_defined"], 0.15, "structural v1 probability that the transport component is defined"),
]
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, sig.to_numpy(), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
