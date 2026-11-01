"""Basis signals, day 4 (2026-10-19): the fire-station mechanism and other low-redundancy signals.

S19: no Overture fire_department place AND a community anchor in the tract (post office,
     town hall, library, police, government office): a station very likely exists there.
S20: partial fire gap: tracts with fewer Overture stations than the physical density prior
     expects (1 - O/lambda, O >= 1).
S21: structural v1 transport contribution in maricopa-az, northern-ca and eastern-wa only.
S22: no Overture EMS place: where an EMS place exists it adds a defined facility type with a
     zero gap, which dilutes the HIFLD half of the POI component.
S23: CDC SVI (overall percentile), a scorecard stratum barely spanned by the current basis.
"""
import numpy as np
import pandas as pd

from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
lam = df["pop_rural"] / 4000 + df["pop_urban"] / 18000 + df["area_km2"] / 2500
partial = np.where(df["poi_fire"] > 0, np.clip(1 - df["poi_fire"] / np.maximum(lam, 1e-9), 0, 1), 0)

jobs = [
    ("s19_fire0_with_community", df["fire0"] * (df["poi_civic"] > 0), 0.15,
     "no Overture fire_department place but a community anchor (post office, town hall, library...)"),
    ("s20_partial_fire_gap", partial, 0.08, "fewer Overture fire stations than the physical density prior expects"),
    ("s21_c_transport_az_ca_wa", st["c_transport"] * df["region"].isin(["maricopa-az", "northern-ca", "eastern-wa"]),
     0.10, "structural v1 transport contribution, maricopa-az / northern-ca / eastern-wa only"),
    ("s22_no_ems_place", df["ems0"], 0.08, "no Overture ambulance_and_ems_services place in the tract"),
    ("s23_svi_overall", df["svi_overall"].fillna(df["svi_overall"].median()), 0.05, "CDC SVI overall percentile"),
]
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
