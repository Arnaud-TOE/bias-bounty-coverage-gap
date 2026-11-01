"""Structural v9L: v9 fire (town cores, rural / urban station rates) with the v7L transport of s140.

    python scripts/make_structural_v9L.py     # writes data/interim/structural_v9L.parquet

Used as the prior of the finals blend f4 (scripts/make_finals.py): the blend weights are pulled towards
the weights that best reproduce this composite from the measured signals, instead of towards zero.
The composite depends on the package data only, not on any leaderboard measurement.
"""
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.structural import Params, fit_lambdas, simulate

W = 0.25  # local names of counted non-Interstate majors, as s140
d = load_table()
for name in ("features_roadref", "features_osmfac", "features_uncounted"):
    d = d.merge(pd.read_parquet(config.FEATURES / f"{name}.parquet"), on="GEOID", how="left")
d["majloc_b10"] = d["majloc_b10"] - d["zloc23_b10"].fillna(0.0)
tx, ok = d[d["region"] == "south-central-tx"], d[d["region"] == "eastern-ok"]
local = lambda x: W * (x["majloc_b10"] - x["majiloc_b10"]).sum()
w_fm = ((tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx))
        / (tx["txfm_b10"].sum() + W * tx["txloc_b10"].sum()))
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
town = d["ruca_primary"].fillna(1).isin([4, 7]).to_numpy()
v9l = simulate(d.assign(fire_misfiled_clean=d["fire_misfiled_clean"].fillna(0) + town), Params(
    n_draws=1000, lam=fit_lambdas(d), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19}, local_name_weight=W,
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9, fire_per_rural_pop=1 / 2000, fire_per_urban_pop=1 / 36000))
v9l.to_parquet(config.INTERIM / "structural_v9L.parquet", index=False)
print(f"FM {w_fm:.3f}, OK county {w_ok:.3f}; mean composite {v9l['score'].mean():.4f}")
