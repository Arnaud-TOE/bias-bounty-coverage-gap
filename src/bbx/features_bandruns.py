"""Boundary-following route km (fourth pass), same conventions as bbx.features_roadref.

The boundary double counting of the road reference (bbx.features_roadref) acts on highways that
follow a tract edge. A fixed 10 m band misses Overture copies lying 10-30 m from the edge and keeps
the few metres of every crossing. Following HHYurdagul's public note (Zindi #35478), route pieces in
an outer ring of 30 m are merged per tract into connected runs and only runs longer than 232 m are
kept: a road crossing the edge at more than about 15 degrees cannot stay that long in the ring.

Outputs per tract (km, EPSG:5070): long-run km in the ring for the v7 route groups (majors with
multiplicity, Texas FM/RM and other secondary systems, county routes), and ring km within 10, 20
and 30 m of the edge for the majors, without the run filter, for comparison.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .features_roadref import LEVEL2_SQL, N_MAJOR2_SQL
from .io import connect, ref_path, strata_path

RING_M = 30
MIN_RUN_M = 232


def band_runs(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads").as_posix()
    to_m = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE tm AS
        SELECT GEOID, ST_Difference(ST_Buffer(g, {RING_M}), g) AS ring,
               ST_Difference(ST_Buffer(g, 10), g) AS ring10, ST_Difference(ST_Buffer(g, 20), g) AS ring20
        FROM (SELECT GEOID, {to_m.format(g='geometry')} AS g FROM '{tracts}')
    """)
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rm AS
        SELECT coalesce({LEVEL2_SQL}, 9) AS lvl2, coalesce({N_MAJOR2_SQL}, 0) AS n_major2,
               coalesce(list_bool_or(list_transform(routes, r -> regexp_full_match(r.network, 'US:TX:(FM|RM)'))), false) AS fmrm,
               {to_m.format(g='geometry')} AS g
        FROM '{roads}' WHERE routes IS NOT NULL
    """)
    con.sql("DELETE FROM rm WHERE lvl2 > 5")
    con.sql("""
        CREATE OR REPLACE TEMP TABLE pc AS
        SELECT t.GEOID, r.lvl2, r.n_major2, r.fmrm, ST_Intersection(t.ring, r.g) AS pg,
               ST_Length(ST_Intersection(t.ring10, r.g)) AS l10, ST_Length(ST_Intersection(t.ring20, r.g)) AS l20
        FROM tm t JOIN rm r ON ST_Intersects(t.ring, r.g)
    """)
    con.sql("DELETE FROM pc WHERE ST_Length(pg) = 0")
    # Connected runs per tract; a piece counts for the part of it lying on a long run.
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE runs AS
        WITH m AS (SELECT GEOID, ST_LineMerge(ST_Union_Agg(pg)) AS mg FROM pc GROUP BY 1),
             d AS (SELECT GEOID, unnest(ST_Dump(mg)) AS c FROM m)
        SELECT GEOID, ST_Buffer(ST_Union_Agg(c.geom), 0.5) AS lb FROM d
        WHERE ST_Length(c.geom) > {MIN_RUN_M} GROUP BY 1
    """)
    df = con.sql("""
        WITH x AS (SELECT p.*, ST_Length(p.pg) AS l30,
                          coalesce(ST_Length(ST_Intersection(p.pg, r.lb)), 0) AS llong
                   FROM pc p LEFT JOIN runs r USING (GEOID))
        SELECT GEOID,
            sum(llong * n_major2) FILTER (lvl2 <= 3) / 1000 AS maj2x_run30,
            sum(llong) FILTER (lvl2 = 4 AND fmrm) / 1000 AS txfm_run30,
            sum(llong) FILTER (lvl2 = 4 AND NOT fmrm) / 1000 AS txoth_run30,
            sum(llong) FILTER (lvl2 = 4) / 1000 AS tx_run30,
            sum(llong) FILTER (lvl2 = 5) / 1000 AS cty2_run30,
            sum(l10 * n_major2) FILTER (lvl2 <= 3) / 1000 AS maj2x_ring10,
            sum(l20 * n_major2) FILTER (lvl2 <= 3) / 1000 AS maj2x_ring20,
            sum(l30 * n_major2) FILTER (lvl2 <= 3) / 1000 AS maj2x_ring30
        FROM x GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(band_runs(con, region))
        print(f"[{region}] boundary-run features done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_bandruns.parquet", index=False)
    return out


if __name__ == "__main__":
    build()
