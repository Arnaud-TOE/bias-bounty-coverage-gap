"""Structural model of the organiser coverage-gap score (no labels).

The organiser score is a deterministic function of Overture counts O and reference
counts R that we cannot see (the reference layers are withdrawn and may not be used).
Each R is replaced by a distribution built only from permitted data, and the prediction
is the Monte-Carlo expectation of the *exact* organiser formula:

    component gap   g = 1 - min(1, O / R), undefined when R = 0
    POI             mean over defined halves of
                      HIFLD half = mean over defined types (fire, EMS, schools)
                      CBP half   = all places vs establishments
    score           mean of the defined components (transport, building, POI)

The expectation is the RMSE-optimal point prediction under those beliefs. Every draw uses
a fixed seed, so predictions are deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config


def _default_p_txsec():
    # P(TIGER has a S1100/S1200 road) for tracts whose highest route is a Texas FM/RM/Loop/
    # Spur road; solved so the share of tracts without one matches the organiser's published
    # "at least one undefined component" share (TX 28 %: 37.5 % without major routes, 20.3 %
    # once FM/RM routes count). See docs/journal.md.
    return {"south-central-tx": 0.55}


def _default_p_county():
    # Same for county-route-only tracts: AZ 55 % (60.0 % -> 52.9 %), CA 37 % (36.5 % -> 27.7 %),
    # OK 21 % (22.2 % -> 21.3 %); eastern-wa has no published share, taken between.
    return {"maricopa-az": 0.70, "northern-ca": 0.0, "eastern-ok": 1.0,
            "eastern-wa": 0.5, "south-central-tx": 0.5}


@dataclass
class Params:
    # Transport: TIGER S1100+S1200 km ~ LogNormal around a route-based proxy.
    p_txsec: dict = field(default_factory=_default_p_txsec)
    p_county: dict = field(default_factory=_default_p_county)
    w_txsec: float = 1.0          # weight of Texas FM/RM/Loop/Spur km in the proxy
    w_county: float = 1.0         # weight of county-route km in the proxy
    w_county_region: dict = field(default_factory=dict)  # per-region override of w_county
    w_other_region: dict = field(default_factory=dict)   # per-region weight of other route km
    ref_scale: dict = field(default_factory=dict)  # per-region multiplier on the proxy (default 1)
    sigma_t: float = 0.5
    q_def_noroute: float = 0.03   # P(transport defined) when no route-tagged road at all
    unrouted_km_if_defined: float = 1.0
    # v3: road-reference artefacts (bbx.features_roadref). With a band of w metres the proxy
    # credits boundary highways to both tracts, and with multiplicity concurrent routes count
    # once per designation, as the TIGER clip does; Overture km are the planar clip.
    roadref_band: int | None = None
    multiplicity: bool = True
    # v4: TIGER files unpaved roads as S1400, so county routes enter the reference by Overture
    # surface: paved at weight 1, unpaved at 0, unknown surface at the region's weight here
    # (replaces w_county_region for the regions listed).
    county_null_weight: dict = field(default_factory=dict)
    # v5: TIGER also stores a route that carries a local street name once more under that name.
    # Weight of the extra copy on route km with a local name (Interstates apart).
    local_name_weight: float = 0.0
    interstate_local_weight: float = 0.0
    # Weight of Texas FM/RM km that Overture classes below secondary (32 % of FM length): 1 keeps
    # v3 (every FM route is S1200), 0 drops them from the reference.
    txsec_unscored_weight: float = 1.0
    # v6: Texas Loop/Spur/Business/Beltway/Toll/Park routes count like state highways, and only
    # Farm/Ranch-to-Market km stay in the secondary-system term (weight w_txsec, definedness
    # p_txsec): the published 28.4 % undefined share is met with almost no FM/RM (30.5 % without
    # any, 19.3 % with all).
    tx_split: bool = False
    # v10 (research of 30 October, round 67): reference km drawn route by route, all or nothing
    # (a route is S1200 or not along its length). Callable (n, D) -> n x D km added to the proxy;
    # a draw with added km is defined. None keeps the fractional weights above. Tested on Texas FM
    # and Oklahoma county routes: in-span orientation -0.08, Texas undefined 26.3 % (28 % published).
    extra_ref: object = None
    # v7: route classification LEVEL2 (bbx.features_roadref): state loop / turnpike / toll systems
    # outside Texas (Phoenix loops, Oklahoma turnpikes) count as state highways, with multiplicity.
    level2: bool = False
    # Building: Microsoft footprint count ~ LogNormal around the Overture count.
    mu_b: float = -0.05
    sigma_b: float = 0.15
    # HIFLD facilities: H = M + K with M ~ Binomial(O, pi) Overture records that are real
    # reference facilities and K ~ Poisson(max(lambda - pi O, 0)) facilities the map misses.
    # lambda is a physical density prior from national aggregates (not tract-level data):
    # ~29,700 US fire stations, about 1 per 4,000 rural and 1 per 18,000 urban residents;
    # ~130,000 K-12 schools (1 per ~2,600 residents); EMS close to 1:1 with Overture (README).
    fire_per_rural_pop: float = 1 / 4000
    fire_per_urban_pop: float = 1 / 18000
    fire_per_km2: float = 1 / 2500
    pi_fire: float = 0.8
    # EMS and schools are close to complete in Overture (README: EMS "close to 1:1 and rarely
    # binds"): extra reference facilities ~ Poisson(kappa * smoothed Overture count).
    pi_ems: float = 0.9
    pi_school: float = 0.9
    kappa_ems: float = 0.1
    kappa_school: float = 0.15
    p_misfiled_fire: float = 0.85  # P(H >= 1) when a fire station is named under another category
    # 'clean': evidence of a reference station = name-verified station under another category
    # (vendors excluded) + OSM fire-station building + fire_department as alternate category
    # (bbx.features_osmfac); 'v1': the original name regex, which also caught extinguisher vendors.
    fire_evidence: str = "v1"
    fire_anchor: float = 0.0       # extra expected stations when a community anchor is mapped
    # CBP establishments ~ LogNormal around a proxy:
    #   'geomean'    geometric mean of population and places proxies (v1);
    #   'county_pop' county establishments allocated by population share, county establishments
    #                estimated as county Overture places / places_per_est.
    cbp_mode: str = "geomean"
    est_per_person: float = 0.0243
    places_per_est: float = 2.0
    sigma_c: float = 0.5
    # Monte-Carlo.
    n_draws: int = 1000
    seed: int = config.SEED
    lam: dict = field(default_factory=dict)  # per-type expected facility counts (set by fit_lambdas)


def fit_lambdas(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Expected Overture facility counts per tract from a Poisson GLM on tract covariates.

    This only smooths the Overture counts themselves (no reference data): it estimates how
    many stations / schools a tract like this one usually carries in the map, which, scaled
    by u, is the rate of facilities the map is missing.
    """
    import statsmodels.api as sm

    X = pd.DataFrame({
        "log_pop": df["log_pop"],
        "log_area": df["log_area"],
        "rural": df["rural_share"].fillna(df["rural_share"].median()),
        "log_hu": df["log_hu"],
    })
    for r in list(config.REGIONS)[1:]:
        X[f"reg_{r}"] = df[f"reg_{r}"]
    X = sm.add_constant(X.astype(float))
    out = {}
    for name, col in [("fire", "poi_fire"), ("ems", "poi_ems"), ("school", "poi_school")]:
        y = df[col].to_numpy(float)
        model = sm.GLM(y, X, family=sm.families.Poisson()).fit()
        out[name] = model.predict(X).to_numpy()
    return out


def _gap(o, r):
    """1 - min(1, o/r) where r > 0, NaN where undefined (r == 0)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        g = 1 - np.minimum(1.0, np.where(r > 0, o / np.where(r > 0, r, 1), np.nan))
    return np.where(r > 0, g, np.nan)


def _nanmean_stack(*arrays):
    stack = np.stack(arrays)
    cnt = np.sum(~np.isnan(stack), axis=0)
    with np.errstate(invalid="ignore"):
        return np.where(cnt > 0, np.nansum(stack, axis=0) / np.maximum(cnt, 1), np.nan)


def simulate(df: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Expected composite and component gaps per tract (columns: score, transport, ...)."""
    rng = np.random.default_rng(p.seed)
    n, D = len(df), p.n_draws
    lam = p.lam or fit_lambdas(df)

    def col(c):
        return df[c].fillna(0).to_numpy(float)[:, None]

    # Transport.
    region = df["region"].to_numpy()
    if p.roadref_band:
        b = f"b{p.roadref_band}"
        o_t = col("sc_in")
        if p.level2:
            major = col(f"maj2x_{b}" if p.multiplicity else f"maj2_{b}")
            txsec, county = col(f"tx_{b}"), col(f"cty2_{b}")
        else:
            major = col(f"majx_{b}" if p.multiplicity else f"maj_{b}")
            txsec, county = col(f"tx_{b}"), col(f"cty_{b}")
        if p.txsec_unscored_weight != 1.0:
            txsec = col(f"txsc_{b}") + p.txsec_unscored_weight * col(f"txun_{b}")
        if p.tx_split:
            major = major + col(f"txoth_{b}")
            txsec = col(f"txfm_{b}")
        if p.local_name_weight or p.interstate_local_weight:
            iloc = col(f"majiloc_{b}")
            major = major + p.local_name_weight * (col(f"majloc_{b}") - iloc) + p.interstate_local_weight * iloc
            txsec = txsec + p.local_name_weight * col(f"txloc_{b}")
        if p.county_null_weight:
            q = np.vectorize(lambda r: p.county_null_weight.get(r, np.nan))(region)[:, None]
            by_surface = col(f"ctypav_{b}") + np.nan_to_num(q) * col(f"ctynul_{b}")
            county = np.where(np.isnan(q), county, by_surface)
    else:
        o_t = col("km_scored")
        major, txsec, county = col("km_rt_major"), col("km_rt_txsec"), col("km_rt_county")
    p_def = np.where(major > 0, 1.0,
             np.where(txsec > 0, np.vectorize(lambda r: p.p_txsec.get(r, 0.5))(region)[:, None],
             np.where(county > 0, np.vectorize(lambda r: p.p_county.get(r, 0.5))(region)[:, None],
                      p.q_def_noroute)))
    defined_t = rng.random((n, D)) < p_def
    scale = np.vectorize(lambda r: p.ref_scale.get(r, 1.0))(region)[:, None]
    w_cty = np.vectorize(lambda r: p.w_county_region.get(r, p.w_county))(region)[:, None]
    w_oth = np.vectorize(lambda r: p.w_other_region.get(r, 0.0))(region)[:, None]
    proxy_t = (major + p.w_txsec * txsec + w_cty * county + w_oth * col("km_rt_other")) * scale
    if p.extra_ref is not None:
        add = p.extra_ref(n, D)
        defined_t = defined_t | (add > 0)
        proxy_t = proxy_t + add
    base_t = np.where(proxy_t > 0, proxy_t, p.unrouted_km_if_defined)
    r_t = np.where(defined_t, base_t * np.exp(p.sigma_t * rng.standard_normal((n, D))), 0.0)
    g_t = _gap(o_t, r_t)

    # Building.
    o_b = col("bld_n")
    r_b = np.where(o_b > 0, o_b * np.exp(p.mu_b + p.sigma_b * rng.standard_normal((n, D))), 0.0)
    r_b = np.round(r_b)
    g_b = _gap(o_b, r_b)

    # HIFLD facilities.
    def facility(o_col, lam_true, pi, misfiled=None):
        o = col(o_col)
        m = rng.binomial(o.astype(np.int64) * np.ones((1, D), dtype=np.int64), pi)
        k = rng.poisson(np.maximum(lam_true[:, None] - pi * o, 0.0) * np.ones((1, D)))
        h = m + k
        if misfiled is not None:
            force = (o == 0) & (misfiled > 0) & (rng.random((n, D)) < p.p_misfiled_fire)
            h = np.where(force, np.maximum(h, 1), h)
        return _gap(o, h)

    pop_u = df["pop_urban"].fillna(0).to_numpy(float)
    pop_r = df["pop_rural"].fillna(0).to_numpy(float)
    area = df["area_km2"].to_numpy(float)
    lam_fire = (pop_r * p.fire_per_rural_pop + pop_u * p.fire_per_urban_pop + area * p.fire_per_km2
                + p.fire_anchor * (df["poi_civic"].to_numpy(float) > 0))
    o_ems, o_school = df["poi_ems"].to_numpy(float), df["poi_school"].to_numpy(float)
    lam_ems = p.pi_ems * o_ems + p.kappa_ems * lam["ems"]
    lam_school = p.pi_school * o_school + p.kappa_school * lam["school"]
    if p.fire_evidence == "clean":
        fire_named = col("fire_misfiled_clean") + col("osm_fire_bld") + col("poi_fire_alt")
    else:
        fire_named = col("poi_fire_misfiled") + col("poi_fire_alt")
    g_fire = facility("poi_fire", lam_fire, p.pi_fire, fire_named)
    g_ems = facility("poi_ems", lam_ems, p.pi_ems)
    g_school = facility("poi_school", lam_school, p.pi_school)
    g_hifld = _nanmean_stack(g_fire, g_ems, g_school)

    # CBP establishments.
    o_c = col("poi_n")
    pop = col("pop_total")
    if p.cbp_mode == "county_pop":
        county = df["GEOID"].str[:5]
        tot = df.groupby(county)[["poi_n", "pop_total"]].transform("sum")
        rate = (tot["poi_n"] / tot["pop_total"].where(tot["pop_total"] > 0)).fillna(0).to_numpy()
        prox_c = (rate / p.places_per_est)[:, None] * pop
    else:
        prox_c = np.sqrt(np.maximum(p.est_per_person * pop, 0.5) * np.maximum(o_c / p.places_per_est, 0.5))
    r_c = np.round(prox_c * np.exp(p.sigma_c * rng.standard_normal((n, D))))
    g_cbp = _gap(o_c, r_c)

    g_poi = _nanmean_stack(g_hifld, g_cbp)
    score = _nanmean_stack(g_t, g_b, g_poi)
    score = np.where(np.isnan(score), 0.0, score)  # all-undefined tracts are not scored anyway

    # Exact additive decomposition of each draw's score into component contributions:
    # score = sum_c 1(defined_c) g_c / n_defined, and inside POI the same with halves/types.
    def w(*gs):
        return 1.0 / np.maximum((~np.isnan(np.stack(gs))).sum(axis=0), 1)

    w_top = w(g_t, g_b, g_poi)
    w_half = w(g_hifld, g_cbp)
    w_type = w(g_fire, g_ems, g_school)

    def contrib(g, weight):
        return np.where(np.isnan(g), 0.0, g * weight).mean(axis=1)

    def e(x):
        return np.nanmean(x, axis=1)

    with np.errstate(invalid="ignore"):
        out = pd.DataFrame({
            "GEOID": df["GEOID"].to_numpy(),
            "score": score.mean(axis=1),
            "transport": e(g_t), "building": e(g_b), "poi": e(g_poi),
            "fire": e(g_fire), "ems": e(g_ems), "school": e(g_school), "cbp": e(g_cbp),
            "c_transport": contrib(g_t, w_top),
            "c_building": contrib(g_b, w_top),
            "c_fire": contrib(g_fire, w_top * w_half * w_type),
            "c_ems": contrib(g_ems, w_top * w_half * w_type),
            "c_school": contrib(g_school, w_top * w_half * w_type),
            "c_cbp": contrib(g_cbp, w_top * w_half),
            "p_transport_defined": (~np.isnan(g_t)).mean(axis=1),
            "p_fire_defined": (~np.isnan(g_fire)).mean(axis=1),
            "n_defined": (~np.isnan(np.stack([g_t, g_b, g_poi]))).sum(axis=0).mean(axis=1),
            # Probability mass at the edges of the score, which a linear blend cannot reproduce.
            "p_zero": (score < 1e-9).mean(axis=1),
            "p_transport_one": (g_t > 0.999).mean(axis=1),
            # Further edges (research of 27 October): transport defined at zero, fire gap of 1,
            # and the upper tail of the composite.
            "p_transport_zero": (g_t < 1e-9).mean(axis=1),
            "p_fire_one": (g_fire > 0.999).mean(axis=1),
            "p_score_ge15": (score >= 0.15).mean(axis=1),
            "p_score_ge30": (score >= 0.30).mean(axis=1),
        })
    return out
