"""Figures and numbers of the Best Documentation write-up (writeup/documentation.md).

    python scripts/make_doc_figures.py

Reads only the project's own files: the modelling table, the submitted signal files, submissions/log.csv and
submissions/zindi_scores_final.csv (public and private RMSE of every submission, copied from the Zindi
Submissions tab after the close on 1 November 2026). Writes PNG figures to writeup/figures/ and the numbers
quoted in the text to writeup/figures/doc_numbers.json.
"""
import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from bbx import config  # noqa: E402
from bbx.dataset import load_table  # noqa: E402
from bbx.io import strata_path  # noqa: E402
from bbx.lb_algebra import implied_cov, moments_from_constants  # noqa: E402

OUT = config.ROOT / "writeup" / "figures"
# Reference palette (dataviz skill, light mode): three categorical slots validated all-pairs.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 200, "savefig.bbox": "tight",
})


def scores() -> pd.DataFrame:
    z = pd.read_csv(config.SUBMISSIONS / "zindi_scores_final.csv")
    log = pd.read_csv(config.SUBMISSIONS / "log.csv", dtype=str, keep_default_na=False)
    log = log[log["zindi_id"] != ""][["file", "expected_public_rmse", "submitted_utc", "purpose"]]
    return z.merge(log, on="file", how="left")


def load(df: pd.DataFrame, f: str) -> np.ndarray:
    s = pd.read_csv(config.SUBMISSIONS / f, dtype={"GEOID": str})
    return df[["GEOID"]].merge(s, on="GEOID", how="left")["coverage_gap_score"].to_numpy()


def is_blend(f: str) -> bool:
    return "blend" in f


def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 3.3))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 44)
    boxes = [
        (1, 25, "Challenge data", "Overture 2026-08-19.0\nACS B25001, strata\n(202 files, SHA-256)"),
        (21, 25, "Per-tract features", "DuckDB spatial\n9,794 tracts\nabout 400 columns"),
        (41, 25, "Structural model", "exact organiser\nformula; unknown\nreferences as priors"),
        (61, 25, "Signals", "74 files, each with\na logged expected\nRMSE and SHA-256"),
        (81, 25, "Zindi public RMSE", "one number per file\n= its covariance\nwith the hidden truth"),
        (81, 2, "Ridge blend", "60 measured signals\nclosed-form weights\n(no labels needed)"),
        (61, 2, "Formula rules", "clip to [0, 1]\nempty water\ntracts = 1"),
        (41, 2, "Final submission", "f2 = Zindi 8DPgZvCX\npublic 0.05751\nprivate 0.05871"),
    ]
    for x, y, title, body in boxes:
        final = title == "Final submission"
        ax.add_patch(FancyBboxPatch((x, y), 17.5, 16, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc="#eaf1fb" if final else "white", ec=BLUE if final else AXIS, lw=1.2))
        ax.text(x + 8.75, y + 13, title, ha="center", va="center", fontsize=8.6, weight="bold", color=INK)
        ax.text(x + 8.75, y + 6.2, body, ha="center", va="center", fontsize=7, color=INK2, linespacing=1.35)
    arrows = [((18.9, 33), (20.6, 33)), ((38.9, 33), (40.6, 33)), ((58.9, 33), (60.6, 33)), ((78.9, 33), (80.6, 33)),
              ((89.75, 24.6), (89.75, 18.6)), ((80.6, 10), (78.9, 10)), ((60.6, 10), (58.9, 10))]
    for a, b in arrows:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=9, color=INK2, lw=1))
    ax.add_patch(FancyArrowPatch((69.75, 24.6), (82, 18.6), arrowstyle="-|>", mutation_scale=9, color=MUTED, lw=0.8,
                                 linestyle=(0, (3, 2)), connectionstyle="arc3,rad=0.25"))
    ax.text(73.2, 19.6, "the files", fontsize=6.6, color=MUTED, rotation=-24)
    ax.text(1, 43, "Two constants give the target's public mean and sd exactly; every later file gives one covariance.",
            fontsize=7.4, color=INK2)
    fig.savefig(OUT / "fig1_pipeline.png")
    plt.close(fig)


def measured_correlations(df: pd.DataFrame, sc: pd.DataFrame) -> pd.DataFrame:
    """Correlation of each signal with the truth, implied by its public and by its private RMSE."""
    g = sc.set_index("file")
    m_pub, s_pub = moments_from_constants(0, g.loc["s01_const_000.csv", "public_rmse"],
                                          0.1, g.loc["s02_const_010.csv", "public_rmse"])
    m_pri, s_pri = moments_from_constants(0, g.loc["s01_const_000.csv", "private_rmse"],
                                          0.1, g.loc["s02_const_010.csv", "private_rmse"])
    wa = (df["region"] == "eastern-wa").to_numpy()
    # Private set: 70 % of the four regions plus all 415 eastern-wa tracts (Section 8); weights reproduce that mix.
    w_pri = np.where(wa, 1.0, 0.7)
    w_pri = w_pri / w_pri.sum()
    rows = []
    for f in sc["file"]:
        if f.startswith(("s01_", "s02_")) or "probe" in f:
            continue
        p = load(df, f)
        q = p[~wa]
        if q.std() < 1e-9:  # the eastern-wa indicator s31 is constant on the public regions
            continue
        rho_pub = implied_cov(q, g.loc[f, "public_rmse"], m_pub, s_pub) / (q.std() * s_pub)
        mu = (w_pri * p).sum()
        var = (w_pri * (p - mu) ** 2).sum()
        cov = (var + s_pri**2 + (mu - m_pri) ** 2 - g.loc[f, "private_rmse"] ** 2) / 2
        rows.append((f, rho_pub, cov / (np.sqrt(var) * s_pri)))
    return pd.DataFrame(rows, columns=["file", "rho_public", "rho_private"]), (m_pub, s_pub, m_pri, s_pri)


def fig_correlations(mc: pd.DataFrame) -> dict:
    fig, ax = plt.subplots(figsize=(4.4, 4.0))
    sig = mc[~mc["file"].map(is_blend)]
    bl = mc[mc["file"].map(is_blend)]
    ax.plot([-0.3, 0.9], [-0.3, 0.9], color=AXIS, lw=1, zorder=1)
    ax.scatter(sig["rho_public"], sig["rho_private"], s=22, color=BLUE, edgecolor="white", lw=0.8, zorder=3,
               label=f"signals ({len(sig)})")
    ax.scatter(bl["rho_public"], bl["rho_private"], s=40, color=ORANGE, edgecolor="white", lw=0.8, zorder=4,
               label=f"blends ({len(bl)})")
    offsets = {"s16": (-24, 4), "s111": (-30, 4), "f2": (8, -10), "f5": (-6, 9)}
    for _, r in bl.iterrows():
        name = r["file"].split("_")[0]
        ax.annotate(name, (r["rho_public"], r["rho_private"]), xytext=offsets.get(name, (6, 4)),
                    textcoords="offset points", fontsize=7, color=INK2)
    ax.set_xlabel("correlation with the truth implied by the public RMSE (30 %)")
    ax.set_ylabel("implied by the private RMSE (70 %)")
    ax.set_xlim(-0.3, 0.9)
    ax.set_ylim(-0.3, 0.9)
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)
    r = np.corrcoef(sig["rho_public"], sig["rho_private"])[0, 1]
    ax.text(0.88, -0.27, f"r = {r:.3f} over the signals", ha="right", fontsize=7.5, color=INK2)
    fig.savefig(OUT / "fig2_public_private_correlation.png")
    plt.close(fig)
    d = sig["rho_private"] - sig["rho_public"]
    return {"corr_rho_pub_priv": round(float(r), 4), "rho_diff_sd": round(float(d.std()), 4),
            "rho_diff_mean": round(float(d.mean()), 4), "n_signals": int(len(sig))}


def fig_public_private(sc: pd.DataFrame) -> dict:
    s = sc[~sc["file"].str.contains("probe") & ~sc["file"].str.startswith(("s01_", "s02_"))]
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4), gridspec_kw={"width_ratios": [1, 1]})
    for ax, (lo, hi) in zip(axes, [(0.054, 0.0915), (0.0555, 0.0625)]):
        ax.plot([lo, hi], [lo, hi], color=AXIS, lw=1, zorder=1)
        sig = s[~s["file"].map(is_blend) & ~s["file"].str.startswith("f")]
        bl = s[s["file"].map(is_blend)]
        ax.scatter(sig["public_rmse"], sig["private_rmse"], s=18, color=BLUE, edgecolor="white", lw=0.7, zorder=3,
                   label="single signals")
        ax.scatter(bl["public_rmse"], bl["private_rmse"], s=36, color=ORANGE, edgecolor="white", lw=0.8, zorder=4,
                   label="blends")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("public RMSE")
    for _, r in s[s["file"].map(is_blend)].iterrows():
        name = r["file"].split("_")[0]
        label = {"f2": "f2 (final)", "f5": "f5 (after the close)", "s111": "s111 (2nd selection)"}.get(name, name)
        if r["public_rmse"] < 0.0625:
            axes[1].annotate(label, (r["public_rmse"], r["private_rmse"]), xytext=(6, -3), textcoords="offset points",
                             fontsize=7.5, color=INK2)
    axes[0].set_ylabel("private RMSE")
    axes[0].legend(frameon=False, loc="upper left", fontsize=7.5)
    axes[0].set_title(f"all {len(s)} scored files (constants and probe left out)", fontsize=8.5, color=INK2, loc="left")
    axes[1].set_title("the blends", fontsize=8.5, color=INK2, loc="left")
    fig.savefig(OUT / "fig3_public_private_rmse.png")
    plt.close(fig)
    gap = (s["private_rmse"] - s["public_rmse"])
    return {"pub_priv_rank_corr": round(float(s["public_rmse"].rank().corr(s["private_rmse"].rank())), 4),
            "mean_priv_minus_pub": round(float(gap.mean()), 5)}


def fig_timeline(sc: pd.DataFrame) -> None:
    s = sc[~sc["file"].str.contains("probe") & sc["submitted_utc"].notna() & (sc["submitted_utc"] != "")].copy()
    s["date"] = pd.to_datetime(s["submitted_utc"].str[:10])
    s = s.sort_values("date")
    days = pd.date_range("2026-10-16", "2026-10-31")
    pub = [s.loc[s["date"] <= d, "public_rmse"].min() for d in days]
    pri = [s.loc[s["date"] <= d, "private_rmse"].min() for d in days]
    fig, ax = plt.subplots(figsize=(7.6, 3.0))
    ax.step(days, pub, where="post", color=BLUE, lw=2, label="best public RMSE so far")
    ax.step(days, pri, where="post", color=ORANGE, lw=2, label="best private RMSE so far (hidden until the close)")
    notes = [("2026-10-16", 0.0825, "strata prior s03"), ("2026-10-18", 0.0782, "first blend s16"),
             ("2026-10-23", 0.0743, "transport v3 (s77)"), ("2026-10-25", 0.0665, "transport v7 (s97)"),
             ("2026-10-26", 0.0600, "blend s111"), ("2026-10-31", 0.0575, "final f2")]
    for d, y, t in notes:
        ax.annotate(t, (pd.Timestamp(d), y), xytext=(4, 6), textcoords="offset points", fontsize=7.2, color=INK2)
    ax.set_ylabel("RMSE")
    ax.set_ylim(0.054, 0.09)
    ax.legend(frameon=False, loc="upper right", fontsize=7.5)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    fig.savefig(OUT / "fig4_timeline.png")
    plt.close(fig)


def fig_maps(df: pd.DataFrame) -> dict:
    pred = df[["GEOID", "region"]].assign(score=load(df, "f2_blend_ridge0005_with_s07_s22.csv"))
    cmap = LinearSegmentedColormap.from_list("blue", RAMP)
    regions = [("south-central-tx", "South-Central Texas\n6,003 tracts"), ("maricopa-az", "Maricopa County AZ\n1,593"),
               ("eastern-ok", "Eastern Oklahoma\n1,192"), ("northern-ca", "Northern California\n591"),
               ("eastern-wa", "Eastern Washington\n415 (private only)")]
    fig, axes = plt.subplots(1, 5, figsize=(7.8, 2.6), gridspec_kw={"width_ratios": [1.25, 1, 1.15, 0.8, 1.15]})
    for ax, (r, title) in zip(axes, regions):
        g = gpd.read_parquet(strata_path(r, "census-tracts"), columns=["GEOID", "geometry"]).merge(pred, on="GEOID")
        g = g.set_crs("OGC:CRS84", allow_override=True).to_crs(5070)
        g.plot(column="score", ax=ax, cmap=cmap, vmin=0, vmax=0.3, linewidth=0.05, edgecolor="white")
        ax.set_axis_off()
        ax.set_title(title, fontsize=6.8, color=INK2)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 0.3))
    cb = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.05, pad=0.04, aspect=50)
    cb.set_label("predicted coverage-gap score (f2); values above 0.3 shown at 0.3", fontsize=7, color=INK2)
    cb.ax.tick_params(labelsize=6.5)
    fig.savefig(OUT / "fig6_maps_f2.png")
    plt.close(fig)
    return {"f2_mean_by_region": pred.groupby("region")["score"].mean().round(4).to_dict()}


def fig_families(costs: dict) -> None:
    items = sorted(costs.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(6.4, 2.4))
    y = np.arange(len(items))
    ax.barh(y, [v for _, v in items], color=BLUE, height=0.6)
    ax.set_yticks(y, [k for k, _ in items], fontsize=7.8, color=INK)
    for i, (_, v) in enumerate(items):
        ax.text(v + 0.0002, i, f"+{v:.4f}", va="center", fontsize=7.4, color=INK2)
    ax.set_xlabel("expected public RMSE added by removing the family from f2 (0.0550)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(costs.values()) * 1.18)
    fig.savefig(OUT / "fig5_family_costs.png")
    plt.close(fig)


FAMILIES = {
    "transport (17)": ["s06", "s17", "s18", "s77", "s78", "s81", "s82", "s83", "s84", "s97", "s98", "s101", "s102",
                       "s106", "s140", "s146", "s147"],
    "fire stations (15)": ["s05", "s14", "s19", "s20", "s39", "s40", "s92", "s95", "s100", "s103", "s107", "s108",
                           "s109", "s134", "s136"],
    "establishments and places (10)": ["s07", "s24", "s25", "s29", "s36", "s37", "s38", "s42", "s43", "s86"],
    "composite and its edges (3)": ["s04", "s79", "s117"],
    "road history, EMS, schools, burns (5)": ["s08", "s22", "s30", "s34", "s93"],
    "strata and region offsets (5)": ["s03", "s09", "s10", "s31", "s32"],
    "buildings (6)": ["s13", "s26", "s27", "s28", "s41", "s80"],
}


def family_costs(df: pd.DataFrame) -> tuple[dict, dict]:
    spec = importlib.util.spec_from_file_location("make_finals", config.ROOT / "scripts" / "make_finals.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    files = [f for f in mf.basis_files() if f not in mf.WEAK]
    _, e0, _, _ = mf.fit_without_wa(df, files, 0.005)
    costs, alone = {}, {}
    for name, keys in FAMILIES.items():
        rest = [f for f in files if f.split("_")[0] not in keys]
        own = [f for f in files if f.split("_")[0] in keys]
        costs[name] = mf.fit_without_wa(df, rest, 0.005)[1] - e0
        alone[name] = mf.fit_without_wa(df, own, 0.005)[1]
    return costs, {"f2_expected": round(e0, 6), "family_alone": {k: round(v, 5) for k, v in alone.items()},
                   "family_cost": {k: round(v, 5) for k, v in costs.items()}}


def scorecard(df: pd.DataFrame) -> dict:
    """Disparity ratios of our own predictions, computed as the Zindi scoring rubric does (mean score by stratum
    over all 9,794 rows; f2 gives rural/urban 2.25 and tribal 2.71, the values shown on Zindi)."""
    from bbx.io import read_strata

    st = read_strata()[["GEOID", "ur_class", "tribal_any", "svi_overall", "cvi_overall", "usfs_WHP_mean",
                        "epht_heat_days_summer", "usdm_summer_dsci"]]
    d = df[["GEOID", "region"]].merge(st, on="GEOID", how="left").assign(f2=load(df, "f2_blend_ridge0005_with_s07_s22.csv"))
    out = {}
    m = d.groupby("ur_class")["f2"].mean()
    out["rural_urban"] = round(m["Rural"] / m["Urban"], 3)
    t = d.groupby("tribal_any")["f2"].mean()
    out["tribal"] = round(t[True] / t[False], 3)
    for col, name in [("svi_overall", "svi"), ("cvi_overall", "cvi"), ("usfs_WHP_mean", "wildfire"),
                      ("epht_heat_days_summer", "heat"), ("usdm_summer_dsci", "drought")]:
        q = pd.qcut(d[col].rank(method="first"), 4, labels=False)
        g = d.groupby(q)["f2"].mean()
        out[f"{name}_q4_over_q1"] = round(g.iloc[3] / g.iloc[0], 3)
    within = {}
    for r, sub in d[d["region"] != "eastern-wa"].groupby("region"):
        mm = sub.groupby("ur_class")["f2"].mean()
        within[r] = round(mm.get("Rural", np.nan) / mm.get("Urban", np.nan), 3)
    out["rural_urban_within_region"] = within
    rural_share = d[d["ur_class"] == "Rural"]["region"].value_counts(normalize=True).round(3).to_dict()
    out["rural_tracts_by_region"] = rural_share
    out["f2_sd"] = round(float(d["f2"].std(ddof=0)), 4)
    out["f2_share_ge_0_8"] = round(float((d["f2"] >= 0.8).mean()), 5)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_table()
    sc = scores()
    numbers = {}
    fig_pipeline()
    mc, moments = measured_correlations(df, sc)
    numbers["moments"] = dict(zip(["m_public", "s_public", "m_private", "s_private"], [round(x, 6) for x in moments]))
    numbers["correlations"] = fig_correlations(mc)
    mc.round(4).to_csv(OUT / "measured_correlations.csv", index=False)
    numbers.update(fig_public_private(sc))
    fig_timeline(sc)
    numbers.update(fig_maps(df))
    costs, fam = family_costs(df)
    numbers.update(fam)
    fig_families(costs)
    numbers["scorecard_f2"] = scorecard(df)
    (OUT / "doc_numbers.json").write_text(json.dumps(numbers, indent=1, default=float), encoding="utf-8")
    print(json.dumps(numbers, indent=1, default=float))


if __name__ == "__main__":
    main()
