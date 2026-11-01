"""Validation blend for 26 October: the final recipe on the signals measured so far.

    python scripts/make_blend_check.py

Same recipe as scripts/make_finals.py f1 (every measured signal except blends, constants and the
two water-driven signals s07/s22; ridge 0.005; formula rule for the two empty water tracts), so
its public score checks the whole chain early (the last blend on the leaderboard, s16, had 8
signals) and gives Zindi a safety selection. Its name contains "blend", so bbx.blend leaves it
out of the measured basis.
"""
import json

import pandas as pd

from bbx import blend, config, submit
from bbx.dataset import load_table

EXCLUDED = {"s07_c_cbp.csv", "s22_no_ems_place.csv"}
RIDGE = 0.005

df = load_table()
files = [f for f in blend.scored_signals()["file"] if "blend" not in f and f not in EXCLUDED]
b = blend.fit(files, ridge=RIDGE, rules=True)
name = f"s111_blend{len(files)}_ridge0005"
submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": b.prediction}), name, b.expected_rmse,
             f"validation blend of {len(files)} measured signals (s07/s22 excluded), ridge {RIDGE}, formula rules")
(config.SUBMISSIONS / f"{name}_weights.json").write_text(
    json.dumps({"files": b.files, "weights": b.weights.tolist(), "ridge": RIDGE}, indent=1), encoding="utf-8")
print(f"{name}.csv: {len(files)} signals, rho {b.rho:.4f}, expected public RMSE {b.expected_rmse:.5f}, mean {b.prediction.mean():.4f}")
