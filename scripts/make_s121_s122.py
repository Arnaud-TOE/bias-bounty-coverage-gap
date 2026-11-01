"""Slopes by tract type for 29 October (research of 28 October, round 23).

Regional copies let the blend weight a mechanism differently by region (s81-s84, s107-s110,
s112-s115). The mechanisms also differ by tract type: boundary double counting dominates small
urban tracts (a boundary highway is long relative to the tract and may leave no Overture road
inside), and Overture's place coverage is weakest on tribal land. On the 51-signal basis:
s121_t7_c_transport_small: v7 transport contribution in tracts under 2 km2 (2,376 tracts), R2 0.19;
s122_t8_c_fire_tribal: v8 fire contribution in tracts more than half tribal (835 tracts), R2 0.37.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8.parquet"), on="GEOID", how="left")
small = (df["area_km2"] < 2).to_numpy()
tribal = (df["tribal_pct"].fillna(0) > 0.5).to_numpy()
for name, sig, rho, purpose in [
    ("s121_t7_c_transport_small", v7["c_transport"] * small, 0.10, "structural v7 transport contribution, tracts under 2 km2 only"),
    ("s122_t8_c_fire_tribal", v8["c_fire"] * tribal, 0.08, "structural v8 fire contribution, tracts more than half tribal only"),
]:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
