"""Business-address proxies (fourth pass), same conventions as bbx.features.

The organiser CBP half allocates ZIP-level establishments to tracts by the tract's share of the
ZIP's USPS business addresses (HUD crosswalk BUS_RATIO), which we may not use. Business delivery
points sit in non-residential buildings, so the footprint area of large buildings and the number
of distinct place addresses (multi-tenant buildings) stand in for the tract's business addresses.
Each tract also gets its dominant postcode (by places), so allocations can be made within ZIPs.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .io import connect, ref_path, strata_path

LARGE_M2 = (300, 1000, 3000)


def business_proxies(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    b = ref_path(region, "overture-buildings").as_posix()
    p = ref_path(region, "overture-pois").as_posix()
    big = ",\n".join(f"count(*) FILTER (a >= {s}) AS bld_ge{s}, sum(a) FILTER (a >= {s}) AS area_ge{s}"
                     for s in LARGE_M2)
    bld = con.sql(f"""
        WITH b AS (
            SELECT ST_Centroid(geometry) AS c,
                   ST_Area(geometry) * 12392.0e6 * cos(radians(ST_Y(ST_Centroid(geometry)))) AS a
            FROM '{b}')
        SELECT t.GEOID, {big}
        FROM '{tracts}' t JOIN b ON ST_Contains(t.geometry, b.c)
        GROUP BY 1
    """).df()
    poi = con.sql(f"""
        WITH q AS (
            SELECT t.GEOID, lower(trim(p.addresses[1].freeform)) AS addr,
                   substr(p.addresses[1].postcode, 1, 5) AS z
            FROM '{tracts}' t JOIN '{p}' p ON ST_Intersects(t.geometry, p.geometry))
        SELECT GEOID,
            count(DISTINCT addr) AS poi_addr_distinct,
            count(*) FILTER (addr IS NOT NULL) AS poi_with_addr,
            mode(z) FILTER (regexp_full_match(z, '\\d{{5}}')) AS zip_main
        FROM q GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    out = base.merge(bld, on="GEOID", how="left").merge(poi, on="GEOID", how="left")
    num = [c for c in out.columns if c not in ("GEOID", "zip_main")]
    out[num] = out[num].fillna(0.0)
    return out


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(business_proxies(con, region))
        print(f"[{region}] business-address proxies done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_bizaddr.parquet", index=False)
    return out
