"""Last day (31 October): record the three last scores, apply the WEAK rule, build and check the finals.

    python scripts/finalize_31.py s146_t7lf_c_transport_delta.csv=ID1:0.0xxxxxxxx \
                                  s142_t10s_c_transport_delta.csv=ID2:0.0xxxxxxxx \
                                  s147_t7linv_c_transport_delta.csv=ID3:0.0xxxxxxxx

1. Records each Zindi id and public RMSE (bbx.submit.record).
2. Refits the finals blend (four regions, ridge 0.005, WEAK and s07/s22 out) and prints, for each new
   signal, its implied correlation and its removal cost.
3. A new signal whose removal cost is below 0.00003 joins WEAK (decision D1-quater): the WEAK set in
   scripts/make_finals.py is rewritten with it.
4. Runs scripts/make_finals.py (f1-f3 and their weights) and checks f1 and f2, the pair to upload and
   select: header, 9,794 rows, no missing value, values in [0, 1], SHA-256 equal to the submission log.
"""
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from bbx import blend, config, submit
from bbx.dataset import load_table
from bbx.lb_algebra import implied_cov
from bbx.signals import M_PUBLIC as m, S_PUBLIC as s

THRESHOLD = 0.00003
FINALS_SCRIPT = Path(__file__).with_name("make_finals.py")


def finals_module():
    spec = importlib.util.spec_from_file_location("make_finals", FINALS_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fit(files, sig, nw, ridge=0.005):
    P = blend.load_predictions(files)[nw]
    live = P.std(0) > 1e-9
    files = [f for f, k in zip(files, live) if k]
    P = P[:, live]
    Pc = P - P.mean(0)
    c = np.array([implied_cov(P[:, i], float(sig.loc[f, "public_rmse"]), m, s) for i, f in enumerate(files)])
    C = Pc.T @ Pc / len(P)
    w = np.linalg.solve(C + ridge * np.diag(np.diag(C)), c)
    return files, float(np.sqrt(max(s**2 - 2 * w @ c + w @ C @ w, 0)))


def main(args: list[str]) -> None:
    new = {}
    for a in args:
        f, rest = a.split("=")
        zid, rmse = rest.split(":")
        submit.record(f, zid, float(rmse), "2026-10-31")
        new[f] = float(rmse)
    df = load_table()
    nw = (df["region"] != "eastern-wa").to_numpy()
    sig = blend.scored_signals().set_index("file")
    mf = finals_module()
    allf = [f for f in sig.index if "blend" not in f and f not in mf.EXCLUDED and f not in mf.WEAK]
    files, e1 = fit(allf, sig, nw)
    _, e0 = fit([f for f in allf if f not in new], sig, nw)
    print(f"finals blend: {e0:.5f} before the 31/10 lot, {e1:.5f} with it ({e1 - e0:+.5f})")
    # A score typed wrong (or one the other measured signals cannot produce) makes the covariance system
    # inconsistent and the blend collapses towards 0; stop before WEAK and the finals are rewritten.
    if not 0.050 < e1 <= e0 + 0.0005:
        raise SystemExit(f"blend RMSE {e1:.5f} is implausible: check the id:rmse typed, then rerun (record overwrites)")
    weak = []
    for f, r in new.items():
        x = blend.load_predictions([f])[nw][:, 0]
        _, ei = fit([g for g in allf if g != f], sig, nw)
        print(f"  {f:36s} rmse {r:.9f}  implied corr {implied_cov(x, r, m, s) / (x.std() * s):+.3f}  removal cost {ei - e1:+.5f}")
        if ei - e1 < THRESHOLD:
            weak.append(f)
    if weak:
        text = FINALS_SCRIPT.read_text(encoding="utf-8")
        start = text.index("WEAK = {")
        end = text.index("}", start)  # the set holds file names only, so its first closing brace ends it
        at = text.rindex("\n", start, end) + 1  # start of the line that closes the set
        extra = "".join(f'        "{f}",  # removal cost < 0.00003 on 31/10\n' for f in weak)
        FINALS_SCRIPT.write_text(text[:at] + extra + text[at:], encoding="utf-8")
        print("added to WEAK:", weak)
    subprocess.run([sys.executable, str(FINALS_SCRIPT)], check=True)
    log = pd.read_csv(config.SUBMISSIONS / "log.csv", dtype=str, keep_default_na=False).drop_duplicates("file", keep="last").set_index("file")
    for name in ("f1_blend_ridge0005.csv", "f2_blend_ridge0005_with_s07_s22.csv"):
        path = config.SUBMISSIONS / name
        d = pd.read_csv(path, dtype={"GEOID": str})
        ok = (list(d.columns) == ["GEOID", "coverage_gap_score"] and len(d) == 9794 and d.isna().sum().sum() == 0
              and d["coverage_gap_score"].between(0, 1).all()
              and hashlib.sha256(path.read_bytes()).hexdigest() == log.loc[name, "sha256"])
        print(f"{name}: {'OK' if ok else 'PROBLEM'}  mean {d['coverage_gap_score'].mean():.4f}")
    print("upload and select: f1_blend_ridge0005.csv and f2_blend_ridge0005_with_s07_s22.csv")


if __name__ == "__main__":
    main(sys.argv[1:])
