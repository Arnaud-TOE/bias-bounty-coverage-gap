"""Two more 25 October signals from the research of 24 October (screened on the 42-signal basis).

s92_fire_osm_noov: the tract has a hand-mapped OpenStreetMap fire-station building (Overture
    buildings carry OSM names and classes; Overture places carry no OSM record) but no Overture
    fire_department place. OSM fire stations follow the same federal inventories as the reference
    (OSM wiki HIFLD/Emergency), so the reference has a station and Overture none: fire gap 1.
    329 tracts; 78.5 % of OSM fire-station tracts do have an Overture place. [R2 0.10]
s93_burn2016_x_dens: MTBS burned share of land, for tracts whose last large wildfire was in 2016 or
    later, times log building density. The building reference (Microsoft US footprints, 2018
    release) still holds homes destroyed since, which Overture has partly removed. 536 tracts.
    [R2 0.11]
The 25 October list becomes s88, s89, s92, s93, s91; s90 and s85 move to 26 October.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.io import read_strata
from bbx.signals import write_signal

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_osmfac.parquet"), on="GEOID", how="left")
st = df[["GEOID"]].merge(read_strata(columns=["GEOID", "mtbs_wildfire_last_year", "mtbs_wildfire_burned_pct_land"]),
                         on="GEOID", how="left")

fire_osm_noov = ((df["osm_fire_bld"] > 0) & (df["poi_fire"] == 0)).astype(float)
recent = (st["mtbs_wildfire_last_year"] >= 2016).fillna(False).astype(float)
burned = (st["mtbs_wildfire_burned_pct_land"].fillna(0) / 100).clip(0, 1)
burn_dens = burned * recent * np.log1p(df["bld_n"] / df["area_km2"])

for name, sig, rho, purpose in [
    ("s92_fire_osm_noov", fire_osm_noov, 0.10,
     "OSM fire-station building in the tract but no Overture fire_department place"),
    ("s93_burn2016_x_dens", burn_dens, 0.08,
     "MTBS burned share (last fire 2016 or later) times log building density"),
]:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s88_t3_transport_gap", "s89_p_transport_one", "s92_fire_osm_noov", "s93_burn2016_x_dens",
         "s91_p_fire_defined"]
(config.SUBMISSIONS / "upload_2026-10-25.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
