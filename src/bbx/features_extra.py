"""Extra per-tract features (second pass), same conventions as bbx.features.

- Facilities just across the tract boundary: a reference facility located inside a tract can be
  mapped by Overture a few hundred metres away in the neighbouring tract (different geocode),
  which leaves O = 0 inside while the reference has one.
- Building footprint size by source: merged or coarse polygons hold several structures each.
- Postcode coverage of places.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .io import connect, ref_path, strata_path

DEG_300M = 0.0030   # ~300 m in latitude; longitudes are slightly shorter at 30-48 N
DEG_1KM = 0.0100


def boundary_facilities(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    pois = ref_path(region, "overture-pois").as_posix()
    fire, ems, school = ("('fire_department')", "('ambulance_and_ems_services')",
                         "('elementary_school','middle_school','high_school','school','private_school','public_school')")
    return con.sql(f"""
        WITH t AS (SELECT GEOID, geometry FROM '{tracts}'),
             f AS (SELECT categories.primary AS cat, geometry FROM '{pois}'
                   WHERE categories.primary IN {fire} OR categories.primary IN {ems} OR categories.primary IN {school})
        SELECT t.GEOID,
            count(*) FILTER (f.cat IN {fire} AND ST_DWithin(t.geometry, f.geometry, {DEG_300M})) AS fire_out_300m,
            count(*) FILTER (f.cat IN {fire}) AS fire_out_1km,
            count(*) FILTER (f.cat IN {school} AND ST_DWithin(t.geometry, f.geometry, {DEG_300M})) AS school_out_300m,
            count(*) FILTER (f.cat IN {ems} AND ST_DWithin(t.geometry, f.geometry, {DEG_300M})) AS ems_out_300m
        FROM t JOIN f ON ST_DWithin(t.geometry, f.geometry, {DEG_1KM}) AND NOT ST_Contains(t.geometry, f.geometry)
        GROUP BY 1
    """).df()


def building_size_by_source(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    b = ref_path(region, "overture-buildings").as_posix()
    return con.sql(f"""
        WITH b AS (
            SELECT ST_Centroid(geometry) AS c, sources[1].dataset AS src,
                   ST_Area(geometry) * 12392.0e6 * cos(radians(ST_Y(ST_Centroid(geometry)))) AS a
            FROM '{b}')
        SELECT t.GEOID,
            avg(a) FILTER (src = 'OpenStreetMap') AS osm_area_mean,
            avg(a) FILTER (src = 'Microsoft ML Buildings') AS msft_area_mean,
            avg(a) FILTER (src = 'Esri Community Maps') AS esri_area_mean,
            count(*) FILTER (src = 'OpenStreetMap' AND a > 500) AS osm_large_n
        FROM '{tracts}' t JOIN b ON ST_Contains(t.geometry, b.c)
        GROUP BY 1
    """).df()


def postcode_coverage(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    pois = ref_path(region, "overture-pois").as_posix()
    return con.sql(f"""
        SELECT t.GEOID,
            count(*) AS poi_n_chk,
            count(*) FILTER (len(p.addresses) > 0 AND p.addresses[1].postcode IS NOT NULL) AS poi_with_postcode,
            count(DISTINCT substr(p.addresses[1].postcode, 1, 5)) AS n_postcodes
        FROM '{tracts}' t JOIN '{pois}' p ON ST_Contains(t.geometry, p.geometry)
        GROUP BY 1
    """).df()


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        parts = [boundary_facilities(con, region), building_size_by_source(con, region), postcode_coverage(con, region)]
        df = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
        for p in parts:
            df = df.merge(p, on="GEOID", how="left")
        frames.append(df)
        print(f"[{region}] extra features done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(config.FEATURES / "features_extra.parquet", index=False)
    return out
