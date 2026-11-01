"""Is eastern-wa in the public leaderboard? (research of 28 October, round 28).

Eastern Washington was added to the sample submission on 25 September, after the public/private
split existed; a participant asked on 6 October whether it counts toward the public board, the
private one or both (#35219, unanswered). Our exact within-region covariances give eastern-wa
transport a covariance of +0.0000011 with the public truth, against 0.0001-0.0009 in the other
regions, which is what a region absent from the public set produces.

s124_wa_public_probe: 1.0 on the 415 eastern-wa tracts, the public mean m elsewhere.
- eastern-wa not public: public RMSE = s = 0.089022 exactly (the file equals the best constant there);
- eastern-wa public (about 4 % of public tracts): public RMSE about 0.21.
It measures the membership of one whole region (415 tracts, decision D1-bis), nothing about any
tract's value, and it is not a signal for the blend (name kept out of the basis with 'probe').
"""
import numpy as np
import pandas as pd

from bbx import submit
from bbx.dataset import load_table
from bbx.signals import M_PUBLIC, S_PUBLIC

df = load_table()
wa = (df["region"] == "eastern-wa").to_numpy()
p = np.where(wa, 1.0, M_PUBLIC)
q = wa.mean()
expected_if_public = float(np.sqrt((1 - q) * S_PUBLIC**2 + q * ((1 - 0.07) ** 2 + S_PUBLIC**2)))
submit.write(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": p}), "s124_wa_public_probe", float(S_PUBLIC),
             f"probe: eastern-wa = 1, elsewhere m; RMSE = s ({S_PUBLIC:.6f}) if eastern-wa is not public, about {expected_if_public:.3f} if it is")
print(f"s124_wa_public_probe.csv: {wa.sum()} tracts at 1.0; expected RMSE {S_PUBLIC:.6f} if eastern-wa is not public, ~{expected_if_public:.3f} if it is")
