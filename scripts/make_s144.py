"""Fire stations: county-level Overture completeness (research of 30 October, round 72).

Companion of s143 (scripts/make_s143.py). Fire services are organised by county (county departments,
Texas emergency services districts, Oklahoma rural fire districts), and Overture's coverage of their
stations varies from county to county. Within each county, known stations (Overture fire_department as
primary or alternate category, name-verified misfiled stations, OSM fire-station buildings, v9 town
cores) are compared with the stations the v9 rate expects; the completeness is shrunk towards the
overall ratio with 5 expected stations' worth of prior. Tracts with no known station, no town core and
not on a region edge get the v9 rate scaled by (overall / county completeness); each region's expected
total is unchanged.

s144_t9_fire_county_completeness: v9 fire contribution with this scaling minus v9 (two seeds averaged).
On the 65-signal basis 75 % new, in-span orientation +0.16; beside s143 72 % new, +0.12; correlation
0.38 with s143 (20 km neighbourhoods instead of counties: +0.17 to +0.18 alone, +0.10 to +0.12 beside
s143, correlation 0.44 to 0.54).
"""
from dataclasses import replace

import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

PRIOR = 5.0  # expected stations' worth of shrinkage towards the overall completeness

df = load_table()
for name in ("features_roadref", "features_osmfac"):
    df = df.merge(pd.read_parquet(config.FEATURES / f"{name}.parquet"), on="GEOID", how="left")
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()) / ok["cty2_b10"].sum()
v9_params = Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9, fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000)
town = df["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
d9 = df.assign(fire_misfiled_clean=df["fire_misfiled_clean"].fillna(0) + town)  # v9: town cores as evidence

known = (df[["poi_fire", "poi_fire_alt", "fire_misfiled_clean", "osm_fire_bld"]].fillna(0) > 0).any(axis=1).to_numpy()
# Region-edge tracts keep the v9 rate, as in s143 (their counties extend beyond the package).
edge = df["GEOID"].isin(pd.read_parquet(config.FEATURES / "region_edge.parquet")["GEOID"]).to_numpy()
free = ~known & ~town & ~edge
pop_r, pop_u, area = df["pop_rural"].fillna(0).to_numpy(), df["pop_urban"].fillna(0).to_numpy(), df["area_km2"].to_numpy()
lam = pop_r * v9_params.fire_per_rural_pop + pop_u * v9_params.fire_per_urban_pop + area * v9_params.fire_per_km2
n_known = np.maximum(df[["poi_fire", "poi_fire_alt", "fire_misfiled_clean"]].fillna(0).sum(axis=1).to_numpy(),
                     df["osm_fire_bld"].fillna(0).to_numpy()) + town
county = df["GEOID"].str[:5].to_numpy()
by_county = pd.DataFrame({"county": county, "known": n_known, "expected": lam}).groupby("county").sum()
overall = n_known.sum() / lam.sum()
completeness = ((by_county["known"].reindex(county).to_numpy() + PRIOR * overall)
                / (by_county["expected"].reindex(county).to_numpy() + PRIOR))
scale = np.where(free, overall / completeness, 1.0)
for r in df["region"].unique():
    k = free & (df["region"] == r).to_numpy()
    if k.sum():
        scale[k] *= lam[k].sum() / (lam[k] * scale[k]).sum()
print(f"{free.sum()} tracts without a known station; scale {scale[free].min():.2f}-{scale[free].max():.2f}")

# bbx.structural reads rural / urban population and area only for the fire rate.
scaled = d9.assign(pop_rural=pop_r * scale, pop_urban=pop_u * scale, area_km2=area * scale)
delta = np.zeros(len(df))
for seed_shift in (0, 1):
    p = replace(v9_params, seed=v9_params.seed + seed_shift)
    delta += (simulate(scaled, p)["c_fire"] - simulate(d9, p)["c_fire"]).to_numpy() / 2
path, exp = write_signal(df, delta, "s144_t9_fire_county_completeness",
                         "v9 fire contribution with the rate scaled by county completeness of known stations, minus v9",
                         rho_guess=0.08)
print(f"{path.name}: expected public RMSE {exp:.6f}")
