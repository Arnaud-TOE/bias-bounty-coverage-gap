"""Majors that the v7 reference counts zero times, per tract (research of 30 October, round 67).

    python scripts/build_uncounted_majors.py     # writes data/features/features_uncounted.parquet

LEVEL2_SQL files every 'US:I:%' and 'US:US:%' network as a major, but N_MAJOR2_SQL counts only
'US:(I|US|<state>)' and the state loop/turnpike systems, so a segment whose only routes are
'US:US:Historic', 'US:US:Old', 'US:I:Business:Loop' or 'US:I:Express' has multiplicity 0: it is
outside the v7 reference length and outside its definedness. The local names of those segments still
enter majloc / majiloc (bbx.features_roadref), so s140 and s141 gave them a reference of their own:
v7L moved the share of tracts without a road component from 52.5 to 49.3 % in Arizona (published
55 %), 37.9 to 34.4 % in California (37 %) and 21.1 to 19.9 % in Oklahoma (21 %).

Columns (km, 10 m band as bbx.features_roadref), for LEVEL2 majors with N_MAJOR2 = 0:
    zbus_b10   Business / Alternate / Bypass / Truck / Spur / Connector / Loop variants
    zexp_b10   Express / Toll / HOV lanes
    zhist_b10  the rest (Historic, Old, Future, Temporary)
    zloc23_b10 local-name km of those segments at LEVEL1 2-3 (inside majloc - majiloc)
    zloc1_b10  local-name km of those segments at LEVEL1 1 (inside majiloc: Interstate business loops)
"""
import pandas as pd

from bbx import config
from bbx.features import ROUTE_LEVEL_SQL, SCORED
from bbx.features_roadref import LEVEL2_SQL, LOCAL_NAME_SQL, N_MAJOR2_SQL
from bbx.io import connect, ref_path, strata_path

TO_M = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"


def uncounted(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads").as_posix()
    con.sql(f"CREATE OR REPLACE TEMP TABLE tm AS SELECT GEOID, ST_Buffer({TO_M.format(g='geometry')}, 10) AS g10 FROM '{tracts}'")
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rm AS
        SELECT coalesce({ROUTE_LEVEL_SQL}, 9) AS lvl, {LOCAL_NAME_SQL} AS n_local, class IN {SCORED} AS scored,
               CASE WHEN regexp_matches(nets, 'Business|Alternate|Bypass|Truck|Spur|Connector|Loop') THEN 'bus'
                    WHEN regexp_matches(nets, 'Express|Toll|HOV') THEN 'exp' ELSE 'hist' END AS kind, g
        FROM (SELECT *, array_to_string(list_transform(routes, r -> r.network), ',') AS nets,
                     coalesce({LEVEL2_SQL}, 9) AS lvl2, coalesce({N_MAJOR2_SQL}, 0) AS n2,
                     {TO_M.format(g='geometry')} AS g
              FROM '{roads}' WHERE routes IS NOT NULL)
        WHERE lvl2 <= 3 AND n2 = 0
    """)
    df = con.sql("""
        WITH s AS (SELECT t.GEOID, r.kind, r.lvl, r.n_local, ST_Length(ST_Intersection(t.g10, r.g)) AS l
                   FROM tm t JOIN rm r ON ST_Intersects(t.g10, r.g))
        SELECT GEOID,
               sum(l) FILTER (kind = 'bus') / 1000 AS zbus_b10,
               sum(l) FILTER (kind = 'exp') / 1000 AS zexp_b10,
               sum(l) FILTER (kind = 'hist') / 1000 AS zhist_b10,
               sum(l * n_local) FILTER (lvl BETWEEN 2 AND 3) / 1000 AS zloc23_b10,
               sum(l * n_local) FILTER (lvl = 1) / 1000 AS zloc1_b10
        FROM s GROUP BY 1""").df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


if __name__ == "__main__":
    con = connect()
    out = pd.concat([uncounted(con, r) for r in config.REGIONS], ignore_index=True)
    out.to_parquet(config.FEATURES / "features_uncounted.parquet", index=False)
    print(out.drop(columns="GEOID").sum().round(1).to_dict())
