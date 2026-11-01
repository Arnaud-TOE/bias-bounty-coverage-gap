"""Fire contribution in the large metro areas (research of 28 October, round 37).

Counterpart of the metro transport copies (s125-s132) for the fire term. In large metro areas,
city fire departments are well covered by Overture places, so the fire gap the v8 model draws
from station densities may not exist there. On the 55-signal basis of the four public regions the
v8 fire contribution restricted to the six large metro areas is 44 % new (42 % once the 28 October
lot and s132 are added) and its in-span part is oriented at -0.06, against +0.26 outside the
metro areas: the measured signals already hint that the fire slope is flatter in the metros.

s133_t8_c_fire_bigmetros: v8 fire contribution (scripts/make_s116_s117.py, structural_v8e) in
Houston, Phoenix, San Antonio, Austin, Dallas-Fort Worth, Oklahoma City and Tulsa (5,762 tracts).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8e.parquet"), on="GEOID", how="left")
BIG = ["48201", "48157", "48339", "48039", "48167", "04013", "48029", "48091", "48187", "48453", "48491", "48209",
       "48113", "48439", "48085", "48121", "48139", "48397", "48257", "48251", "48367", "48221", "48231",
       "40109", "40027", "40017", "40143", "40145", "40131", "40113"]
inside = df["GEOID"].str[:5].isin(BIG).to_numpy()
path, exp = write_signal(df, np.asarray(v8["c_fire"] * inside, float), "s133_t8_c_fire_bigmetros",
                         f"structural v8 fire contribution, large metro areas only ({inside.sum()} tracts)", rho_guess=0.05)
print(f"{path.name}: {inside.sum()} tracts, expected public RMSE {exp:.6f}")
