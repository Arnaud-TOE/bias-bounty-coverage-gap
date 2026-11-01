"""Queue for 23 October, rebuilt after the research of 22 October (docs/04_recherche_2026-10-22.md).

The organiser road reference clips TIGER lines to tracts (boundary highways credited to both
neighbours) and keeps one TIGER record per route number (concurrent routes counted several
times). Structural v3 models both from Overture geometry alone (bbx.features_roadref):

s77_t3_c_transport: v3 transport contribution (10 m boundary band, route multiplicity, county
    routes weighted so the regional Overture/TIGER ratios stay in the README's 0.71-1.59 range),
s78_t3_nomult_c_transport: the same without multiplicity (separates the two mechanisms),
s79_t3_score: v3 composite (edge-only tracts gain a transport component, which re-weights the
    other components),
s80_bgap_s300: building gap when each hand-drawn footprint with a Microsoft counterpart hides
    max(area / 300 m2 - 1, 0) further Microsoft footprints (bbx.features_bldref),
s32_region_ca: already written (completes the regional intercepts).
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table()
df = df.merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_bldref.parquet"), on="GEOID", how="left")
lam = fit_lambdas(df)
# OK county routes: 0.24 of their km gives the README minimum ratio 0.71; the other regions are
# already inside the published range with Interstate / US / state routes (and Texas FM/RM).
cal = dict(w_county_region={"eastern-ok": 0.24, "maricopa-az": 0.0, "northern-ca": 0.0,
                            "eastern-wa": 0.0, "south-central-tx": 0.0})
v3 = simulate(df, Params(n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, **cal))
v3n = simulate(df, Params(n_draws=1000, lam=lam, roadref_band=10, multiplicity=False, **cal))
v3.to_parquet(config.INTERIM / "structural_v3.parquet", index=False)
v3n.to_parquet(config.INTERIM / "structural_v3_nomult.parquet", index=False)

ref = df["bld_msft"] + df["hand_ms"] + df["exc300"]
bgap = (1 - np.minimum(1, df["bld_n"] / ref.where(ref > 0))).fillna(0)
w_top = 1 / v3["n_defined"].clip(lower=1)

jobs = [
    ("s77_t3_c_transport", v3["c_transport"], 0.45,
     "structural v3 transport contribution: boundary highways credited to both tracts, route multiplicity"),
    ("s78_t3_nomult_c_transport", v3n["c_transport"], 0.43,
     "structural v3 transport contribution without route multiplicity"),
    ("s79_t3_score", v3["score"], 0.40, "structural v3 composite score"),
    ("s80_bgap_s300", bgap * w_top, 0.10,
     "building gap contribution: hand-drawn footprints hiding max(area/300-1,0) Microsoft footprints"),
]
for name, sig, rho, purpose in jobs:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s77_t3_c_transport", "s78_t3_nomult_c_transport", "s79_t3_score", "s80_bgap_s300", "s32_region_ca"]
(config.SUBMISSIONS / "upload_2026-10-23.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
