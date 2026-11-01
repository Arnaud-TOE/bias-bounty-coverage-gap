"""Service-road footprint of business activity (sixth pass), same conventions as bbx.features.

Parking aisles (and untyped service roads) are drawn around shopping centres, office parks and
industrial sites: they track the business addresses that drive the organiser's ZIP-to-tract
allocation of CBP establishments, while Overture's places cover consumer-facing businesses far
better than business-to-business ones. Driveways and alleys are kept apart (mostly residential).
Segments are clipped to tracts (planar EPSG:5070 metres, output in km).
"""
from __future__ import annotations

import pandas as pd

from . import config
from .io import connect, ref_path, strata_path


def service_roads(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads-unfiltered").as_posix()
    to_m = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
    df = con.sql(f"""
        WITH t AS (SELECT GEOID, geometry, {to_m.format(g='geometry')} AS gm FROM '{tracts}'),
             r AS (SELECT coalesce(subclass, 'none') AS sub, geometry, {to_m.format(g='geometry')} AS gm
                   FROM '{roads}' WHERE class = 'service')
        SELECT t.GEOID,
            sum(ST_Length(ST_Intersection(t.gm, r.gm))) FILTER (sub = 'parking_aisle') / 1000 AS km_parking_aisle,
            sum(ST_Length(ST_Intersection(t.gm, r.gm))) FILTER (sub = 'none') / 1000 AS km_service_plain,
            sum(ST_Length(ST_Intersection(t.gm, r.gm))) FILTER (sub = 'driveway') / 1000 AS km_driveway,
            sum(ST_Length(ST_Intersection(t.gm, r.gm))) FILTER (sub = 'alley') / 1000 AS km_alley
        FROM t JOIN r ON ST_Intersects(t.geometry, r.geometry)
        GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(service_roads(con, region))
        print(f"[{region}] service roads done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_service.parquet", index=False)
    return out
