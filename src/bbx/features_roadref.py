"""Road-reference artefacts (third pass), same conventions as bbx.features.

The organiser road reference clips TIGER S1100/S1200 lines to tract polygons in EPSG:5070
(overlay intersection) and keeps every TIGER record. Two consequences follow from the
geometry alone, without any reference data:

- Boundary double counting. Census tract boundaries run along TIGER road edges, so a highway
  that forms a tract boundary lies on both polygons and is credited in full to both tracts,
  whereas Overture's copy, a few metres to one side, lands in one. We measure route km within
  a band of w metres outside each tract (the length the reference credits to the tract but
  Overture cannot).
- Duplicate records. TIGER stores a road with several route numbers once per number and the
  reference keeps every copy, so concurrent routes count several times. We weight route km by
  the number of distinct route designations carried by the Overture segment.

Lengths are planar metres in EPSG:5070 (the organiser projection); outputs are km.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .features import ROUTE_LEVEL_SQL, SCORED
from .io import connect, ref_path, strata_path

BANDS_M = (10, 25)
# Distinct signed designations (Interstate, US, state) carried by a segment; Texas secondary
# state systems (FM/RM/Loop/Spur...) counted separately.
N_MAJOR_SQL = """len(list_distinct(list_transform(
    list_filter(routes, r -> regexp_full_match(r.network, 'US:(I|US|[A-Z]{2})')),
    r -> r.network || ' ' || coalesce(r.ref, ''))))"""
# A primary name that is not itself a route designation is a local name, which TIGER stores as
# one more record of the same geometry (iam-dante's public write-up fits this at 0.97).
ROUTE_LIKE_RE = (r"^(north |south |east |west )?(state (route|highway|hwy|rte|road)|s\.?r\.?[ -]?[0-9]|sh[ -]?[0-9]"
                 r"|us (route|highway|hwy|rte)|u\.?s\.?[ -]?[0-9]|interstate|i[- ]?[0-9]|highway [0-9]|hwy [0-9]"
                 r"|route [0-9]|farm to market|fm[ -]?[0-9]|ranch to market|rm[ -]?[0-9]|loop [0-9]|spur [0-9]"
                 r"|county (road|route|highway)|cr[ -]?[0-9]|[a-z]+ state (route|highway) [0-9])")
LOCAL_NAME_SQL = f"""CASE WHEN names.primary IS NULL THEN 0
    WHEN regexp_matches(lower(names.primary), '{ROUTE_LIKE_RE}') THEN 0 ELSE 1 END"""
# Second route classification (v7): state-level loop, turnpike and toll systems outside Texas
# (Phoenix Loop 101/202/303 as US:AZ:Loop, Oklahoma turnpikes as US:OK:Turnpike) are signed
# state highways, not county routes. Texas keeps its own secondary-system level (4).
STATE_SPECIAL = r"US:[A-Z]{2}:(Loop|Turnpike|Toll|Spur|Business|Beltway|Bypass|Alternate|Connector)"
LEVEL2_SQL = f"""list_min(list_transform(routes, r -> CASE
    WHEN r.network = 'US:I' OR r.network LIKE 'US:I:%' THEN 1
    WHEN r.network = 'US:US' OR r.network LIKE 'US:US:%' THEN 2
    WHEN regexp_full_match(r.network, 'US:[A-Z]{{2}}') THEN 3
    WHEN regexp_full_match(r.network, 'US:TX:(FM|RM|Loop|Spur|Business|Beltway|PR|PA|NASA|Toll)') THEN 4
    WHEN regexp_full_match(r.network, '{STATE_SPECIAL}') THEN 3
    WHEN regexp_full_match(r.network, 'US:[A-Z]{{2}}:.+') THEN 5
    ELSE 6 END))"""
N_MAJOR2_SQL = f"""len(list_distinct(list_transform(
    list_filter(routes, r -> regexp_full_match(r.network, 'US:(I|US|[A-Z]{{2}})')
                          OR (regexp_full_match(r.network, '{STATE_SPECIAL}') AND NOT starts_with(r.network, 'US:TX:'))),
    r -> r.network || ' ' || coalesce(r.ref, ''))))"""
N_ANY_SQL = """len(list_distinct(list_transform(
    list_filter(routes, r -> NOT regexp_matches(r.network, 'Historic')),
    r -> r.network || ' ' || coalesce(r.ref, ''))))"""


def road_reference(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads").as_posix()
    to_m = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE tm AS
        SELECT GEOID, {to_m.format(g='geometry')} AS g FROM '{tracts}'
    """)
    for w in BANDS_M:
        con.sql(f"ALTER TABLE tm ADD COLUMN g{w} GEOMETRY")
        con.sql(f"UPDATE tm SET g{w} = ST_Buffer(g, {w})")
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rm AS
        SELECT class IN {SCORED} AS scored, class = 'tertiary' AS tertiary,
               class IN ('motorway', 'trunk', 'primary') AS upper,
               CASE WHEN road_surface IS NULL OR len(road_surface) = 0 THEN 'null'
                    WHEN road_surface[1].value IN ('paved') THEN 'paved'
                    WHEN road_surface[1].value IN ('unpaved', 'gravel', 'dirt', 'compacted', 'ground') THEN 'unpaved'
                    ELSE 'null' END AS surf,
               coalesce({ROUTE_LEVEL_SQL}, 9) AS lvl,
               coalesce({N_MAJOR_SQL}, 0) AS n_major,
               coalesce({N_ANY_SQL}, 0) AS n_any,
               {LOCAL_NAME_SQL} AS n_local,
               coalesce({LEVEL2_SQL}, 9) AS lvl2,
               coalesce({N_MAJOR2_SQL}, 0) AS n_major2,
               coalesce(list_bool_or(list_transform(routes, r -> regexp_full_match(r.network, 'US:TX:(FM|RM)'))), false) AS fmrm,
               {to_m.format(g='geometry')} AS g
        FROM '{roads}'
        WHERE class IN {SCORED} OR class = 'tertiary' OR routes IS NOT NULL
    """)
    w_max = max(BANDS_M)
    lens = ",\n".join(
        [f"ST_Length(ST_Intersection(t.g, r.g)) AS l_in"]
        + [f"ST_Length(ST_Intersection(t.g{w}, r.g)) AS l_b{w}" for w in BANDS_M])
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE seg AS
        SELECT t.GEOID, r.scored, r.tertiary, r.upper, r.surf, r.lvl, r.lvl2, r.n_major, r.n_major2, r.n_any, r.n_local, r.fmrm, {lens}
        FROM tm t JOIN rm r ON ST_Intersects(t.g{w_max}, r.g)
    """)
    groups = {
        "sc": "scored",
        "maj": "lvl <= 3",
        "tx": "lvl = 4",
        "cty": "lvl = 5",
        "rt": "lvl <= 5",
        # Class-dependent splits, to test which routes TIGER files as S1100/S1200.
        "majsc": "lvl <= 3 AND scored",
        "majun": "lvl <= 3 AND NOT scored",
        "txsc": "lvl = 4 AND scored",
        "txun": "lvl = 4 AND NOT scored",
        "ctysc": "lvl = 5 AND scored",
        "ctyun": "lvl = 5 AND NOT scored",
        "othsc": "lvl >= 6 AND scored",
        "tertnr": "lvl = 9 AND tertiary",
        # TIGER files unpaved roads as S1400: county routes split by Overture surface.
        "ctypav": "lvl = 5 AND surf = 'paved'",
        "ctyunp": "lvl = 5 AND surf = 'unpaved'",
        "ctynul": "lvl = 5 AND surf = 'null'",
        "txunp": "lvl = 4 AND surf = 'unpaved'",
        # Unrouted arterials: S1200 "main arteries" need not carry a route number.
        "nrup": "lvl = 9 AND upper",
        "nrsec": "lvl = 9 AND scored AND NOT upper",
        # Texas secondary systems split: Farm/Ranch-to-Market against Loop/Spur/Business/Beltway/Toll/Park.
        "txfm": "lvl = 4 AND fmrm",
        "txoth": "lvl = 4 AND NOT fmrm",
        "txfmsc": "lvl = 4 AND fmrm AND scored",
        # v7 classification (LEVEL2_SQL): majors including state loop / turnpike / toll systems.
        "maj2": "lvl2 <= 3",
        "cty2": "lvl2 = 5",
        "cty2pav": "lvl2 = 5 AND surf = 'paved'",
        "cty2nul": "lvl2 = 5 AND surf = 'null'",
    }
    aggs = []
    for name, cond in groups.items():
        for col in ["l_in"] + [f"l_b{w}" for w in BANDS_M]:
            aggs.append(f"sum({col}) FILTER ({cond}) / 1000 AS {name}_{col[2:]}")
            if name in ("maj", "rt", "maj2"):
                mult = {"maj": "n_major", "rt": "n_any", "maj2": "n_major2"}[name]
                aggs.append(f"sum({col} * {mult}) FILTER ({cond}) / 1000 AS {name}x_{col[2:]}")
            if name in ("maj", "tx"):
                aggs.append(f"sum({col} * n_local) FILTER ({cond}) / 1000 AS {name}loc_{col[2:]}")
                aggs.append(f"sum({col} * n_local) FILTER ({cond} AND lvl = 1) / 1000 AS {name}iloc_{col[2:]}")
    df = con.sql(f"SELECT GEOID, {', '.join(aggs)} FROM seg GROUP BY 1").df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(road_reference(con, region))
        print(f"[{region}] road-reference features done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_roadref.parquet", index=False)
    return out
