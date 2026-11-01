"""Final candidates for 30 October: blends of every measured signal, three ridge strengths.

    python scripts/make_finals.py --dry-run     # print expected public RMSEs only, write nothing
    python scripts/make_finals.py               # write submissions/f1..f3 and their weights
                                                # (four scored regions by default since 30 October)

Each blend uses every scored signal except earlier blends and the two constants (decision
D1-quater: at most 73 measured signals, continuous, ridge-weighted), applies the formula rule for
the two empty water tracts (bbx.postprocess), and stores its weights in
submissions/final_<name>_weights.json. The expected public RMSE is in-sample on the public 30 %.

Expected private RMSE (research of 25 October, round 14). The public covariances are
c_pub = c + e with e of covariance S_e = sigma^2 C / n_public (sigma = blend residual). For
w = (C + ridge D)^-1 c_pub the private MSE averages to
s^2 - 2 tr(A cc') + tr(A C A cc') + tr(A C A S_e), with cc' estimated by c_pub c_pub' - S_e.
With 47 signals this gives 0.0600 at ridge 0, 0.0609 at 0.05 and 0.0615 at 0.10: the bias
added by ridge outweighs the covariance noise. Decision D1-ter keeps every weight regularised,
so the two to select are ridge 0.005 and 0.01 (0.06005 and 0.06019, against 0.05997 at 0).

Diagnostic of 26 October. (1) The noise of a public covariance scales with the full spread of
the target, not only the blend residual: S_e[i, j] = E[p_i p_j r2] / n_public with
r2 = (yhat - m)^2 + sigma^2(yhat); with heavy-tailed signals the private estimate is about
0.063, not 0.060 (the in-sample public figure stays about 0.059). (2) s07 and s22 are extreme on
the two empty water tracts (score 1 by the formula): if those tracts are public they make up to
11 times the measured covariance, and the s07 weight changes sign. Both are left out of the
finals (expected 0.06070 against 0.06080 over the membership scenarios, worst case 0.0629
against 0.0645); new signals give those tracts m (bbx.signals.write_signal).

Hedged pair (27 October). Over the four membership scenarios, the better of f1 (without s07/s22)
and f2 (with them) averages 0.05959, against 0.05988 for two ridge steps of the same recipe: f2
wins (0.0582) when neither water tract is public, f1 otherwise. Select f1 and f2.

Weak recent signals (29 October). Eight signals of the 28 and 29 October lots brought almost
nothing on the public set (removal cost 0 to 0.00007 each): s119, s125-s128, s112, s113, s133.
End-to-end simulation (audit C2 style, 40 synthetic truths on the four scored regions): if they
carry no information beyond the older signals, keeping them costs +0.00022 of private RMSE; if
they carry exactly what the public measured, dropping them costs nothing (-0.00002). They are
left out of every final; s134 and s136 stay. A generic pruning of all weak signals by public
removal cost changes nothing (+/-0.00001), so it is not applied.

Ridge towards the structural model (30 October, round 85). Ridge towards zero is best at 0.005 for
the expected private RMSE; pulling the weights instead towards kappa x the weights that reproduce the
structural composite v9L (scripts/make_structural_v9L.py, prediction-only, kappa fitted on the measured
covariances) improves it as the ridge grows, up to about 0.3-0.5 (f1-type: 0.06193 -> 0.06149; f2-type:
0.06174 -> 0.06114). The gain depends on the noise level of the measured covariances: with half the
modelled noise the ridge-0.005 blend is better (0.05953 against 0.06007), with 1.5 times it the prior
blend wins by 0.0014.
End-to-end simulation (round 86: 80 truths drawn around the blend with the measured-covariance
uncertainty, heavy-tailed residual, random 30 % public split, covariances re-derived from simulated
public RMSEs) rejects it: actual private 0.04645 at ridge 0.005 towards zero, 0.04762 at 0.3 towards
v9L (better in 5 % of the truths); the real public-to-private loss is about 0.001, far below the
formula's, so there is little overfitting to shrink. Ridge 0.001-0.005 towards zero is best
(0.04642-0.04645). The pair to select stays f1 + f2.
"""
import argparse
import json

import numpy as np
import pandas as pd

from bbx import blend, config, submit
from bbx.dataset import load_table
import re

from bbx.lb_algebra import implied_cov
from bbx.postprocess import apply_formula_rules
from bbx.signals import M_PUBLIC, S_PUBLIC

N_PUBLIC = 2814  # 30 % of the 9,379 tracts of the four scored regions (eastern-wa is not scored)
# name: (ridge, keep s07/s22, ridge target). Zindi scores the better of the two selected files on the
# private set, so the pair should differ where we are unsure. f4 pulls the weights towards the
# structural composite v9L instead of towards zero (research of 30 October, round 85).
FINALS = {"f1_blend_ridge0005": (0.005, False, None), "f2_blend_ridge0005_with_s07_s22": (0.005, True, None),
          "f3_blend_ridge001": (0.01, False, None)}
# Finals that keep the WEAK signals (round 86: the calibrated end-to-end simulation finds them neutral to
# slightly useful, the expected-private formula harmful). f1 keeps them so that f1 and f2 also cover that
# disagreement (user: do the best for the private score, 30/10).
KEEP_WEAK: set[str] = {"f1_blend_ridge0005"}
# A ridge target is supported (third field: an interim composite, e.g. "structural_v9L.parquet"); the f4
# recipe was dropped after the end-to-end simulation of round 86 (see the module docstring).
MAX_SIGNALS = 74  # D1-quinquies (31/10, plan B: s150 then f2 alone)
EXCLUDED = {"s07_c_cbp.csv", "s22_no_ems_place.csv"}  # driven by the two water tracts (diagnostic of 26/10)
WEAK = {"s119_ems_station_nofire.csv", "s125_t7_c_transport_houston.csv", "s126_t7_c_transport_phoenix.csv",
        "s127_t7_c_transport_sanantonio.csv", "s128_t7_c_transport_austin.csv", "s112_t7_p_one_tx.csv",
        "s113_t7_p_one_ok.csv", "s133_t8_c_fire_bigmetros.csv",  # no public gain, noise on the private set (29/10)
        "s143_t9_fire_gapfill.csv", "s138_t9_p_zero_delta.csv",  # removal cost < 0.00003 on 30/10
        "s137_t9_p_score_ge30_delta.csv",  # 0.00002 once s138 and s143 are out (30/10)
        "s142_t10s_c_transport_delta.csv",  # removal cost < 0.00003 on 31/10
        "s150_t9lfi_p_score_ge30_delta.csv",  # removal cost < 0.00003 on 31/10
        }


def basis_files() -> list[str]:
    sig = blend.scored_signals()
    files = [f for f in sig["file"] if "blend" not in f]
    if len(files) > MAX_SIGNALS:
        raise SystemExit(f"{len(files)} measured signals exceed the D1-quinquies limit of {MAX_SIGNALS}")
    return files


def prior_weights(Pc: np.ndarray, C: np.ndarray, c: np.ndarray, prior: np.ndarray | None) -> np.ndarray:
    """Ridge target: kappa x the weights that best reproduce the structural composite from the signals
    (prediction-only), kappa fitted to the measured covariances; zero without a prior."""
    if prior is None:
        return np.zeros(len(c))
    w0 = np.linalg.solve(C + 1e-6 * np.diag(np.diag(C)), Pc.T @ (prior - prior.mean()) / len(prior))
    return (w0 @ c) / (w0 @ C @ w0) * w0


def expected_private_rmse(files: list[str], ridge: float, sigma2: float, yhat: np.ndarray, scored: np.ndarray,
                          prior: np.ndarray | None = None) -> float:
    """Expected private RMSE on the scored tracts only (`scored`: the four regions; eastern-wa is not scored).

    With a ridge target w0 the weights are A (c_pub + ridge D w0) = A c_pub + b, which adds
    -2 b'c + 2 b'C A c + b'C b to the error (w0 is fitted once and treated as fixed)."""
    sig = blend.scored_signals().set_index("file").loc[files]
    P = blend.load_predictions(files)[scored]
    live = P.std(axis=0) > 1e-9
    sig, P, yhat = sig[live], P[:, live], yhat[scored]
    c = np.array([implied_cov(P[:, i], float(r), M_PUBLIC, S_PUBLIC) for i, r in enumerate(sig["public_rmse"])])
    Pc = P - P.mean(axis=0)
    C = Pc.T @ Pc / len(P)
    # Spread of the target around its mean, tract by tract: explained part plus a residual that
    # grows with the prediction (skewed target).
    r2 = (yhat - M_PUBLIC) ** 2 + sigma2 * (0.25 + yhat) / (0.25 + yhat).mean()
    S_e = (Pc * r2[:, None]).T @ Pc / len(P) / N_PUBLIC
    cc = np.outer(c, c) - S_e
    D = np.diag(np.diag(C))
    A = np.linalg.inv(C + ridge * D)
    ACA = A @ C @ A
    b = ridge * A @ D @ prior_weights(Pc, C, c, None if prior is None else prior[scored])
    mse = (S_PUBLIC**2 - 2 * (np.trace(A @ cc) + b @ c) + np.trace(ACA @ cc) + np.trace(ACA @ S_e)
           + 2 * b @ C @ A @ c + b @ C @ b)
    return float(np.sqrt(max(mse, 0.0)))


# Region-specific copies (s81-s84, s107-s110, s112-s115, region offsets): their weights say nothing
# about a region absent from the public set.
REGIONAL = re.compile(r"region_|_t3_(tx|az|ok|ca)\.csv|c_transport_tx|_fire_(ok|az|ca|wa)\.csv|p_one_(tx|ok|az|ca)\.csv")


def fit_without_wa(df: pd.DataFrame, files: list[str], ridge: float,
                   prior: np.ndarray | None = None) -> tuple[np.ndarray, float, list[str], np.ndarray]:
    """Blend for the case where eastern-wa is not in the public set (probe s124 = s).

    Covariances and signal moments are then those of the four public regions, so the weights are
    fitted on those tracts only; eastern-wa tracts get a blend without region-specific signals,
    whose weights carry over from the other regions instead of the near-zero eastern-wa terms.
    """
    sig = blend.scored_signals().set_index("file")
    wa = (df["region"] == "eastern-wa").to_numpy()
    out = np.full(len(df), np.nan)
    expected = np.nan
    for first, (subset, mask) in enumerate([(files, ~wa), ([f for f in files if not REGIONAL.search(f)], wa)]):
        P = blend.load_predictions(subset)
        # Signals constant on the public regions (the eastern-wa indicator s31) carry nothing there.
        live = P[~wa].std(axis=0) > 1e-9
        subset = [f for f, keep in zip(subset, live) if keep]
        P = P[:, live]
        Pn = P[~wa]
        c = np.array([implied_cov(Pn[:, i], float(sig.loc[f, "public_rmse"]), M_PUBLIC, S_PUBLIC) for i, f in enumerate(subset)])
        mu = Pn.mean(axis=0)
        C = (Pn - mu).T @ (Pn - mu) / len(Pn)
        D = np.diag(np.diag(C))
        target = prior_weights(Pn - mu, C, c, None if prior is None else prior[~wa])
        w = np.linalg.solve(C + ridge * D, c + ridge * D @ target)
        out[mask] = M_PUBLIC + (P[mask] - mu) @ w
        if first == 0:
            expected = float(np.sqrt(max(S_PUBLIC**2 - 2 * w @ c + w @ C @ w, 0.0)))
            used_files, used_weights = subset, w
    return apply_formula_rules(df, np.clip(out, 0, 1)), expected, used_files, used_weights


def main(dry_run: bool, include_wa: bool = False) -> None:
    """Finals fitted on the four scored regions (default since the audit of 30 October): eastern-wa is
    neither public (probe s124) nor private (Info page), so its tracts must not enter the moments."""
    df = load_table()
    scored = (df["region"] != "eastern-wa").to_numpy()
    every = basis_files()
    print(f"{len(every)} measured signals")
    for name, (ridge, keep, target) in FINALS.items():
        files = [f for f in (every if keep else [f for f in every if f not in EXCLUDED]) if name in KEEP_WEAK or f not in WEAK]
        k = len(files)
        prior = None
        if target:
            prior = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / target), on="GEOID", how="left")["score"].to_numpy()
        b0 = blend.fit(files, ridge=0.0, rules=False)
        private_rmse = expected_private_rmse(files, ridge, b0.expected_rmse ** 2, b0.prediction, scored, prior)
        if include_wa:  # legacy: moments over all 9,794 rows
            if prior is not None:
                raise SystemExit("--include-wa does not support a ridge target")
            b = blend.fit(files, ridge=ridge, rules=True)
            pred, exp_pub, used_files, used_weights = b.prediction, b.expected_rmse, b.files, b.weights
        else:
            pred, exp_pub, used_files, used_weights = fit_without_wa(df, files, ridge, prior)
        print(f"{name}: {k} signals, ridge {ridge:.3f}{' towards ' + target if target else ''}  expected public {exp_pub:.5f}  "
              f"expected private {private_rmse:.5f}  mean (4 regions) {pred[scored].mean():.4f}")
        if dry_run:
            continue
        submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": pred}), name, exp_pub,
                     f"final blend of {k} measured signals, ridge {ridge}{' towards ' + target if target else ''}, "
                     "formula rules, four scored regions")
        (config.SUBMISSIONS / f"final_{name}_weights.json").write_text(
            json.dumps({"files": list(used_files), "weights": np.asarray(used_weights).tolist(), "ridge": ridge,
                        "ridge_target": target, "fitted_on": "all 9,794 rows" if include_wa else "four scored regions"},
                       indent=1), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--wa-not-public", action="store_true", help="kept for compatibility: this is now the default")
    ap.add_argument("--include-wa", action="store_true", help="legacy fit with moments over all 9,794 rows")
    a = ap.parse_args()
    main(a.dry_run, a.include_wa)
