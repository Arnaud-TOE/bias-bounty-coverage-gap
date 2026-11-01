"""Re-ranked queue for 20-21 October after the 19 October scores.

The CBP-half contrast (s07 +3.4 vs s25 -3.5 in the blend) is the strongest new mechanism, so
two more CBP allocation variants join the queue; the never-measured building / road-history
signals stay. Upload lists: submissions/upload_2026-10-20.txt and ..._10-21.txt.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.candidates import _gap, county_relative_density
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
st = df[["GEOID"]].merge(pd.read_parquet("data/interim/structural_v1.parquet"), on="GEOID", how="left")
w_half = 1 / (2 * st["n_defined"].clip(lower=1))

rel_hu = county_relative_density(df, "poi_n", "housing_units")
rel_bld = county_relative_density(df, "poi_n", "bld_n")
rel_area = county_relative_density(df, "poi_n", "ALAND")
new = [
    ("s36_cbp_hu_k2", _gap(rel_hu / 2.0) * w_half, 0.05,
     "CBP half if establishments are allocated by housing units, 0.5 place per establishment"),
    ("s37_logrel_places_per_bld", np.log(np.clip(np.nan_to_num(rel_bld, nan=1.0), 1e-3, 1e3)), 0.05,
     "log of places per building relative to the county (continuous)"),
    ("s38_cbp_area_k025", _gap(rel_area / 0.25) * w_half, 0.05,
     "CBP half if establishments are allocated by land area, 4 places per establishment"),
]
for name, sig, rho, purpose in new:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

days = {
    "2026-10-20": ["s26_bld_per_hu_low", "s27_bld_small_share", "s30_import_share", "s36_cbp_hu_k2",
                   "s37_logrel_places_per_bld"],
    "2026-10-21": ["s31_region_wa", "s28_bld_esri_share", "s29_poi_closed_share", "s38_cbp_area_k025",
                   "s34_unnamed_share"],
}
for day, files in days.items():
    (config.SUBMISSIONS / f"upload_{day}.txt").write_text(
        "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
    print(day, files)
