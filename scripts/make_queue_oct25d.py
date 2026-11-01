"""Structural v6 for 25 October (research of 24 October, round 7): Texas FM/RM roads are not S1200.

v3 put every Texas secondary-system route (FM, RM, Loop, Spur, Business, Beltway, Toll, Park) in
the TIGER proxy at weight 1, and needed a 0.55 definedness patch to meet the published share of
tracts without a road component (28.4 %). Splitting the systems settles it with the organisers' own
figures, no reference data:
- without FM/RM, Loops/Spurs/Business counting as state highways: 30.5 % undefined (28.4 published),
  with every FM/RM: 19.3 %;
- FM/RM km at weight 0.15 put the Texas Overture/TIGER length ratio at 1.586, the published maximum
  (1.59) -- at weight 1 it was 0.96.
So the reference carries only a small part of the 50,600 km of FM/RM roads (Overture classes a
third of them tertiary, #35542), and v3 charged Texas tracts for gaps on roads TIGER does not hold
(the blend already down-weights Texas transport to 0.8 against 1.4-1.9 elsewhere).

s96_t6_c_transport: v6 transport contribution (tx_split, FM/RM weight 0.15, FM-only definedness 0.19).
The 25 October list becomes s96, s92, s95, s93, s89; s94 and s88 move to 26 October.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
cal = dict(w_county_region={"eastern-ok": 0.24, "maricopa-az": 0.0, "northern-ca": 0.0,
                            "eastern-wa": 0.0, "south-central-tx": 0.0})
v6 = simulate(df, Params(n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True,
                         tx_split=True, w_txsec=0.15, p_txsec={"south-central-tx": 0.19}, **cal))
v6.to_parquet(config.INTERIM / "structural_v6.parquet", index=False)
tx = (df["region"] == "south-central-tx").to_numpy()
print(f"TX undefined share {1 - v6['p_transport_defined'][tx].mean():.3f} (published 0.284)")
path, exp = write_signal(df, v6["c_transport"].to_numpy(float), "s96_t6_c_transport",
                         "structural v6 transport contribution: Texas FM/RM at weight 0.15, Loop/Spur as state routes",
                         rho_guess=0.57)
print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s96_t6_c_transport", "s92_fire_osm_noov", "s95_fire_misfiled_noov", "s93_burn2016_x_dens",
         "s89_p_transport_one"]
(config.SUBMISSIONS / "upload_2026-10-25.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
