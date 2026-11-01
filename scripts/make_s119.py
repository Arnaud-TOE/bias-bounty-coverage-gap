"""Public EMS stations as fire-reference evidence (research of 27 October, round 19).

The official text names the facility reference as "USGS National Map facility counts". USGS
structures file fire and EMS stations in one type, "Fire Station/EMS Station", and private
ambulance companies in another, "Ambulance Service". That reading fits the README: EMS (matched to
Overture ambulance_and_ems_services, mostly private companies) is "close to 1:1 and rarely binds",
while "fire stations carry the component". A public EMS station (county or city EMS, rescue
squad) then counts as a reference fire station, so a tract holding one but no Overture
fire_department place has a fire gap of 1, which the model does not foresee.

s119_ems_station_nofire: tract with an Overture place that names a public EMS station (category
ambulance_and_ems_services or an EMS-station name elsewhere; companies excluded) and no
fire_department place, weighted 1 / (4 n_defined) (facility half shared with schools, POI half,
composite mean). 103 tracts, 78 without other fire evidence; new to the 51-signal basis (R2 0.15).
"""
import duckdb
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.io import ref_path, strata_path
from bbx.signals import write_signal

STATION = r"(\bems\b|\bmedic\s*\d|\bmedic station|ambulance station|rescue squad|\bsquad\b|emergency medical services station|\bems station|\bstation\s*\d)"
OTHER = r"(\bems station|ems\s+(station|post|base)\s*\d*|medic station|ambulance station|rescue squad)"
PRIVATE = (r"(\binc\b|\bllc\b|transport|transportation|billing|medical transport|non-?emergency|wheelchair|amr\b|acadian"
           r"|careflite|air ambulance|air evac|training|academy|school|supply)")

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
frames = []
for r in config.REGIONS:
    pois, tracts = ref_path(r, "overture-pois").as_posix(), strata_path(r, "census-tracts").as_posix()
    frames.append(con.sql(f"""
        SELECT t.GEOID,
            count(*) FILTER (p.categories.primary = 'ambulance_and_ems_services'
                             AND regexp_matches(lower(p.names.primary), '{STATION}')
                             AND NOT regexp_matches(lower(p.names.primary), '{PRIVATE}')) AS ems_station_cat,
            count(*) FILTER (p.categories.primary NOT IN ('ambulance_and_ems_services', 'fire_department')
                             AND regexp_matches(lower(p.names.primary), '{OTHER}')
                             AND NOT regexp_matches(lower(p.names.primary), '{PRIVATE}')) AS ems_station_other,
            count(*) FILTER (p.categories.primary = 'fire_department') AS fire
        FROM '{tracts}' t JOIN '{pois}' p ON ST_Intersects(t.geometry, p.geometry)
        WHERE p.categories.primary IN ('ambulance_and_ems_services', 'fire_department')
           OR regexp_matches(lower(p.names.primary), '(ems|medic|ambulance|rescue squad)')
        GROUP BY 1""").df())
df = load_table()
d = df[["GEOID"]].merge(pd.concat(frames), on="GEOID", how="left").fillna(0)
evidence = ((d["ems_station_cat"] + d["ems_station_other"]) > 0) & (d["fire"] == 0)
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8.parquet"), on="GEOID", how="left")
sig = evidence.to_numpy(float) / (4 * v8["n_defined"].clip(lower=1).to_numpy())
print(f"tracts with public-EMS evidence and no fire_department place: {int(evidence.sum())}")
path, exp = write_signal(df, sig, "s119_ems_station_nofire",
                         "public EMS station named in Overture, no fire_department place, weighted 1/(4 n_defined)",
                         rho_guess=0.08)
print(f"{path.name}: expected public RMSE {exp:.6f}")
