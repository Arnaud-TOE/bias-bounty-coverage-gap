"""Per-tract features from the permitted challenge layers (DuckDB spatial).

One parquet per (region, layer) in data/features/<region>/, keyed on GEOID. Every scored
tract is present in every layer table (tracts with no feature get zeros), so downstream
joins never drop rows.

Geometry conventions (bucket README): layers are lon/lat (OGC:CRS84). Lengths use
ST_Length_Spheroid(ST_FlipCoordinates(.)) and areas a cos(latitude) scaling; both are
covered by tests/test_data_contract.py.
"""
from __future__ import annotations

import time

from . import config
from .io import connect, ref_path, strata_path

# Fire-station names filed under another category (organiser counts categories.primary only).
FIRE_NAME_RE = (
    r"(fire (dept|department|station|protection|district|rescue|company|co\b|hall)"
    r"|volunteer fire|\bv\.?f\.?d\.?\b|fire ?& ?rescue|fire and rescue|\bfpd\b|fire control)"
)
EMS_NAME_RE = r"(\bems\b|ambulance|emergency medical|paramedic)"
SCHOOL_NAME_RE = r"(\bschool\b|elementary|\bacademy\b|middle sch|high sch|\bisd\b)"

# Highest route level carried by a segment: 1 Interstate, 2 US highway, 3 state route,
# 4 Texas secondary state systems (FM/RM/Loop/Spur/Business/Beltway), 5 county or other
# sub-state network, 6 any other route designation.
ROUTE_LEVEL_SQL = """
list_min(list_transform(routes, r -> CASE
    WHEN r.network = 'US:I' OR r.network LIKE 'US:I:%' THEN 1
    WHEN r.network = 'US:US' OR r.network LIKE 'US:US:%' THEN 2
    WHEN regexp_full_match(r.network, 'US:[A-Z]{2}') THEN 3
    WHEN regexp_full_match(r.network, 'US:TX:(FM|RM|Loop|Spur|Business|Beltway|PR|PA|NASA|Toll)') THEN 4
    WHEN regexp_full_match(r.network, 'US:[A-Z]{2}:.+') THEN 5
    ELSE 6 END))
"""

SCORED = "('motorway','trunk','primary','secondary')"


def _sql_list(values) -> str:
    return "(" + ",".join(f"'{v}'" for v in values) + ")"


def _tracts(con, region: str) -> None:
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE tracts AS
        SELECT GEOID, ALAND, geometry FROM '{strata_path(region, "census-tracts").as_posix()}'
    """)


def _complete(con, table: str):
    """Left-join the per-tract aggregate onto all tracts, zero-filling counts."""
    cols = [c for c in con.sql(f"SELECT * FROM {table} LIMIT 0").columns if c != "GEOID"]
    sel = ", ".join(f"coalesce(a.{c}, 0) AS {c}" if not c.endswith("_mean") else f"a.{c}" for c in cols)
    return con.sql(f"SELECT t.GEOID, {sel} FROM tracts t LEFT JOIN {table} a USING (GEOID) ORDER BY t.GEOID").df()


def pois(con, region: str):
    path = ref_path(region, "overture-pois").as_posix()
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE p AS
        SELECT categories.primary AS cat,
               coalesce(categories.alternate, []) AS alt,
               lower(coalesce(names.primary, '')) AS nm,
               confidence, operating_status AS status,
               sources[1].dataset AS src, len(sources) AS n_src,
               geometry
        FROM '{path}'
    """)
    fire, ems, school = (_sql_list(x) for x in
                         (config.FIRE_CATEGORIES, config.EMS_CATEGORIES, config.SCHOOL_CATEGORIES))
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE agg AS
        SELECT t.GEOID,
            count(*) AS poi_n,
            count(*) FILTER (status = 'permanently_closed') AS poi_closed,
            count(*) FILTER (cat IN {fire}) AS poi_fire,
            count(*) FILTER (cat IN {ems}) AS poi_ems,
            count(*) FILTER (cat IN {school}) AS poi_school,
            count(*) FILTER (cat = 'elementary_school') AS poi_school_elem,
            count(*) FILTER (cat = 'high_school') AS poi_school_high,
            count(*) FILTER (cat IN {fire} AND status IS DISTINCT FROM 'permanently_closed') AS poi_fire_open,
            count(*) FILTER (cat IN {school} AND status IS DISTINCT FROM 'permanently_closed') AS poi_school_open,
            count(*) FILTER (cat = 'fire_protection_service') AS poi_fire_protsvc,
            count(*) FILTER (cat NOT IN {fire} AND regexp_matches(nm, '{FIRE_NAME_RE}')) AS poi_fire_misfiled,
            count(*) FILTER (cat NOT IN {fire} AND list_has_any(alt, ['fire_department'])) AS poi_fire_alt,
            count(*) FILTER (cat NOT IN {ems} AND regexp_matches(nm, '{EMS_NAME_RE}')) AS poi_ems_misfiled,
            count(*) FILTER (cat NOT IN {school} AND regexp_matches(nm, '{SCHOOL_NAME_RE}')) AS poi_school_misfiled,
            count(*) FILTER (cat = 'hospital') AS poi_hospital,
            count(*) FILTER (cat IN ('police_department','post_office','town_hall','library',
                                     'public_service_and_government','central_government_office')) AS poi_civic,
            count(*) FILTER (src = 'meta') AS poi_src_meta,
            count(*) FILTER (src = 'Microsoft') AS poi_src_msft,
            count(*) FILTER (src = 'Foursquare') AS poi_src_fsq,
            count(*) FILTER (src = 'BrightQuery') AS poi_src_bq,
            count(*) FILTER (src = 'AllThePlaces') AS poi_src_atp,
            count(*) FILTER (n_src > 1) AS poi_multisrc,
            avg(confidence) AS poi_conf_mean
        FROM tracts t JOIN p ON ST_Contains(t.geometry, p.geometry)
        GROUP BY 1
    """)
    return _complete(con, "agg")


def buildings(con, region: str):
    path = ref_path(region, "overture-buildings").as_posix()
    # Footprints are assigned to the tract containing their centroid.
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE agg AS
        WITH b AS (
            SELECT ST_Centroid(geometry) AS c,
                   ST_Area(geometry) * 12392.0e6 * cos(radians(ST_Y(ST_Centroid(geometry)))) AS area_m2,
                   sources[1].dataset AS src,
                   list_transform(sources, s -> s.dataset) AS srcs,
                   num_floors, height
            FROM '{path}'
        )
        SELECT t.GEOID,
            count(*) AS bld_n,
            count(*) FILTER (src = 'OpenStreetMap') AS bld_osm,
            count(*) FILTER (src = 'Microsoft ML Buildings') AS bld_msft,
            count(*) FILTER (src = 'Esri Community Maps') AS bld_esri,
            count(*) FILTER (src = 'USGS Lidar') AS bld_usgs,
            count(*) FILTER (src NOT IN ('OpenStreetMap','Microsoft ML Buildings','Esri Community Maps','USGS Lidar')) AS bld_other,
            count(*) FILTER (list_contains(srcs, 'Microsoft ML Buildings')) AS bld_any_msft,
            count(*) FILTER (len(srcs) > 1) AS bld_multisrc,
            count(*) FILTER (area_m2 < 50) AS bld_small,
            count(*) FILTER (height IS NOT NULL OR num_floors IS NOT NULL) AS bld_with_height,
            sum(area_m2) AS bld_area_m2
        FROM tracts t JOIN b ON ST_Contains(t.geometry, b.c)
        GROUP BY 1
    """)
    return _complete(con, "agg")


def roads(con, region: str):
    path = ref_path(region, "overture-roads").as_posix()
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE r AS
        SELECT class, subclass,
               names.primary IS NULL AS unnamed,
               {ROUTE_LEVEL_SQL} AS lvl,
               sources[1].update_time < '2012' AS import_era,
               geometry
        FROM '{path}'
    """)
    # Each segment is clipped to the tract; segments fully inside skip the intersection.
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE seg AS
        SELECT t.GEOID, r.class, r.subclass, r.unnamed, r.lvl, r.import_era,
               ST_Length_Spheroid(ST_FlipCoordinates(
                   CASE WHEN ST_Contains(t.geometry, r.geometry) THEN r.geometry
                        ELSE ST_Intersection(t.geometry, r.geometry) END)) / 1000 AS km
        FROM tracts t JOIN r ON ST_Intersects(t.geometry, r.geometry)
    """)
    classes = ["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "unclassified"]
    by_class = ",\n".join(f"sum(km) FILTER (class = '{c}') AS km_{c}" for c in classes)
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE agg AS
        SELECT GEOID,
            sum(km) AS km_road,
            count(*) AS road_seg_n,
            {by_class},
            sum(km) FILTER (class IN {SCORED}) AS km_scored,
            sum(km) FILTER (class IN {SCORED} AND subclass = 'link') AS km_scored_link,
            sum(km) FILTER (lvl = 1) AS km_rt_i,
            sum(km) FILTER (lvl = 2) AS km_rt_us,
            sum(km) FILTER (lvl = 3) AS km_rt_state,
            sum(km) FILTER (lvl = 4) AS km_rt_txsec,
            sum(km) FILTER (lvl = 5) AS km_rt_county,
            sum(km) FILTER (lvl = 6) AS km_rt_other,
            sum(km) FILTER (lvl <= 3) AS km_rt_major,
            sum(km) FILTER (lvl <= 3 AND class IN {SCORED}) AS km_rt_major_scored,
            sum(km) FILTER (lvl <= 3 AND class NOT IN {SCORED}) AS km_rt_major_unscored,
            sum(km) FILTER (lvl IN (4, 5) AND class IN {SCORED}) AS km_rt_minor_scored,
            sum(km) FILTER (lvl IN (4, 5) AND class NOT IN {SCORED}) AS km_rt_minor_unscored,
            sum(km) FILTER (lvl IS NULL AND class IN {SCORED}) AS km_nort_scored,
            sum(km) FILTER (unnamed) AS km_unnamed,
            sum(km) FILTER (import_era) AS km_import_era,
            sum(km) FILTER (unnamed AND import_era) AS km_unnamed_import
        FROM seg GROUP BY 1
    """)
    return _complete(con, "agg")


def roads_unfiltered(con, region: str):
    """Classes dropped from the scored layer (service, track, paths); midpoint assignment."""
    path = ref_path(region, "overture-roads-unfiltered").as_posix()
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE agg AS
        WITH u AS (
            SELECT class, ST_Length_Spheroid(ST_FlipCoordinates(geometry)) / 1000 AS km,
                   ST_LineInterpolatePoint(geometry, 0.5) AS mid
            FROM '{path}'
            WHERE class NOT IN ('motorway','trunk','primary','secondary','tertiary','residential','unclassified')
              AND ST_GeometryType(geometry) = 'LINESTRING'
        )
        SELECT t.GEOID,
            sum(km) FILTER (class = 'service') AS km_service,
            sum(km) FILTER (class = 'track') AS km_track,
            sum(km) FILTER (class IN ('footway','path','cycleway','pedestrian','steps','bridleway')) AS km_paths,
            sum(km) FILTER (class = 'living_street') AS km_living,
            sum(km) FILTER (class NOT IN ('service','track','footway','path','cycleway','pedestrian',
                                          'steps','bridleway','living_street')) AS km_other_minor
        FROM tracts t JOIN u ON ST_Contains(t.geometry, u.mid)
        GROUP BY 1
    """)
    return _complete(con, "agg")


def infrastructure_rail(con, region: str):
    infra = ref_path(region, "overture-infrastructure").as_posix()
    rail = ref_path(region, "overture-rail").as_posix()
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE agg AS
        WITH i AS (SELECT class, ST_PointOnSurface(geometry) AS g FROM '{infra}'),
             ia AS (
                SELECT t.GEOID,
                       count(*) AS infra_n,
                       count(*) FILTER (class ILIKE '%bus%') AS infra_bus,
                       count(*) FILTER (class ILIKE '%airport%' OR class ILIKE '%aerodrome%'
                                        OR class ILIKE '%helipad%' OR class ILIKE '%runway%') AS infra_air
                FROM tracts t JOIN i ON ST_Contains(t.geometry, i.g) GROUP BY 1),
             rl AS (SELECT ST_Length_Spheroid(ST_FlipCoordinates(geometry)) / 1000 AS km,
                           ST_LineInterpolatePoint(geometry, 0.5) AS mid
                    FROM '{rail}' WHERE ST_GeometryType(geometry) = 'LINESTRING'),
             ra AS (SELECT t.GEOID, sum(km) AS km_rail
                    FROM tracts t JOIN rl ON ST_Contains(t.geometry, rl.mid) GROUP BY 1)
        SELECT t.GEOID, ia.infra_n, ia.infra_bus, ia.infra_air, ra.km_rail
        FROM tracts t LEFT JOIN ia USING (GEOID) LEFT JOIN ra USING (GEOID)
    """)
    return _complete(con, "agg")


def acs(con, region: str):
    path = ref_path(region, "census-acs-housing").as_posix()
    return con.sql(f"""
        SELECT t.GEOID, a.housing_units
        FROM tracts t LEFT JOIN '{path}' a USING (GEOID) ORDER BY t.GEOID
    """).df()


LAYERS = {
    "pois": pois,
    "buildings": buildings,
    "roads": roads,
    "roads_unfiltered": roads_unfiltered,
    "infra_rail": infrastructure_rail,
    "acs": acs,
}


def build(region: str, layers=None, threads: int | None = None, memory_limit: str = "9GB") -> dict:
    out_dir = config.FEATURES / region
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = config.INTERIM / "duckdb_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    con = connect(threads)
    con.sql(f"SET memory_limit='{memory_limit}'; SET temp_directory='{tmp.as_posix()}';")
    con.sql("SET preserve_insertion_order=false;")
    _tracts(con, region)
    timings = {}
    for name in layers or LAYERS:
        t0 = time.time()
        df = LAYERS[name](con, region)
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
        timings[name] = round(time.time() - t0, 1)
        print(f"[{region}] {name}: {len(df)} tracts, {timings[name]} s", flush=True)
    con.close()
    return timings
