"""Fire-station gap filling (research of 30 October, round 71).

True fire stations are spread fairly regularly (rural stations every 10 to 15 km; NFPA counts about
54,600 in the US), and Overture's fire_department places hold only about 60 % of the reference ones
(research of 25 October). So a tract with no known station is more likely to hold a reference station
when it is far from every known station, and less likely when known stations surround it. The v9
prior looks at the tract alone (rural and urban population, area).

Known stations: Overture places with fire_department as primary or alternate category, name-verified
fire stations under other categories (bbx.features_osmfac.FIRE_VERIFIED_RE), and OSM fire-station
buildings. For tracts with no known station and no town-core evidence, the v9 fire rate is scaled by
exp(0.35 z), z the log distance from the tract's interior point to the nearest known station,
standardised within each region; each region's expected total is unchanged.

s143_t9_fire_gapfill: v9 fire contribution with gap filling minus v9 (same seeds, two seeds averaged
to damp the Monte Carlo noise of the Poisson draws). On the 65-signal basis 55 % new, in-span
orientation +0.20 (beta 0.25 to 0.5 and a global centring give +0.19 to +0.20; beta -0.5 gives
-0.21; a seed-only control gives +0.00). Highest correlation with a scored signal 0.50 (s136).
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from bbx import config
from bbx.dataset import load_table
from bbx.features_osmfac import FIRE_RE, FIRE_VENDOR_RE, FIRE_VERIFIED_RE
from bbx.io import connect, ref_path, strata_path
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

BETA = 0.35
TO_M = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"


def nearest_known_station_km() -> pd.DataFrame:
    con = connect()
    stations, points = [], []
    for region in config.REGIONS:
        pois = ref_path(region, "overture-pois").as_posix()
        bld = ref_path(region, "overture-buildings").as_posix()
        stations.append(con.sql(f"""
            SELECT ST_X(g) AS x, ST_Y(g) AS y FROM (
                SELECT {TO_M.format(g='ST_Centroid(geometry)')} AS g, categories.primary AS cat,
                       coalesce(categories.alternate, []) AS alt, lower(coalesce(names.primary, '')) AS nm FROM '{pois}')
            WHERE cat = 'fire_department' OR list_has_any(alt, ['fire_department'])
               OR (regexp_matches(nm, '{FIRE_VERIFIED_RE}') AND NOT regexp_matches(nm, '{FIRE_VENDOR_RE}'))""").df())
        stations.append(con.sql(f"""
            SELECT ST_X(g) AS x, ST_Y(g) AS y FROM (
                SELECT {TO_M.format(g='ST_Centroid(geometry)')} AS g, class AS cls, lower(coalesce(names.primary, '')) AS nm
                FROM '{bld}' WHERE class = 'fire_station' OR names.primary IS NOT NULL)
            WHERE cls = 'fire_station' OR regexp_matches(nm, '{FIRE_RE}')""").df())
        points.append(con.sql(f"""SELECT GEOID, ST_X(g) AS x, ST_Y(g) AS y FROM (
            SELECT GEOID, {TO_M.format(g='ST_PointOnSurface(geometry)')} AS g FROM '{strata_path(region, "census-tracts").as_posix()}')""").df())
    pts = pd.concat(points, ignore_index=True)
    d, _ = cKDTree(pd.concat(stations).to_numpy()).query(pts[["x", "y"]].to_numpy())
    return pts.assign(dist_km=d / 1000)[["GEOID", "dist_km"]]


df = load_table()
for name in ("features_roadref", "features_osmfac"):
    df = df.merge(pd.read_parquet(config.FEATURES / f"{name}.parquet"), on="GEOID", how="left")
df = df.merge(nearest_known_station_km(), on="GEOID", how="left")
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
# Region-edge tracts keep the v9 rate: stations beyond the region boundary are not in the package, so
# their distances are overstated (154 of the 690 tracts farther than 8 km).
edge = df["GEOID"].isin(pd.read_parquet(config.FEATURES / "region_edge.parquet")["GEOID"]).to_numpy()
free = ~known & ~town & ~edge
pop_r, pop_u, area = df["pop_rural"].fillna(0).to_numpy(), df["pop_urban"].fillna(0).to_numpy(), df["area_km2"].to_numpy()
lam = pop_r * v9_params.fire_per_rural_pop + pop_u * v9_params.fire_per_urban_pop + area * v9_params.fire_per_km2
log_d = np.log(np.maximum(df["dist_km"].to_numpy(), 0.2))
scale = np.ones(len(df))
for r in df["region"].unique():
    k = free & (df["region"] == r).to_numpy()
    if k.sum() > 5:
        scale[k] = np.exp(BETA * (log_d[k] - log_d[k].mean()) / log_d[k].std())
        scale[k] *= lam[k].sum() / (lam[k] * scale[k]).sum()
print(f"{free.sum()} tracts without a known station; scale {scale[free].min():.2f}-{scale[free].max():.2f}")

# bbx.structural reads rural / urban population and area only for the fire rate.
gapfill = d9.assign(pop_rural=pop_r * scale, pop_urban=pop_u * scale, area_km2=area * scale)
delta = np.zeros(len(df))
for seed_shift in (0, 1):
    p = replace(v9_params, seed=v9_params.seed + seed_shift)
    delta += (simulate(gapfill, p)["c_fire"] - simulate(d9, p)["c_fire"]).to_numpy() / 2
path, exp = write_signal(df, delta, "s143_t9_fire_gapfill",
                         "v9 fire contribution with gap filling (rate x exp(0.35 z(log distance to nearest known station))), minus v9",
                         rho_guess=0.10)
print(f"{path.name}: expected public RMSE {exp:.6f}")
