"""Structural v7 for 25 October (research of 24-25 October, round 8): route classification fixed.

ROUTE_LEVEL_SQL filed every 'US:<state>:<system>' network as a county route. Two of them are freeway
systems: Phoenix Loop 101/202/303 ('US:AZ:Loop', 560 km, all motorway) and the Oklahoma turnpikes
('US:OK:Turnpike', 1,824 km). They had no or little weight in the TIGER proxy, so boundary
double counting along them and the transport component of the tracts they cross were missing.
LEVEL2_SQL (bbx.features_roadref) counts state loop / turnpike / toll systems outside Texas as state
highways. With only the organisers' published figures:
- share of tracts without a road component, computed as the model does: Arizona 62.6 % (v6) ->
  54.9 % (published 55 %), Texas 29.7 % -> 28.4 % (published 28 %);
- Texas FM/RM weight re-solved to the published maximum Overture/TIGER ratio (1.59): 0.112;
  Oklahoma county routes re-solved to the published minimum (0.71): 0.152;
- county-only definedness: Arizona 0 (its loops are now majors), others unchanged.
v7 also carries v6 (Texas FM/RM are almost absent from TIGER).

s97_t7_c_transport: v7 transport contribution,
s98_t7_p_defined: v7 probability that the transport component is defined (93 % outside the span
    of the v3 one; Texas FM-only tracts drop from 0.55 to 0.19, Phoenix loop tracts rise to 1).
The 25 October list becomes s97, s98, s92, s95, s93; s96, s89, s94, s88 move to later days.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
tx = df[df["region"] == "south-central-tx"]
ok = df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()) / ok["cty2_b10"].sum()
print(f"TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
params = Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
)
v7 = simulate(df, params)
v7.to_parquet(config.INTERIM / "structural_v7.parquet", index=False)
for r in config.REGIONS:
    m = (df["region"] == r).to_numpy()
    print(f"  {r:17s} undefined {1 - v7['p_transport_defined'][m].mean():.3f}")

for name, sig, rho, purpose in [
    ("s97_t7_c_transport", v7["c_transport"], 0.57,
     "structural v7 transport contribution: state loops/turnpikes as highways, TX FM/RM 0.112, OK county 0.152"),
    ("s98_t7_p_defined", v7["p_transport_defined"], 0.25,
     "structural v7 probability that the transport component is defined"),
]:
    path, exp = write_signal(df, np.asarray(sig, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s97_t7_c_transport", "s98_t7_p_defined", "s92_fire_osm_noov", "s95_fire_misfiled_noov",
         "s93_burn2016_x_dens"]
(config.SUBMISSIONS / "upload_2026-10-25.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
