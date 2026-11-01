"""Queue for 23 October (4 signals now; the 5th slot is blend_v2, built after the 22 Oct scores).

s32_region_ca (already written), s35_whp_log (already written),
s44_blend_tail_hinge: max(z - 2, 0) with z the standardised 27-signal blend (ridge 0.02) of
    21 October -- lets the final blend steepen the tail (4.3 % of tracts),
s45_school0_nbr300: no Overture school in the tract but one within ~300 m across its boundary.
The weights behind z are saved to submissions/blend27_weights.json for reproducibility.
"""
import json

import numpy as np

from bbx import blend, config
from bbx.candidates_extra import build as build_extra
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
sig = blend.scored_signals()
basis = [f for f in sig["file"] if not f.startswith("s16") and f[:3] not in ("s39", "s40", "s41", "s42", "s43")]
b = blend.fit(basis, ridge=0.02, rules=False)
(config.SUBMISSIONS / "blend27_weights.json").write_text(
    json.dumps({"files": b.files, "weights": b.weights.tolist(), "ridge": 0.02}, indent=1), encoding="utf-8")
z = (b.prediction - b.prediction.mean()) / b.prediction.std()

ex = df[["GEOID"]].merge(build_extra(), on="GEOID", how="left")
feat = df.merge(__import__("pandas").read_parquet(config.FEATURES / "features_extra.parquet"), on="GEOID", how="left")
school0_nbr = ((feat["poi_school"] == 0) & (feat["school_out_300m"].fillna(0) > 0)).astype(float)

for name, sigv, rho, purpose in [
    ("s44_blend_tail_hinge", np.maximum(z - 2, 0), 0.10, "tail hinge max(z-2,0) of the 27-signal blend of 21 Oct"),
    ("s45_school0_nbr300", school0_nbr.to_numpy(), 0.03,
     "no Overture school in the tract but one within ~300 m across its boundary"),
]:
    path, exp = write_signal(df, np.asarray(sigv, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = ["s32_region_ca", "s35_whp_log", "s44_blend_tail_hinge", "s45_school0_nbr300", "s46_blend_v2 (prepared on 22 Oct)"]
(config.SUBMISSIONS / "upload_2026-10-23.txt").write_text(
    "\n".join(f"{i}. {f}.csv" if "prepared" not in f else f"{i}. {f}" for i, f in enumerate(files, 1)) + "\n",
    encoding="utf-8")
print(files)
