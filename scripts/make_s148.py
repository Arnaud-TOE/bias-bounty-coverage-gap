"""Which local names TIGER stores: street names only (research of 30 October, round 82).

s140 (local names of counted non-Interstate majors at 0.25, every kind of name) scored on 30 October
(removal cost 0.00111). Overture's primary names of those majors mix three kinds: street names that
carry addresses (Main Street, Katy Freeway, Grand Avenue), named intercity highways ('Globe-Lordsburg
Highway', 5,043 km in Arizona) and honorary designations ('Veterans Memorial Highway', a third of
Oklahoma's). TIGER takes its feature names from local address files, so the street names are the
ones it surely stores; the joint grid of round 78 also favours more local-name weight (0.35).

v7S: local names of counted non-Interstate majors at 0.35, street names only (same definition as
scripts/make_s142.py: ends with a street type, not a route designation, not honorary), Texas FM/RM
and Oklahoma county weights re-solved to the published 1.59 and 0.71.

s148_t7s_c_transport_delta: v7S minus v7L (s140's model; same seed). On the 71-signal basis about
27 % new, in-span orientation +0.30; its new part is independent of s146, s142 and s147 (|r| <= 0.04).
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.features import ROUTE_LEVEL_SQL
from bbx.features_roadref import LEVEL2_SQL, N_MAJOR2_SQL
from bbx.io import connect, ref_path, strata_path
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

W_STREET, W_V7L = 0.35, 0.25
TO_M = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
# the street-name test of s142, without running s142
_spec = importlib.util.spec_from_file_location("s142", Path(__file__).with_name("make_s142.py"))
_src = Path(_spec.origin).read_text(encoding="utf-8")
IS_STREET = None
exec(_src[_src.index("ROUTE = ("):_src.index("def street_km")], globals())


def street_local_km(con, region: str) -> pd.DataFrame:
    """10 m band km of street-named counted non-Interstate majors (lo_street) and Texas level-4 routes (lt_street)."""
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads").as_posix()
    con.sql(f"CREATE OR REPLACE TEMP TABLE tm AS SELECT GEOID, ST_Buffer({TO_M.format(g='geometry')}, 10) AS g10 FROM '{tracts}'")
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rm AS SELECT * FROM (
            SELECT coalesce({ROUTE_LEVEL_SQL}, 9) AS lvl, coalesce({LEVEL2_SQL}, 9) AS lvl2, coalesce({N_MAJOR2_SQL}, 0) AS n2,
                   {IS_STREET} AS street, {TO_M.format(g='geometry')} AS g
            FROM '{roads}' WHERE routes IS NOT NULL)
        WHERE street AND ((lvl2 <= 3 AND n2 > 0 AND lvl <> 1) OR lvl = 4)""")
    d = con.sql("""SELECT t.GEOID,
                          sum(ST_Length(ST_Intersection(t.g10, r.g))) FILTER (r.lvl <> 4) / 1000 AS lo_street,
                          sum(ST_Length(ST_Intersection(t.g10, r.g))) FILTER (r.lvl = 4) / 1000 AS lt_street
                   FROM tm t JOIN rm r ON ST_Intersects(t.g10, r.g) GROUP BY 1""").df()
    return pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"]).merge(d, on="GEOID", how="left").fillna(0.0)


con = connect()
streets = pd.concat([street_local_km(con, r) for r in config.REGIONS], ignore_index=True)
df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_uncounted.parquet"), on="GEOID", how="left")
df = df.merge(streets, on="GEOID", how="left")
df[["lo_street", "lt_street"]] = df[["lo_street", "lt_street"]].fillna(0.0)
lam = fit_lambdas(df)


def model(d: pd.DataFrame, W: float) -> pd.DataFrame:
    tx, ok = d[d["region"] == "south-central-tx"], d[d["region"] == "eastern-ok"]
    local = lambda x: W * (x["majloc_b10"] - x["majiloc_b10"]).sum()
    w_fm = ((tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx))
            / (tx["txfm_b10"].sum() + W * tx["txloc_b10"].sum()))
    w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
    print(f"local names {W}: TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
    return simulate(d, Params(
        n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, level2=True,
        tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19}, local_name_weight=W,
        w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                         "eastern-wa": 0.0, "south-central-tx": 0.0},
        p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
                  "south-central-tx": 0.5}))


v7l = model(df.assign(majloc_b10=df["majloc_b10"] - df["zloc23_b10"].fillna(0.0)), W_V7L)  # s140's model
saved = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7L.parquet"), on="GEOID", how="left")
assert np.abs(v7l["c_transport"] - saved["c_transport"]).max() < 1e-12, "v7L no longer reproduces s140's model"
# bbx.structural reads local names as majloc - majiloc (non-Interstate) and txloc (Texas level 4)
v7s = model(df.assign(majloc_b10=df["majiloc_b10"] + df["lo_street"], txloc_b10=df["lt_street"]), W_STREET)
for r in config.REGIONS:
    m = (df["region"] == r).to_numpy()
    print(f"  {r:17s} undefined {1 - v7s['p_transport_defined'][m].mean():.3f} (v7L {1 - v7l['p_transport_defined'][m].mean():.3f})")
path, exp = write_signal(df, np.asarray(v7s["c_transport"] - v7l["c_transport"], float), "s148_t7s_c_transport_delta",
                         "v7 with street-type local names only at 0.35 (FM and OK county re-solved), minus v7L", rho_guess=0.08)
print(f"{path.name}: expected public RMSE {exp:.6f}")
