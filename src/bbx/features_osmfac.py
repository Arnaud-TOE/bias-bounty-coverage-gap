"""Facility evidence from Overture *buildings* (fifth pass), same conventions as bbx.features.

Overture places carry no OpenStreetMap record, but Overture buildings do, with OSM's name and
building class. OSM fire stations in the US were largely mapped from, or checked against, the
same federal facility inventories as the organiser reference (OSM wiki: HIFLD/Emergency). A
hand-mapped fire-station building in a tract therefore signals a reference fire station, and when
Overture has no fire_department place there the fire gap is 1. Schools and EMS likewise.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .io import connect, ref_path, strata_path

FIRE_RE = (r"(fire (station|dept|department|hall|house|district|rescue|company|protection)"
           r"|\bvfd\b|volunteer fire|fire ?& ?rescue|fire and rescue)")
EMS_RE = r"(\bems\b|ambulance|emergency medical|paramedic)"
SCHOOL_RE = r"(elementary|middle school|high school|junior high|intermediate school|\bacademy\b|\bschool\b)"


def osm_facilities(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    b = ref_path(region, "overture-buildings").as_posix()
    df = con.sql(f"""
        WITH b AS (
            SELECT ST_Centroid(geometry) AS c, class AS cls, lower(coalesce(names.primary, '')) AS nm
            FROM '{b}'
            WHERE class IN ('fire_station', 'school', 'ambulance_station') OR names.primary IS NOT NULL)
        SELECT t.GEOID,
            count(*) FILTER (cls = 'fire_station' OR regexp_matches(nm, '{FIRE_RE}')) AS osm_fire_bld,
            count(*) FILTER (cls = 'ambulance_station' OR regexp_matches(nm, '{EMS_RE}')) AS osm_ems_bld,
            count(*) FILTER (regexp_matches(nm, '{SCHOOL_RE}')) AS osm_school_named,
            count(*) FILTER (cls = 'school') AS osm_school_cls
        FROM '{tracts}' t JOIN b ON ST_Contains(t.geometry, b.c)
        GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


# Name-verified fire stations filed under another Overture category; the exclusion list drops the
# extinguisher and alarm vendors that make up much of fire_protection_service (Luca925, #34925).
FIRE_VERIFIED_RE = (r"\bfire\s+(station|dept|department|protection district|district|authority|rescue|company|co\b|house|hall)"
                    r"|\bvfd\b|\bfpd\b|\bcal ?fire\b|volunteer fire|fire\s*/\s*ems|fire & ems|fire and ems")
FIRE_VENDOR_RE = (r"auxil|thrift|supply|equipment|extinguish|sprinkler|safety|alarm|training|museum|store|shop|academy"
                  r"|insurance|grill|pizza|subs|kitchen|cafe|coffee|roofing|fitness|fireworks|church|gallery|old fire"
                  r"|education services|bar and")


def misfiled_fire(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    pois = ref_path(region, "overture-pois").as_posix()
    df = con.sql(f"""
        WITH p AS (SELECT categories.primary AS cat, lower(coalesce(names.primary, '')) AS nm, geometry FROM '{pois}')
        SELECT t.GEOID,
            count(*) FILTER (cat IS DISTINCT FROM 'fire_department' AND regexp_matches(nm, '{FIRE_VERIFIED_RE}')
                             AND NOT regexp_matches(nm, '{FIRE_VENDOR_RE}')) AS fire_misfiled_clean
        FROM '{tracts}' t JOIN p ON ST_Intersects(t.geometry, p.geometry)
        GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(osm_facilities(con, region).merge(misfiled_fire(con, region), on="GEOID", how="left"))
        print(f"[{region}] OSM facility buildings done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_osmfac.parquet", index=False)
    return out
