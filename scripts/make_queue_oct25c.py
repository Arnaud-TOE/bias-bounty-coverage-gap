"""Structural v5 for 25 October: TIGER local-name duplicates (research of 24 October, round 4).

TIGER/Line primary-secondary roads hold one record per name of a road, and the organiser clip keeps
every record. The concurrent route numbers are already in v3 (one copy per route number). A route
that also carries a local street name ("US Hwy 77" and "S Main St") has one copy more; a public
write-up (iam-dante, METHOD.md) fits that duplicate at 0.97. Overture keeps the local name as the
segment's primary name, so km of route segments whose primary name is not a route designation get
one extra reference copy (bbx.features_roadref: majloc, txloc).

The README range of Overture/TIGER ratios (max 1.59, matched by v3 in Arizona) argues against it,
so this is a measurement: the v5-minus-v3 direction is 69 % outside the 42-signal span and its
in-span part points the right way (+0.24).

s94_t5_c_transport: v5 transport contribution (local-name copies at weight 1, Interstates too).
The 25 October list becomes s94, s88, s89, s92, s93 (s91 moves to 26 October).
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
v5 = simulate(df, Params(n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True,
                         local_name_weight=1.0, interstate_local_weight=1.0, **cal))
v5.to_parquet(config.INTERIM / "structural_v5.parquet", index=False)
path, exp = write_signal(df, v5["c_transport"].to_numpy(float), "s94_t5_c_transport",
                         "structural v5 transport contribution: v3 plus one TIGER copy per local street name",
                         rho_guess=0.55)
print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s94_t5_c_transport", "s88_t3_transport_gap", "s89_p_transport_one", "s92_fire_osm_noov",
         "s93_burn2016_x_dens"]
(config.SUBMISSIONS / "upload_2026-10-25.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
