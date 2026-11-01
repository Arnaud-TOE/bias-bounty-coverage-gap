"""Nonlinear forms suggested by the blend itself (prepared 25 October, research round 10).

For each component, the blend's own part (weighted sum of its CBP or fire signals) was compared
with simple closed forms of the organiser rule, to find the nonlinearity a linear blend can only
approximate (no reference data; only our measured signals and permitted features):

- CBP part of the blend (s07, s24, s25, s36, s38, s42, s43, s86) tracks 1 - min(1, places / (k pop))
  with k about 0.005-0.01 (corr 0.60-0.65): tracts with almost no places per resident.
  s104_cbp_pop_k0075: that gap at k = 0.0075 (4 % of tracts), weighted 1 / (2 n_defined) (v7).
  [R2 about 0.55 on the 42-signal basis]
- fire part of the blend (s05, s14, s19, s20, s22, s39, s40) tracks "no Overture fire station x
  log area" (corr 0.73); the closed form P(reference station) = 1 - exp(-area / A) with A = 20 km2
  has R2 0.75 on the basis and an in-span direction of +0.235 (structural c_fire: +0.10).
  s105_fire_parea20: no Overture fire_department place x (1 - exp(-area / 20 km2)).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
places = df["poi_n"].to_numpy(float)
pop = df["pop_total"].fillna(0).to_numpy(float)
gap_cbp = np.where(pop > 0, 1 - np.minimum(1, places / np.maximum(0.0075 * pop, 1e-9)), 0.0)
w_half = 1 / (2 * v7["n_defined"].clip(lower=1).to_numpy())
nofire = (df["poi_fire"] == 0).to_numpy(float)
p_station = 1 - np.exp(-df["area_km2"].to_numpy(float) / 20.0)

for name, sig, rho, purpose in [
    ("s104_cbp_pop_k0075", gap_cbp * w_half, 0.08, "CBP gap 1-min(1, places/(0.0075 pop)) weighted 1/(2 n_defined)"),
    ("s105_fire_parea20", nofire * p_station, 0.20, "no Overture fire station x (1 - exp(-area/20 km2))"),
]:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
