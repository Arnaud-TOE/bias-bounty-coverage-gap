"""Queue for 25 October, after the 24 October scores (blend 42 signals: rho 0.673, expected 0.0658).

The regional transport copies showed that OK, AZ and CA transport gaps are larger than v3 says
(blend weights 1.9 / 1.5 / 1.4 against 0.8 for TX). Linear re-weighting is now in the span; the
candidates below add what a linear blend cannot build (component-level gaps, threshold masses)
and screen as novel on the 42-signal basis (R2 in brackets):

s88_t3_transport_gap: v3 expected transport gap per tract, not divided by the number of defined
    components [0.67],
s89_p_transport_one: v3 probability that the transport gap is exactly 1 (TIGER highway, no
    Overture scored road: edge-only tracts, routes classed below secondary) [0.14],
s90_blend_x_pzero: the 42-signal blend (ridge 0) times v3's probability of a zero score [0.66];
    weights saved to submissions/blend42_weights.json,
s91_p_fire_defined: v3 probability that the reference has a fire station in the tract [0.56],
s85_t3_txfm05: already written (Texas FM/RM at weight 0.5; TX gets the lowest regional weight).
"""
import json

import numpy as np
import pandas as pd

from bbx import blend, config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
o = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v3_full.parquet"), on="GEOID", how="left")
sig = blend.scored_signals()
basis = [f for f in sig["file"] if not f.startswith("s16")]
b = blend.fit(basis, ridge=0.0, rules=False)
(config.SUBMISSIONS / "blend42_weights.json").write_text(
    json.dumps({"files": b.files, "weights": b.weights.tolist(), "ridge": 0.0}, indent=1), encoding="utf-8")

jobs = [
    ("s88_t3_transport_gap", o["transport"].fillna(0), 0.45, "structural v3 expected transport gap (component level)"),
    ("s89_p_transport_one", o["p_transport_one"], 0.10, "structural v3 probability that the transport gap equals 1"),
    ("s90_blend_x_pzero", b.prediction * o["p_zero"], 0.10, "42-signal blend times v3 probability of a zero score"),
    ("s91_p_fire_defined", o["p_fire_defined"], 0.15, "structural v3 probability that the reference has a fire station"),
]
for name, s, rho, purpose in jobs:
    path, exp = write_signal(df, np.asarray(s, float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

files = [j[0] for j in jobs] + ["s85_t3_txfm05"]
(config.SUBMISSIONS / "upload_2026-10-25.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
