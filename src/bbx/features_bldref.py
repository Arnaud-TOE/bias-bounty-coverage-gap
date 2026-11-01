"""Building-reference artefacts (third pass), same conventions as bbx.features.

Overture adds a Microsoft ML footprint only where no OpenStreetMap / Esri footprint overlaps
it; an OSM or Esri building that absorbed an ML footprint lists 'Microsoft ML Buildings' as a
secondary source. The organiser building reference counts Microsoft footprints by centroid, so
a hand-drawn polygon that covers k > 1 Microsoft footprints (a merged block, a large complex)
leaves k - 1 reference buildings that Overture never shows, while a hand-drawn building with no
Microsoft counterpart adds one Overture building the reference does not have.

Per tract: hand-drawn buildings with and without a Microsoft counterpart, and the area excess of
the matched ones over typical Microsoft footprint sizes (a proxy for the hidden k - 1).
"""
from __future__ import annotations

import pandas as pd

from . import config
from .io import connect, ref_path, strata_path

AREA_STEPS_M2 = (150, 300, 600)


def building_reference(con, region: str) -> pd.DataFrame:
    tracts = strata_path(region, "census-tracts").as_posix()
    b = ref_path(region, "overture-buildings").as_posix()
    excess = ",\n".join(
        f"sum(greatest(a / {s} - 1, 0)) FILTER (hand AND has_ms) AS exc{s}" for s in AREA_STEPS_M2)
    df = con.sql(f"""
        WITH b AS (
            SELECT ST_Centroid(geometry) AS c,
                   sources[1].dataset IN ('OpenStreetMap', 'Esri Community Maps', 'USGS Lidar') AS hand,
                   list_contains(list_transform(sources[2:], s -> s.dataset), 'Microsoft ML Buildings') AS has_ms,
                   ST_Area(geometry) * 12392.0e6 * cos(radians(ST_Y(ST_Centroid(geometry)))) AS a
            FROM '{b}')
        SELECT t.GEOID,
            count(*) FILTER (hand AND has_ms) AS hand_ms,
            count(*) FILTER (hand AND NOT has_ms) AS hand_only,
            sum(a) FILTER (hand AND has_ms) AS hand_ms_area,
            {excess}
        FROM '{tracts}' t JOIN b ON ST_Contains(t.geometry, b.c)
        GROUP BY 1
    """).df()
    base = pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"])
    return base.merge(df, on="GEOID", how="left").fillna(0.0)


def build(regions=None) -> pd.DataFrame:
    con = connect()
    con.sql("SET enable_progress_bar=false; SET preserve_insertion_order=false;")
    frames = []
    for region in regions or config.REGIONS:
        frames.append(building_reference(con, region))
        print(f"[{region}] building-reference features done", flush=True)
    out = pd.concat(frames, ignore_index=True)
    if regions is None:
        out.to_parquet(config.FEATURES / "features_bldref.parquet", index=False)
    return out
