"""Local street names counted as extra TIGER records (research of 30 October, round 51).

TIGER/Line technical documentation (2024 edition, section 4.12.4): "The All Roads shapefiles will
contain multiple overlapping road segments where a segment is associated with more than one road
feature. For example, if a road segment is associated with US Route 36 and State Highway 7 and
28th Street, the associated All Roads shapefile will contain three spatially coincident segments,
each with a different name." The organisers' TIGER layer held all roads and was filtered to
S1100/S1200 at scoring (tutorial history, research of 28 October, round 26), so a highway that also
carries a local street name can be counted once more.

This "v5" idea was set aside on 24 October because it pushed the Arizona ratio below the published
maximum of 1.59; since v7, the maximum is held by Texas and the minimum by Oklahoma, and a partial
weight fits both. v7L: local-name copies of non-Interstate major routes at weight 0.25
(bbx.features_roadref majloc - majiloc), Texas FM/RM and Oklahoma county weights re-solved to the
published 1.59 and 0.71 (0.051 and 0.073; Arizona 1.32, California 1.43, inside the range).

s140_t7l_c_transport_delta: v7L transport contribution minus v7 (same seed, so only the reference
length moves). On the 65-signal basis 69 % new, in-span orientation +0.22 (weight 0.45: 67 % new,
+0.21, correlation 0.97 with this one).

Correction of 30 October (round 67, scripts/build_uncounted_majors.py): local names count only on
segments that the v7 reference counts as majors. The local names of 'US:US:Historic' / 'Old'
segments (multiplicity 0 in v7) gave tracts without any counted major a reference of their own, and
the share of tracts without a road component fell away from the published figures (Arizona 52.5 ->
49.3 % for 55 %, California 37.9 -> 34.4 % for 37 %, Oklahoma 21.1 -> 19.9 % for 21 %). Without
them the shares are those of v7; FM 0.051, OK county 0.075; 67 % new, in-span orientation +0.23;
correlation 0.87 with the first version.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

W_LOCAL = 0.25
df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_uncounted.parquet"), on="GEOID", how="left")
df["majloc_b10"] = df["majloc_b10"] - df["zloc23_b10"].fillna(0.0)  # local names of counted majors only
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
local = lambda d: W_LOCAL * (d["majloc_b10"] - d["majiloc_b10"]).sum()
# bbx.structural also adds W_LOCAL x txloc (local names of Texas secondary-system routes) to the term
# that w_fm multiplies, so the 1.59 ratio is solved on that sum.
w_fm = ((tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum() - local(tx))
        / (tx["txfm_b10"].sum() + W_LOCAL * tx["txloc_b10"].sum()))
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum() - local(ok)) / ok["cty2_b10"].sum()
print(f"TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
v7l = simulate(df, Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    local_name_weight=W_LOCAL, interstate_local_weight=0.0,
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5}))
v7l.to_parquet(config.INTERIM / "structural_v7L.parquet", index=False)
v7 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v7.parquet"), on="GEOID", how="left")
path, exp = write_signal(df, np.asarray(v7l["c_transport"] - v7["c_transport"], float), "s140_t7l_c_transport_delta",
                         f"v7 transport with local street names as extra TIGER records (weight {W_LOCAL}), minus v7",
                         rho_guess=0.10)
print(f"{path.name}: expected public RMSE {exp:.6f}")
