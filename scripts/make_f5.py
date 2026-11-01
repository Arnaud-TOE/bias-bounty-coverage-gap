"""Replacement final after f2's public score (31 October, evening).

f2 (WEAK out, with s07/s22, ridge 0.005) scored 0.057507575 for 0.0550 expected. The public RMSE of a linear blend
is an exact function of its signals' public RMSEs and of which tracts are public; the miss is a composition shock
on q = B^2 - sum_i w_i p_i^2, about 3 sd (journal, 31/10). s07/s22 make f2 the most exposed recipe (the two water
tracts carry q of 0.26 and 0.23, against 0.05 at most for f3).

f5_blend_ridge002: WEAK and s07/s22 out (as f3), ridge 0.02. Least exposed to the public composition among the
candidates (corr of q with f2's 0.71), favoured by the corrected private simulation, between it and the formula
on the ridge. Expected public given f2's score about 0.0568 (one water tract public), private about 0.057.
Writes only f5 and its weights; f1-f3 are left untouched.
"""
import importlib.util
import json
from pathlib import Path

import pandas as pd

from bbx import config, submit
from bbx.dataset import load_table

RIDGE = 0.02
NAME = "f5_blend_ridge002"
_spec = importlib.util.spec_from_file_location("make_finals", Path(__file__).with_name("make_finals.py"))
mf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mf)

df = load_table()
files = [f for f in mf.basis_files() if f not in mf.EXCLUDED and f not in mf.WEAK]
pred, exp_pub, used_files, used_weights = mf.fit_without_wa(df, files, RIDGE)
print(f"{NAME}: {len(files)} signals, ridge {RIDGE}, expected public (algebra) {exp_pub:.5f}")
submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": pred}), NAME, exp_pub,
             f"final blend of {len(files)} measured signals, WEAK and s07/s22 out, ridge {RIDGE}, formula rules, "
             "four scored regions")
(config.SUBMISSIONS / f"final_{NAME}_weights.json").write_text(
    json.dumps({"files": list(used_files), "weights": [float(x) for x in used_weights], "ridge": RIDGE,
                "ridge_target": None, "fitted_on": "four scored regions"}, indent=1), encoding="utf-8")
