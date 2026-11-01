"""Street-named FM and county routes as the S1200 ones (research of 30 October, round 68).

S1200 is "main arteries" (TIGER technical documentation). The published ratios leave room in TIGER
for about 11 % of Texas FM/RM length and 15 % of Oklahoma county-route length, which v7 spreads as a
fractional weight over every km. Here the S1200 share sits on the routes that carry a street name in
Overture (Bandera Road, Parmer Lane; in Oklahoma named county roads), i.e. the arteries through
built-up areas:
- Texas: FM/RM km with a street name (8,643 km in the 10 m band) take weight 0.74 (published 1.59
  ratio); FM-only definedness 1 - exp(-alpha x eligible km), alpha keeping v7's undefined share;
- Oklahoma: county routes with a street name (5,796 km) take weight 0.70 (published 0.71 ratio);
  undefined share unchanged (21.1 %).
Every other component as v7 (same seed). The 70 measured signals carry almost no information on
the Texas FM split (every FM rule tested so far: in-span orientation -0.05 to +0.04), so only a
score can tell.

s142_t10s_c_transport_delta: Texas part (v7 elsewhere) plus Oklahoma part, minus v7, three seeds averaged. sd 0.0123,
84 % new on the 65-signal basis, in-span orientation +0.04 (+0.02 beside s140); correlation 0.09
with s140, about 0 with s141 and s139.
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from bbx import config
from bbx.dataset import load_table
from bbx.features import ROUTE_LEVEL_SQL
from bbx.features_roadref import LEVEL2_SQL
from bbx.io import connect, ref_path, strata_path
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

TO_M = "ST_Transform({g}, 'OGC:CRS84', 'EPSG:5070', true)"
# A street name: ends with a street type (optionally followed by a direction) and is neither a route
# designation nor an honorary name.
ROUTE = (r"^(north |south |east |west )?(u\.s\.|united states|us|u s|state|texas|oklahoma|interstate|ranch|farm-to-market"
         r"|farm to market|ranch-to-market)( |-)(highway|route|hwy|rte|road|[0-9])|^(sh|ok|tx|us|i|fm|rm)[- ]?[0-9]+[a-z]?$"
         r"|^(business|bus\.?|loop|spur|bypass|alternate|alt\.?) ")
HONORARY = (r"memorial|veteran|purple heart|blue star|medal of honor|world war|korean|vietnam|pearl harbor|code talker"
            r"|trooper|officer|deputy|sheriff|division|scenic|historic|heroes|gold star|fallen|infantry|patriot")
STREET = (r"(^| )(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|parkway|pkwy|freeway|fwy|expressway"
          r"|expy|turnpike|tpke|pike|loop|place|court|circle|trail|trl|run|pass|plaza|row|terrace|bypass|beltway|tollway"
          r"|skyway|causeway)( (north|south|east|west))?$")
IS_STREET = (f"(names.primary IS NOT NULL AND NOT regexp_matches(lower(names.primary), '{ROUTE}') "
             f"AND NOT regexp_matches(lower(names.primary), '{HONORARY}') AND regexp_matches(lower(names.primary), '{STREET}') "
             f"AND NOT regexp_matches(names.primary, '^[NSEW] ?[0-9]{{3,4}} ?(Road|Rd)$'))")


def street_km(con, region: str) -> pd.DataFrame:
    """10 m band km of Texas FM/RM (fm_street) and county routes (cty_street) carrying a street name."""
    tracts = strata_path(region, "census-tracts").as_posix()
    roads = ref_path(region, "overture-roads").as_posix()
    con.sql(f"CREATE OR REPLACE TEMP TABLE tm AS SELECT GEOID, ST_Buffer({TO_M.format(g='geometry')}, 10) AS g10 FROM '{tracts}'")
    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE rm AS SELECT * FROM (
            SELECT coalesce({ROUTE_LEVEL_SQL}, 9) = 4
                       AND coalesce(list_bool_or(list_transform(routes, r -> regexp_full_match(r.network, 'US:TX:(FM|RM)'))), false) AS fm,
                   coalesce({LEVEL2_SQL}, 9) = 5 AS cty, {IS_STREET} AS street, {TO_M.format(g='geometry')} AS g
            FROM '{roads}' WHERE routes IS NOT NULL)
        WHERE street AND (fm OR cty)""")
    d = con.sql("""SELECT t.GEOID, sum(ST_Length(ST_Intersection(t.g10, r.g))) FILTER (r.fm) / 1000 AS fm_street,
                          sum(ST_Length(ST_Intersection(t.g10, r.g))) FILTER (r.cty) / 1000 AS cty_street
                   FROM tm t JOIN rm r ON ST_Intersects(t.g10, r.g) GROUP BY 1""").df()
    return pd.read_parquet(strata_path(region, "census-tracts"), columns=["GEOID"]).merge(d, on="GEOID", how="left").fillna(0.0)


con = connect()
streets = pd.concat([street_km(con, r) for r in ("south-central-tx", "eastern-ok")], ignore_index=True)
df = load_table().merge(pd.read_parquet(config.FEATURES / "features_roadref.parquet"), on="GEOID", how="left")
df = df.merge(streets, on="GEOID", how="left")
df[["fm_street", "cty_street"]] = df[["fm_street", "cty_street"]].fillna(0.0)
istx, isok = (df["region"] == "south-central-tx").to_numpy(), (df["region"] == "eastern-ok").to_numpy()
tx, ok = df[istx], df[isok]
need_tx = tx["sc_in"].sum() / 1.59 - tx["maj2x_b10"].sum() - tx["txoth_b10"].sum()
need_ok = ok["sc_in"].sum() / 0.71 - ok["maj2x_b10"].sum()
w_fm, w_ok = need_tx / tx["txfm_b10"].sum(), need_ok / ok["cty2_b10"].sum()
lam = fit_lambdas(df)
county_w = {"eastern-ok": float(w_ok), "maricopa-az": 0.0, "northern-ca": 0.0, "eastern-wa": 0.0, "south-central-tx": 0.0}
county_p = {"maricopa-az": 0.0, "northern-ca": 0.0, "eastern-ok": 1.0, "eastern-wa": 0.5, "south-central-tx": 0.5}
v7_params = dict(n_draws=1000, lam=lam, roadref_band=10, multiplicity=True, level2=True, tx_split=True)

# Texas: eligible FM km = street-named FM km; FM-only definedness 1 - exp(-alpha E), binned into
# pseudo-regions so that p_txsec can vary by tract.
E = np.where(istx, df["fm_street"].to_numpy(), df["txfm_b10"].to_numpy())
w_e = need_tx / E[istx].sum()
nomaj = istx & (df["maj2x_b10"].to_numpy() <= 0) & (df["txoth_b10"].to_numpy() <= 0)
n_def = 0.19 * (nomaj & (df["txfm_b10"].to_numpy() > 0)).sum()  # v7's expected count of defined FM-only tracts
alpha = brentq(lambda a: (1 - np.exp(-a * E[nomaj])).sum() - n_def, 1e-6, 100)
bins = np.clip(np.round(np.where(nomaj, 1 - np.exp(-alpha * E), 0.0) * 20).astype(int), 0, 20)
region = np.where(nomaj & (E > 0), np.char.add("txp", bins.astype(str)), df["region"].to_numpy())
p_tx, wc, pc = {"south-central-tx": 0.19}, dict(county_w), dict(county_p)
for k in range(21):
    p_tx[f"txp{k}"], wc[f"txp{k}"], pc[f"txp{k}"] = k / 20, 0.0, 0.5
tx_params = Params(**v7_params, w_txsec=float(w_e), p_txsec=p_tx, w_county_region=wc, p_county=pc)
# Oklahoma: county reference km = street-named county routes.
ok_params = Params(**v7_params, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19},
                   w_county_region={**county_w, "eastern-ok": float(need_ok / ok["cty_street"].sum())}, p_county=county_p)
base_params = Params(**v7_params, w_txsec=float(w_fm), p_txsec={"south-central-tx": 0.19}, w_county_region=county_w, p_county=county_p)
# The Texas part moves FM-only definedness, which the common seed does not cancel: three seeds, each
# against v7 at the same seed (one seed: correlation 0.990 with another seed's run).
SEEDS = 3
delta = np.zeros(len(df))
for k in range(SEEDS):
    seed = base_params.seed + k
    t10 = simulate(df.assign(txfm_b10=E, region=region), replace(tx_params, seed=seed))
    o10 = simulate(df.assign(cty2_b10=np.where(isok, df["cty_street"], df["cty2_b10"])), replace(ok_params, seed=seed))
    v7 = simulate(df, replace(base_params, seed=seed))
    delta += (np.where(istx, t10["c_transport"] - v7["c_transport"], 0.0)
              + np.where(isok, o10["c_transport"] - v7["c_transport"], 0.0)) / SEEDS
print(f"Texas: weight {w_e:.3f} on street-named FM km, alpha {alpha:.3f}, undefined {1 - t10['p_transport_defined'][istx].mean():.3f}")
print(f"Oklahoma: weight {need_ok / ok['cty_street'].sum():.3f} on street-named county km, "
      f"undefined {1 - o10['p_transport_defined'][isok].mean():.3f}")
path, exp = write_signal(df, delta, "s142_t10s_c_transport_delta",
                         "v7 transport with street-named FM (TX) and county routes (OK) as the S1200 ones, minus v7",
                         rho_guess=0.05)
print(f"{path.name}: expected public RMSE {exp:.6f}")
