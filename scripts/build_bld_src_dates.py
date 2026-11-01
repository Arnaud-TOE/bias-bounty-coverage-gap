"""Per-tract Overture buildings by source, Microsoft ML imagery-year bucket and confidence (bbox centre).

Writes data/interim/bld_src_dates.parquet (used by scripts/make_s123.py). Microsoft ML
sources[1].update_time is the imagery capture date (2000 = undated).
"""
import duckdb, pandas as pd, time
from bbx import config
from bbx.io import ref_path
con = duckdb.connect(); con.sql("INSTALL spatial; LOAD spatial;")
out = []
for r in config.REGIONS:
    t0 = time.time()
    tp = ref_path(r, "census-acs-housing").as_posix()
    bp = ref_path(r, "overture-buildings").as_posix()
    con.sql(f"CREATE OR REPLACE TEMP TABLE tr AS SELECT GEOID, geometry g FROM '{tp}'")
    df = con.sql(f"""
      WITH b AS (
        SELECT ST_Point((bbox.xmin+bbox.xmax)/2, (bbox.ymin+bbox.ymax)/2) p,
               sources[1].dataset src,
               year(TRY_CAST(sources[1].update_time AS TIMESTAMP)) yr,
               sources[1].confidence conf,
               (bbox.xmax-bbox.xmin)*(bbox.ymax-bbox.ymin) bba
        FROM '{bp}')
      SELECT t.GEOID,
        count(*) n,
        count(*) FILTER (src='Microsoft ML Buildings') ml,
        count(*) FILTER (src='Microsoft ML Buildings' AND yr=2000) ml_y2000,
        count(*) FILTER (src='Microsoft ML Buildings' AND yr BETWEEN 2001 AND 2019) ml_le2019,
        count(*) FILTER (src='Microsoft ML Buildings' AND yr IN (2020,2021)) ml_2021,
        count(*) FILTER (src='Microsoft ML Buildings' AND yr >= 2022) ml_ge2022,
        count(*) FILTER (src='Microsoft ML Buildings' AND conf IS NOT NULL) ml_conf,
        count(*) FILTER (src='Google Open Buildings') goog,
        count(*) FILTER (src='Esri Community Maps') esri,
        count(*) FILTER (src='OpenStreetMap') osm,
        count(*) FILTER (src='OpenStreetMap' AND yr >= 2020) osm_ge2020
      FROM tr t JOIN b ON ST_Intersects(t.g, b.p) GROUP BY 1""").df()
    df["region"] = r
    out.append(df); print(r, len(df), round(time.time()-t0), "s", flush=True)
pd.concat(out).to_parquet(config.INTERIM / "bld_src_dates.parquet", index=False)
