"""First three submissions: two constants (target moments) and one strata-only prior.

S01  all 0.00 -> RMSE^2 = s^2 + m^2
S02  all 0.10 -> RMSE^2 = s^2 + (m - 0.1)^2      => m, s exactly (bbx.lb_algebra)
S03  rurality / tribal prior from strata only     => its correlation with the truth

Expected RMSEs are pre-registered with prior guesses m = 0.06, s = 0.09 (S03: rho = 0.3);
they are expectations, not inputs to any model.
"""
import numpy as np
import pandas as pd

from bbx import submit
from bbx.io import read_sample_submission, read_strata
from bbx.lb_algebra import expected_rmse

M_GUESS, S_GUESS = 0.06, 0.09


def zscore(x: pd.Series) -> pd.Series:
    x = x.astype(float)
    return (x - x.mean()) / x.std(ddof=0)


def main():
    base = read_sample_submission()[["GEOID", "region"]]

    for name, c in [("s01_const_000", 0.0), ("s02_const_010", 0.10)]:
        p = np.full(len(base), c)
        exp = float(np.sqrt(S_GUESS**2 + (M_GUESS - c) ** 2))
        submit.write(pd.DataFrame({"GEOID": base.GEOID, "coverage_gap_score": p}), name, exp,
                     f"constant {c:.2f}: measures target mean and sd")

    st = read_strata(columns=["GEOID", "ALAND", "pct_urban", "tribal_pct"])
    df = base.merge(st, on="GEOID", how="left")
    # Missing pct_urban (a handful of tracts) -> regional median; missing tribal -> 0.
    df["pct_urban"] = df["pct_urban"].fillna(df.groupby("region")["pct_urban"].transform("median"))
    df["tribal_pct"] = df["tribal_pct"].fillna(0.0)
    z = (zscore(1 - df["pct_urban"]) + zscore(np.log1p(df["ALAND"].clip(lower=0) / 1e6))
         + zscore(df["tribal_pct"])) / 3
    z = zscore(z)
    p = np.clip(M_GUESS + 0.3 * S_GUESS * z, 0, 1)
    exp = expected_rmse(p, M_GUESS, S_GUESS, 0.3)
    submit.write(pd.DataFrame({"GEOID": df.GEOID, "coverage_gap_score": p}), "s03_strata_rural_tribal",
                 exp, "strata-only prior: non-urban share, log land area, tribal share")


if __name__ == "__main__":
    main()
