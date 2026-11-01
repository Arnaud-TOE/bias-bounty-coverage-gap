"""Open-status test for 28 October (research of 27 October, round 17).

The official text says each facility gap compares "Overture places in that category" with the
reference counts, without saying which places count. A quarter of Overture fire_department places
(916 of 3,641, nearly all from Meta, Microsoft or Foursquare) have no operating_status; in 542
tracts no fire place has the status 'open'. If the organiser kept only open places, those tracts
have no Overture station in the reference comparison, so a fire gap of 1 wherever the reference
has a station, which our model does not predict.

s118_t8o_fire_open_diff: v8 fire contribution with only 'open' fire places counted, minus v8
(nonzero only where some fire place lacks the open status). New to the 51-signal basis (R2 about
0.13). A clearly positive score means the organiser filtered on status, and the CBP and other
facility halves would then need the same treatment; a null one closes the question.
"""
import duckdb
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.io import ref_path, strata_path
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
frames = []
for r in config.REGIONS:
    pois, tracts = ref_path(r, "overture-pois").as_posix(), strata_path(r, "census-tracts").as_posix()
    frames.append(con.sql(f"""SELECT t.GEOID, count(*) FILTER (f.operating_status = 'open') AS poi_fire_status_open
        FROM '{tracts}' t JOIN '{pois}' f ON ST_Intersects(t.geometry, f.geometry)
        WHERE f.categories.primary = 'fire_department' GROUP BY 1""").df())
df = load_table()
df = df.merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(pd.read_parquet(config.FEATURES / "features_osmfac.parquet"), on="GEOID", how="left")
df = df.merge(pd.concat(frames), on="GEOID", how="left")
df["poi_fire_status_open"] = df["poi_fire_status_open"].fillna(0)
tx, ok = df[df["region"] == "south-central-tx"], df[df["region"] == "eastern-ok"]
w_fm = (tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()) / tx["txfm_b10"].sum()
w_ok = (ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()) / ok["cty2_b10"].sum()
params = Params(n_draws=1000, lam=fit_lambdas(df), roadref_band=10, multiplicity=True, level2=True,
    tx_split=True, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
    w_county_region={"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0, "eastern-wa": 0.0, "south-central-tx": 0.0},
    p_county={"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5, "south-central-tx": 0.5},
    fire_evidence="clean", p_misfiled_fire=0.9)
v8 = simulate(df, params)
# Same draws, with the Overture fire count restricted to open places; the stations dropped from
# the count still exist, so they enter the evidence of a reference station.
dfo = df.assign(poi_fire=df["poi_fire_status_open"],
                fire_misfiled_clean=df["fire_misfiled_clean"].fillna(0) + (df["poi_fire"] - df["poi_fire_status_open"]))
v8o = simulate(dfo, params)
v8o.to_parquet(config.INTERIM / "structural_v8o.parquet", index=False)
# Changing the counts shifts the random stream, so the difference is kept only where the count
# actually changes (elsewhere it is Monte Carlo noise).
touched = (df["poi_fire"] != df["poi_fire_status_open"]).to_numpy()
diff = np.where(touched, v8o["c_fire"].to_numpy() - v8["c_fire"].to_numpy(), 0.0)
print(f"tracts with a difference: {touched.sum()}, mean diff there {diff[touched].mean():.4f}, none open: {((df.poi_fire > 0) & (df.poi_fire_status_open == 0)).sum()}")
path, exp = write_signal(df, diff, "s118_t8o_fire_open_diff",
                         "v8 fire contribution counting only 'open' Overture fire places, minus v8", rho_guess=0.05)
print(f"{path.name}: expected public RMSE {exp:.6f}")
