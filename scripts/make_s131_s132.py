"""Mid-size metro transport slope, and the pooled remaining metros (research of 28 October, round 36).

The metro copies s125-s130 cover the six large metro areas (about 32 % of the v7 transport
variance). The next tier, the cores of mid-size metro areas, is too small county by county
(each under 300 tracts) but carries more transport variance pooled than any single large metro.

s131_t7_c_transport_midmetro: v7 transport contribution in the mid-size metro cores
  Texas: Hidalgo, Cameron, Lubbock, Nueces, Bell, Webb, Brazos, McLennan, Smith, Taylor (909),
  Arizona: Pima, Pinal, Yavapai (437),
  California: Sacramento, Placer, Butte, Shasta (388),
  Washington: Spokane, Yakima (184, see below).
  1,734 public-region tracts, 19.6 % of the v7 transport variance; on the 55-signal basis of the
  four public regions 59 % new (49 % once s119 and s125-s130 are added), orientation +0.24.
s132_t7_c_transport_othermetros: the same contribution over Dallas-Fort Worth, Oklahoma City +
  Tulsa and the mid-size cores together (4,084 public-region tracts, 38 % of the variance; 56 %
  new, 50 % with the 28 October lot, orientation +0.36). One file instead of s129 + s130 + s131, to use if the
  four metro copies scored on 28 October get blend weights of the same sign.
Spokane and Yakima (eastern-wa) are mid-size metro cores too and are included. eastern-wa is not
public, so their values leave the public score and the fitted weights unchanged (the finals fit on
the four public regions, `--wa-not-public`); they only let the final blend give those two metros
the mid-metro slope learned elsewhere instead of the rural one.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
county = df["GEOID"].str[:5]
MID = ["48215", "48061", "48303", "48355", "48027", "48479", "48041", "48309", "48423", "48441",
       "04019", "04021", "04025", "06067", "06061", "06007", "06089", "53063", "53077"]
DFW = ["48113", "48439", "48085", "48121", "48139", "48397", "48257", "48251", "48367", "48221", "48231"]
OKC_TULSA = ["40109", "40027", "40017", "40143", "40145", "40131", "40113"]
for name, counties, label in [("s131_t7_c_transport_midmetro", MID, "mid-size metro cores"),
                              ("s132_t7_c_transport_othermetros", DFW + OKC_TULSA + MID, "Dallas-Fort Worth, Oklahoma City, Tulsa and mid-size metro cores")]:
    inside = county.isin(counties).to_numpy()
    path, exp = write_signal(df, np.asarray(v7["c_transport"] * inside, float), name,
                             f"structural v7 transport contribution, {label} only ({inside.sum()} tracts)", rho_guess=0.08)
    print(f"{path.name}: {inside.sum()} tracts, expected public RMSE {exp:.6f}")
