"""Local names that s140 leaves out: Interstates and Texas state loops (research of 30 October, round 74).

s140 (v7L, local names of counted non-Interstate majors at 0.25) scored on 30 October: removal cost
0.00111, new part correlated +0.15 with the truth, so TIGER does store a route's local name as one
more record. Two sets of local names are still missing from v7L:
- Interstates (Pan Am Expressway, Katy Freeway, the Oklahoma turnpikes), left to s141;
- Texas state Loop / Spur / Beltway / Toll routes (Loop 1604 'Anderson Loop', Loop 1 'MoPac',
  Beltway 8 'Sam Houston Parkway', SH 130 'Pickle Parkway', Grand Parkway: 3,386 km in the 10 m
  band), which bbx.structural routes through the FM term, so v7L gives them 0.25 x 0.051.
s141 (Interstates at 0.5 on top of v7) cannot sit beside s140: with both, the Texas FM weight needed
for the published 1.59 ratio turns negative. At 0.25 both sets fit (FM 0.017, Oklahoma county 0.053).

Oklahoma turnpikes carry an unnumbered 'US:OK:Turnpike' network beside the route number, which
the multiplicity already counts as the turnpike's own record ('I- 44' + 'Turner Tpke'). Their local
names ('Governor Roy Joseph Turner Turnpike', 1,005 km of Interstate segments) are that same record,
so they are left out here.

s146_t7lf_c_transport_delta: v7L with Interstate local names (counted Interstates only, business
loops and unnumbered toll systems out) and Texas loop local names at 0.25, minus v7L (same seed).
Shares of tracts without a road component unchanged.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.features import ROUTE_LEVEL_SQL
from bbx.features_roadref import LOCAL_NAME_SQL, STATE_SPECIAL
from bbx.io import connect, ref_path, strata_path
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

W = 0.25
TO_M = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
REGION = "south-central-tx"

con = connect()
con.sql(f"CREATE OR REPLACE TEMP TABLE tm AS SELECT GEOID, ST_Buffer({TO_M.format(g='geometry')}, 10) AS g10 "
        f"FROM '{strata_path(REGION, 'census-tracts').as_posix()}'")
con.sql(f"""
    CREATE OR REPLACE TEMP TABLE rm AS SELECT g FROM (
        SELECT coalesce({ROUTE_LEVEL_SQL}, 9) AS lvl, {LOCAL_NAME_SQL} AS n_local,
               coalesce(list_bool_or(list_transform(routes, r -> regexp_full_match(r.network, 'US:TX:(FM|RM)'))), false) AS fm,
               {TO_M.format(g='geometry')} AS g
        FROM '{ref_path(REGION, 'overture-roads').as_posix()}' WHERE routes IS NOT NULL)
    WHERE lvl = 4 AND NOT fm AND n_local = 1""")
loops = con.sql("""SELECT t.GEOID, sum(ST_Length(ST_Intersection(t.g10, r.g))) / 1000 AS txothloc_b10
                   FROM tm t JOIN rm r ON ST_Intersects(t.g10, r.g) GROUP BY 1""").df()


def toll_interstate_local_km(region: str) -> pd.DataFrame:
    """10 m band km of Interstate local names on segments that also carry an unnumbered toll system."""
    con.sql(f"CREATE OR REPLACE TEMP TABLE tz AS SELECT GEOID, ST_Buffer({TO_M.format(g='geometry')}, 10) AS g10 "
            f"FROM '{strata_path(region, 'census-tracts').as_posix()}'")
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rz AS SELECT g FROM (
            SELECT coalesce({ROUTE_LEVEL_SQL}, 9) AS lvl, {LOCAL_NAME_SQL} AS n_local,
                   coalesce(list_bool_or(list_transform(routes, r -> regexp_full_match(r.network, '{STATE_SPECIAL}')
                                                                 AND coalesce(r.ref, '') = '')), false) AS toll,
                   {TO_M.format(g='geometry')} AS g
            FROM '{ref_path(region, 'overture-roads').as_posix()}' WHERE routes IS NOT NULL)
        WHERE lvl = 1 AND n_local = 1 AND toll""")
    return con.sql("""SELECT t.GEOID, sum(ST_Length(ST_Intersection(t.g10, r.g))) / 1000 AS ztoll1_b10
                      FROM tz t JOIN rz r ON ST_Intersects(t.g10, r.g) GROUP BY 1""").df()


tolls = pd.concat([toll_interstate_local_km(r) for r in config.REGIONS], ignore_index=True)

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_uncounted.parquet"), on="GEOID", how="left")
df = df.merge(loops, on="GEOID", how="left").merge(tolls, on="GEOID", how="left")
df[["txothloc_b10", "ztoll1_b10"]] = df[["txothloc_b10", "ztoll1_b10"]].fillna(0.0)
df["majloc_b10"] = df["majloc_b10"] - df["zloc23_b10"].fillna(0.0)  # as s140: local names of counted majors only
lam = fit_lambdas(df)


def v7l_params(d, w_interstate, extra):
    """v7L parameters with the Texas FM and Oklahoma county weights re-solved to 1.59 / 0.71."""
    tx, ok = d[d["region"] == "south-central-tx"], d[d["region"] == "eastern-ok"]
    local = lambda x: W * (x["majloc_b10"] - x["majiloc_b10"]).sum() + w_interstate * x["majiloc_b10"].sum()
    w_fm = ((tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx) - extra[tx.index].sum())
            / (tx["txfm_b10"].sum() + W * tx["txloc_b10"].sum()))
    w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
    print(f"  Interstate local weight {w_interstate}: TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
    return Params(
        n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, level2=True,
        tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
        local_name_weight=W, interstate_local_weight=w_interstate,
        w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                         "eastern-wa": 0.0, "south-central-tx": 0.0},
        p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
                  "south-central-tx": 0.5})


zero = np.zeros(len(df))
v7l = simulate(df, v7l_params(df, 0.0, zero))
saved = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7L.parquet"), on="GEOID", how="left")
assert np.abs(v7l["c_transport"] - saved["c_transport"]).max() < 1e-12, "v7L no longer reproduces s140's model"

# Interstate local names of counted Interstates only (business loops and toll-system names out); loop
# local names enter the major term at W (bbx.structural reads them as extra major km).
left_out = df["zloc1_b10"].fillna(0.0) + df["ztoll1_b10"]
full_df = df.assign(majiloc_b10=df["majiloc_b10"] - left_out, majloc_b10=df["majloc_b10"] - left_out)
extra = W * df["txothloc_b10"].to_numpy()
full = simulate(full_df.assign(maj2x_b10=full_df["maj2x_b10"] + extra), v7l_params(full_df, W, extra))
for r in config.REGIONS:
    m = (df["region"] == r).to_numpy()
    print(f"  {r:17s} undefined {1 - full['p_transport_defined'][m].mean():.3f} (v7L {1 - v7l['p_transport_defined'][m].mean():.3f})")
path, exp = write_signal(df, np.asarray(full["c_transport"] - v7l["c_transport"], float), "s146_t7lf_c_transport_delta",
                         "v7L plus Interstate and Texas loop local names (weight 0.25), minus v7L", rho_guess=0.05)
print(f"{path.name}: expected public RMSE {exp:.6f}")
