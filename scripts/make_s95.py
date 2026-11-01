"""s95 (for 26 October): a name-verified fire station filed under another Overture category, in a
tract with no Overture fire_department place.

The organiser counts Overture fire stations on categories.primary = fire_department only, so a
station Overture files as fire_protection_service, government office, non-profit, police... is a
reference station (the inventory has it) with Overture count 0: fire gap 1. Names are verified
with a station pattern and an exclusion list for extinguisher vendors and "firehouse" businesses
(bbx.features_osmfac.misfiled_fire; pattern adapted from Luca925, #34925). 370 tracts, 101 of
them shared with s92 (OSM fire-station building). [R2 0.38 on the 42-signal basis, in-span +0.11]
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_osmfac.parquet"), on="GEOID", how="left")
sig = ((df["fire_misfiled_clean"] > 0) & (df["poi_fire"] == 0)).astype(float)
path, exp = write_signal(df, np.asarray(sig, float), "s95_fire_misfiled_noov",
                         "name-verified fire station under another category, no Overture fire_department place",
                         rho_guess=0.10)
print(f"{path.name}: expected public RMSE {exp:.6f} ({int(sig.sum())} tracts)")
