"""Structural v9 (research of 24 October, round 12): boundary-following routes up to 30 m.

    python -m bbx.features_bandruns     # data/features/features_bandruns.parquet (about 4 minutes)
    python scripts/make_s106.py

v9 = v8 (v7 transport, clean fire evidence) with the road proxy's boundary term taken from
bbx.features_bandruns: in-tract route km plus long runs (> 232 m) in a 30 m outer ring, instead
of all route km in a 10 m band. HHYurdagul (Zindi #35478) reports that this cleaner "highway along
the edge" term improved their public RMSE (change correlation about +0.23).
- Long runs add about 6,700 km of majors lying 10-30 m from an edge (25,600 km against 17,300 km
  in the 10 m band). Re-solving the published ratios then gives Texas FM/RM a weight of 0.005
  (0.112 in v7) and Oklahoma county routes 0.095 (0.152); undefined shares are unchanged.
- Caveat: dual carriageways and Texas frontage roads put a second line 15-40 m from an edge that
  the reference does not double count, so the 30 m ring may over-credit; the leaderboard decides.
- Screening: v9 c_transport has R2 0.71 on the 42-signal basis and 0.89 once s97/s98 (v7) are
  added; about 11 % of it would be new after the 25 October scores.
s106_t9_c_transport: v9 transport contribution.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table()
df = df.merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_osmfac.parquet"), on="GEOID", how="left")
runs = pd.read_parquet(config.FEATURES / "features_bandruns.parquet")
df = df.merge(runs, on="GEOID", how="left")
df[runs.columns[1:]] = df[runs.columns[1:]].fillna(0.0)
for g in ["maj2x", "txoth", "txfm", "tx", "cty2"]:
    df[f"{g}_b30r"] = df[f"{g}_in"] + df[f"{g}_run30"]
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b30r"].sum() - tx["txoth_b30r"].sum()) / tx["txfm_b30r"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b30r"].sum()) / ok["cty2_b30r"].sum()
print(f"TX FM/RM weight {w_fm:.3f}, OK county weight {w_ok:.3f}")
v9 = simulate(df, Params(
    n_draws=1000, lam=fit_lambdas(df), roadref_band="30r", multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(max(w_fm, 0.0)), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0,
                     "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5,
              "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9))
v9.to_parquet(config.INTERIM / "structural_v9.parquet", index=False)
for r in config.REGIONS:
    m = (df["region"] == r).to_numpy()
    print(f"  {r:17s} undefined {1 - v9['p_transport_defined'][m].mean():.3f}")

path, exp = write_signal(df, np.asarray(v9["c_transport"], float), "s106_t9_c_transport",
                         "structural v9 transport contribution: boundary-following routes (runs > 232 m) up to 30 m",
                         rho_guess=0.55)
print(f"{path.name}: expected public RMSE {exp:.6f}")
