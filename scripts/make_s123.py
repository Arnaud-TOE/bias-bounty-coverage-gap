"""Building-reference vintage for 29 October (research of 28 October, round 25).

The organisers' tutorial (github.com/kentstephen/bias-bounty-map-tutorial, version before the
25 September commit that dropped the removed layers) described the building reference layer as
"Microsoft GlobalML Building Footprints", the same source as Overture's ML buildings. The building
gap can then only come from the two snapshots differing: Overture carries the ML version of
February 2025 (imagery up to 2024), while the reference was taken in mid-2026, after Microsoft's
2026 US additions (about 4.4 M footprints from 2021-2025 Vexcel imagery). Where Overture's ML
footprints are still from old imagery, the reference probably holds more buildings, so a positive
building gap. Uses only Overture's own `sources[1].update_time` (imagery capture date).

s123_bld_ml_old_imagery: share of the tract's Overture buildings that are Microsoft ML from imagery
of 2019 or earlier (or undated), weighted 1 / n_defined. New to the 51-signal basis (R2 0.23),
in-span orientation +0.13. Needs data/interim/bld_src_dates.parquet (research round 12).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
b = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "bld_src_dates.parquet").drop(columns="region"),
                        on="GEOID", how="left").fillna(0)
v8 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v8.parquet"), on="GEOID", how="left")
old_share = (b["ml_y2000"] + b["ml_le2019"]) / b["n"].clip(lower=1)
sig = old_share.to_numpy() / v8["n_defined"].clip(lower=1).to_numpy()
path, exp = write_signal(df, sig, "s123_bld_ml_old_imagery",
                         "share of Overture buildings that are Microsoft ML from imagery <= 2019, weighted 1/n_defined",
                         rho_guess=0.10)
print(f"{path.name}: expected public RMSE {exp:.6f}")
