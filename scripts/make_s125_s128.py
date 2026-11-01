"""Metro-level transport slopes (research of 28 October, round 32).

The blend lets transport weigh differently by region (s81-s84), not within a region, while the
reference and the map differ most between metropolitan cores and the rest: urban arterials are
classed differently by TIGER and OSM, and a dense grid puts more highways on tract edges. The v7
transport contribution restricted to each large metro is new to the 54-signal basis on the four
public regions (R2 0.06-0.09, in-span orientation +0.06 to +0.10) and the four copies are nearly
independent of one another (|residual correlation| <= 0.09). Each group is over 300 tracts
(decision D1-bis); eastern-wa is not public, so it gets no metro copy.

s125_t7_c_transport_houston: Harris, Fort Bend, Montgomery, Brazoria, Galveston (1,483 tracts),
s126_t7_c_transport_phoenix: Maricopa County (1,009),
s127_t7_c_transport_sanantonio: Bexar, Comal, Guadalupe (449),
s128_t7_c_transport_austin: Travis, Williamson, Hays (471).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
county = df["GEOID"].str[:5]
METROS = [("s125_t7_c_transport_houston", ["48201", "48157", "48339", "48039", "48167"]),
          ("s126_t7_c_transport_phoenix", ["04013"]),
          ("s127_t7_c_transport_sanantonio", ["48029", "48091", "48187"]),
          ("s128_t7_c_transport_austin", ["48453", "48491", "48209"])]
for name, counties in METROS:
    inside = county.isin(counties).to_numpy()
    path, exp = write_signal(df, np.asarray(v7["c_transport"] * inside, float), name,
                             f"structural v7 transport contribution, counties {'/'.join(counties)} only ({inside.sum()} tracts)",
                             rho_guess=0.08)
    print(f"{path.name}: {inside.sum()} tracts, expected public RMSE {exp:.6f}")
